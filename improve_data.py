# -*- coding: utf-8 -*-
"""
ADVANCED DATA IMPROVEMENT
Подобрява качеството на адресите за максимална точност при геокодиране
"""
import pandas as pd
import re

def advanced_address_normalization(address):
    """Разширена нормализация на адрес"""
    if pd.isna(address) or not address:
        return address
    
    addr = str(address).strip()
    
    # 1. Премахване на излишни символи и формати
    addr = addr.replace('№', '').replace('No', '').replace('no', '')
    addr = addr.replace('ет.', '').replace('етаж', '')
    addr = addr.replace('вх.', '').replace('вход', '')
    addr = addr.replace('ап.', '').replace('апартамент', '')
    addr = addr.replace('партер', '').replace('сутерен', '')
    addr = addr.replace('кабинет', '').replace('каб.', '')
    
    # 2. Стандартизация на съкращения
    addr = re.sub(r'\bул\.\s*', 'ул. ', addr)
    addr = re.sub(r'\bбул\.\s*', 'бул. ', addr)
    addr = re.sub(r'\bжк\s+', 'жк ', addr, flags=re.IGNORECASE)
    addr = re.sub(r'\bж\.к\.\s*', 'жк ', addr, flags=re.IGNORECASE)
    addr = re.sub(r'\bпл\.\s*', 'пл. ', addr)
    
    # 3. Коригиране на често срещани грешки
    replacements = {
        'Боо Божилов': 'Божко Божилов',
        'Боo Божилов': 'Божко Божилов',
        'Христо Смиpненски': 'Христо Смирненски',
        'Христо Смирнeнски': 'Христо Смирненски',
        'Цаp Симеон': 'Цар Симеон',
        'Цаp Освободител': 'Цар Освободител',
        'Шосе Банкя': 'Банкя',
        'пл.пл.': 'пл.',
        'ул.ул.': 'ул.',
        'бул.бул.': 'бул.',
    }
    
    for old, new in replacements.items():
        addr = addr.replace(old, new)
    
    # 4. Премахване на дублирани интервали
    addr = re.sub(r'\s+', ' ', addr)
    
    # 5. Премахване на trailing запетаи и точки
    addr = re.sub(r'[,\.]+$', '', addr).strip()
    
    # 6. Почистване на номера - премахване на текст след номера
    # Пример: "ул. Иван Вазов 15 до болница" -> "ул. Иван Вазов 15"
    match = re.match(r'^(.*?\d+[А-Яа-яA-Za-z]?)(?:\s+(?:до|до|срещу|зад|пред|над|под|в|на)\s+.*)?$', addr)
    if match:
        addr = match.group(1).strip()
    
    # 7. Нормализация на формат "жк + име + номер"
    # "жк Младост 1 бл 20" -> "жк Младост 1, бл. 20"
    addr = re.sub(r'\bбл\s+(\d+)', r'бл. \1', addr)
    addr = re.sub(r'\bблок\s+(\d+)', r'бл. \1', addr)
    
    return addr.strip()

def improve_city_name(city):
    """Подобрена нормализация на град"""
    if pd.isna(city) or not city:
        return city
    
    city = str(city).strip()
    
    # Премахване на префикси
    city = re.sub(r'^ГР\.\s*', '', city, flags=re.IGNORECASE)
    city = re.sub(r'^Г[РP]\s+', '', city, flags=re.IGNORECASE)
    city = re.sub(r'^С\.\s*', '', city, flags=re.IGNORECASE)
    city = re.sub(r'^СЕЛ[ОO]\s+', '', city, flags=re.IGNORECASE)
    city = re.sub(r'^К\.К\.\s*', '', city, flags=re.IGNORECASE)
    
    # Коригиране на грешки
    replacements = {
        'СОФИЯ - ГРАД': 'София',
        'СОФИЯ-ГРАД': 'София',
        'СОФИЯ ГРАД': 'София',
        'С О Ф И Я': 'София',
        'ПЛОВДИВ - ГРАД': 'Пловдив',
        'ПЛОВДИВ-ГРАД': 'Пловдив',
        'ВАРНА - ГРАД': 'Варна',
        'ВАРНА-ГРАД': 'Варна',
        'БУРГАС - ГРАД': 'Бургас',
        'БУРГАС-ГРАД': 'Бургас',
    }
    
    for old, new in replacements.items():
        if city.upper() == old:
            city = new
    
    # Премахване на дублирани интервали
    city = re.sub(r'\s+', ' ', city)
    
    # Title case (първа буква главна)
    # Но запазваме оригинала ако е изцяло главни букви
    if city.isupper() and len(city) > 2:
        city = city.title()
    
    return city.strip()

def extract_building_number(address):
    """Извлича номер на сграда за по-лесно търсене"""
    if pd.isna(address):
        return None
    
    # Търси номер в края или след "бл."
    match = re.search(r'(?:бл\.|блок)\s*(\d+[А-Яа-я]?)', address, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Търси номер в края на адреса
    match = re.search(r'\b(\d+[А-Яа-яA-Za-z]?)(?:\s*[,.]?\s*)?$', address)
    if match:
        return match.group(1)
    
    return None

def extract_street_name_clean(address):
    """Извлича чисто име на улица без префикси и номер"""
    if pd.isna(address):
        return None
    
    addr = str(address)
    
    # Премахване на префикси
    addr = re.sub(r'^(?:ул\.|бул\.|жк|пл\.)\s*', '', addr, flags=re.IGNORECASE)
    
    # Премахване на номер и всичко след него
    addr = re.sub(r'\s+\d+.*$', '', addr)
    
    # Премахване на "бл." и след него
    addr = re.sub(r'\s+бл\..*$', '', addr, re.IGNORECASE)
    
    return addr.strip() if addr.strip() else None

def standardize_hospital_name(name):
    """Стандартизира имена на болници"""
    if pd.isna(name) or not name:
        return name
    
    name = str(name).strip()
    
    # Премахване на излишни кавички
    name = name.replace('"', '').replace('"', '').replace('"', '')
    
    # Стандартизация на МБАЛ
    name = re.sub(r'МБАЛ\s+', 'МБАЛ ', name)
    name = re.sub(r'М\.Б\.А\.Л\.', 'МБАЛ', name)
    
    # Премахване на дублирани интервали
    name = re.sub(r'\s+', ' ', name)
    
    return name.strip()

def main():
    print("="*70)
    print("ADVANCED DATA IMPROVEMENT")
    print("="*70)
    print()
    
    # Зареждане на данни
    df = pd.read_csv('hospitals_official_cleaned.csv', encoding='utf-8')
    print(f"Loaded {len(df)} hospitals")
    print()
    
    # Запазване на оригинални колони за сравнение
    df['original_address'] = df['Адрес'].copy()
    df['original_city'] = df['Населено място'].copy()
    
    # Статистики преди подобрение
    before_empty_addresses = df['Адрес'].isna().sum()
    before_empty_cities = df['Населено място'].isna().sum()
    
    print("Before improvement:")
    print(f"  Empty addresses: {before_empty_addresses}")
    print(f"  Empty cities: {before_empty_cities}")
    print()
    
    # 1. Подобрение на адреси
    print("Step 1: Normalizing addresses...")
    df['Адрес'] = df['Адрес'].apply(advanced_address_normalization)
    
    # 2. Подобрение на градове
    print("Step 2: Normalizing cities...")
    df['Населено място'] = df['Населено място'].apply(improve_city_name)
    
    # 3. Подобрение на имена на болници
    print("Step 3: Standardizing hospital names...")
    if 'Наименование' in df.columns:
        df['Наименование'] = df['Наименование'].apply(standardize_hospital_name)
    
    # 4. Извличане на допълнителни полета за подобрено геокодиране
    print("Step 4: Extracting metadata...")
    df['street_number'] = df['Адрес'].apply(extract_building_number)
    df['street_name_clean'] = df['Адрес'].apply(extract_street_name_clean)
    
    # 5. Създаване на подобрен пълен адрес за геокодиране
    print("Step 5: Creating optimized search queries...")
    df['search_query'] = df.apply(
        lambda row: f"{row['Адрес']}, {row['Населено място']}, България" 
        if pd.notna(row['Адрес']) and pd.notna(row['Населено място']) 
        else None,
        axis=1
    )
    
    # Статистики след подобрение
    after_empty_addresses = df['Адрес'].isna().sum()
    after_empty_cities = df['Населено място'].isna().sum()
    
    # Колко адреса са променени
    changed_addresses = (df['original_address'] != df['Адрес']).sum()
    changed_cities = (df['original_city'] != df['Населено място']).sum()
    
    print()
    print("="*70)
    print("IMPROVEMENT RESULTS")
    print("="*70)
    print(f"Addresses normalized: {changed_addresses}/{len(df)} ({changed_addresses/len(df)*100:.1f}%)")
    print(f"Cities normalized: {changed_cities}/{len(df)} ({changed_cities/len(df)*100:.1f}%)")
    print()
    print(f"Street numbers extracted: {df['street_number'].notna().sum()}")
    print(f"Clean street names: {df['street_name_clean'].notna().sum()}")
    print(f"Search queries created: {df['search_query'].notna().sum()}")
    print()
    
    # Показване на примери за подобрения
    print("Sample improvements:")
    print("-" * 70)
    
    changed = df[df['original_address'] != df['Адрес']].head(10)
    for idx, row in changed.iterrows():
        print(f"\nBefore: {row['original_address']}")
        print(f"After:  {row['Адрес']}")
        if pd.notna(row['street_number']):
            print(f"Number: {row['street_number']}")
        if pd.notna(row['street_name_clean']):
            print(f"Street: {row['street_name_clean']}")
    
    # Запазване на подобрените данни
    output = 'hospitals_official_improved.csv'
    df.to_csv(output, index=False, encoding='utf-8')
    
    print()
    print("="*70)
    print(f"Improved data saved to: {output}")
    print("="*70)
    print()
    print("New columns added:")
    print("  - street_number: Extracted building number")
    print("  - street_name_clean: Clean street name without number")
    print("  - search_query: Optimized query for geocoding")
    print("  - original_address: Original address for comparison")
    print("  - original_city: Original city for comparison")
    print()
    print("Ready for enhanced geocoding!")

if __name__ == '__main__':
    main()
