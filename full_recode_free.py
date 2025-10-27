#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Complete re-geocoding with free methods only
Clears cache and re-geocodes ALL rows
"""
import os, json, time, shutil
import pandas as pd
import geocode_hospitals as gh

print('=== COMPLETE RE-GEOCODING (FREE METHODS) ===')
print()

# Backup
for f in ['geocode_cache.json', 'hospitals_with_coords.csv']:
    if os.path.exists(f):
        shutil.copy(f, f + '.backup2')
        print(f'Backup: {f} -> {f}.backup2')

# CLEAR CACHE COMPLETELY
gh.CACHE = {}
print('Cache cleared - starting fresh')
print()

# Load source
df = pd.read_csv('hospitals.csv', encoding='utf-8')
print(f'Loaded {len(df)} hospitals')
print()

# Add result columns
for col in ['lat', 'lng', 'provider', 'display_name']:
    if col not in df.columns:
        df[col] = None

# Counters
good = 0
city_level = 0
failed = 0

# Geocode ALL rows
for i, row in df.iterrows():
    addr = str(row.get('Адрес') or '').strip()
    city_raw = row.get('Населено място')
    city = str(city_raw).strip() if pd.notna(city_raw) and str(city_raw).strip() != '' else str(row.get('Област') or '')
    oblast = str(row.get('Област') or '')
    name = str(row.get('Наименование') or '')
    
    print(f'[{i+1}/{len(df)}] {name[:55]}...')
    print(f'  {addr} | {city}')
    
    try:
        res = gh.geocode_address(addr, city, oblast, name_hint=name)
    except Exception as e:
        print(f'  ERROR: {e}')
        res = None
    
    if res and res[0] and res[1]:
        lat, lng, provider, display = res
        
        # Validate
        city_match = gh._validate_result_city_match(display, city)
        
        if provider in ('nominatim_city', 'city_fallback'):
            print(f'  CITY-LEVEL (inaccurate): {display[:60]}')
            city_level += 1
            # Save it but mark as city-level
            df.at[i, 'lat'] = lat
            df.at[i, 'lng'] = lng
            df.at[i, 'provider'] = provider + '_INACCURATE'
            df.at[i, 'display_name'] = display
        elif not city_match:
            print(f'  REJECTED (wrong city): {display[:60]}')
            failed += 1
        else:
            df.at[i, 'lat'] = lat
            df.at[i, 'lng'] = lng
            df.at[i, 'provider'] = provider
            df.at[i, 'display_name'] = display
            good += 1
            print(f'  OK: ({lat:.5f}, {lng:.5f}) {provider}')
    else:
        print(f'  FAILED')
        failed += 1
    
    time.sleep(1.1)
    print()

# Save
df.to_csv('hospitals_with_coords.csv', index=False, encoding='utf-8')
with open('geocode_cache.json', 'w', encoding='utf-8') as f:
    json.dump(gh.CACHE, f, ensure_ascii=False, indent=2)

print()
print('=== SUMMARY ===')
print(f'Total: {len(df)}')
print(f'Good coords: {good}')
print(f'City-level (inaccurate): {city_level}')
print(f'Failed/Missing: {failed}')
print()
print(f'Success rate: {good*100//len(df)}%')
print()
print('Saved: hospitals_with_coords.csv')
print('Saved: geocode_cache.json')
