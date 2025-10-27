# -*- coding: utf-8 -*-
"""
Fix and normalize hospital addresses for better geocoding
"""
import pandas as pd
import re

def normalize_address(addr, city):
    """Normalize address to be more Nominatim-friendly"""
    if pd.isna(addr) or not addr.strip():
        return addr
    
    addr = str(addr).strip()
    
    # Common typos and issues
    fixes = {
        # Typo fixes
        'Боо Божилов': 'Божко Божилов',
        'Пков': 'Петков',
        
        # Remove problematic prefixes/suffixes that confuse geocoder
        'к.к. Албена МЦ Медика-Албена': 'Албена',
        'парк Кайлъка местност Стражата': 'парк Кайлъка',
        'кв. Запад': 'ул. Христо Ботев 1',  # Generic neighborhood, use street instead
        
        # Simplify complex addresses
        'ж.к. Лазур бл. 158': 'жк Лазур 158',
        
        # Fix boulevard/street names
        '25-ти Септември': 'бул. 25-ти Септември',
        'ул. Доц.д-р Константин Кънчев': 'ул. Константин Кънчев',
    }
    
    # Apply direct fixes
    for old, new in fixes.items():
        if old in addr:
            addr = addr.replace(old, new)
    
    # Normalize number signs
    addr = addr.replace('№', '').replace('No.', '').replace('N.', '')
    
    # Normalize жк/ж.к.
    addr = re.sub(r'ж\.к\.\s*', 'жк ', addr)
    
    # Remove floor/entrance details (confuses geocoder)
    addr = re.sub(r'\s+ет\.\s*\d+', '', addr)
    addr = re.sub(r'\s+вх\.\s*[А-Яа-я\d]+', '', addr)
    addr = re.sub(r'\s+партер.*$', '', addr, flags=re.IGNORECASE)
    
    # Remove extra spaces
    addr = re.sub(r'\s+', ' ', addr).strip()
    
    return addr

def fix_city_name(city):
    """Clean up city names"""
    if pd.isna(city):
        return city
    
    city = str(city).strip()
    
    # Remove prefixes
    city = city.replace('ГР.', '').replace('С.', '').replace('К.К.', '')
    city = city.strip()
    
    # Handle special cases
    if 'ОБРОЧИЩЕ' in city or 'АЛБЕНА' in city:
        return 'Албена'
    if 'ДОБРИЧ-ГРАД' in city:
        return 'Добрич'
    
    return city

def main():
    # Read original CSV
    df = pd.read_csv('hospitals.csv', encoding='utf-8')
    
    print(f"Loaded {len(df)} rows")
    
    # Create cleaned version
    df_clean = df.copy()
    
    # Fix addresses
    for i in range(len(df_clean)):
        old_addr = df_clean.at[i, 'Адрес']
        city = df_clean.at[i, 'Населено място']
        
        new_addr = normalize_address(old_addr, city)
        new_city = fix_city_name(city)
        
        if old_addr != new_addr or city != new_city:
            print(f"\n[{i+1}] {df_clean.at[i, 'Наименование'][:50]}")
            if old_addr != new_addr:
                print(f"  Addr: '{old_addr}' -> '{new_addr}'")
            if city != new_city:
                print(f"  City: '{city}' -> '{new_city}'")
        
        df_clean.at[i, 'Адрес'] = new_addr
        df_clean.at[i, 'Населено място'] = new_city
    
    # Save cleaned version
    df_clean.to_csv('hospitals_cleaned.csv', index=False, encoding='utf-8')
    print(f"\n\nSaved cleaned addresses to hospitals_cleaned.csv")
    print(f"Total addresses fixed: {(df['Адрес'] != df_clean['Адрес']).sum()}")

if __name__ == '__main__':
    main()
