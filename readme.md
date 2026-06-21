# DocMind AI — Project Manual & Deployment Guide

Welcome to the **DocMind AI** Project Manual. This document contains the complete system architecture, RAG pipelines, authentication flows, developer guides, environment variable references, and the cloud deployment guide for hosting on Vercel.

Find the Live Demo: https://doc-qa-systems.vercel.app
---

## Table of Contents
1. [System Architecture Overview](#1-system-architecture-overview)
2. [RAG Pipeline Flow](#2-rag-pipeline-flow)
3. [Authentication Flow (Passwordless OTP)](#3-authentication-flow-passwordless-otp)
4. [PDF Upload & Embedding Flow](#4-pdf-upload--embedding-flow)
5. [Query & Caching Pipeline](#5-query--caching-pipeline)
6. [Environment Variables Reference](#6-environment-variables-reference)
7. [Developer Local Setup Guide](#7-developer-local-setup-guide)
8. [Vercel Cloud Deployment Guide](#8-vercel-cloud-deployment-guide)

---

## 1. System Architecture Overview

DocMind AI is structured as a decoupled monorepo containing a **React (Vite) Frontend** and a **FastAPI Backend**, supported by relational metadata storage, vector storage, an local caching layer, and an LLM client.

```mermaid
graph TB
    subgraph Frontend["React Frontend (Vite — port 5173)"]
        LP[LoginPage]
        SB[Sidebar]
        CA[ChatArea]
        WS[WelcomeScreen]
    end

    subgraph Backend["FastAPI Backend (port 8000)"]
        AUTH["/auth/login\n/auth/register\n/auth/me"]
        UPLOAD["/upload/pdf"]
        QUERY["/query/"]
        DOCS["/documents/{id}"]
    end

    subgraph Storage["Storage & Services"]
        DB_ST[(SQLite / PostgreSQL\nuser & doc metadata)]
        REDIS[(Redis\nquery cache)]
        CHROMA[(ChromaDB\nvector embeddings)]
        GROQ[Groq Cloud API\nllama-3.1-8b-instant]
        ST["SentenceTransformer\nall-MiniLM-L6-v2\n(local)"]
    end

    LP -->|POST /auth/...| AUTH
    SB -->|POST /upload/pdf| UPLOAD
    CA -->|POST /query/| QUERY
    SB -->|GET /documents/id| DOCS
    AUTH -->|GET /auth/me| DB_ST

    AUTH --> DB_ST
    UPLOAD --> DB_ST
    UPLOAD --> ST
    ST --> CHROMA
    QUERY --> REDIS
    QUERY --> CHROMA
    QUERY --> GROQ
    QUERY --> DB_ST
    DOCS --> REDIS
    DOCS --> DB_ST
```

---

## 2. RAG Pipeline Flow

This flowchart describes the semantic search retrieval and synthesis pipeline:

```mermaid
flowchart TD
    A([User asks a question]) --> B{Cache hit?}
    B -- Yes --> C[Return cached response\n⚡ from_cache = true]
    B -- No --> D[Embed query\nvia SentenceTransformer]
    D --> E[Search ChromaDB\ntop-5 cosine matches]
    E --> F{Matches found?}
    F -- No --> G[Return 404\nNo relevant content]
    F -- Yes --> H[Filter matches\nscore >= 0.35]
    H --> I{Any match meets threshold?}
    I -- No --> J[Fallback: Use top-1 chunk]
    I -- Yes --> K[Retrieve matching chunks\n1 to 5 sources]
    J --> L[Build RAG Prompt]
    K --> L
    L --> M[Send to Groq API\nllama-3.1-8b-instant]
    M --> N[Increment user total token count]
    N --> O[Save result in cache\nTTL = 300s]
    O --> P([Return answer to user\nfrom_cache = false])

    style C fill:#0f4,color:#000
    style G fill:#f44,color:#fff
    style P fill:#44f,color:#fff
```

---

## 3. Authentication Flow (Passwordless OTP)

DocMind AI uses secure passwordless authentication. Verification codes are stored in Redis or fallback in-memory cache, and accounts are automatically provisioned on the first login:

```mermaid
sequenceDiagram
    actor U as User (React)
    participant LP as LoginPage.jsx
    participant API as FastAPI /auth
    participant REDIS as Redis / Memory
    participant EMAIL as SMTP / Console
    participant DB as SQLite / Postgres

    U->>LP: Enter email → click "Send Login Code"
    LP->>API: POST /auth/send-otp { email }
    API->>API: Generate random 6-digit OTP
    API->>REDIS: Store OTP with 300s TTL (otp:email)
    API->>EMAIL: Send OTP template (background task)
    API-->>LP: { message, email, expires_in }
    LP->>U: Show OTP boxes and countdown

    U->>LP: Enter 6-digit OTP code
    LP->>API: POST /auth/verify-otp { email, otp }
    API->>REDIS: Retrieve stored OTP

    alt OTP matches
        API->>REDIS: Delete OTP (one-time use)
        API->>DB: Check if user exists
        alt User does not exist
            API->>DB: Create User record (auto-register)
        end
        API->>API: Sign JWT token (sub: user.id)
        API-->>LP: { access_token, email, is_new_user }
        LP->>U: Authenticate session and redirect
    else OTP mismatch / expired
        API-->>LP: 401 Unauthorized
        LP->>U: Show "Incorrect or expired code" error
    end
```

---

## 4. PDF Upload & Embedding Flow

```mermaid
flowchart TD
    A([User drops PDF]) --> B[POST /upload/pdf\nmultipart/form-data]
    B --> C{File validation}
    C -- Invalid --> D[400 Bad Request]
    C -- Valid --> E[Save PDF to uploads/]
    E --> F[Create Document record in DB]
    F --> G[Extract & chunk PDF text\nsize=1000, overlap=200]
    G --> H[Generate Local embeddings\nSentenceTransformer]
    H --> I[Add vectors to ChromaDB\ncollection: doc_id]
    I --> J[Save metadata to DB]
    J --> K[Remove temporary PDF file]
    K --> L([Return document_id\nchunks_created])

    style D fill:#f44,color:#fff
    style L fill:#0f4,color:#000
```

---

## 5. Query & Caching Pipeline

All user queries are routed through a lookup chain to maximize efficiency:

1. **Cache Validation**: Generate MD5 hash of the normalized question: `query:{document_id}:{md5(question.lower().strip())}`. Check Redis/Memory cache.
2. **Cache Hit**: Returns answer instantly. The backend dynamically queries the DB for the current user's profile and overrides the cached response's `total_tokens_consumed` field, reporting `tokens_used: 0` for the current call.
3. **Cache Miss**: Computes cosine similarity, retrieves top-matching chunks, filters by semantic score threshold (`>= 0.35`), fetches from Groq API, updates the user's total token count in the DB, and saves the new answer to the cache.

---

## 6. Environment Variables Reference

A `.env` file must be placed in the project root folder. Refer to the table below for configuration details:

| Variable | Description | Example / Default | Required in Production |
|---|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./docqa.db` | Yes (Use Postgres on Vercel) |
| `SECRET_KEY` | Key to sign JWT access tokens | `super-secret-key-change-this` | Yes |
| `ALGORITHM` | JWT hashing algorithm | `HS256` | No (defaults to HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token validity timeframe | `1440` (24 hours) | No |
| `REDIS_URL` | Redis URL for query/OTP cache | `redis://localhost:6379` | Yes (Use Upstash on Vercel) |
| `GROQ_API_KEY` | API Key for Groq Cloud completions | `gsk_...` | Yes |
| `SMTP_HOST` | SMTP server for OTP emails | `smtp.gmail.com` | No (Prints to terminal if empty) |
| `SMTP_PORT` | SMTP port | `587` | No |
| `SMTP_USER` | SMTP username | `your-email@gmail.com` | No |
| `SMTP_PASS` | SMTP email-specific app password | `xxxx xxxx xxxx xxxx` | No |

---

## 7. Developer Local Setup Guide

Follow these steps to spin up the application in a local developer environment:

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (Optional — for Redis/Postgres)

### Step 1: Clone and Configure Environment
1. Clone the repository and navigate to the project directory.
2. Create a `.env` file in the root based on the table in Section 6.

### Step 2: Install and Run Backend
1. **Initialize Virtual Environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate   # Windows
   source venv/bin/activate  # macOS/Linux
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Pre-Cache Embedding Model**:
   Download the SentenceTransformer weights locally:
   ```bash
   python download_model.py
   ```
4. **Launch FastAPI server**:
   ```bash
   py -m uvicorn app.main:app --reload
   # Runs at: http://localhost:8000
   # Swagger UI: http://localhost:8000/docs
   ```
   *Note: If no SMTP variables are set in `.env`, verify codes (OTPs) will print directly to the backend uvicorn terminal window for testing.*

### Step 3: Install and Run Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm modules:
   ```bash
   npm install
   ```
3. Launch React dev server:
   ```bash
   npm run dev
   # Runs at: http://localhost:5173
   ```

---

## 8. Vercel Cloud Deployment Guide

Vercel hosts static frontend pages and Serverless Python API routes. Deploying DocMind AI requires moving away from local filesystems.

### ⚠️ Critical Serverless Constraints on Vercel
Because serverless functions have ephemeral, read-only filesystems:
1. **SQLite Database (`docqa.db`) is read-only**: Writes will fail.
2. **ChromaDB (`chroma_data/`) is read-only**: Adding document vectors will fail.
3. **Local Embedding Models (`model_cache/`)**: Loading local SentenceTransformers weights during function calls will trigger cold-start timeouts on Vercel's free tier.

### Monorepo Cloud Migration Steps

#### 1. Setup Remote Database & Cache
- **Database**: Spin up a managed PostgreSQL database (e.g., Supabase, Neon, or Vercel Postgres). Update `DATABASE_URL` in Vercel to:
  `postgresql://user:password@hostname:5432/dbname`
- **Cache**: Spin up a remote Redis instance (e.g., Upstash Redis). Update `REDIS_URL` in Vercel to:
  `rediss://default:password@hostname:port`

#### 2. Adapt ChromaDB & Embeddings for Serverless
For production deployments on Vercel:
- **Embeddings API**: Replace local `SentenceTransformer` with a serverless-friendly API (e.g. Hugging Face Inference API or OpenAI Embeddings) to prevent cold starts.
- **Hosted Vector DB**: Replace local Chroma `PersistentClient` with a hosted client (`HttpClient`) connecting to a Chroma Cloud cluster or migrate Chroma backend to a remote vector database (such as Pinecone orpgvector).

#### 3. Deployment Configuration (`vercel.json`)
The `vercel.json` file in the root matches frontend builds and routes FastAPI server requests:
- Root paths redirect to `frontend/dist/index.html` (Vite static output).
- Backend routes (`/api`, `/auth`, `/query`, `/documents`, `/upload`, `/health`) route to `api/index.py` (which runs FastAPI).

#### 4. Step-by-Step Vercel Deployment
1. Log in to Vercel and create a **New Project**.
2. Link your Git repository.
3. Configure the **Build & Development Settings**:
   - Vercel will automatically discover the root configurations. Keep standard monorepo defaults.
4. Add the following **Environment Variables** in Vercel settings:
   - `DATABASE_URL` (Remote PostgreSQL URL)
   - `REDIS_URL` (Remote Redis URL)
   - `GROQ_API_KEY` (Your Groq API key)
   - `SECRET_KEY` (Your JWT secret key)
   - `SMTP_USER` / `SMTP_PASS` (Optional, for OTP email delivery)
5. Click **Deploy**. Vercel will build the React bundle, launch serverless Python environments, and provide your live application link!
