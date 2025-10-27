#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Complete re-geocoding for failed and city-level rows with clean cache
"""
import os, json, time, shutil
import pandas as pd
import geocode_hospitals as gh

print('Starting complete re-geocoding...')
print()

# Backup old cache and CSV
for f in ['geocode_cache.json', 'hospitals_with_coords.csv']:
    if os.path.exists(f):
        shutil.copy(f, f + '.pre_recode')
        print(f'Backed up: {f} -> {f}.pre_recode')

# Clear cache completely
gh.CACHE = {}
print('Cleared cache - starting fresh')
print()

# Load input
df_in = pd.read_csv('hospitals.csv', encoding='utf-8')
df_out = pd.read_csv('hospitals_with_coords.csv', encoding='utf-8')

# Load lists
failed_df = pd.read_csv('geocoded_failed.csv', encoding='utf-8')
city_df = pd.read_csv('geocoded_city_level.csv', encoding='utf-8')

# Combine indices
indices_to_fix = set(failed_df['row'].tolist() + city_df['row'].tolist())
print(f'Total rows to re-geocode: {len(indices_to_fix)}')
print()

updated = 0
still_failed = []

for idx in sorted(indices_to_fix):
    row = df_in.iloc[idx]
    addr = str(row.get('Адрес') or '').strip()
    city_raw = row.get('Населено място')
    city = str(city_raw).strip() if pd.notna(city_raw) and str(city_raw).strip() != '' else str(row.get('Област') or '')
    oblast = str(row.get('Област') or '')
    name = str(row.get('Наименование') or '')
    
    print(f'[{idx+1}] {name[:60]}')
    print(f'    Addr: {addr}')
    print(f'    City: {city}')
    
    try:
        res = gh.geocode_address(addr, city, oblast, name_hint=name)
    except Exception as e:
        print(f'    ERROR: {e}')
        res = None
    
    if res and res[0] and res[1]:
        lat, lng, provider, display = res
        
        # Validate city match
        city_match = gh._validate_result_city_match(display, city)
        
        # Reject city-level
        if provider in ('nominatim_city', 'city_fallback'):
            print(f'    SKIP (city-level): {display[:70]}')
            still_failed.append((idx, name[:50], 'City-level'))
        elif not city_match:
            print(f'    SKIP (city mismatch): {display[:70]}')
            still_failed.append((idx, name[:50], 'City mismatch'))
        else:
            df_out.at[idx, 'lat'] = lat
            df_out.at[idx, 'lng'] = lng
            df_out.at[idx, 'provider'] = provider
            df_out.at[idx, 'display_name'] = display
            updated += 1
            print(f'    OK: ({lat:.6f}, {lng:.6f}) via {provider}')
            print(f'        {display[:70]}')
    else:
        print(f'    FAILED (no result)')
        still_failed.append((idx, name[:50], 'No result'))
    
    print()
    time.sleep(1.3)

# Save results
df_out.to_csv('hospitals_with_coords.csv', index=False, encoding='utf-8')
with open('geocode_cache.json', 'w', encoding='utf-8') as f:
    json.dump(gh.CACHE, f, ensure_ascii=False, indent=2)

print('=== SUMMARY ===')
print(f'Attempted: {len(indices_to_fix)}')
print(f'Updated: {updated}')
print(f'Still failed: {len(still_failed)}')
print()

if still_failed:
    print('Still failed/rejected:')
    for item in still_failed[:20]:
        print(f'  Row {item[0]}: {item[1]} - {item[2]}')

print('Done!')
