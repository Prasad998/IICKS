# Phases

## Phase 1: Local Prototype
- FastAPI backend
- static frontend
- TF-IDF classifier
- cosine similarity retrieval
- CSV datasets
- unit tests

## Phase 2: Enterprise Gateway
- Spring Boot API gateway
- gateway-to-inference HTTP client
- shared DTOs and request forwarding

## Phase 3: Messaging And Cache
- Kafka request/result events
- Redis response caching
- async worker consumer

## Phase 4: Evaluation
- holdout split evaluation
- accuracy, precision, recall, F1
- confusion matrix
- per-class categorical accuracy

## Phase 5: Observability
- Prometheus metrics endpoint
- Grafana dashboards
- ELK/EFK log collection

## Phase 6: Optional Transformer Path
- BERT classifier adapter
- Sentence-BERT embedder adapter
- trained model artifact integration

## Phase 7: Deployment Hardening
- Docker Compose
- Kubernetes manifests
- bare-metal container deployment
- environment variable driven configuration

## Phase 8: Dataset Upgrade
- replace synthetic data with real labeled data if required
- retrain or validate the BERT path
- refresh evaluation metrics

