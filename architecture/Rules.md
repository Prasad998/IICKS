# Rules

## Core Rules
- Prefer the older enterprise NLP stack from 2020-2022.
- Use Spring Boot as the API gateway and Python FastAPI as the ML service.
- Keep TF-IDF as the default runnable backend.
- Keep BERT and Sentence-BERT as optional adapter paths only.
- Keep Kafka and Redis as part of the architecture and docs.

## Libraries To Use
- Spring Boot 2.7
- Java 11
- FastAPI
- Uvicorn
- Pydantic
- redis-py
- kafka-python
- prometheus-client
- Optional: transformers
- Optional: sentence-transformers

## Libraries To Avoid As Primary Architecture
- GPT-based pipelines
- Agent frameworks
- Modern RAG-first design
- ChromaDB as the primary store
- LangChain or LangGraph as the main orchestration layer

## Engineering Rules
- Keep the offline path runnable without external model downloads.
- Preserve a clean API contract across Spring Boot and Python.
- Prefer deterministic, explainable behavior over hidden heuristics.
- Keep datasets synthetic unless explicitly replacing them with real data.
- Add tests for API behavior, evaluation, and model inference changes.

## Error Handling Rules
- Python endpoints should fail cleanly with readable API errors.
- Optional Redis and Kafka dependencies must degrade gracefully when unavailable.
- Optional transformer adapters must not break the default runnable path.
- Evaluation endpoints should return structured JSON, not ad hoc text.

## Documentation Rules
- Update README when API endpoints, workflow, or run commands change.
- Update Memory.md whenever the coding state changes in a meaningful way.
- Keep architecture docs aligned with the actual code.

## AI Behavior Rules
- Do not invent capabilities not present in the repo.
- Do not switch the system to a newer architecture without explicit instruction.
- When unsure, preserve the existing implementation style.
- Make small, reversible edits unless a larger refactor is clearly justified.

