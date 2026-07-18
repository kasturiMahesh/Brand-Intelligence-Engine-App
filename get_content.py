import requests
import json
from datetime import datetime

url = "http://localhost:8000/api/v1/content/"
params = {
    "query": "happiness",
    "limit": 10,
    "include_text": True
}

response = requests.get(url, params=params)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"context_{timestamp}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Context saved to {filename}")
else:
    print("Error:", response.text)