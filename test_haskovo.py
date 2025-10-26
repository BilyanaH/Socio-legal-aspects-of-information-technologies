from geocode_hospitals import geocode_address, nominatim_free_text_search, geocode_with_overpass, geocode_with_nominatim

cases = [
    ("ул. Георги Кирков №24", "Хасково", "Хасково", "ОЧЕН МЕДИЦИНСКИ ЦЕНТЪР ХАСКОВО ООД"),
    ("ул. Хаджи Димитър №2 партер кабинет №1", "Хасково", "Хасково", "ОЧЕН МЕДИЦИНСКИ ЦЕНТЪР ХАСКОВО ООД"),
    ("ул. П. Евтимий №1 ет. нула-партер", "Хасково", "Хасково", "ОЧЕН МЕДИЦИНСКИ ЦЕНТЪР ХАСКОВО ООД"),
]

for addr, city, oblast, name in cases:
    print('\n===')
    print('Input:', addr, city, oblast)
    geoc = geocode_address(addr, city, oblast, name_hint=name)
    print('geocode_address ->', geoc)

    print('\nFree-text Nominatim candidates:')
    ft = nominatim_free_text_search(addr, city, oblast, limit=10)
    if not ft:
        print(' - none')
    for i, r in enumerate(ft, 1):
        print(i, r.get('display_name'), r.get('lat'), r.get('lon'))

    print('\nNominatim structured candidates:')
    try:
        structured = geocode_with_nominatim(addr, city, oblast, name_hint=name, limit=8)
        print(' -> geocode_with_nominatim returns:', structured)
    except Exception as e:
        print('structured error', e)

    print('\nOverpass candidates (by name):')
    try:
        op = geocode_with_overpass(name, city, oblast)
        print(' -> geocode_with_overpass returns:', op)
    except Exception as e:
        print('overpass error', e)

print('\nDone')
