<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=32&duration=2500&pause=1000&color=00F7FF&center=true&vCenter=true&width=700&lines=WEB+INTELLIGENCE+INGESTION+ENGINE;Fetch+%E2%86%92+Crawl+%E2%86%92+Clean+%E2%86%92+Score+%E2%86%92+Store;Production-Grade+Brand+Intelligence" alt="Typing SVG" />

```
██╗    ██╗███████╗██████╗       ██╗███╗   ██╗████████╗███████╗██╗
██║    ██║██╔════╝██╔══██╗      ██║████╗  ██║╚══██╔══╝██╔════╝██║
██║ █╗ ██║█████╗  ██████╔╝█████╗██║██╔██╗ ██║   ██║   █████╗  ██║
██║███╗██║██╔══╝  ██╔══██╗╚════╝██║██║╚██╗██║   ██║   ██╔══╝  ██║
╚███╔███╔╝███████╗██████╔╝      ██║██║ ╚████║   ██║   ███████╗███████╗
 ╚══╝╚══╝ ╚══════╝╚═════╝       ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝
```

**A self-hosted pipeline that turns a search query into structured, AI-scored brand intelligence — in minutes, not weeks.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-URL_Tracking-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-Document_Store-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)
[![Redis](https://img.shields.io/badge/Redis-Job_Queue-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-Async_API-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Anthropic](https://img.shields.io/badge/Claude-AI_Scoring-D4A574?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)

![Status](https://img.shields.io/badge/status-production--ready-brightgreen?style=flat-square)
![Workers](https://img.shields.io/badge/workers-20_concurrent-orange?style=flat-square)
![License](https://img.shields.io/badge/setup_time-5_minutes-blueviolet?style=flat-square)

</div>

---

## ⚡ What This Actually Does

> Feed it a phrase like `"Nike brand reputation 2024"`. It searches the web, crawls every result, strips the noise, asks Claude to summarize and score relevance, and hands you back clean structured JSON — searchable, filterable, and stored forever.

```
┌──────────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐    ┌───────────┐    ┌─────────┐
│  QUERY   │──▶│  FETCH   │──▶│  CRAWL  │──▶│  CLEAN   │──▶│ AI-SCORE  │──▶│  STORE  │
│  "Nike"  │    │ 30 URLs │    │  pages  │    │  & parse │    │  Claude   │    │ Mongo +  │
└──────────┘    └─────────┘    └─────────┘    └──────────┘    └───────────┘    │ Postgres │
                                                                                  └─────────┘
```

<div align="center">

| 🔎 Search | 🕷️ Crawl | 🧹 Clean | 🤖 Score | 🗄️ Store |
|:---:|:---:|:---:|:---:|:---:|
| DuckDuckGo / SerpAPI | 20 parallel workers | HTML → text, dedupe | Claude relevance + sentiment | Postgres + Mongo + Redis |

</div>

---

## 🚀 Quick Start — 5 Minutes to First Result

<table>
<tr><td>

### ✅ Prerequisites

| Tool | Why | Get it |
|---|---|---|
| **Python 3.11+** | Runs the API server | [python.org](https://python.org/downloads) |
| **Docker Desktop** | Spins up Postgres/Mongo/Redis | [docker.com](https://docker.com/products/docker-desktop) |
| **Git** *(optional)* | Cloning the repo | — |

```bash
python --version   # confirm 3.11+
```

</td></tr>
</table>

### `Step 1` 📦 Extract the Project

```bash
unzip web-intelligence-engine.zip
cd web-intelligence-engine
```

### `Step 2` 🐳 Launch Infrastructure

```bash
docker-compose up -d
```

Wait ~10 seconds, then confirm all three services are healthy:

```bash
docker-compose ps
```

**Expect to see:** `wi_postgres` · `wi_mongodb` · `wi_redis` → all **`Up (healthy)`** ✅

### `Step 3` 🧪 Create & Activate a Virtual Environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows (PowerShell / cmd — not Git Bash)
venv\Scripts\activate
```

### `Step 4` 📚 Install Dependencies

```bash
pip install -r requirements.txt
```

⏱️ Takes 1–2 minutes.

### `Step 5` 🔑 Configure Environment

```bash
cp .env.example .env
```

Then edit `.env`:

```env
# REQUIRED for AI scoring — free at console.anthropic.com
ANTHROPIC_API_KEY=sk-ant-your-key-here

# REQUIRED for web search — pick ONE:
# Option A — SerpAPI (100 free searches/month)
SERPAPI_KEY=your-serpapi-key

# Option B — leave blank to auto-fallback to free DuckDuckGo search
```

> 💡 **Zero-cost path:** leave both blank. `SERPAPI_KEY` blank → DuckDuckGo fallback. `ANTHROPIC_API_KEY` blank → keyword heuristic scoring instead of Claude.

### `Step 6` ▶️ Run the Server

```bash
python main.py
```

**You should see:**

```
INFO:     Starting Web Intelligence Engine...
✅ Redis queue ready (batch poller started)
🚀 20 workers starting
INFO:     Uvicorn running on http://0.0.0.0:8000
```

<div align="center">

### 🎉 Live at **http://localhost:8000** 🎉

</div>

---

## 🕹️ How to Use It

### Option A — Interactive Swagger UI *(easiest)*

Open **http://localhost:8000/docs** and click through every endpoint visually — no terminal required.

### Option B — `curl` from the Command Line

**① Submit a search query**

```bash
curl -X POST http://localhost:8000/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Nike brand reputation 2024",
    "max_results": 30
  }'
```

```json
{
  "job_id": "abc123-...",
  "query": "Nike brand reputation 2024",
  "urls_found": 30,
  "queued": 28,
  "message": "28 URLs queued. Poll /api/v1/search/status/abc123-..."
}
```

**② Poll for progress**

```bash
curl http://localhost:8000/api/v1/search/status/YOUR_JOB_ID_HERE
```

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

**③ Pull the structured results**

```bash
curl "http://localhost:8000/api/v1/content/?query=Nike+brand+reputation+2024&min_relevance=0.5"
```

```json
{
  "query": "Nike brand reputation 2024",
  "total": 18,
  "returned": 18,
  "results": [
    {
      "url": "https://example.com/nike-article",
      "title": "Nike's Brand Strategy in 2024",
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

**④ Analytics & full-text search**

```bash
curl "http://localhost:8000/api/v1/analytics/summary?query=Nike+brand+reputation+2024"
curl "http://localhost:8000/api/v1/content/search?q=brand+strategy&query=Nike+brand+reputation+2024"
```

<details>
<summary><b>Option C — 🐍 Full Python Script (click to expand)</b></summary>

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

```bash
pip install httpx
python test_query.py
```

</details>

---

## 📡 API Reference

<div align="center">

| Method | Endpoint | Description |
|:---:|---|---|
| 🟢 `POST` | `/api/v1/search/` | Submit a search query |
| 🔵 `GET` | `/api/v1/search/status/{job_id}` | Check job progress |
| 🔵 `GET` | `/api/v1/content/` | Get processed results for a query |
| 🔵 `GET` | `/api/v1/content/search` | Full-text search across content |
| 🔵 `GET` | `/api/v1/content/{url_hash}` | Get single document by hash |
| 🔵 `GET` | `/api/v1/content/domain/{domain}` | Get all results from a domain |
| 🔵 `GET` | `/api/v1/analytics/summary` | Summary stats for a query |
| 🔵 `GET` | `/api/v1/analytics/domains` | Domain breakdown |
| 🔵 `GET` | `/api/v1/analytics/quality` | Relevance score distribution |
| 🔵 `GET` | `/api/v1/crawl/queue` | Queue depth |
| 💚 `GET` | `/health/` | Health check |
| 📘 `GET` | `/docs` | Swagger UI |

</div>

---

## 🛑 Stopping the System

```bash
# Stop the Python server
Ctrl+C

# Stop Docker services
docker-compose down

# Stop Docker AND wipe all stored data (fresh start)
docker-compose down -v
```

---

## 🧯 Troubleshooting

<details>
<summary><b>❌ "Connection refused" on startup</b></summary>

```bash
docker-compose ps
docker-compose restart
```
Make sure all three services report `healthy` before starting `main.py`.
</details>

<details>
<summary><b>🔍 "No search results found"</b></summary>

- You need at least one search API key, **or** rely on DuckDuckGo (may be rate-limited)
- Try a simpler query first — `"Apple"` instead of a long phrase
</details>

<details>
<summary><b>📉 Every result shows relevance_score 0.4–0.5</b></summary>

This means `ANTHROPIC_API_KEY` isn't set, so the system is in **heuristic mode**. Add your key in `.env` to unlock real AI scoring.
</details>

<details>
<summary><b>🔌 Port 5432 / 27017 / 6379 already in use</b></summary>

```bash
lsof -i :5432
```

Or remap the port in `docker-compose.yml`:
```yaml
ports: ["5433:5432"]   # left side = your laptop's port
```
Then update `.env`:
```env
POSTGRES_URL=postgresql+asyncpg://postgres:password@localhost:5433/web_intelligence
```
</details>

<details>
<summary><b>🪟 Windows-specific notes</b></summary>

- Use `venv\Scripts\activate` — **not** `source venv/bin/activate`
- Use PowerShell or Command Prompt for venv activation — **not** Git Bash
</details>

---

## 🗃️ Viewing Data Directly

<details>
<summary><b>🍃 MongoDB — processed content</b></summary>

```bash
docker exec -it wi_mongodb mongosh
```
```js
use web_intelligence
db.processed_content.find({query: "your query here"}).limit(5).pretty()
db.processed_content.countDocuments()
db.processed_content.find().sort({relevance_score: -1}).limit(3).pretty()
```
</details>

<details>
<summary><b>🐘 PostgreSQL — URL tracking</b></summary>

```bash
docker exec -it wi_postgres psql -U postgres -d web_intelligence
```
```sql
SELECT status, COUNT(*) FROM search_results GROUP BY status;
SELECT url, status, relevance_score FROM search_results LIMIT 10;
\q
```
</details>

<details>
<summary><b>🔴 Redis — queue depth</b></summary>

```bash
docker exec -it wi_redis redis-cli
```
```
ZCARD wi:queue          # pending jobs in queue
KEYS wi:job:*:stats     # all job stats keys
HGETALL wi:job:YOUR_JOB_ID:stats
```
</details>

---

<div align="center">

### 🧠 `Query in.` → `Intelligence out.`

*Built for teams who need signal, not noise.*

![Made with](https://img.shields.io/badge/made%20with-Python%20%2B%20Docker%20%2B%20Claude-informational?style=for-the-badge)

</div>
