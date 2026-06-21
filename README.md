# DocMind AI

A production-grade **Document Q&A system** built with FastAPI, React (Vite), PostgreSQL, Redis, ChromaDB, and Groq LLM.

**Developed by:** [vijay_sathappan](https://github.com/vijay_sathappan)

---

## Architecture

```
User → React Frontend (Vite) → FastAPI Backend → PostgreSQL (metadata)
                                               → Redis (caching)
                                               → ChromaDB (vector search)
                                               → Groq LLM (answer generation)
```

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| API Framework | FastAPI | REST API with automatic docs |
| Database | PostgreSQL + SQLAlchemy | Document and chunk metadata |
| Cache | Redis | Cache LLM responses, document lookups |
| Vector Store | ChromaDB | Semantic search over document chunks |
| Embeddings | sentence-transformers (local) | Convert text to vectors, no API dependency |
| LLM | Groq (Llama 3.1) | Generate answers from retrieved context |
| Auth | JWT + bcrypt | Secure user authentication |
| Frontend | **React (Vite)** | Chat-style Q&A interface |
| Containerization | Docker + docker-compose | Consistent deployment |

## Features

- User registration and JWT-based authentication
- PDF upload with automatic text extraction and chunking
- Local embedding generation (no external API dependency for embeddings)
- Semantic search using ChromaDB vector store
- LLM-powered question answering grounded in document content
- Response caching to avoid redundant LLM calls
- Rate limiting on auth endpoints
- Chat-style React frontend with conversation history, typing indicators, and cache badges
- Drag-and-drop PDF upload
- Toast notifications

## How It Works (RAG Pipeline)

1. User uploads a PDF via the React frontend
2. Document is split into overlapping text chunks (1000 chars, 200 overlap)
3. Each chunk is converted into a vector embedding (locally, via sentence-transformers)
4. Embeddings are stored in ChromaDB
5. When a user asks a question, the question is embedded and compared against stored chunks
6. The most relevant chunks (top 5) are retrieved and sent to Groq LLM along with the question
7. The LLM generates an answer grounded in the retrieved context
8. Repeated questions are served from Redis cache (300s TTL)

## Getting Started

### Prerequisites
- Docker Desktop installed and running
- Node.js 18+ installed
- A free Groq API key ([console.groq.com](https://console.groq.com))

### Setup

```bash
git clone <your-repo-url>
cd doc-qa-system-main-1
```

Create a `.env` file:
```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/docqa
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REDIS_URL=redis://redis:6379
GROQ_API_KEY=your-groq-key
```

### Run the backend (Docker):
```bash
docker-compose up --build
```

### Run the React frontend (in a separate terminal):
```bash
cd frontend
npm install
npm run dev
```

- **API docs**: http://localhost:8000/docs
- **React frontend**: http://localhost:5173

> The old Streamlit interface is preserved as `streamlit_app.py` for reference, but the primary frontend is now React.

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /auth/register | No | Register new user |
| POST | /auth/login | No | Login, returns JWT |
| POST | /upload/pdf | Yes | Upload and process a PDF |
| POST | /query/ | Yes | Ask a question about a document |
| GET | /documents/{id} | Yes | Get document metadata (cached) |
| GET | /health | No | Health check |

## Project Structure

```
doc-qa-system-main-1/
├── app/
│   ├── main.py                  # App setup, middleware, CORS, routers
│   ├── database.py              # DB engine and session factory
│   ├── auth_utils.py            # JWT encode/decode, bcrypt hashing
│   ├── cache.py                 # Redis get/set/delete helpers
│   ├── middleware.py            # Global 500 and 404 handlers
│   ├── models/
│   │   ├── document.py          # Document + DocumentChunk ORM models
│   │   └── user.py              # User ORM model
│   ├── routes/
│   │   ├── auth.py              # /auth/register + /auth/login
│   │   ├── documents.py         # /documents/ CRUD (cache-first)
│   │   ├── upload.py            # /upload/pdf (chunk + embed)
│   │   └── query.py             # /query/ (RAG + Groq + cache)
│   └── services/
│       ├── document_processor.py  # PyPDF + LangChain chunking
│       └── embedding_service.py   # SentenceTransformer + ChromaDB
├── frontend/                    # React (Vite) frontend
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx             # React entry point
│       ├── App.jsx              # Root component + global state
│       ├── api.js               # Axios API layer
│       ├── index.css            # Design system
│       └── components/
│           ├── LoginPage.jsx    # Auth screen
│           ├── Sidebar.jsx      # Upload + controls
│           ├── ChatArea.jsx     # Chat interface
│           ├── ChatMessage.jsx  # Message bubble
│           ├── WelcomeScreen.jsx # Landing before doc load
│           └── Footer.jsx       # Developer credit
├── streamlit_app.py             # Legacy Streamlit frontend (reference)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
└── DEVELOPER_GUIDE.md           # Full developer guide with flow diagrams
```

## System Design Decisions

**Why local embeddings instead of an API?**
Avoids external network dependency and per-call costs. Runs entirely offline once the model is cached.

**Why ChromaDB?**
Lightweight embedded vector database — no separate server to manage.

**Why cache LLM responses?**
LLM calls are the slowest and most expensive part of the pipeline. MD5 hashing of the question+document pair gives consistent cache keys.

**Why JWT over sessions?**
Stateless auth scales horizontally without server-side session storage.

**Why React (Vite) over Streamlit?**
React gives full control over UI/UX — custom animations, drag-and-drop, typing indicators, toast notifications, and persistent state without page reruns.

**Why Docker?**
Eliminates environment inconsistencies. One command runs the full stack anywhere.

## Known Limitations
- Frontend manages active document per session (not persisted server-side)
- No async job queue for large document processing (synchronous for now)
- Single-document context per query (no cross-document search)
- Cache TTL is 300 seconds — tune in `cache.py`

## Developer

**vijay_sathappan** — [GitHub](https://github.com/vijay_sathappan)

See [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) for a full technical walkthrough with flow diagrams.