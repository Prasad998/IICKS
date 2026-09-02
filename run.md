

You need: **Python 3.10–3.12**, **JDK 11+**, and **Maven** installed. Redis/Kafka/Docker are optional — the app runs fully without them (falls back to local TF-IDF, no cache, no events).

**1. Python ML service** (terminal 1):
```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Check it: `http://127.0.0.1:8000/docs`

**2. Spring Boot gateway** (terminal 2, from repo root):
```bash
cd spring-api
mvn spring-boot:run
```
Check it: `http://127.0.0.1:8080/health`

**3. Frontend** (terminal 3, from repo root):
```bash
cd frontend
npm install
npm run dev
```
Open `http://127.0.0.1:5173`, type a ticket, click **Analyze Ticket**.

**4. Run the tests** (confirms the fix worked):
```bash
cd backend
python -m unittest discover -s tests
```
You should now see `Ran 6 tests / OK` — this would have failed before the `httpx` fix.

**Sample data**: you don't need to create anything — `backend/data/incidents.csv` and `kb_articles.csv` already ship with 1,000 synthetic rows each across 5 categories, and the engine loads them automatically on startup.

**Docker Compose** (all services, incl. Redis + Kafka) — from repo root: `docker compose up --build`.

--------------

## Real results (50 concurrent users, 2-minute sustained run, via Spring gateway)

| Metric | `/api/analyze` | `/health` | Aggregated |
|---|---|---|---|
| Requests | 1,383 | 272 | 1,655 |
| **Failures** | **0** | **0** | **0 (0%)** |
| Median response time | 2,900 ms | 55 ms | 2,700 ms |
| Average response time | 3,067 ms | 124 ms | 2,583 ms |
| Min | 55 ms | 8 ms | 8 ms |
| p95 | 5,200 ms | 460 ms | 5,100 ms |
| p99 | 6,400 ms | 1,400 ms | 6,300 ms |
| Max | 8,153 ms | 3,378 ms | 8,153 ms |
| Overall throughput | — | — | **~13.8 req/s** sustained over the run |


## Workflow Analysis

Early in the ramp-up (10–20 concurrent users), median response time was **140–500ms** — fast. 
As concurrency climbed to and held at 50 users, median response time climbed steadily to **2,700–2,900ms**,
and stayed there for the rest of the 2-minute run rather than stabilizing lower. 
That's not noise — it's a saturation curve. 
**50 concurrent users is already past this setup's comfortable capacity.**

## Intuition

`analyze_ticket()` in `main.py` is a plain `def`, not `async def`. FastAPI/Starlette runs synchronous endpoints in a bounded background thread pool. But the actual work inside that endpoint — TF-IDF vectorization plus cosine similarity against ~2,000 stored vectors — is CPU-bound Python code, and Python's GIL means only one thread can execute Python bytecode at a time, *regardless of how many threads are in the pool*. So 50 concurrent requests don't run in parallel — they queue and take turns on one CPU core. That's exactly the linear-latency-growth-under-fixed-concurrency pattern in your data.

> *"Load-tested the incident-triage API with Locust at 50 concurrent users; identified that synchronous FastAPI endpoints performing CPU-bound TF-IDF inference queued under Python's GIL, causing p95 latency to degrade from ~500ms to ~5.2s under sustained concurrency — diagnosed the bottleneck as thread-pool saturation rather than I/O wait, informing a scale-out strategy (multi-process workers) over further code optimization."*
---

## **Axtria Inc. | Software Engineer (ML/GenAI) | Pune, India**

**September 2024 – Present**

* Architected **Requirement Genie**, a multi-agent GenAI platform converting meeting transcripts and business inputs into structured **BRD/URS documents**, cutting manual documentation effort by **40%+**.

* Designed agentic **RAG pipelines** using **LangChain, GPT-4o-mini, Azure OpenAI, ChromaDB, and FAISS** for semantic retrieval and knowledge-grounded requirement extraction aligned with pharma documentation standards.

* Built **FastAPI** microservices integrating LLM workflows with React frontends and **Axtria InsightsMax**, covering transcript preprocessing, prompt orchestration, structured extraction, document assembly, and automated DOCX generation.

* Developed AI copilots for **Power BI automation**, enabling natural-language-driven report generation and metadata-aware analytics; authored advanced **DAX** measures and optimized BI data models for pharma commercial workflows.

---

# Selected AI Project

### **IICKS — Intelligent Incident Categorization & Knowledge Search**

*Personal Project | 2026* · GitHub

* Architected a **3-tier NLP incident-triage platform** using React/Next.js, Spring Boot WebFlux, and Python FastAPI, integrating asynchronous API communication with **BERT/Sentence-BERT-based inference and semantic knowledge retrieval**.

* Diagnosed and resolved a **concurrency bottleneck in Spring WebFlux** caused by blocking `.block()` calls on Reactor Netty event-loop threads; refactored the gateway to a fully non-blocking **Mono-based pipeline** for reliable concurrent request handling.

* Audited and rebuilt a synthetic **1,000-ticket dataset**, identifying **79% duplicate textual records** despite balanced categories; developed a combinatorial data-generation pipeline achieving **100% textual uniqueness** while preserving IDs and category distributions.

* Built and benchmarked a **TF-IDF centroid classifier achieving 98% accuracy / 0.98 macro-F1**, outperforming a fine-tuned BERT baseline at **95% accuracy**, demonstrating that simpler representations were better suited to the dataset's domain-specific vocabulary.

* Implemented a configurable **TF-IDF / BERT / Sentence-BERT model backend** with graceful fallback and dependency validation, enabling experimentation across classical NLP and transformer-based approaches without changing the service architecture.

---

This is where I would add one more bullet **after we actually run the test**:

> **Stress-tested the end-to-end inference pipeline with 50–200 concurrent users using Locust, achieving [X] requests/sec at [Y]ms p95 latency with [Z]% error rate.**

That's a **real engineering metric**, and much stronger than an invented "24,000 requests/sec."

For example, if your actual result turns out to be:

> 37 requests/sec, 420 ms p95, 0% errors at 50 concurrent users

then that's what goes on the resume.

Don't worry if the number isn't huge. **A measured 37 RPS is more credible and valuable than a fabricated 10,000 RPS.**

---

# And regarding the 100-person scenario

This is where we should separate **system performance** from **business impact**.

Suppose we model:

* 100 support/incident agents
* 15 tickets/agent/day
* 5 minutes manual categorization/search per ticket
* IICKS requires ~30 seconds of human verification after generating the recommendation

Then:

**Manual:**

100 × 15 × 5 = **7,500 minutes/day**

With IICKS:

100 × 15 × 0.5 = **750 minutes/day**

Potential saving:

**6,750 minutes/day = 112.5 agent-hours/day**

That's an **85% reduction in triage time** under those assumptions.

But that's a **model**, not an observed production result.

And I'd actually use a more conservative scenario for your interview story:

| Assumption           |              Conservative |
| -------------------- | ------------------------: |
| Agents               |                       100 |
| Tickets/agent/day    |                        10 |
| Manual triage/search |                     5 min |
| AI-assisted review   |                     1 min |
| Time saved           |              4 min/ticket |
| Tickets/day          |                     1,000 |
| Potential time saved |  **66.7 agent-hours/day** |
| Weekly               | **~333 agent-hours/week** |

So your defensible statement becomes:

> **"Using a conservative scenario of 100 agents handling 10 tickets/day, I modeled approximately 67 agent-hours of potential time savings per day, assuming manual triage takes five minutes and AI-assisted verification takes one minute."**

That's actually a **good interview answer** because you're demonstrating that you understand the difference between **measured engineering performance** and **projected business impact**.

---

## One important correction to your existing IICKS bullet

I would change:

> "production-grade concurrency bug"

to:

> **"concurrency bottleneck"** or **"concurrency failure"**

unless IICKS has genuinely been deployed in production.

Likewise, don't call the system **production-grade** simply because you designed it like a production system.

You can say:

> **"production-oriented 3-tier incident-triage platform"**

if you want that signal.

This keeps your resume **ambitious but interview-defensible**, which is exactly what you want at the Senior GenAI/Applied AI level.

**Next step:** run the Locust test we discussed. Once you give me the `results_direct_stats.csv` and `results_gateway_stats.csv` (or simply paste the Locust output), I can calculate the **RPS, p50/p95/p99, throughput degradation, gateway overhead, and concurrency ceiling** and turn the actual numbers into the final IICKS bullet.
