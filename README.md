# MSC Super Friend

MSC Super Friend is an evidence-based reference and retrieval tool for Medical Service Corps officers.

## Architecture
- Legacy backend (RAG + ingestion): `backend/`
- New API service (FastAPI): `api/`
- Legacy UI (Streamlit): `frontend/`
- New UI (Next.js): `web/`

## Windows Notes
If PowerShell blocks `npm.ps1` with `PSSecurityException`, use either:
- `cmd.exe` terminal, or
- `npm.cmd` directly (for example `npm.cmd run build`).

## Local Run (Web + API)
1. Build/refresh index (if needed):
   - `python scripts/build_index.py`
2. Start API:
   - `cd api`
   - `python -m pip install -r requirements.txt`
   - `python -m uvicorn main:app --host 0.0.0.0 --port 8000`
3. Start web app in a second terminal:
   - `cd web`
   - `npm install`
   - `npm run dev`
4. Open `http://localhost:3000`.

## Env Vars
### API (`api/.env`)
- `OPENAI_API_KEY` (required)
- `INDEX_DIR` (optional, default `backend/data/index`)
- `DOCS_DIR` (optional, default `backend/data/toolkit_docs`)
- `LLM_MODEL` (optional, default `gpt-4o-mini`)
- `EMBEDDING_MODEL` (optional, default `text-embedding-3-small`)

See `api/.env.example`.

### Web (`web/.env.local`)
- `NEXT_PUBLIC_API_BASE_URL` (required for Ask page)
- `NEXT_PUBLIC_RATE_URL` (optional)
- `NEXT_PUBLIC_APP_VERSION` (optional)
- `NEXT_PUBLIC_ENABLE_SW` (optional)

See `web/.env.example`.

## Utility Scripts
- Copy docs into Next.js public folder:
  - `python scripts/copy_docs.py`
- Build RAG index:
  - `python scripts/build_index.py`
- API smoke test (`POST /ask`):
  - `python scripts/smoke_test_api.py`

## Deploy
### Web on Vercel (`web/`)
- Framework: Next.js
- Root directory: `web`
- Build command: `next build` (or `npm run build`)
- Output: `.next` (managed by Vercel)
- Required env vars:
  - `NEXT_PUBLIC_API_BASE_URL=https://<your-api>.onrender.com`

### API on Render (`api/`)
- Runtime: Python
- Root directory: `api`
- Build command: `python -m pip install -r requirements.txt`
- Start command: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
- Required env vars:
  - `OPENAI_API_KEY=<your_key>`
- Optional env vars:
  - `INDEX_DIR=backend/data/index`
  - `DOCS_DIR=backend/data/toolkit_docs`
  - `LLM_MODEL=gpt-4o-mini`
  - `EMBEDDING_MODEL=text-embedding-3-small`

## Safety
- Do not commit `api/.env` or other secret files.
