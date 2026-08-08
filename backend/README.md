# Codebase Context Platform — Backend

An API-based cross-AI codebase context platform. Runs 100% locally — no Docker,
no Redis, no cloud services.

## Progress

- [x] Step 1: FastAPI project setup
- [x] Step 2: SQLite + SQLAlchemy
- [x] Step 3: Git repository cloning
- [x] Step 4: Repository scanner
- [x] Step 5: Tree-sitter parser
- [ ] Step 6: Metadata extraction
- [ ] Step 7: Code chunking
- [ ] Step 8: Embeddings & vector database
- [ ] Step 9: Semantic search
- [ ] Step 10: Architecture & dependency graph
- [ ] Step 11: Documentation generator
- [ ] Step 12: Repository synchronization (re-indexing)
- [ ] Step 13: Security scanner
- [ ] Step 14: Cross-AI context API
- [ ] Step 15: Testing & production readiness

## Setup

```bash
python3.12 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python -m app.main
# or
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Test

- Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/v1/health

```bash
curl http://127.0.0.1:8000/api/v1/health
```
