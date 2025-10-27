#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Complete re-geocoding with strict validation rules.
Clears bad cache entries and re-geocodes all rows with better providers.
"""

import os
import json
import time
import shutil
import pandas as pd
import geocode_hospitals as gh

CACHE_FILE = 'geocode_cache.json'
CSV_IN = 'hospitals.csv'
CSV_OUT = 'hospitals_with_coords.csv'
BACKUP_SUFFIX = '.backup'

print('=== COMPLETE RE-GEOCODING WITH STRICT VALIDATION ===\n')

# Backup existing files
for f in [CACHE_FILE, CSV_OUT]:
    if os.path.exists(f):
        shutil.copy(f, f + BACKUP_SUFFIX)
        print(f'Backed up: {f} -> {f + BACKUP_SUFFIX}')

# Clear cache completely - start fresh
gh.CACHE = {}
print('\nCleared geocode cache - starting fresh\n')

# Load input hospitals
if not os.path.exists(CSV_IN):
    print(f'ERROR: {CSV_IN} not found')
    raise SystemExit(1)

df = pd.read_csv(CSV_IN, encoding='utf-8')
print(f'Loaded {len(df)} hospitals from {CSV_IN}\n')

# Add result columns if missing
for col in ['lat', 'lng', 'provider', 'display_name']:
    if col not in df.columns:
        df[col] = None

# Re-geocode ALL rows with strict validation
updated = 0
failed = []
city_level = []

for i, row in df.iterrows():
    addr = row.get('Адрес') or ''
    if pd.isna(addr):
        addr = ''
    else:
        addr = str(addr).strip()
    
    city = row.get('Населено място')
    if pd.isna(city) or str(city).strip() == '':
        city = row.get('Област')
    else:
        city = str(city).strip()
    
    oblast = row.get('Област') or ''
    if not pd.isna(oblast):
        oblast = str(oblast).strip()
    
    name = row.get('Наименование') or ''
    
    print(f'\n[{i+1}/{len(df)}] {name}')
    print(f'  Address: {addr}')
    print(f'  City: {city}, Oblast: {oblast}')
    
    try:
        res = gh.geocode_address(addr, city, oblast, name_hint=name)
    except Exception as e:
        print(f'  ERROR: {e}')
        res = None
    
    if res and res[0] and res[1]:
        lat, lng, provider, display = res
        
        # STRICT VALIDATION: reject if display looks wrong
        display_lower = display.lower() if display else ''
        city_lower = city.lower() if city else ''
        
        # Check if result is clearly wrong (different city in display)
        is_suspicious = False
        
        # If provider is city-level, mark it
        if provider in ('nominatim_city', 'city_fallback'):
            print(f'  WARNING: City-level result')
            city_level.append((i, name, addr, city, provider, display))
            is_suspicious = True
        
        # If display doesn't contain expected city name, suspicious
        if city and len(city) > 3:
            city_clean = city.replace('ГР.', '').replace('С.', '').strip()
            if city_clean and len(city_clean) > 3:
                if city_clean.lower() not in display_lower:
                    print(f'  WARNING: Display does not contain city "{city_clean}"')
                    is_suspicious = True
        
        if not is_suspicious:
            df.at[i, 'lat'] = lat
            df.at[i, 'lng'] = lng
            df.at[i, 'provider'] = provider
            df.at[i, 'display_name'] = display
            updated += 1
            print(f'  ✓ ACCEPTED: ({lat}, {lng}) via {provider}')
            print(f'    Display: {display}')
        else:
            # Don't save suspicious results
            print(f'  ✗ REJECTED (suspicious): {display}')
            failed.append((i, name, addr, city))
    else:
        print(f'  ✗ NOT FOUND')
        failed.append((i, name, addr, city))
    
    # Be polite to APIs
    time.sleep(1.3)

# Save results
print(f'\n\n=== SAVING RESULTS ===')
df.to_csv(CSV_OUT, index=False, encoding='utf-8')
print(f'Saved CSV: {CSV_OUT}')

with open(CACHE_FILE, 'w', encoding='utf-8') as f:
    json.dump(gh.CACHE, f, ensure_ascii=False, indent=2)
print(f'Saved cache: {CACHE_FILE}')

# Summary
print(f'\n\n=== SUMMARY ===')
print(f'Total rows: {len(df)}')
print(f'Successfully geocoded (accepted): {updated}')
print(f'City-level (needs review): {len(city_level)}')
print(f'Failed/Rejected: {len(failed)}')

if city_level:
    print(f'\n--- City-level results (may be inaccurate) ---')
    for item in city_level[:10]:
        print(f'  Row {item[0]}: {item[1][:50]} | {item[2]} | {item[3]}')
        print(f'    Provider: {item[4]}, Display: {item[5]}')

if failed:
    print(f'\n--- Failed/Rejected rows ---')
    for item in failed[:15]:
        print(f'  Row {item[0]}: {item[1][:50]}')
        print(f'    Address: {item[2]}, City: {item[3]}')

print('\nDone!')
