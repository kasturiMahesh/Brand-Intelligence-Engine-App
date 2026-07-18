import requests

url = "http://localhost:8000/api/v1/search"
data = {
    "query": "happiness",
    "max_results": 5,
    "search_engine": "auto"
}

response = requests.post(url, json=data)
print(response.status_code)
print(response.json())