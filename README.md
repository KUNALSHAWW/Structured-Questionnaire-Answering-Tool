# Structured Questionnaire Answering Tool

> **Almabase GTM Engineering Internship — Take-Home Assignment**

A full-stack RAG (Retrieval-Augmented Generation) application that automatically answers vendor/compliance questionnaires using uploaded reference documents. Every answer is grounded in source material with explicit citations and evidence snippets — questions without supporting evidence return `Not found in references.`

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![React](https://img.shields.io/badge/React-19-61DAFB)
![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-orange)

---

## Live Demo

| Component | URL |
|---|---|
| **Frontend** | [structured-questionnaire-answering-tool.pages.dev](https://structured-questionnaire-answering-tool.pages.dev) |
| **Backend API** | [almabase-backend-production.up.railway.app](https://almabase-backend-production.up.railway.app/api/health) |

### How It Works

1. **Register / Login** → JWT-authenticated session
2. **Upload** a questionnaire (PDF/XLSX/TXT) + one or more reference documents (PDF/TXT/CSV/DOCX)
3. **Build Index** → documents are parsed, split into passages, embedded, and indexed in FAISS
4. **Generate Answers** → each question is semantically matched to top-K passages and answered with citations
5. **Review** → view confidence scores, evidence snippets; edit or regenerate individual answers
6. **Export** → download all answers as XLSX or PDF

---

## Features

| Feature | Description |
|---|---|
| **JWT Auth** | Secure register/login with bcrypt password hashing |
| **Questionnaire Parsing** | Auto-detect questions from PDF/XLSX/TXT (numbered, `Q:` prefixed, or `?` ending) |
| **Multi-Strategy Passage Splitting** | Page → numbered section → titled section → paragraph → line fallback |
| **Semantic Retrieval** | FAISS cosine similarity search over sentence-transformer embeddings |
| **Grounded Generation** | OpenAI GPT-4o-mini (if API key set) or zero-hallucination extractive fallback |
| **Smart Extractive Fallback** | Bigram-scored sentence selection with keyword density, content dedup, noise filtering |
| **Multi-File Upload** | Drag-and-drop multiple references; duplicate filename prevention (409) |
| **Citations** | Every answer includes `[filename \| section/page]` source references |
| **Evidence Snippets** | Verbatim quotes from source passages |
| **Confidence Scores** | 0–100% calibrated from cosine similarity (piecewise mapping tuned for MiniLM) |
| **Edit & Regenerate** | Manually refine any answer or regenerate from the same passages |
| **XLSX / PDF Export** | Download answers preserving question order and formatting |
| **Prompt Injection Guard** | Regex-based sanitisation strips known injection patterns before generation |
| **Per-User Isolation** | Each user gets a separate FAISS index — no cross-tenant data leakage |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+ · FastAPI · SQLAlchemy · SQLite |
| **Frontend** | React 19 · Vite 6 · Vanilla CSS |
| **Vector Search** | FAISS (faiss-cpu) · cosine similarity via normalized inner product |
| **Embeddings** | sentence-transformers `all-MiniLM-L6-v2` (local, CPU) or OpenAI `text-embedding-3-small` |
| **Generation** | OpenAI `gpt-4o-mini` (optional) or smart extractive fallback |
| **Auth** | JWT (python-jose) + bcrypt |
| **Export** | openpyxl (XLSX) · reportlab (PDF) |
| **Deployment** | Railway (backend) · Cloudflare Pages (frontend) |

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
# Edit .env — set JWT_SECRET (required for production)
# Optionally set OPENAI_API_KEY for LLM-powered answers
```

### 3. Run

```bash
# Terminal 1 — Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open **http://localhost:3000**

### 4. Try It Out

1. Register a new account
2. Upload `sample_data/questionnaire.txt` as the questionnaire
3. Upload all reference documents from `sample_data/`
4. Click **Build Index** → **Generate Answers**
5. Review answers with citations, confidence scores, and evidence snippets
6. Export as XLSX or PDF

---

## Architecture

```
┌───────────────┐    ┌────────────────────────────────────────────┐
│   React UI    │──▷│  FastAPI Backend                           │
│  (Vite, :3000)│    │                                           │
└───────────────┘    │  ┌─────────┐  ┌───────────┐  ┌──────────┐ │
                     │  │ Upload  │→ │ Splitter  │→ │ Embed +  │ │
                     │  │ & Parse │  │ (4-tier)  │  │  FAISS   │ │
                     │  └─────────┘  └───────────┘  └────┬─────┘ │
                     │                                   │      │
                     │  ┌─────────┐  ┌──────────────┐    │      │
                     │  │Question │→ │Retrieve Top-K│◁───┘      │
                     │  └─────────┘  └──────┬───────┘           │
                     │                      │                   │
                     │              ┌───────▽────────┐          │
                     │              │ LLM Generate   │          │
                     │              │ or Extractive  │          │
                     │              │ Fallback       │          │
                     │              └───────┬────────┘          │
                     │                      │                   │
                     │              ┌───────▽────────┐          │
                     │              │ Answer + Cite  │          │
                     │              │ + Evidence     │          │
                     │              └────────────────┘          │
                     └──────────────────────────────────────────┘
```

### Passage Splitting Strategy (4-tier)

The splitter uses a priority-ordered strategy to produce the most granular passages possible:

1. **Page-based** — split on form-feed (`\f`) or `Page N` markers; each page further split by section headers
2. **Numbered sections** — detect `1. Title`, `Section 2:` patterns and split at boundaries
3. **Titled sections** — detect title-case heading lines (e.g. `Authentication & Access Control`, `High-level architecture`) using a line-by-line heuristic
4. **Paragraph fallback** — double-newline → single-newline grouping with token-size windowing

Each tier produces overlapping chunks (default 200 tokens, 40-token overlap) for context continuity.

### Extractive Fallback (No-LLM Mode)

When no `OPENAI_API_KEY` is set, answers are generated via a zero-hallucination extractive pipeline:

- **Keyword + bigram scoring** — question keywords and bigrams scored against candidate sentences
- **Keyword density thresholds** — sentences matching < 25% of question keywords are penalised
- **Content-based dedup** — 60% word-overlap threshold prevents near-duplicate sentences
- **Noise filtering** — strips section titles, table headers, metadata fragments, enum lists
- **Passage rank decay** — sentences from higher-similarity passages get priority
- **Max 3 sentences** — concise, focused answers

### Anti-Hallucination Guarantees

1. **Strict system prompt** — LLM instructed to use ONLY provided passages
2. **Similarity threshold gate** — below 0.20 cosine → `Not found in references.`
3. **Citation verification** — generated citations checked against retrieved passage filenames
4. **Evidence snippets** — verbatim source quotes returned with every answer
5. **Extractive fallback** — no LLM = no hallucination

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `JWT_SECRET` | **Yes** | `dev-secret-change-me` | JWT signing key. **Must change in production.** |
| `ENV` | No | `development` | Set `production` to enforce JWT_SECRET |
| `OPENAI_API_KEY` | No | — | Enables OpenAI embeddings + LLM generation |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000,http://localhost:5173` | Comma-separated CORS origins |
| `MAX_UPLOAD_BYTES` | No | `52428800` (50 MB) | Max upload file size |
| `MIN_PASSWORD_LENGTH` | No | `8` | Minimum password length |
| `JWT_EXPIRY_MINUTES` | No | `60` | JWT token lifetime |
| `RETRIEVAL_THRESHOLD` | No | `0.20` | Minimum cosine similarity for relevance |
| `RETRIEVAL_TOP_K` | No | `5` | Passages retrieved per question |
| `PASSAGE_TOKEN_SIZE` | No | `200` | Tokens per passage chunk |
| `PASSAGE_OVERLAP` | No | `40` | Overlapping tokens between chunks |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/auth/register` | Register new user |
| `POST` | `/api/auth/login` | Login → JWT token |
| `POST` | `/api/uploads/questionnaire` | Upload questionnaire |
| `POST` | `/api/uploads/reference` | Upload single reference |
| `POST` | `/api/uploads/references/bulk` | Upload multiple references |
| `DELETE` | `/api/uploads/reference/:id` | Delete a reference |
| `GET` | `/api/uploads/questionnaires` | List questionnaires |
| `GET` | `/api/uploads/references` | List references |
| `GET` | `/api/uploads/questionnaire/:id/questions` | Get parsed questions |
| `POST` | `/api/index/build` | Build FAISS index |
| `POST` | `/api/generate` | Generate answers |
| `POST` | `/api/regenerate/:question_id` | Regenerate one answer |
| `PUT` | `/api/answers/:answer_id` | Edit an answer |
| `GET` | `/api/runs` | List generation runs |
| `GET` | `/api/runs/:run_id` | Get run with answers |
| `GET` | `/api/export/:run_id?format=xlsx\|pdf` | Export answers |

---

## Testing

```bash
# Unit + security tests (30 tests)
python -m pytest tests/ -v

# End-to-end test (register → upload → index → generate → export)
python e2e_test.py
```

**Test coverage includes:**
- Question detection (numbered, `Q:` prefix, `?` fallback)
- Questionnaire parsing (TXT + PDF)
- Reference text extraction
- Passage splitting (company overview, section-based, small-text)
- FAISS embedding + retrieval
- Auth validation (email format, password length)
- Per-user FAISS isolation
- Prompt injection sanitisation
- Citation verification
- CORS configuration

---

## Sample Data

The `sample_data/` directory contains a fictional company **"NovaTech Solutions"**:

| File | Content |
|---|---|
| `questionnaire.txt` | 10 questions: company overview, policies, HR, DR, ESG |
| `company_overview.txt` | Revenue ($78.4M), products, clients |
| `security_policy.txt` | Data privacy, retention, ISO 27001 |
| `hr_report.txt` | Headcount (342 FTE), turnover, remote work |
| `disaster_recovery.txt` | DR/BCP plan, RTO/RPO targets |
| `esg_report.txt` | Carbon goals, governance, sustainability |

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry, CORS, health, logging
│   │   ├── config.py            # Environment configuration
│   │   ├── database.py          # SQLAlchemy engine & session
│   │   ├── auth_utils.py        # Ownership verification helpers
│   │   ├── models/models.py     # ORM models
│   │   ├── routers/
│   │   │   ├── auth.py          # Register / login
│   │   │   ├── uploads.py       # File upload, bulk, duplicate check, delete
│   │   │   ├── index.py         # Per-user FAISS index
│   │   │   ├── generate.py      # Answer generation + background jobs
│   │   │   ├── answers.py       # Answer editing (IDOR-safe)
│   │   │   ├── export.py        # XLSX / PDF export
│   │   │   └── references.py    # Passage snippet retrieval
│   │   └── services/
│   │       ├── parser.py        # PDF/XLSX/TXT/CSV/DOCX parsing
│   │       ├── splitter.py      # 4-tier passage splitting
│   │       ├── embeddings.py    # Embedding + FAISS build/search
│   │       └── generation.py    # LLM generation + extractive fallback
│   ├── worker.py                # Background job worker
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Router, Nav, ProtectedRoute
│   │   ├── api.js               # API client wrapper
│   │   └── pages/
│   │       ├── AuthPage.jsx     # Login / register
│   │       ├── Dashboard.jsx    # Upload, index, generate
│   │       └── QuestionnaireView.jsx  # Answer review, edit, export
│   ├── package.json
│   └── vite.config.js
├── sample_data/                 # NovaTech test data
├── tests/                       # pytest unit + security tests (30 tests)
├── e2e_test.py                  # Full E2E test script
├── Dockerfile                   # Production container
├── .github/workflows/ci.yml     # CI pipeline
└── docs/                        # Deployment & demo scripts
```

---

## Security

| # | Measure | Description |
|---|---|---|
| 1 | **Auth** | JWT secret enforcement, bcrypt hashing, password length validation |
| 2 | **Upload Safety** | UUID filenames, size limit, MIME validation, path traversal prevention |
| 3 | **Tenant Isolation** | Per-user FAISS indices — no cross-user data access |
| 4 | **IDOR Prevention** | Ownership checks on all mutation endpoints |
| 5 | **Prompt Injection** | Regex sanitisation strips known injection phrases |
| 6 | **Citation Verification** | Generated citations validated against retrieved filenames |
| 7 | **CORS** | Explicit allowed origins (not wildcard in production) |
| 8 | **Export Safety** | Sanitised filenames, size-limited output |

---

## Deployment

**Backend** is deployed on [Railway](https://railway.app) with a persistent volume at `/data` for SQLite + uploaded files.
**Frontend** is deployed on [Cloudflare Pages](https://pages.cloudflare.com).

```bash
# Deploy backend to Railway
cd backend
railway up --detach

# Build frontend for Cloudflare Pages
cd frontend
npm run build
```

See [docs/deploy_railway.md](docs/deploy_railway.md) for detailed instructions.

---

## What I'd Improve Next

1. **LLM-powered generation** — Add OpenAI/Anthropic API integration for higher-quality answers
2. **Streaming answers** — SSE/WebSocket to show answers as they generate
3. **Semantic chunking** — Content-aware splitting instead of fixed token windows
4. **PostgreSQL + pgvector** — Production DB with integrated vector search
5. **Rate limiting & caching** — Redis for embeddings cache + API throttling
6. **Answer quality metrics** — RAGAS / faithfulness evaluation pipeline
