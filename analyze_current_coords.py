#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import pandas as pd
import geocode_hospitals as gh

# Clear cache
gh.CACHE = {}

# Load all hospitals
df = pd.read_csv('hospitals.csv', encoding='utf-8')

accepted = []
city_level = []
failed = []

# Process all rows (no API calls, just check what would happen)
for i, row in df.iterrows():
    name = row.get('Наименование') or ''
    addr = str(row.get('Адрес') or '').strip()
    city_raw = row.get('Населено място')
    city = str(city_raw).strip() if pd.notna(city_raw) and str(city_raw).strip() != '' else str(row.get('Област') or '')
    oblast = str(row.get('Област') or '')
    
    # Check current status in hospitals_with_coords.csv
    coords_df = pd.read_csv('hospitals_with_coords.csv', encoding='utf-8')
    current_row = coords_df.iloc[i]
    lat = current_row.get('lat')
    lng = current_row.get('lng')
    provider = current_row.get('provider')
    display = current_row.get('display_name')
    
    if pd.isna(lat) or pd.isna(lng):
        failed.append({
            'row': i,
            'name': name[:60],
            'addr': addr,
            'city': city,
            'reason': 'Missing coords'
        })
    elif provider in ('nominatim_city', 'city_fallback'):
        city_level.append({
            'row': i,
            'name': name[:60],
            'addr': addr,
            'city': city,
            'provider': provider,
            'display': display[:80] if display else ''
        })
    else:
        # Check city match
        city_match = gh._validate_result_city_match(display, city) if display else False
        if city_match:
            accepted.append({
                'row': i,
                'name': name[:60],
                'provider': provider,
                'display': display[:80] if display else ''
            })
        else:
            failed.append({
                'row': i,
                'name': name[:60],
                'addr': addr,
                'city': city,
                'reason': f'City mismatch: {display[:80] if display else ""}'
            })

# Export results
pd.DataFrame(accepted).to_csv('geocoded_accepted.csv', index=False, encoding='utf-8')
pd.DataFrame(city_level).to_csv('geocoded_city_level.csv', index=False, encoding='utf-8')
pd.DataFrame(failed).to_csv('geocoded_failed.csv', index=False, encoding='utf-8')

print(f"Total: {len(df)}")
print(f"Accepted (good coords): {len(accepted)}")
print(f"City-level (inaccurate): {len(city_level)}")
print(f"Failed (missing/wrong): {len(failed)}")
print()
print(f"Exported:")
print(f"  - geocoded_accepted.csv ({len(accepted)} rows)")
print(f"  - geocoded_city_level.csv ({len(city_level)} rows)")
print(f"  - geocoded_failed.csv ({len(failed)} rows)")
