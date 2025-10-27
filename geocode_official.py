#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Geocode hospitals_official_cleaned.csv with Nominatim
Optimized for maximum accuracy with cleaned addresses
"""
import os, json, time, shutil, sys, codecs
import pandas as pd
import geocode_hospitals as gh

# Fix console encoding for Windows
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

print('=== GEOCODING OFFICIAL HOSPITALS (NOMINATIM) ===')
print()

# Backup existing files
for f in ['geocode_cache.json', 'hospitals_official_with_coords.csv']:
    if os.path.exists(f):
        backup_num = 1
        while os.path.exists(f'{f}.backup{backup_num}'):
            backup_num += 1
        shutil.copy(f, f'{f}.backup{backup_num}')
        print(f'Backup: {f} -> {f}.backup{backup_num}')

# Clear cache for fresh start
gh.CACHE = {}
gh.save_cache(gh.CACHE)
print('Cache cleared')
print()

# Load cleaned addresses
df = pd.read_csv('hospitals_official_cleaned.csv', encoding='utf-8')
print(f'Loaded {len(df)} hospitals')
print(f'Estimated time: {len(df) * 1.0 / 60:.1f} minutes')
print()

# Add result columns
for col in ['lat', 'lng', 'provider', 'display_name']:
    if col not in df.columns:
        df[col] = None

# Statistics
stats = {'good': 0, 'city_level': 0, 'failed': 0}

# Geocode
start_time = time.time()
for i, row in df.iterrows():
    addr = str(row.get('Адрес') or '').strip()
    city_raw = row.get('Населено място')
    city = str(city_raw).strip() if pd.notna(city_raw) and str(city_raw).strip() != '' else str(row.get('Област') or '')
    oblast = str(row.get('Област') or '')
    name = str(row.get('Наименование') or '')
    
    # Progress indicator every 50 rows
    if (i + 1) % 50 == 0 or i == 0:
        elapsed = time.time() - start_time
        rate = (i + 1) / elapsed if elapsed > 0 else 0
        remaining = (len(df) - i - 1) / rate if rate > 0 else 0
        print(f'[{i+1}/{len(df)}] Progress: {(i+1)/len(df)*100:.1f}% | Elapsed: {elapsed/60:.1f}m | Remaining: ~{remaining/60:.1f}m')
        print(f'  Stats so far: Good={stats["good"]} CityLevel={stats["city_level"]} Failed={stats["failed"]}')
    
    # Geocode
    lat, lng, provider, display = gh.geocode_address(addr, city, oblast, name_hint=name)
    
    df.at[i, 'lat'] = lat
    df.at[i, 'lng'] = lng
    df.at[i, 'provider'] = provider
    df.at[i, 'display_name'] = display
    
    # Update stats
    if lat and lng:
        if provider and 'city' in str(provider).lower():
            stats['city_level'] += 1
        else:
            stats['good'] += 1
    else:
        stats['failed'] += 1
    
    # Rate limiting
    time.sleep(1.0)  # Nominatim requires 1 req/sec

# Save results
output_file = 'hospitals_with_coords.csv'
df.to_csv(output_file, index=False, encoding='utf-8')

# Final report
total_time = time.time() - start_time
print()
print('='*70)
print('GEOCODING COMPLETE')
print('='*70)
print(f'Total hospitals: {len(df)}')
print(f'  ✓ Good coordinates: {stats["good"]} ({stats["good"]/len(df)*100:.1f}%)')
print(f'  ~ City-level (inaccurate): {stats["city_level"]} ({stats["city_level"]/len(df)*100:.1f}%)')
print(f'  ✗ Failed: {stats["failed"]} ({stats["failed"]/len(df)*100:.1f}%)')
print(f'Total time: {total_time/60:.1f} minutes')
print(f'Average: {total_time/len(df):.2f} seconds per hospital')
print(f'Output: {output_file}')
print('='*70)

# Save problematic rows for review
problematic = df[(df['lat'].isna()) | (df['provider'].str.contains('city', case=False, na=False))]
if len(problematic) > 0:
    problematic.to_csv('hospitals_official_problems.csv', index=False, encoding='utf-8')
    print(f'\nProblematic rows exported to: hospitals_official_problems.csv ({len(problematic)} rows)')
