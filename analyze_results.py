# -*- coding: utf-8 -*-
"""
Analyze and improve failed geocoding results
"""
import pandas as pd

# Load data
df_all = pd.read_csv('hospitals_ultimate_coords.csv', encoding='utf-8')
df_needs = pd.read_csv('hospitals_needs_manual.csv', encoding='utf-8')

print("="*70)
print("GEOCODING RESULTS ANALYSIS")
print("="*70)
print()

# Overall statistics
total = len(df_all)
scores = df_all['quality_score'].fillna(0)

excellent = (scores >= 80).sum()
good = ((scores >= 60) & (scores < 80)).sum()
fair = ((scores >= 40) & (scores < 60)).sum()
failed = (scores < 40).sum()

print(f"Total hospitals: {total}")
print(f"  Excellent (80-100): {excellent} ({excellent/total*100:.1f}%)")
print(f"  Good (60-79): {good} ({good/total*100:.1f}%)")
print(f"  Fair (40-59): {fair} ({fair/total*100:.1f}%)")
print(f"  Failed (<40): {failed} ({failed/total*100:.1f}%)")
print()
print(f"SUCCESS RATE: {(excellent+good+fair)/total*100:.1f}%")
print()

# Analyze failed cases
print("="*70)
print("FAILED GEOCODING ANALYSIS")
print("="*70)
print()

no_coords = df_needs[df_needs['lat'].isna()].shape[0]
print(f"Without coordinates: {no_coords}")
print()

# Sample problematic addresses
print("Sample of problematic addresses (first 20):")
print("-"*70)
for i, row in df_needs.head(20).iterrows():
    addr = row.get('Адрес', 'N/A')
    city = row.get('Населено място', 'N/A')
    name = row.get('Наименование', 'N/A')[:50]
    print(f"{name}")
    print(f"  Address: {addr}")
    print(f"  City: {city}")
    print()

# Export summary
summary = {
    'Total': total,
    'Excellent': excellent,
    'Good': good,
    'Fair': fair,
    'Failed': failed,
    'Success_Rate': f"{(excellent+good+fair)/total*100:.1f}%"
}

print("="*70)
print("RECOMMENDATIONS:")
print("="*70)
print()
print("1. Manual review needed for 199 hospitals")
print("2. Consider using Google Geocoding API for remaining addresses")
print("3. Some addresses may need correction in source data")
print()

# Save summary
with open('geocoding_summary.txt', 'w', encoding='utf-8') as f:
    f.write("GEOCODING SUMMARY\n")
    f.write("="*70 + "\n\n")
    for key, value in summary.items():
        f.write(f"{key}: {value}\n")

print("Summary saved to: geocoding_summary.txt")
