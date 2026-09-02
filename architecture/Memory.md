# Memory

## Purpose
This file is the working context log for future AI coding sessions.

## Current Project State
- Spring Boot gateway exists in `spring-api/`
- Python FastAPI inference service exists in `backend/app/main.py`
- Default inference backend is TF-IDF
- Optional BERT and Sentence-BERT adapters are present
- Redis cache support is present
- Kafka event publishing and worker support are present
- Evaluation API is present at `POST /api/evaluate`
- Metrics endpoint is present at `GET /metrics`
- Swagger UI is available from `http://127.0.0.1:8000/docs#/`

## Important Call Chain
- Frontend -> Spring Boot controller -> Spring WebClient -> Python FastAPI -> NLP engine

## Important Files
- [README.md](./README.md)
- [PRD.md](./PRD.md)
- [Architecture.md](./Architecture.md)
- [Rules.md](./Rules.md)
- [Phases.md](./Phases.md)
- [Design.md](./Design.md)

## Implementation Notes
- The project is intentionally aligned to older enterprise NLP patterns from 2020-2022.
- Do not reframe it as GPT, agentic, or RAG-first architecture.
- Keep the runnable path working without optional model downloads.
- If the code changes, update this file with the new status and any blockers.

## Recent Verified State
- Backend Python tests passed
- Spring Boot package build passed
- `/api/evaluate` returns confusion-matrix and metric output
- `/metrics` returns Prometheus-style exposition

