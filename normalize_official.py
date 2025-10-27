# -*- coding: utf-8 -*-
"""
Advanced address normalization for hospitals_official.csv
Prepares addresses for maximum geocoding accuracy
"""
import pandas as pd
import re
import sys
import codecs

# Fix console encoding for Windows
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def normalize_address_advanced(addr, city, name):
    """Advanced address normalization for better geocoding"""
    if pd.isna(addr) or not addr.strip():
        return addr
    
    addr = str(addr).strip()
    
    # STEP 1: Remove problematic characters and formatting
    # Remove № symbol (causes issues with some geocoders)
    addr = addr.replace('№', '').replace('No.', '').replace('N.', '')
    
    # Remove floor/entrance/apartment details (confuses geocoders)
    addr = re.sub(r'\s+ет\.\s*\d+', '', addr, flags=re.IGNORECASE)
    addr = re.sub(r'\s+етаж\s+\d+', '', addr, flags=re.IGNORECASE)
    addr = re.sub(r'\s+вх\.\s*[А-Яа-я\d]+', '', addr, flags=re.IGNORECASE)
    addr = re.sub(r'\s+партер.*$', '', addr, flags=re.IGNORECASE)
    addr = re.sub(r'\s+каб\.\s*\d+', '', addr, flags=re.IGNORECASE)
    addr = re.sub(r'\s+апартамент\s+\d+', '', addr, flags=re.IGNORECASE)
    addr = re.sub(r'\s+ап\.\s*\d+', '', addr, flags=re.IGNORECASE)
    
    # STEP 2: Fix common typos and variations
    typo_fixes = {
        'Боо Божилов': 'Божко Божилов',
        'Пков': 'Петков',
        'Доц.д-р': 'Доц. д-р',
        'Д-р': 'д-р',
    }
    
    for old, new in typo_fixes.items():
        addr = addr.replace(old, new)
    
    # STEP 3: Normalize жк/ж.к. and standardize format
    addr = re.sub(r'ж\.к\.\s*', 'жк ', addr)
    addr = re.sub(r'жк\s+', 'жк ', addr)
    
    # STEP 4: Normalize бул/бл/ул abbreviations
    addr = re.sub(r'\bбул\.\s*', 'бул. ', addr)
    addr = re.sub(r'\bул\.\s*', 'ул. ', addr)
    addr = re.sub(r'\bбл\.\s*', 'бл. ', addr)
    
    # STEP 5: Handle specific problematic addresses
    specific_fixes = {
        # Resort/complex addresses
        'к.к. Албена МЦ Медика-Албена': 'Албена',
        'к.к.Албена МЦ Медика-Албена': 'Албена',
        
        # Park/locality addresses
        'парк Кайлъка местност Стражата': 'парк Кайлъка',
        
        # Generic neighborhoods (replace with known street if possible)
        'кв. Запад': city + ' център',  # Use city center as fallback
        
        # Complex medical building descriptions - extract street only
    }
    
    for old, new in specific_fixes.items():
        if old in addr:
            addr = addr.replace(old, new)
    
    # STEP 6: Remove overly detailed building descriptions
    # Example: "бул. Стефан Стамболов №73 приземен етаж ет.1 и част от ет.2..."
    # Keep only: "бул. Стефан Стамболов 73"
    addr = re.sub(r'(бул\.|ул\.)\s*([А-Яа-я\s\-\.]+?)\s+(\d+[А-Яа-я]?)\s+.*?(корпус|блок|сграда|част).*$', 
                  r'\1 \2 \3', addr, flags=re.IGNORECASE)
    
    # STEP 7: Clean up жк addresses with block numbers
    # "жк Лазур бл. 158" -> "жк Лазур 158"
    addr = re.sub(r'(жк\s+[А-Яа-я\s]+)\s+бл\.\s*(\d+)', r'\1 \2', addr)
    
    # STEP 8: Remove extra whitespace
    addr = re.sub(r'\s+', ' ', addr).strip()
    addr = re.sub(r'\s*,\s*', ', ', addr)
    
    # STEP 9: Ensure street number is properly separated
    # "ул. Название123" -> "ул. Название 123"
    addr = re.sub(r'([А-Яа-я])(\d)', r'\1 \2', addr)
    
    return addr

def fix_city_name(city):
    """Clean and normalize city names"""
    if pd.isna(city):
        return city
    
    city = str(city).strip()
    
    # Remove all prefixes
    prefixes = ['ГР.', 'гр.', 'Гр.', 'С.', 'с.', 'К.К.', 'к.к.']
    for prefix in prefixes:
        city = city.replace(prefix, '')
    
    city = city.strip()
    
    # Handle compound names
    city_mappings = {
        'ДОБРИЧ-ГРАД': 'Добрич',
        'СОФИЯ-ГРАД': 'София',
        'ОБРОЧИЩЕ К.К.АЛБЕНА': 'Албена',
        'ОБРОЧИЩЕ АЛБЕНА': 'Албена',
    }
    
    for old, new in city_mappings.items():
        if old in city.upper():
            city = new
            break
    
    # Capitalize properly (first letter uppercase, rest as-is)
    if city.isupper() and len(city) > 3:
        city = city.title()
    
    return city

def main():
    print("=== ADVANCED ADDRESS NORMALIZATION ===\n")
    
    # Read official hospitals file
    df = pd.read_csv('hospitals_offical.csv', encoding='utf-8')
    print(f"Loaded {len(df)} hospitals\n")
    
    # Create cleaned version
    df_clean = df.copy()
    
    # Counters
    addr_fixed = 0
    city_fixed = 0
    
    # Normalize all addresses
    for i in range(len(df_clean)):
        old_addr = df_clean.at[i, 'Адрес']
        old_city = df_clean.at[i, 'Населено място']
        name = df_clean.at[i, 'Наименование']
        
        new_addr = normalize_address_advanced(old_addr, old_city, name)
        new_city = fix_city_name(old_city)
        
        if str(old_addr) != str(new_addr):
            addr_fixed += 1
        
        if str(old_city) != str(new_city):
            city_fixed += 1
        
        df_clean.at[i, 'Адрес'] = new_addr
        df_clean.at[i, 'Населено място'] = new_city
    
    # Save cleaned version
    output_file = 'hospitals_official_cleaned.csv'
    df_clean.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  Total hospitals: {len(df)}")
    print(f"  Addresses normalized: {addr_fixed}")
    print(f"  Cities normalized: {city_fixed}")
    print(f"  Output: {output_file}")
    print(f"{'='*60}\n")
    
    # Show some statistics
    print(f"Unique cities: {df_clean['Населено място'].nunique()}")
    print(f"Unique addresses: {df_clean['Адрес'].nunique()}")

if __name__ == '__main__':
    main()
