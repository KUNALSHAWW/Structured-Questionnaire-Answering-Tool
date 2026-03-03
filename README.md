# Structured Questionnaire Answering Tool

> **Almabase GTM Engineering Internship — Home Assignment**

A full-stack RAG (Retrieval-Augmented Generation) application that automatically answers questionnaires using uploaded reference documents. Every answer is grounded in source material with explicit citations and evidence snippets — questions without supporting evidence return `Not found in references.`

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![React](https://img.shields.io/badge/React-19-61DAFB)
![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-orange)

---

## Demo Flow

1. **Register/Login** → JWT-authenticated session
2. **Upload** questionnaire (PDF/XLSX/TXT) + reference documents (PDF/TXT/CSV/DOCX)
3. **Build Index** → passages are split, embedded, and indexed in FAISS
4. **Generate Answers** → each question is matched to relevant passages and answered with citations
5. **Review** → confidence scores, evidence snippets, edit or regenerate individual answers
6. **Export** → download as XLSX or PDF

---

## Features

| Feature | Description |
|---|---|
| **JWT Auth** | Secure register/login with bcrypt password hashing |
| **File Upload & Parsing** | Automatically extract questions from PDF/XLSX/TXT questionnaires |
| **RAG Pipeline** | Passage splitting → embedding → FAISS retrieval → grounded generation |
| **Anti-Hallucination** | Strict prompt enforcement + similarity threshold gating |
| **Citations** | Every answer includes `[filename \| page/para]` source references |
| **Evidence Snippets** | Verbatim quotes from source passages shown alongside answers |
| **Confidence Scores** | 0–100% score derived from retrieval similarity with calibrated mapping |
| **Edit & Regenerate** | Manually edit any answer or regenerate from the same passages |
| **XLSX/PDF Export** | Download all answers preserving question order and formatting |
| **Smart Extractive Fallback** | Keyword-scored sentence extraction when no LLM API key is set |
| **Loading States** | Animated spinners during index building, generation, and regeneration |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+ · FastAPI · SQLAlchemy · SQLite |
| **Frontend** | React 19 · Vite 6 · Vanilla CSS (custom design system) |
| **Vector Search** | FAISS (faiss-cpu) · cosine similarity via normalized L2 |
| **Embeddings** | sentence-transformers `all-MiniLM-L6-v2` (default, local) or OpenAI `text-embedding-3-small` |
| **Generation** | OpenAI `gpt-4o-mini` (if API key set) or smart extractive fallback |
| **Auth** | JWT (python-jose) + bcrypt |
| **Export** | openpyxl (XLSX) · reportlab (PDF) |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+

### 1. Clone & Install

```bash
git clone https://github.com/KUNALSHAWW/Structured-Questionnaire-Answering-Tool.git
cd Structured-Questionnaire-Answering-Tool

# Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Configure Environment

```bash
cd backend
cp .env.example .env
# Edit .env — set JWT_SECRET (required)
# Optionally set OPENAI_API_KEY for LLM-powered answers
```

### 3. Run

**Terminal 1 — Backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open **http://localhost:3000**

### 4. Try It Out

1. Register a new account
2. Upload `sample_data/questionnaire.txt`
3. Upload all 5 reference documents from `sample_data/`
4. Click **Build Index**
5. Click **Generate Answers**
6. Review answers with citations, confidence scores, and evidence
7. Export as XLSX or PDF

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `JWT_SECRET` | **Yes** | `dev-secret-change-me` | Secret key for JWT token signing. **Must be changed in production.** |
| `ENV` | No | `development` | Set to `production` to enforce JWT_SECRET |
| `OPENAI_API_KEY` | No | — | Enables OpenAI embeddings + LLM generation |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000,http://localhost:5173` | Comma-separated CORS origins |
| `MAX_UPLOAD_BYTES` | No | `52428800` (50 MB) | Max upload file size in bytes |
| `MIN_PASSWORD_LENGTH` | No | `8` | Minimum password length |
| `JWT_EXPIRY_MINUTES` | No | `60` | JWT token lifetime |
| `USE_BACKGROUND_JOBS` | No | `false` | Enable async job queue for generation |
| `RETRIEVAL_THRESHOLD` | No | `0.20` | Minimum similarity score to consider a passage relevant |
| `RETRIEVAL_TOP_K` | No | `5` | Number of passages to retrieve per question |
| `PASSAGE_TOKEN_SIZE` | No | `200` | Token count per passage chunk |
| `PASSAGE_OVERLAP` | No | `40` | Overlapping tokens between adjacent passages |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check (status, version, timestamp) |
| `POST` | `/api/auth/register` | Register new user |
| `POST` | `/api/auth/login` | Login → JWT token |
| `POST` | `/api/uploads/questionnaire` | Upload questionnaire file |
| `POST` | `/api/uploads/reference` | Upload reference document |
| `GET` | `/api/uploads/questionnaires` | List questionnaires |
| `GET` | `/api/uploads/references` | List references |
| `GET` | `/api/uploads/questionnaire/:id/questions` | Get parsed questions |
| `POST` | `/api/index/build` | Build FAISS index from references |
| `POST` | `/api/generate` | Generate answers for a questionnaire |
| `GET` | `/api/jobs/:job_id` | Poll background job status |
| `POST` | `/api/regenerate/:question_id` | Regenerate one answer |
| `PUT` | `/api/answers/:answer_id` | Edit an answer |
| `GET` | `/api/runs` | List generation runs |
| `GET` | `/api/runs/:run_id` | Get run with all answers |
| `GET` | `/api/export/:run_id?format=xlsx\|pdf` | Export answers |
| `GET` | `/api/references/:id/snippet` | Get passage snippet |

---

## Testing

```bash
# Unit + security tests
python -m pytest tests/ -v

# End-to-end test (register → upload → index → generate → export)
python e2e_test.py
```

### Security Tests (`tests/test_security_isolation.py`)
- Auth validation (email format, password length)
- Per-user FAISS index isolation
- Prompt injection sanitisation
- Citation verification
- CORS configuration
- Health endpoint schema

---

## Sample Data

The `sample_data/` directory contains a fictional company **"NovaTech Solutions"** with:

| File | Content |
|---|---|
| `questionnaire.txt` | 10 questions covering company overview, policies, HR, DR, ESG |
| `company_overview.txt` | Company description, revenue ($78.4M), products, clients |
| `security_policy.txt` | Data privacy, retention policy, ISO 27001 certification |
| `hr_report.txt` | Headcount (342 FTE), turnover rate, remote work policy |
| `disaster_recovery.txt` | DR/BCP plan with RTO/RPO targets, testing schedule |
| `esg_report.txt` | Environmental commitments, carbon goals, governance |

---

## Architecture

```
┌───────────────┐    ┌───────────────────────────────────────────┐
│   React UI    │──▷│  FastAPI Backend                          │ 
│  (Vite, :3000)│    │                                          │ 
└───────────────┘    │   ┌─────────┐  ┌──────────┐  ┌─────────┐ │
                     │   │ Upload  │→ │ Splitter │→ │ Embed + │ │
                     │   │ & Parse │  │ (200 tok)│  │  FAISS  │ │
                     │   └─────────┘  └──────────┘  └─────┬───┘ │
                     │                                    │     │
                     │  ┌─────────┐  ┌───────────────┐    │     │
                     │  │Question │→ │ Retrieve Top-K│◁──┘      │
                     │  └─────────┘  └──────┬────────┘          │
                     │                      │                   │
                     │              ┌───────▽────────┐         │
                     │              │ LLM Generate   │         │
                     │              │ or Extractive  │         │
                     │              │ Fallback       │         │
                     │              └───────┬────────┘         │
                     │                      │                  │
                     │              ┌───────▽────────┐        │
                     │              │ Answer + Cite  │         │
                     │              │ + Evidence     │         │
                     │              └────────────────┘         │
                     └─────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| **Smart extractive fallback** | Keyword-scored sentence selection from top passages — works offline with zero API cost |
| **Calibrated confidence scoring** | Piecewise similarity→confidence mapping tuned for MiniLM output ranges |
| **Header stripping** | Document titles and metadata lines are filtered from passage text before answering |
| **Low threshold (0.20)** | Prevents false negatives on relevant but semantically distant queries |
| **SQLite** | Zero-config for reviewers; swap to Postgres for production |
| **FAISS flat index** | Exact search — fast enough for <10K passages |
| **200-token passages** | More granular retrieval than larger chunks; better sentence-level matching |

### Anti-Hallucination Strategy

1. **Strict system prompt** — LLM instructed to use ONLY provided passages
2. **Similarity threshold gate** — below threshold → `Not found in references.`
3. **Mandatory citations** — prompt enforces `[filename | page/para]` format
4. **Evidence snippets** — verbatim source quotes returned with every answer
5. **Extractive fallback** — no LLM means no hallucination possible

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point, CORS, health, logging
│   │   ├── config.py                  # Environment configuration
│   │   ├── database.py                # SQLAlchemy engine & session
│   │   ├── auth_utils.py              # Shared ownership verification helpers
│   │   ├── models/models.py           # ORM models (User, Question, Answer, Job, etc.)
│   │   ├── routers/
│   │   │   ├── auth.py                # Register / login with validation
│   │   │   ├── uploads.py             # Secure file upload & parsing
│   │   │   ├── index.py               # Per-user FAISS index building
│   │   │   ├── generate.py            # Answer generation + background jobs
│   │   │   ├── answers.py             # Manual answer editing (IDOR-safe)
│   │   │   ├── export.py              # XLSX / PDF export (sanitised filenames)
│   │   │   └── references.py          # Passage snippet retrieval (IDOR-safe)
│   │   └── services/
│   │       ├── parser.py              # PDF/XLSX/TXT parsing
│   │       ├── splitter.py            # Overlapping passage splitting
│   │       ├── embeddings.py          # Per-user embedding + FAISS build/search
│   │       └── generation.py          # LLM generation + prompt injection guard
│   ├── worker.py                      # Background job worker
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx                    # Router, Nav, ProtectedRoute
│   │   ├── api.js                     # API client wrapper
│   │   ├── index.css                  # Design system (cards, badges, spinners)
│   │   ├── main.jsx                   # React entry point
│   │   └── pages/
│   │       ├── AuthPage.jsx           # Login / register form
│   │       ├── Dashboard.jsx          # Upload, index, generate
│   │       └── QuestionnaireView.jsx  # Answer review, edit, export
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── sample_data/                       # NovaTech Solutions test data
├── tests/                             # pytest unit + security tests
├── e2e_test.py                        # Full end-to-end test script
├── Dockerfile                         # Production container image
├── .github/workflows/ci.yml           # GitHub Actions CI pipeline
├── docs/
│   ├── deploy_railway.md              # Deployment guide (Railway/Fly/CF Pages)
│   ├── run_worker.sh                  # Background worker startup script
│   ├── demo.sh                        # Bash demo script
│   └── demo.ps1                       # PowerShell demo script
└── README.md
```

---

## Security Hardening (v1.0)

The following production-readiness fixes have been applied:

| # | Fix | Status |
|---|---|---|
| 1 | JWT secret enforcement + password validation | ✅ |
| 2 | Upload sanitisation (UUID filenames, size limit, path traversal) | ✅ |
| 3 | Per-user FAISS isolation (multi-tenant safe) | ✅ |
| 4 | IDOR prevention (ownership checks on all mutations) | ✅ |
| 5 | Background job queue (optional, poll-based) | ✅ |
| 6 | Prompt injection mitigation + citation verification | ✅ |
| 7 | Export filename sanitisation | ✅ |
| 8 | CORS hardening (explicit origins, not `*`) | ✅ |
| 9 | Structured logging + global error handler | ✅ |
| 10 | Health endpoint (`/api/health`) | ✅ |
| 11 | Dockerfile + GitHub Actions CI | ✅ |
| 12 | Deployment docs (Railway / Fly / Cloudflare Pages) | ✅ |

---

## Deployment

See [docs/deploy_railway.md](docs/deploy_railway.md) for full deployment instructions.

```bash
# Quick Docker test
docker build -t almabase-rag .
docker run -p 8000:8000 -e JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(48))") almabase-rag
```

---

## What I'd Improve Next

1. **Streaming generation** — SSE/WebSocket to show answers as they're generated
2. **Semantic chunking** — Content-aware splitting instead of fixed token windows
3. **Rate limiting & caching** — API throttling + Redis for embeddings cache
4. **Production DB** — PostgreSQL with pgvector for integrated vector search
5. **Answer quality evaluation** — RAGAS / faithfulness metrics
6. **Docker Compose** — One-command deployment with all services
