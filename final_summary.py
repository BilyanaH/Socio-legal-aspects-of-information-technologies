# -*- coding: utf-8 -*-
"""
Final Summary of Geocoding Results
"""
import pandas as pd

print("="*70)
print("ФИНАЛНИ РЕЗУЛТАТИ ОТ ГЕОКОДИРАНЕ")
print("="*70)
print()

df = pd.read_csv('hospitals_ultimate_coords.csv', encoding='utf-8')

print(f"📊 Общо болници: {len(df)}")
print()

# Coordinates stats
has_coords = df['lat'].notna()
print(f"✅ С координати: {has_coords.sum()} ({has_coords.sum()/len(df)*100:.1f}%)")
print(f"❌ Без координати: {(~has_coords).sum()} ({(~has_coords).sum()/len(df)*100:.1f}%)")
print()

if has_coords.sum() > 0:
    scores = df[has_coords]['quality_score']
    
    excellent = (scores >= 80).sum()
    good = ((scores >= 60) & (scores < 80)).sum()
    fair = ((scores >= 40) & (scores < 60)).sum()
    poor = (scores < 40).sum()
    
    print("Разбивка по качество:")
    print(f"  ★★★ Отлично (80-100):  {excellent:3d} ({excellent/has_coords.sum()*100:5.1f}%) - Високо доверие")
    print(f"  ★★  Добро (60-79):      {good:3d} ({good/has_coords.sum()*100:5.1f}%) - Средно доверие")
    print(f"  ★   Приемливо (40-59): {fair:3d} ({fair/has_coords.sum()*100:5.1f}%) - Ниско доверие")
    print(f"  ✗   Много ниско (<40):  {poor:3d} ({poor/has_coords.sum()*100:5.1f}%) - Много ниско доверие")
    print()
    
    print("Разбивка по източник:")
    providers = df[has_coords]['provider'].value_counts()
    for provider, count in providers.items():
        pct = count/has_coords.sum()*100
        conf = "ниска точност" if 'lowconf' in provider else "висока точност"
        print(f"  {provider:30s}: {count:3d} ({pct:5.1f}%) - {conf}")
    print()

# Missing breakdown
if (~has_coords).sum() > 0:
    print(f"📋 Болници БЕЗ координати ({(~has_coords).sum()}):")
    missing_df = df[~has_coords][['Наименование', 'Населено място', 'Адрес']].head(10)
    for idx, row in missing_df.iterrows():
        city = row['Населено място']
        addr = row['Адрес'][:50]
        print(f"  - {city}: {addr}")
    
    if (~has_coords).sum() > 10:
        print(f"  ... и още {(~has_coords).sum() - 10}")
    print()

print("="*70)
print("ФАЙЛОВЕ:")
print("="*70)
print(f"  📁 hospitals_ultimate_coords.csv - Всички резултати ({len(df)} реда)")

excellent_df = df[df['quality_score'] >= 80]
if len(excellent_df) > 0:
    excellent_df.to_csv('hospitals_excellent.csv', index=False, encoding='utf-8')
    print(f"  ⭐ hospitals_excellent.csv - Само отлични ({len(excellent_df)} реда)")

lowconf_df = df[(df['quality_score'] < 60) & (df['quality_score'] > 0)]
if len(lowconf_df) > 0:
    lowconf_df.to_csv('hospitals_lowconf.csv', index=False, encoding='utf-8')
    print(f"  ⚠️  hospitals_lowconf.csv - Ниска точност ({len(lowconf_df)} реда)")

missing_df = df[~has_coords]
if len(missing_df) > 0:
    missing_df.to_csv('hospitals_missing.csv', index=False, encoding='utf-8')
    print(f"  ❌ hospitals_missing.csv - Без координати ({len(missing_df)} реда)")

print()
print("="*70)
print("СЛЕДВАЩИ СТЪПКИ:")
print("="*70)
print("  1. Отворете index.html в браузър за визуализация")
print("  2. Проверете hospitals_lowconf.csv за подобрения")
print("  3. Проверете hospitals_missing.csv за ръчно добавяне")
print("="*70)
