# Web Intelligence Ingestion Engine

Production-grade brand intelligence data foundation.
Fetches → Crawls → Cleans → AI-scores → Structures → Stores.

---

## QUICK START (5 minutes)

### Step 1 — Prerequisites

Install these on your laptop if not already installed:

- **Python 3.11+** → https://python.org/downloads
- **Docker Desktop** → https://docker.com/products/docker-desktop
- **Git** (optional)

Verify Python version:
```bash
python --version   # must be 3.11 or higher
```

---

### Step 2 — Extract the project

```bash
unzip web-intelligence-engine.zip
cd web-intelligence-engine
```

---

### Step 3 — Start infrastructure (PostgreSQL + MongoDB + Redis)

```bash
docker-compose up -d
```

Wait ~10 seconds. Verify all 3 services are running:
```bash
docker-compose ps
```
You should see `wi_postgres`, `wi_mongodb`, `wi_redis` all with status **Up (healthy)**.

---

### Step 4 — Create Python virtual environment

```bash
# Create venv
python -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

---

### Step 5 — Install dependencies

```bash
pip install -r requirements.txt
```

This takes 1-2 minutes. You'll see packages installing.

---

### Step 6 — Configure environment

```bash
# Copy the example config
cp .env.example .env
```

Open `.env` in any text editor and set your API keys:

```env
# REQUIRED for AI scoring (get free at console.anthropic.com)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# REQUIRED for web search — pick ONE:
# Option A: SerpAPI (serpapi.com — 100 free searches/month)
SERPAPI_KEY=your-serpapi-key

# Option B: If you have no API keys, the system uses DuckDuckGo (free, no key needed)
# Just leave SERPAPI_KEY blank — it auto-falls back
```

**Minimum config** (zero cost to start):
- Leave `SERPAPI_KEY` blank → uses DuckDuckGo free fallback
- Leave `ANTHROPIC_API_KEY` blank → uses keyword heuristic scoring

---

### Step 7 — Run the server

```bash
python main.py
```

You should see:
```
INFO:     Starting Web Intelligence Engine...
✅ Redis queue ready (batch poller started)
🚀 20 workers starting
INFO:     Uvicorn running on http://0.0.0.0:8000
```

The server is now live at **http://localhost:8000**

---

## HOW TO USE

### Option A — Interactive API Docs (easiest)

Open your browser:
```
http://localhost:8000/docs
```

This opens the Swagger UI where you can click and test every endpoint visually.

---

### Option B — curl commands

#### Submit a search query
```bash
curl -X POST http://localhost:8000/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Nike brand reputation 2024",
    "max_results": 30
  }'
```

Response:
```json
{
  "job_id": "abc123-...",
  "query": "Nike brand reputation 2024",
  "urls_found": 30,
  "queued": 28,
  "message": "28 URLs queued. Poll /api/v1/search/status/abc123-..."
}
```

#### Check processing progress
```bash
curl http://localhost:8000/api/v1/search/status/YOUR_JOB_ID_HERE
```

Response:
```json
{
  "job_id": "abc123-...",
  "total_urls": 28,
  "pending": 12,
  "completed": 14,
  "failed": 1,
  "skipped": 1,
  "progress_pct": 57.1
}
```

Keep polling until `progress_pct` reaches 100.

#### Retrieve processed results
```bash
curl "http://localhost:8000/api/v1/content/?query=Nike+brand+reputation+2024&min_relevance=0.5"
```

Response — array of structured documents:
```json
{
  "query": "Nike brand reputation 2024",
  "total": 18,
  "returned": 18,
  "results": [
    {
      "url": "https://example.com/nike-article",
      "query": "Nike brand reputation 2024",
      "title": "Nike's Brand Strategy in 2024",
      "meta_description": "...",
      "headings": {"h1": ["Nike's 2024 Strategy"], "h2": [...], "h3": [...]},
      "clean_text": "Full cleaned article text...",
      "relevant_text": "Only sentences relevant to the query...",
      "content_summary": "2-4 sentence summary...",
      "key_points": ["Point 1", "Point 2", "..."],
      "relevance_score": 0.87,
      "confidence_score": 0.74,
      "sentiment": "neutral",
      "source_credibility": "high",
      "word_count": 1240,
      "language": "en",
      "source_domain": "reuters.com",
      "timestamp": "2026-04-16T10:30:00Z"
    }
  ]
}
```

#### Get analytics summary
```bash
curl "http://localhost:8000/api/v1/analytics/summary?query=Nike+brand+reputation+2024"
```

#### Full-text search across stored content
```bash
curl "http://localhost:8000/api/v1/content/search?q=brand+strategy&query=Nike+brand+reputation+2024"
```

---

### Option C — Python script

Create a file `test_query.py`:

```python
import httpx
import time

BASE = "http://localhost:8000"

# 1. Submit query
resp = httpx.post(f"{BASE}/api/v1/search/", json={
    "query": "Tesla electric vehicle market share",
    "max_results": 30,
})
data = resp.json()
job_id = data["job_id"]
print(f"Job: {job_id} | {data['queued']} URLs queued")

# 2. Poll until done
while True:
    status = httpx.get(f"{BASE}/api/v1/search/status/{job_id}").json()
    pct = status["progress_pct"]
    print(f"Progress: {pct}% | done={status['completed']+status['skipped']+status['failed']}/{status['total_urls']}")
    if pct >= 100:
        break
    time.sleep(3)

# 3. Fetch results
results = httpx.get(f"{BASE}/api/v1/content/", params={
    "query": "Tesla electric vehicle market share",
    "min_relevance": 0.5,
    "limit": 20,
}).json()

print(f"\n✅ {results['total']} documents stored")
for doc in results["results"]:
    print(f"  [{doc['relevance_score']:.2f}] {doc['title'][:60]} — {doc['source_domain']}")
```

Run it:
```bash
pip install httpx
python test_query.py
```

---

## ALL API ENDPOINTS

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/search/` | Submit a search query |
| GET | `/api/v1/search/status/{job_id}` | Check job progress |
| GET | `/api/v1/content/` | Get processed results for a query |
| GET | `/api/v1/content/search` | Full-text search across content |
| GET | `/api/v1/content/{url_hash}` | Get single document by hash |
| GET | `/api/v1/content/domain/{domain}` | Get all results from a domain |
| GET | `/api/v1/analytics/summary` | Summary stats for a query |
| GET | `/api/v1/analytics/domains` | Domain breakdown |
| GET | `/api/v1/analytics/quality` | Relevance score distribution |
| GET | `/api/v1/crawl/queue` | Queue depth |
| GET | `/health/` | Health check |
| GET | `/docs` | Swagger UI |

---

## STOPPING THE SYSTEM

```bash
# Stop the Python server: Ctrl+C in the terminal running main.py

# Stop Docker services
docker-compose down

# Stop Docker AND delete all stored data (fresh start)
docker-compose down -v
```

---

## TROUBLESHOOTING

### "Connection refused" on startup
```bash
# Make sure Docker services are running
docker-compose ps
# If any are not healthy, restart them
docker-compose restart
```

### "No search results found"
- You need at least one search API key, OR let DuckDuckGo work (may be rate-limited)
- Try with a simpler query first: `"Apple"` instead of a long phrase

### Results show `relevance_score: 0.4-0.5` for everything
- This means `ANTHROPIC_API_KEY` is not set — heuristic mode is active
- Add your Anthropic API key in `.env` for better scoring

### Port 5432/27017/6379 already in use
```bash
# Check what's using the port
lsof -i :5432

# Or change the port in docker-compose.yml:
# ports: ["5433:5432"]   ← left side is your laptop's port
# Then update .env: POSTGRES_URL=postgresql+asyncpg://postgres:password@localhost:5433/web_intelligence
```

### Windows-specific
- Use `venv\Scripts\activate` (not `source venv/bin/activate`)
- Use PowerShell or Command Prompt, not Git Bash for venv activation

---

## VIEWING DATA DIRECTLY

### MongoDB (processed content)
```bash
# Connect to MongoDB shell
docker exec -it wi_mongodb mongosh

# In the shell:
use web_intelligence
db.processed_content.find({query: "your query here"}).limit(5).pretty()
db.processed_content.countDocuments()
db.processed_content.find().sort({relevance_score: -1}).limit(3).pretty()
```

### PostgreSQL (URL tracking)
```bash
# Connect to PostgreSQL
docker exec -it wi_postgres psql -U postgres -d web_intelligence

# In the shell:
SELECT status, COUNT(*) FROM search_results GROUP BY status;
SELECT url, status, relevance_score FROM search_results LIMIT 10;
\q
```

### Redis (queue depth)
```bash
docker exec -it wi_redis redis-cli
ZCARD wi:queue          # pending jobs in queue
KEYS wi:job:*:stats     # all job stats keys
HGETALL wi:job:YOUR_JOB_ID:stats
```
