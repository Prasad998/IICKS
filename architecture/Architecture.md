# Architecture

## System Overview
The project uses a two-layer backend pattern:

1. Spring Boot API gateway
2. Python FastAPI ML inference service

The frontend talks to Spring Boot. Spring Boot forwards requests to Python. Python performs preprocessing, classification, similarity retrieval, caching, and Kafka event publishing.

## Request Flow
1. `frontend/app.js` sends a request to the Spring Boot gateway.
2. `spring-api/src/main/java/com/ibm/incident/gateway/controller/IncidentController.java` receives the request.
3. `spring-api/src/main/java/com/ibm/incident/gateway/client/NlpServiceClient.java` forwards the request to Python.
4. `backend/app/main.py` receives the request in FastAPI.
5. `backend/app/cache.py` checks Redis for a cached analysis result.
6. `backend/app/events.py` publishes Kafka workflow events.
7. `backend/app/nlp_engine.py` runs preprocessing, category prediction, ticket similarity, and KB retrieval.
8. `backend/app/evaluation.py` computes holdout metrics when `/api/evaluate` is used.
9. `backend/app/main.py` returns the final response to Spring Boot and then to the frontend.

## Key Files
### Spring Boot Gateway
- `spring-api/src/main/java/com/ibm/incident/gateway/IncidentGatewayApplication.java`
- `spring-api/src/main/java/com/ibm/incident/gateway/controller/IncidentController.java`
- `spring-api/src/main/java/com/ibm/incident/gateway/client/NlpServiceClient.java`
- `spring-api/src/main/java/com/ibm/incident/gateway/config/WebClientConfig.java`
- `spring-api/src/main/java/com/ibm/incident/gateway/config/NlpServiceProperties.java`

### Python ML Service
- `backend/app/main.py`
- `backend/app/nlp_engine.py`
- `backend/app/preprocessing.py`
- `backend/app/vector_store.py`
- `backend/app/evaluation.py`
- `backend/app/cache.py`
- `backend/app/events.py`
- `backend/app/worker.py`
- `backend/app/transformer_backends.py`
- `backend/app/schemas.py`
- `backend/app/settings.py`

### Frontend
- `frontend/index.html`
- `frontend/app.js`
- `frontend/styles.css`

### Data
- `backend/data/incidents.csv`
- `backend/data/kb_articles.csv`

## Technical Stack
- Spring Boot 2.7 / Java 11 for the gateway
- FastAPI for Python inference
- TF-IDF centroid classifier as the default offline backend
- Hugging Face BERT adapter as an optional model path
- Sentence-BERT adapter as an optional retrieval path
- Redis for response caching
- Kafka for async workflow events
- Prometheus metrics endpoint for monitoring
- Docker and Docker Compose for local deployment

## Inference Flow
### Startup
- `IncidentNlpEngine.load()` loads CSV data
- `TfidfVectorizer.fit()` builds vocabulary and IDF values
- `build_category_centroids()` creates category prototypes
- `SparseVectorIndex.build()` prepares similarity indexes

### Ticket Analysis
- `IncidentController.analyze()` calls `NlpServiceClient.analyze()`
- Python `analyze_ticket()` checks cache and publishes request events
- `IncidentNlpEngine.analyze()` converts text to vectors and predicts category
- `predict_category()` compares against category centroids
- `find_similar_tickets()` returns top similar incidents
- `find_articles()` returns top KB articles
- Response is cached and published as a Kafka result event

### Evaluation
- `POST /api/evaluate` uses a deterministic stratified holdout split
- It reports accuracy, macro precision, macro recall, macro F1, and a confusion matrix

### Observability
- `GET /metrics` exposes Prometheus-style metrics
- Logs are intended to go to stdout for ELK/EFK collection in deployment

## Folder Structure
```text
backend/
  app/
  data/
  tests/
frontend/
spring-api/
docs/
scripts/
```

