

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

## On deploying to Vercel

Worth knowing before you get there: **Vercel can't run this architecture as-is.** Vercel hosts static sites and short-lived serverless functions — it has no support for long-running Java/Spring Boot processes, and Python on Vercel only works as stateless serverless functions (cold-started per request, no persistent in-memory state). This app depends on:
- A Spring Boot process staying up on port 8080
- A FastAPI process staying up on port 8000, holding the loaded CSVs and TF-IDF index in memory between requests

Neither fits Vercel's model. Realistic options when you get there:
- **Frontend only on Vercel** (it's just static HTML/JS), with the Spring Boot + FastAPI services deployed elsewhere (Render, Railway, Fly.io, an EC2/VM, or a small Kubernetes cluster) — closer to the real "enterprise" story anyway.
- Or skip Vercel for this one and use Render/Railway for the whole stack, which do support long-running containers via your existing Dockerfiles with minimal changes.

Happy to help set up whichever path once you're ready — just let me know which host you land on and I'll walk through the config.
