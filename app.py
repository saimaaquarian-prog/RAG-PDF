import os

import faiss
import streamlit as st
from groq import Groq
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

APP_TITLE = "PDF RAG Assistant"
LLM_MODEL = "openai/gpt-oss-120b"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
TOP_K = 5

st.set_page_config(page_title=APP_TITLE, page_icon="📚", layout="wide")

@st.cache_resource
def load_embedding_model():
    return SentenceTransformer(EMBEDDING_MODEL)

def get_groq_api_key():
    try:
        key = st.secrets.get("GROQ_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY")

def extract_pdf_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    page_texts = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            page_texts.append(f"[Page {page_number}]\n{text.strip()}")
    return "\n\n".join(page_texts)

def create_chunks(text):
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + CHUNK_SIZE, len(words))
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(words):
            break
        start = end - CHUNK_OVERLAP
    return chunks

def create_faiss_index(chunks, embedding_model):
    embeddings = embedding_model.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).astype("float32")
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return index

def retrieve_chunks(query, chunks, index, embedding_model, top_k=TOP_K):
    query_embedding = embedding_model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).astype("float32")
    k = min(top_k, len(chunks))
    scores, indices = index.search(query_embedding, k)
    return [
        {"text": chunks[int(i)], "score": float(score)}
        for score, i in zip(scores[0], indices[0])
        if i >= 0
    ]

def generate_answer(query, retrieved_chunks, client):
    context = "\n\n".join(
        f"--- Retrieved Context {i} ---\n{item['text']}"
        for i, item in enumerate(retrieved_chunks, start=1)
    )
    system_prompt = """You are a helpful PDF question-answering assistant.
Use ONLY the retrieved context from the uploaded PDF.
Do not invent information. If the answer is not supported by the context, say:
'I could not find that information in the uploaded PDF.'
Keep the answer clear and useful. When possible, mention the page number shown in the context."""
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Retrieved PDF context:\n\n{context}\n\nUser question:\n{query}"},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content

for key, default in [("chunks", []), ("faiss_index", None), ("file_name", None), ("chat_history", [])]:
    if key not in st.session_state:
        st.session_state[key] = default

st.title("📚 PDF RAG Assistant")
st.markdown("Upload a PDF and ask questions using semantic retrieval and Groq GPT-OSS 120B.")

with st.sidebar:
    st.header("⚙️ RAG Configuration")
    st.write(f"**LLM:** `{LLM_MODEL}`")
    st.write(f"**Embedding:** `{EMBEDDING_MODEL}`")
    st.write(f"**Chunk size:** `{CHUNK_SIZE}` words")
    st.write(f"**Chunk overlap:** `{CHUNK_OVERLAP}` words")
    st.write(f"**Top-K:** `{TOP_K}`")
    if st.button("🗑️ Clear"):
        st.session_state.chunks = []
        st.session_state.faiss_index = None
        st.session_state.file_name = None
        st.session_state.chat_history = []
        st.rerun()

api_key = get_groq_api_key()
if not api_key:
    st.warning("GROQ_API_KEY is not configured. Add it to Streamlit Secrets.")

uploaded_file = st.file_uploader("📄 Upload your PDF", type=["pdf"])

if uploaded_file:
    if st.session_state.file_name != uploaded_file.name:
        with st.spinner("Extracting PDF, creating chunks, generating embeddings, and building FAISS..."):
            try:
                text = extract_pdf_text(uploaded_file)
                if not text.strip():
                    st.error("No text could be extracted. Scanned PDFs require OCR support.")
                    st.stop()
                chunks = create_chunks(text)
                embedding_model = load_embedding_model()
                index = create_faiss_index(chunks, embedding_model)
                st.session_state.chunks = chunks
                st.session_state.faiss_index = index
                st.session_state.file_name = uploaded_file.name
                st.session_state.chat_history = []
            except Exception as e:
                st.error(f"PDF processing failed: {e}")
                st.stop()

    st.success(f"✅ `{uploaded_file.name}` processed successfully. Created **{len(st.session_state.chunks)} chunks**.")

    if api_key:
        client = Groq(api_key=api_key)
        st.subheader("💬 Ask Questions")
        question = st.chat_input("Ask something about your PDF...")
        if question:
            st.session_state.chat_history.append({"role": "user", "content": question})
            embedding_model = load_embedding_model()
            with st.spinner("🔎 Searching the document..."):
                retrieved = retrieve_chunks(question, st.session_state.chunks, st.session_state.faiss_index, embedding_model)
            with st.spinner("🤖 Generating answer..."):
                try:
                    answer = generate_answer(question, retrieved, client)
                    st.session_state.chat_history.append({"role": "assistant", "content": answer, "sources": retrieved})
                except Exception as e:
                    st.session_state.chat_history.append({"role": "assistant", "content": f"Groq API error: {e}"})

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and message.get("sources"):
                    with st.expander("🔎 View Retrieved Sources"):
                        for i, source in enumerate(message["sources"], start=1):
                            st.markdown(f"**Source {i} — similarity {source['score']:.3f}**")
                            st.write(source["text"])
                            st.divider()
    else:
        st.info("Add GROQ_API_KEY to Streamlit Secrets to enable question answering.")
else:
    st.info("👆 Upload a PDF to begin.")
