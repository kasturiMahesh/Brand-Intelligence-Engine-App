import requests
import time

job_id = "aee9ba5f-33f5-459f-b498-26779d96e22a"
url = f"http://localhost:8000/api/v1/search/status/{job_id}"

while True:
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(f"Progress: {data['progress_pct']}% - Completed: {data['completed']}, Failed: {data['failed']}")
        if data['progress_pct'] == 100.0:
            break
    else:
        print(f"Error: {response.status_code}")
        break
    time.sleep(5)

print("Crawling complete.")