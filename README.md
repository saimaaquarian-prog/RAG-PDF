# RAG-PDF
# 📚 PDF RAG Assistant

A simple Retrieval-Augmented Generation (RAG) application that allows users to upload a PDF document and ask questions about its content.

The application extracts text from the PDF, divides the text into smaller chunks, generates semantic embeddings, stores the embeddings in a FAISS vector index, retrieves the most relevant chunks for a user's question, and uses **Groq GPT-OSS 120B** to generate an answer based only on the retrieved document context.

---

## 🚀 Features

* 📄 Upload PDF documents
* 🔍 Extract text from PDF files
* ✂️ Split documents into overlapping chunks
* 🧠 Generate semantic embeddings using Sentence Transformers
* 🗂️ Store embeddings in FAISS
* 🔎 Perform semantic similarity search
* 🤖 Generate answers using Groq GPT-OSS 120B
* 💬 Chat-style question answering interface
* 📑 Display retrieved document sources
* 📊 Show similarity scores
* 🗑️ Clear the current document and chat
* ☁️ Deployable on Streamlit Community Cloud

---

# 🏗️ System Architecture

```text
                    ┌──────────────────────────┐
                    │        User              │
                    │                          │
                    │ Upload PDF + Ask Query   │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      Streamlit UI        │
                    │        app.py             │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────┴─────────────┐
                    │                          │
                    ▼                          ▼
          ┌──────────────────┐       ┌──────────────────┐
          │   PDF Processing │       │  User Question   │
          └────────┬─────────┘       └────────┬─────────┘
                   │                          │
                   ▼                          ▼
          ┌──────────────────┐       ┌──────────────────┐
          │     pypdf        │       │ Sentence         │
          │ Text Extraction  │       │ Transformer      │
          └────────┬─────────┘       │ Embedding        │
                   │                 └────────┬─────────┘
                   ▼                          │
          ┌──────────────────┐                │
          │ Text Chunking    │                │
          │ 900 words        │                │
          │ 150 overlap      │                │
          └────────┬─────────┘                │
                   │                          │
                   ▼                          ▼
          ┌────────────────────────────────────────────┐
          │              FAISS Vector Index            │
          │        Semantic Similarity Search           │
          └────────────────────┬───────────────────────┘
                               │
                               ▼
                    ┌──────────────────────────┐
                    │ Top-K Relevant Chunks    │
                    │       Top K = 5           │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      Groq API            │
                    │   GPT-OSS 120B           │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      Final Answer        │
                    │                          │
                    │ Based on PDF Context     │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      Streamlit UI        │
                    │ Answer + Sources         │
                    └──────────────────────────┘
```

---

# 🔄 RAG Pipeline

The application follows a two-stage RAG pipeline.

## Stage 1 — Document Ingestion

```text
PDF
 │
 ▼
Text Extraction
 │
 ▼
Text Cleaning
 │
 ▼
Chunking
 │
 ▼
Embedding Generation
 │
 ▼
FAISS Vector Index
```

### Step 1: PDF Upload

The user uploads a PDF through the Streamlit interface.

The application accepts:

```text
.pdf
```

---

### Step 2: Text Extraction

The application uses `pypdf` to extract text from each PDF page.

Page information is preserved in the extracted text:

```text
[Page 1]
Document content...

[Page 2]
More document content...
```

This allows the application to provide page information when possible.

---

### Step 3: Text Chunking

Large documents cannot be sent directly to the language model.

Therefore, the extracted text is divided into smaller chunks.

Current configuration:

```text
Chunk size   = 900 words
Overlap      = 150 words
```

The overlap helps preserve context between neighboring chunks.

Example:

```text
Chunk 1:
Words 1 → 900

Chunk 2:
Words 751 → 1650

Chunk 3:
Words 1501 → 2400
```

---

# 🧠 Embedding Generation

Each text chunk is converted into a numerical vector using:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Conceptually:

```text
Text Chunk
    │
    ▼
Embedding Model
    │
    ▼
Numerical Vector
```

For example:

```text
"Machine learning is a branch of AI..."
                  │
                  ▼
       [0.12, -0.45, 0.78, ...]
```

These vectors represent the semantic meaning of the text.

---

# 🗂️ FAISS Vector Database

The generated embeddings are stored in a FAISS index.

The application uses:

```text
FAISS IndexFlatIP
```

The embeddings are normalized before indexing, so inner-product similarity can be used as a cosine-similarity-style semantic search.

Architecture:

```text
PDF Chunks
    │
    ▼
Embeddings
    │
    ▼
FAISS
    │
    ▼
Vector Index
```

The FAISS index is kept in memory during the Streamlit session.

---

# 🔎 Query Retrieval

When the user asks a question:

```text
User Question
      │
      ▼
Question Embedding
      │
      ▼
FAISS Similarity Search
      │
      ▼
Top 5 Relevant Chunks
```

The application retrieves the five most relevant chunks.

Current configuration:

```text
TOP_K = 5
```

---

# 🤖 LLM Generation

The retrieved chunks are sent to the Groq API together with the user's question.

The configured model is:

```text
openai/gpt-oss-120b
```

The LLM receives:

```text
System Instructions
        +
Retrieved PDF Context
        +
User Question
```

The system prompt instructs the model to:

* Use only the retrieved PDF context
* Avoid inventing information
* Say when the answer cannot be found
* Provide page information when possible

---

# 💬 Final Response

The generated answer is displayed in the Streamlit chat interface.

The application also provides:

```text
🔎 View Retrieved Sources
```

This allows the user to inspect the document chunks used to generate the answer.

---

# 🛠️ Technology Stack

| Component            | Technology                |
| -------------------- | ------------------------- |
| Programming Language | Python                    |
| Frontend             | Streamlit                 |
| PDF Processing       | pypdf                     |
| Embedding Model      | all-MiniLM-L6-v2          |
| Vector Search        | FAISS                     |
| LLM API              | Groq                      |
| LLM                  | GPT-OSS 120B              |
| Deployment           | Streamlit Community Cloud |
| Source Control       | GitHub                    |

---

# 📁 Project Structure

```text
pdf-rag-assistant/
│
├── app.py
├── requirements.txt
└── README.md
```

### `app.py`

Main application containing:

* Streamlit interface
* PDF processing
* Text chunking
* Embedding generation
* FAISS indexing
* Semantic retrieval
* Groq LLM interaction
* Chat history
* Source display

### `requirements.txt`

Contains all Python dependencies required by the application.

### `README.md`

Project documentation and setup instructions.

---

# ⚙️ Configuration

The main RAG parameters are:

```python
LLM_MODEL = "openai/gpt-oss-120b"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 900

CHUNK_OVERLAP = 150

TOP_K = 5
```

These parameters can be adjusted depending on document size and retrieval requirements.

---

# 🔐 API Key Configuration

The application requires a Groq API key.

The expected secret name is:

```text
GROQ_API_KEY
```

Do **not** place the API key directly inside `app.py`.

For Streamlit Cloud, add the key through the application's Secrets configuration.

Example:

```toml
GROQ_API_KEY = "your_groq_api_key"
```

Never upload your real API key to GitHub.

---

# 💻 Local Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/pdf-rag-assistant.git
```

Move into the project directory:

```bash
cd pdf-rag-assistant
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the environment.

### Windows

```bash
venv\Scripts\activate
```

### macOS/Linux

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set your API key.

### Windows PowerShell

```powershell
$env:GROQ_API_KEY="your_api_key"
```

Run the application:

```bash
streamlit run app.py
```

The application will open in your browser.

---

# ☁️ Streamlit Cloud Deployment

## Step 1 — Create GitHub Repository

Create a repository named:

```text
pdf-rag-assistant
```

Upload:

```text
app.py
requirements.txt
README.md
```

---

## Step 2 — Connect Streamlit

Open Streamlit Community Cloud and connect your GitHub account.

Create a new application and select:

```text
Repository: pdf-rag-assistant
Branch: main
Main file: app.py
```

---

## Step 3 — Add Secret

Open the application's settings and add:

```toml
GROQ_API_KEY = "your_groq_api_key"
```

Then deploy the application.

---

# 📌 Important Notes

### Scanned PDFs

This application currently works best with text-based PDFs.

If the PDF contains only scanned images, `pypdf` may not be able to extract the text.

OCR would be required for scanned documents.

### Vector Storage

FAISS is currently used as an in-memory vector index.

The index is created when the PDF is processed and is not stored permanently on the server.

### Embedding Model

The application uses:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The embedding model automatically handles the tokenization required for generating embeddings.

---

# 🔐 RAG Grounding

The application is designed to reduce hallucination by instructing the LLM to answer using the retrieved PDF context.

The intended flow is:

```text
Question
   ↓
Semantic Retrieval
   ↓
Relevant PDF Chunks
   ↓
LLM
   ↓
Grounded Answer
```

If relevant information is not found in the retrieved context, the assistant is instructed to respond:

```text
I could not find that information in the uploaded PDF.
```

---

# 🎯 Use Cases

This application can be used for:

* 📚 Research papers
* 🎓 Study materials
* 📖 Books and notes
* 📄 Technical documentation
* 🧪 Scientific documents
* 🏢 Reports
* 📑 Academic PDFs
* 📝 Project documentation

---

# 🚀 Future Improvements

Possible future improvements include:

* OCR support for scanned PDFs
* Multiple PDF uploads
* Persistent FAISS storage
* Metadata-based filtering
* Better chunking strategies
* Hybrid keyword + semantic retrieval
* Re-ranking
* Conversation memory
* Citation generation
* PDF page previews
* Document summarization
* Multi-document RAG
* Authentication
* Evaluation of retrieval quality
* RAGAS-based RAG evaluation

---

# 📊 High-Level Architecture

```text
                  PDF RAG ASSISTANT
                         │
        ┌────────────────┴────────────────┐
        │                                 │
   DOCUMENT FLOW                     QUERY FLOW
        │                                 │
        ▼                                 ▼
    Upload PDF                       User Question
        │                                 │
        ▼                                 ▼
   Extract Text                     Create Embedding
        │                                 │
        ▼                                 │
   Create Chunks                          │
        │                                 │
        ▼                                 │
 Generate Embeddings                      │
        │                                 │
        ▼                                 ▼
      FAISS ◄──────────── Similarity Search
        │
        ▼
  Top-K Relevant Chunks
        │
        └───────────────┐
                        ▼
                 Groq GPT-OSS 120B
                        │
                        ▼
                  Final Answer
                        │
                        ▼
                 Streamlit Chat UI
```

---

# 👩‍💻 Author

**Saima Ashraf**

MS Computer Science | Machine Learning | Generative AI | Agentic AI

---

# ⭐ Project Goal

The goal of this project is to demonstrate a practical end-to-end **Retrieval-Augmented Generation (RAG)** system using open-source embedding technology, FAISS vector search, a Groq-hosted LLM, and Streamlit.

This project demonstrates the complete pipeline:

```text
Document
   ↓
Text Extraction
   ↓
Chunking
   ↓
Embeddings
   ↓
Vector Search
   ↓
Context Retrieval
   ↓
LLM Generation
   ↓
Grounded Answer
```

