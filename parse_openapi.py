import json
from pathlib import Path

path = Path('backend_openapi.json')
obj = json.loads(path.read_text(encoding='utf-8'))
print('title:', obj['info']['title'])
print('version:', obj['info']['version'])
print('\n--- Paths ---')
for path, methods in obj['paths'].items():
    for method, spec in methods.items():
        print(f"{method.upper()} {path} -> {spec.get('summary','')}")
print('\n--- Schemas ---')
for name in obj.get('components', {}).get('schemas', {}):
    print(name)
