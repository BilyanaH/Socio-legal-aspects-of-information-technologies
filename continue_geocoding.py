# -*- coding: utf-8 -*-
"""
Continue geocoding for hospitals without coordinates
"""
import pandas as pd
import sys
import os

# Import the geocoder
sys.path.insert(0, os.path.dirname(__file__))
from ultimate_geocode import UltimateGeocoder
import time

def main():
    print("="*70)
    print("CONTINUE GEOCODING - Process remaining hospitals")
    print("="*70)
    print()
    
    # Load existing results
    df = pd.read_csv('hospitals_ultimate_coords.csv', encoding='utf-8')
    
    # Find hospitals without coordinates
    missing = df['lat'].isna()
    missing_count = missing.sum()
    
    print(f"Total hospitals: {len(df)}")
    print(f"With coordinates: {(~missing).sum()}")
    print(f"Missing coordinates: {missing_count}")
    print()
    
    if missing_count == 0:
        print("All hospitals already have coordinates!")
        return
    
    print(f"Estimated time: ~{missing_count * 3 / 60:.1f} minutes")
    print()
    
    # Initialize geocoder
    geocoder = UltimateGeocoder()
    
    # Process missing
    start = time.time()
    processed = 0
    
    for i, row in df[missing].iterrows():
        addr = str(row.get('Адрес') or '').strip()
        city = str(row.get('Населено място') or '').strip()
        oblast = str(row.get('Област') or '').strip()
        name = str(row.get('Наименование') or '').strip()
        
        # Use metadata if available
        street_number = row.get('street_number') if pd.notna(row.get('street_number')) else None
        street_name = row.get('street_name_clean') if pd.notna(row.get('street_name_clean')) else None
        
        processed += 1
        
        # Progress
        if processed % 10 == 0 or processed == 1:
            elapsed = time.time() - start
            rate = processed / elapsed if elapsed > 0 else 0
            remaining = (missing_count - processed) / rate if rate > 0 else 0
            
            print(f"[{processed}/{missing_count}] {processed/missing_count*100:.1f}% | "
                  f"Elapsed: {elapsed/60:.1f}m | Remaining: ~{remaining/60:.1f}m")
        
        # Geocode
        lat, lng, provider, display, score = geocoder.geocode(
            addr, city, oblast, name,
            street_number_hint=street_number,
            street_name_hint=street_name
        )
        
        # Update dataframe
        df.at[i, 'lat'] = lat
        df.at[i, 'lng'] = lng
        df.at[i, 'provider'] = provider
        df.at[i, 'display_name'] = display
        df.at[i, 'quality_score'] = score
        
        # Save every 20 hospitals
        if processed % 20 == 0:
            df.to_csv('hospitals_ultimate_coords.csv', index=False, encoding='utf-8')
            print(f"  Saved checkpoint at {processed}/{missing_count}")
    
    # Final save
    df.to_csv('hospitals_ultimate_coords.csv', index=False, encoding='utf-8')
    
    # Final stats
    total_time = time.time() - start
    final_missing = df['lat'].isna().sum()
    
    print()
    print("="*70)
    print("GEOCODING COMPLETE")
    print("="*70)
    print(f"Processed: {processed} hospitals")
    print(f"Time: {total_time/60:.1f} minutes")
    print(f"Still missing: {final_missing}")
    print(f"Total with coordinates: {(~df['lat'].isna()).sum()}/{len(df)}")
    print()
    print("Output: hospitals_ultimate_coords.csv")

if __name__ == '__main__':
    main()
