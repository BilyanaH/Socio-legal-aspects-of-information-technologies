import re
import time
import pandas as pd
import geocode_hospitals as gh

infile = 'missing_coords.csv'
try:
    df = pd.read_csv(infile, encoding='utf-8')
except Exception as e:
    print('Could not read', infile, e)
    raise

outputs = []

def normalize_addr(a):
    if pd.isna(a):
        return ''
    s = str(a)
    s = s.replace('к.к.', '').replace('к.к', '').replace('кв.', '').replace('ж.к.', '').replace('ж.к', '')
    s = s.replace('№', '').replace('  ', ' ').strip()
    return s

for i, row in df.iterrows():
    name = row.get('Наименование', '')
    addr = normalize_addr(row.get('Адрес', ''))
    city = row['Населено място'] if pd.notna(row['Населено място']) and str(row['Населено място']).strip() != '' else row['Област']
    oblast = row['Област']
    print('\n---')
    print(f'Row {i}: {name} | {addr} | {city} | {oblast}')

    tried = set()
    found = None

    variants = [
        f"{name}, {addr}, {city}",
        f"{name}, {city}",
        f"{addr}, {city}",
        f"{addr}",
        f"{name} {addr} {city}",
    ]

    # special fixes: if addr contains 'Албена' but city is weird, try Balchik/Albena
    if 'албен' in addr.lower() or 'албена' in str(city).lower():
        variants += [f"{name}, Албена, Балчик", f"МЦ Медика Албена, Албена, Балчик", f"МЦ Медика, Албена"]

    # for Sofia boulevard variants
    if 'бул' in addr.lower() or 'бул.' in addr.lower():
        variants += [addr.replace('бул.','бул').replace('бул','бул.'), addr.replace('бул.',''), addr.replace('Бул.','')]

    # clean up duplicates
    new_vars = []
    for v in variants:
        vv = re.sub(r'\s+', ' ', str(v)).strip(', ').strip()
        if vv and vv not in tried:
            new_vars.append(vv)
            tried.add(vv)
    variants = new_vars

    for q in variants:
        print('Trying variant:', q)
        # try free-text
        results = gh.nominatim_free_text_search(q, city, oblast, limit=8)
        for cand in results:
            disp = cand.get('display_name','')
            try:
                lat = float(cand.get('lat'))
                lon = float(cand.get('lon'))
            except Exception:
                continue
            print(' -> free-text hit:', disp, lat, lon)
            found = ('nominatim_free', lat, lon, disp, q)
            break
        if found:
            break
        time.sleep(1.0)
        # try Overpass by name only if name exists
        if name and not found:
            o_lat, o_lon, o_disp = gh.geocode_with_overpass(name, city, oblast)
            if o_lat and o_lon:
                print(' -> overpass hit:', o_disp, o_lat, o_lon)
                found = ('overpass', o_lat, o_lon, o_disp, q)
                break
        time.sleep(1.0)
        # google
        gkey = gh.os.environ.get('GOOGLE_API_KEY')
        if gkey and not found:
            g_lat, g_lon, g_disp = gh.geocode_with_google(addr or name, city, oblast, name_hint=name, api_key=gkey)
            if g_lat and g_lon:
                print(' -> google hit:', g_disp, g_lat, g_lon)
                found = ('google', g_lat, g_lon, g_disp, q)
                break
        time.sleep(0.8)

    outputs.append({'index': i, 'name': name, 'addr': addr, 'city': city, 'found': bool(found), 'result': found})

print('\nSummary:')
for o in outputs:
    print(o)

# Optionally, we could write found results to a CSV for review
import csv
with open('missing_coords_attempts.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['index','name','addr','city','found','result'])
    w.writeheader()
    for o in outputs:
        w.writerow(o)

print('\nWrote missing_coords_attempts.csv')
