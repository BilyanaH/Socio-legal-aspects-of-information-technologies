import os
import shutil
import json
import time
import pandas as pd
import geocode_hospitals as gh

CACHE_FILE = 'geocode_cache.json'
CSV_FILE = 'hospitals_with_coords.csv'
BACKUP_SUFFIX = '.bak'
THRESHOLD = 3  # cluster size threshold for removal

print('Backing up files...')
for f in (CACHE_FILE, CSV_FILE):
    if os.path.exists(f):
        shutil.copy(f, f + BACKUP_SUFFIX)
        print(f' - backed up {f} -> {f+BACKUP_SUFFIX}')
    else:
        print(f' - {f} not found; continuing')

# Load cache (read file to reflect disk)
try:
    with open(CACHE_FILE, 'r', encoding='utf-8') as fh:
        cache = json.load(fh)
except Exception as e:
    print('Could not read cache file, using gh.CACHE in memory:', e)
    cache = getattr(gh, 'CACHE', {}) or {}

# Group by coordinates
coord_groups = {}
for k, v in cache.items():
    lat = v.get('lat')
    lng = v.get('lng')
    if lat is None or lng is None:
        continue
    key = (str(lat), str(lng))
    coord_groups.setdefault(key, []).append(k)

# Find keys to remove: clusters >= THRESHOLD or generic displays
keys_to_remove = set()
for coord, keys in coord_groups.items():
    if len(keys) >= THRESHOLD:
        keys_to_remove.update(keys)
for k, v in cache.items():
    disp = v.get('display_name')
    try:
        if gh._is_generic_display(disp):
            keys_to_remove.add(k)
    except Exception:
        pass

print(f'Found {len(keys_to_remove)} cache keys to remove (threshold >= {THRESHOLD})')

# Remove keys from cache
if keys_to_remove:
    for k in keys_to_remove:
        cache.pop(k, None)
    # Save cleaned cache immediately
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as fh:
            json.dump(cache, fh, ensure_ascii=False, indent=2)
        print('Wrote cleaned cache to', CACHE_FILE)
    except Exception as e:
        print('Failed to write cleaned cache:', e)
else:
    print('No cache keys to remove')

# Update gh.CACHE in memory to the cleaned cache
gh.CACHE = cache

# Load hospitals CSV
if not os.path.exists(CSV_FILE):
    print('CSV file not found:', CSV_FILE)
    raise SystemExit(1)
df = pd.read_csv(CSV_FILE, encoding='utf-8')

# Build list of rows to re-geocode: those whose cache_key was removed or where lat/lng/provider are missing
rows_to_fix = []
for i, row in df.iterrows():
    addr = '' if pd.isna(row.get('Адрес')) else str(row.get('Адрес'))
    city = row['Населено място'] if pd.notna(row.get('Населено място')) and str(row.get('Населено място')).strip() != '' else row.get('Област')
    oblast = row.get('Област') or ''
    cache_key = f"{addr}||{city}||{oblast}"
    missing = pd.isna(row.get('lat')) or pd.isna(row.get('lng')) or pd.isna(row.get('provider')) or str(row.get('provider')).strip() == ''
    if cache_key in keys_to_remove or missing:
        rows_to_fix.append((i, addr, city, oblast, row.get('Наименование')))

print(f'Rows to re-geocode: {len(rows_to_fix)}')

# Re-geocode affected rows
updated = 0
failed = []
for i, addr, city, oblast, name in rows_to_fix:
    print(f'Re-geocoding row {i}: {name} | {addr} | {city} | {oblast}')
    try:
        res = gh.geocode_address(addr, city, oblast, name_hint=name)
    except Exception as e:
        print(' geocode_address exception:', e)
        res = None
    if res and res[0] and res[1]:
        lat, lng, provider, display = res
        df.at[i, 'lat'] = lat
        df.at[i, 'lng'] = lng
        df.at[i, 'provider'] = provider
        df.at[i, 'display_name'] = display
        updated += 1
        print(f' -> Updated: ({lat}, {lng}) via {provider}')
    else:
        print(' -> Not found')
        failed.append((i, name, addr, city))
    # be polite
    time.sleep(1.2)

# Save updated CSV and cache
if updated:
    df.to_csv(CSV_FILE, index=False, encoding='utf-8')
    print(f'Wrote updated CSV with {updated} updates to {CSV_FILE}')
else:
    print('No updates made to CSV')

try:
    with open(CACHE_FILE, 'w', encoding='utf-8') as fh:
        json.dump(gh.CACHE, fh, ensure_ascii=False, indent=2)
    print('Saved final cache to', CACHE_FILE)
except Exception as e:
    print('Failed saving final cache:', e)

print('\nSummary:')
print(' - cache keys removed:', len(keys_to_remove))
print(' - rows re-geocoded attempted:', len(rows_to_fix))
print(' - rows updated:', updated)
print(' - rows failed:', len(failed))
if failed:
    for f in failed:
        print('  *', f)

print('Done')
