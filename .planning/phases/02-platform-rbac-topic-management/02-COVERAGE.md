# API Coverage — Phase 2 (Platform, RBAC & Topic Management)

No external API integration: Phase 2 calls no third-party API, SDK or hosted service. Its only integration seam is the in-process AI title-check stub (`backend/app/services/ai_client.py`, D-10), a stand-in for the project's own first-party AI service that Phase 4 builds (`/check-title` contract §3.3.5); all other endpoints are the project's own FastAPI Web API behind its own Apache reverse proxy.
