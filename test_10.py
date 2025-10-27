#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Quick test of first 10 rows with new logic"""
import os, json, time
import pandas as pd
import geocode_hospitals as gh

gh.CACHE = {}

df = pd.read_csv('hospitals.csv', encoding='utf-8')
df = df.head(10)

for col in ['lat', 'lng', 'provider', 'display_name']:
    if col not in df.columns:
        df[col] = None

good = 0
city_level = 0
failed = 0

for i, row in df.iterrows():
    addr = str(row.get('Адрес') or '').strip()
    city_raw = row.get('Населено място')
    city = str(city_raw).strip() if pd.notna(city_raw) and str(city_raw).strip() != '' else str(row.get('Област') or '')
    oblast = str(row.get('Област') or '')
    name = str(row.get('Наименование') or '')
    
    print(f'[{i+1}/10] {name[:50]}')
    
    try:
        res = gh.geocode_address(addr, city, oblast, name_hint=name)
    except Exception as e:
        print(f'  ERROR: {e}')
        res = None
    
    if res and res[0] and res[1]:
        lat, lng, provider, display = res
        city_match = gh._validate_result_city_match(display, city)
        
        if provider in ('nominatim_city', 'city_fallback'):
            print(f'  CITY-LEVEL')
            city_level += 1
        elif not city_match:
            print(f'  REJECTED')
            failed += 1
        else:
            df.at[i, 'lat'] = lat
            df.at[i, 'lng'] = lng
            df.at[i, 'provider'] = provider
            df.at[i, 'display_name'] = display
            good += 1
            print(f'  OK: {provider}')
    else:
        print(f'  FAILED')
        failed += 1
    
    time.sleep(1.1)

print()
print(f'Good: {good}, City-level: {city_level}, Failed: {failed}')

df.to_csv('test_10_rows.csv', index=False, encoding='utf-8')
print('Saved: test_10_rows.csv')
