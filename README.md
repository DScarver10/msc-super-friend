# MSC Super Friend

MSC Super Friend is an evidence-based reference and retrieval tool designed for
Medical Service Corps officers.

## Architecture
- FastAPI backend (RAG + ingestion)
- Streamlit frontend (reference UI + evidence-based queries)
- Public, unclassified sources only

## Principles
- Evidence-first answers
- Citations always shown
- Refusal when evidence is insufficient
- No CAC, no PHI, no user tracking

## Local Development
1. Activate Conda environment: `msc-backend`
2. Run backend with Uvicorn
3. Access `/health` to verify service is running
