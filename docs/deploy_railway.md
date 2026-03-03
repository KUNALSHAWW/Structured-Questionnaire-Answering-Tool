# Deploying to Railway (Backend) + Cloudflare Pages (Frontend)

## Prerequisites
- [Railway CLI](https://docs.railway.app/develop/cli) installed
- [Cloudflare account](https://dash.cloudflare.com/) with Pages access
- Git repo pushed to GitHub

---

## 1. Backend on Railway

### a) Create project
```bash
railway login
railway init          # creates a new Railway project
railway link          # links to your repo
```

### b) Set environment variables
```bash
railway variables set JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
railway variables set ENV=production
railway variables set ALLOWED_ORIGINS=https://your-frontend.pages.dev
railway variables set OPENAI_API_KEY=sk-...       # optional
railway variables set USE_BACKGROUND_JOBS=false    # set true if running worker
```

### c) Deploy
Railway auto-detects the Dockerfile. Push to `main` or run:
```bash
railway up
```

The backend will be available at `https://<project>.up.railway.app`.

### d) Background worker (optional)
If `USE_BACKGROUND_JOBS=true`, create a second Railway service in the same project:
- Set the **Start Command** to: `python worker.py`
- Use the same environment variables
- Both services share the same database via `DATABASE_URL`

---

## 2. Frontend on Cloudflare Pages

### a) Build settings
- **Framework:** Vite
- **Build command:** `npm run build`
- **Build output:** `dist`
- **Root directory:** `frontend`

### b) Environment variables
In the Cloudflare Pages dashboard, set:
```
VITE_API_URL=https://<project>.up.railway.app
```

### c) Deploy
Connect your GitHub repo → Cloudflare auto-builds on push to `main`.

---

## 3. Alternative: Fly.io (Backend)

### a) Create app
```bash
fly launch --dockerfile Dockerfile
```

### b) Set secrets
```bash
fly secrets set JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
fly secrets set ENV=production
fly secrets set ALLOWED_ORIGINS=https://your-frontend.pages.dev
```

### c) Deploy
```bash
fly deploy
```

---

## 4. Health Check

After deploying, verify:
```bash
curl https://<backend-url>/api/health
# Expected: {"status":"ok","timestamp":"...","version":"1.0.0"}
```

## 5. Storage Notes

- **SQLite** works for demos but should be replaced with **PostgreSQL** for production.
  Railway provides managed Postgres: `railway add postgresql`.
- **FAISS indices** and **uploads** are stored on disk. For production persistence,
  mount a volume or use object storage (Cloudflare R2 / S3).
- Set `DATABASE_URL=postgresql://...` to use Postgres.
