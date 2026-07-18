import httpx
from pathlib import Path

BASE = 'http://127.0.0.1:8000'

resp = httpx.get(f'{BASE}/openapi.json', timeout=30.0)
resp.raise_for_status()
Path('backend_openapi.json').write_text(resp.text, encoding='utf-8')
print('saved backend_openapi.json')
