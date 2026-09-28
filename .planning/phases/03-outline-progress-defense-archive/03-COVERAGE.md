# API Coverage — Phase 3 (Outline, Progress, Defense & Archive)

No external API integration: Phase 3 calls no third-party API, SDK or hosted service. Its only integration seam is the in-process AI client stub (`backend/app/services/ai_client.py`), extended with `check_document` and `ingest` to match the project's own first-party AI service contract (§3.3.5 `/check-document`, `/ingest`) that Phase 4 builds; file text extraction uses local libraries (python-docx, PyMuPDF). All other endpoints are the project's own FastAPI Web API behind its own Apache reverse proxy.
