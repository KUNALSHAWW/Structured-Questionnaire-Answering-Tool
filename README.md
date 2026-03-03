# Structured Questionnaire Answering Tool

> **Almabase GTM Engineering Internship — Home Assignment**

A full-stack prototype that lets users upload questionnaires and reference documents, then generates **grounded, citation-backed answers** using Retrieval-Augmented Generation (RAG). Every answer includes explicit citations and evidence snippets; questions without supporting evidence return exactly `Not found in references.`

---

## Features

| Feature | Description |
|---|---|
| **Auth** | JWT-based register/login with bcrypt password hashing |
| **Upload** | Upload questionnaire (PDF/XLSX/TXT) and reference docs (PDF/TXT/CSV/DOCX) |
| **Parsing** | Automatic question extraction from uploaded questionnaires |
| **Indexing** | Passage splitting (250 tokens, 50 overlap) → embeddings → FAISS vector index |
| **Generation** | Grounded answer generation with strict anti-hallucination prompt |
| **Citations** | Every answer includes `[filename \| page/para]` citations |
| **Evidence Snippets** | Show the exact passages used to support each answer |
| **Confidence Score** | 0–100 score derived from retrieval similarity |
| **Edit** | Manually edit any generated answer |
| **Regenerate** | Re-generate a single question's answer without re-running the full set |
| **Export** | Download answers as XLSX or PDF preserving question order |
| **Optional Sanity/GROQ** | Sync reference metadata to Sanity CMS if env vars are set |

---

## Tech Stack

- **Backend**: Python 3.10+ / FastAPI / SQLAlchemy / SQLite
- **Frontend**: React (Vite) with vanilla CSS
- **Vector Search**: FAISS (faiss-cpu)
- **Embeddings**: sentence-transformers (`all-MiniLM-L6-v2`) by default; OpenAI `text-embedding-3-small` if `OPENAI_API_KEY` is set
- **Generation**: OpenAI `gpt-4o-mini` if API key available; extractive fallback otherwise
- **Auth**: JWT + bcrypt (python-jose, passlib)
- **Export**: openpyxl (XLSX), reportlab (PDF)

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- pip

### 1. Clone & Setup Backend

```bash
cd Almabase

# Create virtual environment (recommended)
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set JWT_SECRET (required), optionally OPENAI_API_KEY
```

### 2. Start Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** in your browser.

### 4. Demo Flow

1. **Register** a new account on the login page
2. **Upload** the sample questionnaire (`sample_data/questionnaire.txt`)
3. **Upload** reference documents from `sample_data/` (all 5 `.txt` files)
4. Click **Build Index** to process references into embeddings
5. Click **Generate Answers** on the questionnaire
6. **Review** answers with citations, evidence snippets, and confidence scores
7. **Edit** or **Regenerate** individual answers as needed
8. **Export** as XLSX or PDF

### 5. Scripted Demo

```bash
# Start the backend first, then in another terminal:
# Linux/Mac:
bash docs/demo.sh

# Windows (PowerShell):
.\docs\demo.ps1
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `JWT_SECRET` | Yes | `dev-secret-change-me` | Secret for JWT token signing |
| `OPENAI_API_KEY` | No | — | Enables OpenAI embeddings + generation |
| `RETRIEVAL_THRESHOLD` | No | `0.35` | Min similarity score to consider a passage relevant |
| `RETRIEVAL_TOP_K` | No | `5` | Number of passages to retrieve per question |
| `SANITY_ENABLED` | No | `false` | Enable Sanity/GROQ metadata integration |
| `SANITY_PROJECT_ID` | No | — | Sanity project ID |
| `SANITY_TOKEN` | No | — | Sanity API token |
| `SANITY_DATASET` | No | `production` | Sanity dataset name |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, returns JWT |
| POST | `/api/uploads/questionnaire` | Upload questionnaire file |
| POST | `/api/uploads/reference` | Upload reference document |
| GET | `/api/uploads/questionnaires` | List user's questionnaires |
| GET | `/api/uploads/references` | List user's references |
| GET | `/api/uploads/questionnaire/:id/questions` | Get parsed questions |
| POST | `/api/index/build` | Build FAISS index from references |
| POST | `/api/generate` | Generate answers for a questionnaire |
| POST | `/api/regenerate/:question_id` | Regenerate one answer |
| PUT | `/api/answers/:answer_id` | Edit an answer |
| GET | `/api/runs` | List generation runs |
| GET | `/api/runs/:run_id` | Get run with all answers |
| GET | `/api/export/:run_id?format=xlsx\|pdf` | Export answers |
| GET | `/api/references/:id/snippet` | Get passage snippet |

---

## Sample Data

The `sample_data/` directory contains a fictional company **"NovaTech Solutions"** with:

- **questionnaire.txt** — 10 questions covering company overview, policies, HR, DR, and ESG
- **company_overview.txt** — Company description, revenue, products, clients
- **security_policy.txt** — Data privacy, retention, ISO 27001 cert details
- **hr_report.txt** — Headcount, turnover, remote work policy, benefits
- **disaster_recovery.txt** — DR/BCP plan with RTO/RPO, infrastructure, testing
- **esg_report.txt** — Environmental commitments, social responsibility, governance

---

## Testing

```bash
cd Almabase
python -m pytest tests/ -v
```

15 tests covering:
- Question detection heuristics
- Question text cleaning
- Questionnaire parsing (TXT)
- Reference text extraction
- Passage splitting
- Embeddings + FAISS build/search

---

## Architecture & Design Decisions

### Anti-Hallucination Strategy
- **Strict system prompt**: The LLM is instructed to use ONLY the provided passages
- **Confidence threshold**: If the best passage similarity is below `RETRIEVAL_THRESHOLD`, the system returns `Not found in references.` instead of generating
- **Explicit citations required**: The prompt enforces `[filename | page/para]` format
- **Evidence snippets**: Verbatim quotes from source passages are returned alongside answers

### Embedding Fallback
- If `OPENAI_API_KEY` is set → uses `text-embedding-3-small` (1536-dim)
- Otherwise → uses `all-MiniLM-L6-v2` via sentence-transformers (384-dim, runs locally, no API needed)

### Generation Fallback
- If `OPENAI_API_KEY` is set → uses `gpt-4o-mini` with the strict prompt
- Otherwise → extractive fallback that selects the top passage as the answer (no LLM hallucination possible)

### Optional Sanity/GROQ Integration
When `SANITY_ENABLED=true` with valid credentials:
- Reference metadata is synced to Sanity via its HTTP Mutations API
- FAISS remains the retrieval engine — Sanity is only a metadata/content store
- This enables GROQ queries for reference metadata (e.g., filtering by file type)

---

## Trade-offs

| Decision | Rationale |
|---|---|
| SQLite over Postgres | Prototype simplicity; zero config for reviewers |
| FAISS flat index | Good enough for <10K passages; no need for IVF at prototype scale |
| sentence-transformers default | Works offline, no API key needed — important for evaluation |
| Single-process backend | Sufficient for demo; would add Celery/background workers for production |
| No WebSocket streaming | Kept HTTP-only for simplicity; would add SSE for generation progress |

---

## What I'd Improve

1. **Streaming generation** — SSE/WebSocket to show answers as they're generated
2. **Chunking strategy** — Semantic chunking instead of fixed token windows
3. **Multi-user FAISS** — Per-user index isolation (currently shared)
4. **Background processing** — Celery queue for index building and generation
5. **UI polish** — Tailwind CSS, loading skeletons, drag-and-drop upload
6. **Containerization** — Docker Compose for one-command deployment
7. **Evaluation harness** — Automated answer quality metrics (RAGAS, faithfulness)
8. **Rate limiting** — API rate limits and request throttling
9. **Caching** — Redis cache for embeddings and frequent queries
10. **Production DB** — PostgreSQL with pgvector for integrated vector search

---

## Project Structure

```
Almabase/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Environment config
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models/
│   │   │   └── models.py        # ORM models
│   │   ├── routers/
│   │   │   ├── auth.py          # Register/login
│   │   │   ├── uploads.py       # File upload & parsing
│   │   │   ├── index.py         # FAISS index building
│   │   │   ├── generate.py      # Answer generation
│   │   │   ├── answers.py       # Edit answers
│   │   │   ├── export.py        # XLSX/PDF export
│   │   │   └── references.py    # Snippet retrieval
│   │   └── services/
│   │       ├── parser.py        # File parsing utilities
│   │       ├── splitter.py      # Passage splitting
│   │       ├── embeddings.py    # Embeddings + FAISS
│   │       └── generation.py    # LLM generation logic
│   ├── storage/                 # Runtime file storage
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main app with routing
│   │   ├── api.js               # API client
│   │   ├── pages/
│   │   │   ├── AuthPage.jsx     # Login/register
│   │   │   ├── Dashboard.jsx    # Upload, index, generate
│   │   │   └── QuestionnaireView.jsx  # Review answers
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
├── sample_data/                 # Fictional NovaTech Solutions
├── tests/                       # pytest unit tests
├── docs/
│   ├── demo.sh                  # Bash demo script
│   ├── demo.ps1                 # PowerShell demo script
│   └── submission_message.txt
├── .gitignore
└── README.md
```

---

## Submission Summary

I built a **Structured Questionnaire Answering Tool** — a full-stack RAG application that uploads questionnaires and reference documents, generates grounded answers with explicit citations, and exports results as XLSX/PDF. The system uses FAISS for vector retrieval with a strict anti-hallucination prompt that ensures every answer is backed by evidence from the uploaded references.

- **Tech**: FastAPI + React + SQLite + FAISS + sentence-transformers
- **Run locally**: `pip install -r backend/requirements.txt` → `uvicorn app.main:app` → `npm run dev`
- **Tests**: 15 passing (parsing, splitting, embeddings, retrieval)
- **What it solves**: Eliminates manual questionnaire answering by automatically finding and citing relevant information from reference documents, while guaranteeing no hallucinated content
