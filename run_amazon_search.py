import httpx
import json
import time
import sys
from pathlib import Path

BASE = "http://127.0.0.1:8000"
REPORT_PATH = Path("amazon_search_report.json")

print("Submitting search request for query 'amazon'...")
with httpx.Client(timeout=120.0) as client:
    resp = client.post(
        f"{BASE}/api/v1/search/",
        json={"query": "amazon", "max_results": 30},
    )
    print("search status code:", resp.status_code)
    if resp.status_code != 200:
        print("Search request failed:\n", resp.text)
        sys.exit(1)
    data = resp.json()
    print("search response:", data)
    job_id = data["job_id"]

status = None
for attempt in range(60):
    time.sleep(2)
    resp_status = httpx.get(f"{BASE}/api/v1/search/status/{job_id}")
    if resp_status.status_code != 200:
        print("status request failed:", resp_status.status_code, resp_status.text)
        continue
    status = resp_status.json()
    print(
        f"poll {attempt+1}: {status['progress_pct']}% | pending={status['pending']} completed={status['completed']} failed={status['failed']} skipped={status['skipped']}"
    )
    if status["progress_pct"] >= 100 or status["pending"] == 0:
        break
else:
    print("Timeout waiting for search processing")
    sys.exit(1)

print("Fetching processed content for query 'amazon'...")
resp_content = httpx.get(
    f"{BASE}/api/v1/content/",
    params={"query": "amazon", "min_relevance": 0.0, "limit": 50},
)
print("content status code:", resp_content.status_code)
if resp_content.status_code != 200:
    print(resp_content.text)
    sys.exit(1)
content = resp_content.json()

REPORT_PATH.write_text(
    json.dumps({"search_response": data, "job_status": status, "results": content}, indent=2),
    encoding="utf-8",
)
print("Saved report to", REPORT_PATH)
print("result count", content.get("returned"), "total", content.get("total"))
