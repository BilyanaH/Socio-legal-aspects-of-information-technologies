#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple script to re-geocode first 5 rows as a test"""

import os
import json
import time
import pandas as pd
import geocode_hospitals as gh

print('Testing re-geocoding with strict validation...')
print()

# Clear cache
gh.CACHE = {}

# Load first 5 rows
df = pd.read_csv('hospitals.csv', encoding='utf-8')
df = df.head(5)

for col in ['lat', 'lng', 'provider', 'display_name']:
    if col not in df.columns:
        df[col] = None

for i, row in df.iterrows():
    addr = str(row.get('Адрес') or '').strip()
    city = row.get('Населено място')
    if pd.isna(city) or str(city).strip() == '':
        city = row.get('Област')
    else:
        city = str(city).strip()
    
    oblast = str(row.get('Област') or '').strip()
    name = row.get('Наименование') or ''
    
    print(f'\n[{i+1}/5] {name}')
    print(f'  Address: {addr}, City: {city}')
    
    try:
        res = gh.geocode_address(addr, city, oblast, name_hint=name)
    except Exception as e:
        print(f'  ERROR: {e}')
        res = None
    
    if res and res[0] and res[1]:
        lat, lng, provider, display = res
        df.at[i, 'lat'] = lat
        df.at[i, 'lng'] = lng
        df.at[i, 'provider'] = provider
        df.at[i, 'display_name'] = display
        print(f'  OK: ({lat}, {lng}) via {provider}')
        print(f'      {display}')
    else:
        print(f'  FAILED - no result')
    
    time.sleep(1.2)

df.to_csv('test_first_5.csv', index=False, encoding='utf-8')
print('\n\nSaved to test_first_5.csv')
print('Cache entries:', len(gh.CACHE))
