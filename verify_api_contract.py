import httpx

BASE = 'http://127.0.0.1:8000'

def main():
    endpoints = [
        ('health', '/health/'),
        ('content', '/api/v1/content/'),
        ('content_search', '/api/v1/content/search'),
        ('analytics_summary', '/api/v1/analytics/summary'),
        ('analytics_domains', '/api/v1/analytics/domains'),
        ('analytics_quality', '/api/v1/analytics/quality'),
        ('crawl_queue', '/api/v1/crawl/queue'),
        ('openapi', '/openapi.json'),
    ]

    params = {
        'content': {'query': 'amazon', 'min_relevance': 0.0, 'limit': 2},
        'content_search': {'q': 'amazon', 'limit': 2},
        'analytics_summary': {'query': 'amazon'},
        'analytics_domains': {'query': 'amazon'},
        'analytics_quality': {'query': 'amazon'},
    }

    with httpx.Client(timeout=30.0) as client:
        for name, path in endpoints:
            try:
                r = client.get(BASE + path, params=params.get(name))
                print(f'--- {name} ---')
                print('status_code:', r.status_code)
                text = r.text
                if len(text) > 2000:
                    text = text[:2000] + '...'
                print(text)
            except Exception as exc:
                print(f'ERROR {name}:', exc)

if __name__ == '__main__':
    main()
