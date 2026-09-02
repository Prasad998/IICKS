# Project Requirements

## Project Name
IBM Intelligent Incident Categorization & Knowledge Search

## Summary
Build an enterprise-style incident triage system inspired by 2020-2022 NLP architecture. The system receives incoming support tickets, classifies them into incident categories, retrieves similar historical incidents, and recommends knowledge-base articles.

## Target Users
- IT service desk analysts
- Support engineers
- Knowledge management teams
- Platform owners who want observability on triage quality and system health

## Problem Statement
Manual ticket triage is slow and inconsistent. Analysts need to read the ticket, determine the category, search prior incidents, and find the right knowledge article. This creates delay and variation in resolution quality.

## Goals
- Classify incident text into a stable category
- Retrieve similar historical incidents using semantic similarity
- Recommend relevant KB articles
- Expose the workflow through documented APIs
- Support enterprise-style deployment with Spring Boot, Python inference, Kafka, Redis, Docker, and Kubernetes
- Provide evaluation and observability endpoints for correctness and operations

## Functional Requirements
- Spring Boot API gateway accepts requests from the frontend and external callers
- Python FastAPI service performs NLP inference
- Incident analysis returns category, confidence, similar tickets, and recommended articles
- Async submit endpoint publishes ticket analysis requests to Kafka
- Redis can cache repeated analysis responses
- Evaluation endpoint reports accuracy, precision, recall, F1, and confusion matrix
- Metrics endpoint exposes Prometheus-style runtime metrics
- Swagger UI must be usable from the backend service

## Data Requirements
- `backend/data/incidents.csv` is the labeled historical incident corpus
- `backend/data/kb_articles.csv` is the KB retrieval corpus
- Both datasets are synthetic prototype data and not external production data

## Non-Goals
- No GPT-based generation workflow
- No agent orchestration
- No modern RAG stack
- No ChromaDB or similar new vector database dependency as the primary design
- No cloud-native SaaS dependency requirement for the core local run path

## Success Criteria
- The project runs locally with clear setup instructions
- The APIs are documented and callable from the browser
- The evaluation API can measure model quality on a holdout split
- The observability endpoint can be scraped by Prometheus
- The architecture remains faithful to the older enterprise stack

