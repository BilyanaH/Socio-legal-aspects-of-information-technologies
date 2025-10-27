import json
from collections import defaultdict
import sys

CACHE_FILE = r'c:\Users\user\Desktop\hospitals\proba\geocode_cache.json'
try:
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    print('Error reading cache:', e)
    sys.exit(1)

groups = defaultdict(list)
for k, v in data.items():
    try:
        lat = v.get('lat')
        lng = v.get('lng')
        if lat is None or lng is None:
            continue
        key = (str(lat), str(lng))
        groups[key].append((k, v.get('display_name')))
    except Exception:
        continue

# find groups with more than 1 key
dups = [(coord, items) for coord, items in groups.items() if len(items) > 1]
# sort by size desc
dups.sort(key=lambda x: -len(x[1]))

print(f'Total cache entries: {len(data)}')
print(f'Coordinate groups with >1 entry: {len(dups)}\n')
for coord, items in dups[:30]:
    print(f'Count={len(items)} coord={coord}')
    for k, disp in items[:20]:
        print(' -', k, '->', disp)
    print()

print('Done')
