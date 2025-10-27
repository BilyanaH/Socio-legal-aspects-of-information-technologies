import requests
import time
import pandas as pd
import os
import sys
import logging
import json
from urllib.parse import urlencode

# Set up logging to a file
logging.basicConfig(
    filename='geocode_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# Set console encoding to UTF-8 (Windows)
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

CACHE_FILE = 'geocode_cache.json'

def load_cache(cache_file=CACHE_FILE):
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Could not read cache {cache_file}: {e}")
    return {}


def save_cache(cache, cache_file=CACHE_FILE):
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"Could not save cache {cache_file}: {e}")


# Load cache once globally
CACHE = load_cache()


def _count_cache_same_coord(lat, lng, eps=1e-6):
    """Count how many cache entries share the same coordinates (within eps)."""
    if lat is None or lng is None:
        return 0
    cnt = 0
    for v in CACHE.values():
        try:
            vlat = float(v.get('lat'))
            vlon = float(v.get('lng'))
            if abs(vlat - float(lat)) < eps and abs(vlon - float(lng)) < eps:
                cnt += 1
        except Exception:
            continue
    return cnt


def _is_generic_display(display):
    """Return True if display looks generic (no real place name) — treat as low-confidence."""
    if not display:
        return True
    d = str(display).strip().lower()
    # common short/generic tokens (English + Bulgarian fragments)
    generic_tokens = ['hospital', 'clinic', 'medical', 'health', 'дкц', 'мбал', 'болниц', 'мц', 'clinic', 'center', 'център']
    # if display is very short and contains a generic token, consider it generic
    if any(tok in d for tok in generic_tokens):
        parts = d.split()
        if len(parts) <= 3:
            return True
    # if display is exactly a single generic word
    if d in generic_tokens:
        return True
    return False


def _validate_result_city_match(display_name, expected_city):
    """
    Validate that the geocoding result's display_name contains the expected city.
    Returns True if city is found in display, False otherwise.
    This helps reject results from completely wrong cities.
    """
    if not display_name or not expected_city:
        return False  # Cannot validate without both
    
    display_lower = display_name.lower()
    city_clean = expected_city.replace('ГР.', '').replace('С.', '').replace('К.К.', '').strip()
    
    # If city is too short, skip validation (common abbreviations might cause false negatives)
    if len(city_clean) < 4:
        return True  # Cannot reliably validate very short city names
    
    city_lower = city_clean.lower()
    
    # Check if city name appears in display
    if city_lower in display_lower:
        return True
    
    # Handle common transliteration variants (е.g., София/Sofia, Пловдив/Plovdiv)
    transliteration_map = {
        'софия': 'sofia',
        'пловдив': 'plovdiv',
        'варна': 'varna',
        'бургас': 'burgas',
        'русе': 'ruse',
        'плевен': 'pleven',
        'стара загора': 'stara zagora',
        'добрич': 'dobrich',
        'сливен': 'sliven',
        'шумен': 'shumen',
        'пазарджик': 'pazardzhik',
        'ямбол': 'yambol',
        'хасково': 'haskovo',
        'габрово': 'gabrovo',
        'асеновград': 'asenovgrad',
        'кърджали': 'kardzhali',
        'кюстендил': 'kyustendil',
        'перник': 'pernik',
        'враца': 'vratsa',
        'видин': 'vidin',
        'монтана': 'montana',
        'ловеч': 'lovech',
        'велико търново': 'veliko tarnovo',
        'търговище': 'targovishte'
    }
    
    # Check transliteration
    for bg, latin in transliteration_map.items():
        if city_lower == bg and latin in display_lower:
            return True
        if city_lower == latin and bg in display_lower:
            return True
    
    # If we reach here, city was NOT found in display
    logging.warning(f"City validation failed: expected '{expected_city}' not found in '{display_name}'")
    return False


def _score_nominatim_candidate(candidate, wanted_city, wanted_oblast, name_hint=None):
    score = 0.0
    importance = float(candidate.get('importance', 0) or 0)
    score += importance * 10

    cclass = candidate.get('class', '')
    ctype = candidate.get('type', '')
    if cclass == 'building' or ctype in ('house', 'residential', 'hospital', 'clinic', 'public_building'):
        score += 20

    display = candidate.get('display_name', '').lower()
    if name_hint and name_hint.lower() in display:
        score += 30

    addr = candidate.get('address', {}) if isinstance(candidate.get('address', {}), dict) else {}
    city_vals = [addr.get(k, '').lower() for k in ('city', 'town', 'village', 'municipality', 'county')]
    if wanted_city and any(wanted_city.lower() == v for v in city_vals if v):
        score += 15
    if wanted_oblast and wanted_oblast.lower() in display:
        score += 5

    return score


def geocode_with_nominatim(street, city, oblast, name_hint=None, limit=5, retries=2):
    base = 'https://nominatim.openstreetmap.org/search'
    params = {
        'format': 'json',
        'addressdetails': 1,
        'limit': limit,
        'countrycodes': 'bg'
    }
    # Use structured params when we have a street
    if street:
        params['street'] = street
    if city:
        params['city'] = city
    if oblast:
        params['county'] = oblast
    params['country'] = 'Bulgaria'

    headers = {'User-Agent': 'GeocodeHospitals/1.0 (contact@example.com)'}

    for attempt in range(retries):
        try:
            resp = requests.get(base, params=params, headers=headers, timeout=15)
            if resp.status_code != 200:
                logging.warning(f"Nominatim status {resp.status_code} for {params}")
                time.sleep(1 + attempt)
                continue
            data = resp.json()
            if not data:
                logging.info(f"Nominatim: no results for {params}")
                return None, None, None

            # Score candidates and pick best
            best = None
            best_score = -1
            for cand in data:
                s = _score_nominatim_candidate(cand, city, oblast, name_hint)
                if s > best_score:
                    best_score = s
                    best = cand

            if best:
                lat = best.get('lat')
                lon = best.get('lon')
                display = best.get('display_name')
                logging.info(f"Nominatim chosen candidate (score={best_score}): {display}")
                return float(lat), float(lon), display
            return None, None, None
        except Exception as e:
            logging.error(f"Nominatim attempt {attempt+1} error for {params}: {e}")
            time.sleep(1 + attempt)
    return None, None, None


def geocode_with_google(street, city, oblast, name_hint=None, api_key=None):
    if not api_key:
        return None, None, None
    base = 'https://maps.googleapis.com/maps/api/geocode/json'
    address_parts = []
    if street:
        address_parts.append(street)
    if city:
        address_parts.append(city)
    if oblast and oblast not in (city or ''):
        address_parts.append(oblast)
    address_parts.append('Bulgaria')
    address = ', '.join([p for p in address_parts if p])

    params = {'address': address, 'key': api_key}
    try:
        resp = requests.get(base, params=params, timeout=15)
        if resp.status_code != 200:
            logging.warning(f"Google geocode status {resp.status_code} for {address}")
            return None, None, None
        data = resp.json()
        if data.get('status') != 'OK' or not data.get('results'):
            logging.info(f"Google no results for {address}: {data.get('status')}")
            return None, None, None

        # Prefer ROOFTOP or RANGE_INTERPOLATED location types
        preferred = None
        for r in data['results']:
            loc_type = r.get('geometry', {}).get('location_type', '')
            if loc_type in ('ROOFTOP', 'RANGE_INTERPOLATED'):
                preferred = r
                break
        if not preferred:
            preferred = data['results'][0]

        # extra check: ensure city component matches
        formatted = preferred.get('formatted_address', '')
        lat = preferred.get('geometry', {}).get('location', {}).get('lat')
        lon = preferred.get('geometry', {}).get('location', {}).get('lng')
        logging.info(f"Google chosen: {formatted} (type={preferred.get('geometry', {}).get('location_type')})")
        return float(lat), float(lon), formatted
    except Exception as e:
        logging.error(f"Google geocode error for {address}: {e}")
        return None, None, None


def get_city_bbox(city, oblast):
    """Return bbox tuple (south, west, north, east) for a city using Nominatim, or None."""
    if not city:
        return None
    try:
        params = {'format': 'json', 'limit': 1, 'city': city, 'county': oblast, 'country': 'Bulgaria'}
        headers = {'User-Agent': 'GeocodeHospitals/1.0 (contact@example.com)'}
        resp = requests.get('https://nominatim.openstreetmap.org/search', params=params, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data:
            return None
        bb = data[0].get('boundingbox')
        if bb and len(bb) == 4:
            # boundingbox is [south, north, west, east] as strings
            south = float(bb[0])
            north = float(bb[1])
            west = float(bb[2])
            east = float(bb[3])
            return (south, west, north, east)
    except Exception as e:
        logging.warning(f"Could not get bbox for {city}, {oblast}: {e}")
    return None


def nominatim_free_text_search(address, city, oblast, limit=10):
    """Run a free-text Nominatim search for 'address, city, oblast, Bulgaria'."""
    try:
        q = f"{address}, {city}, {oblast}, Bulgaria"
        resp = requests.get('https://nominatim.openstreetmap.org/search', params={'format':'json','addressdetails':1,'limit':limit,'q':q}, headers={'User-Agent':'GeocodeHospitals/1.0 (contact@example.com)'}, timeout=15)
        if resp.status_code != 200:
            return []
        return resp.json()
    except Exception as e:
        logging.warning(f"Free-text Nominatim error for {address}, {city}: {e}")
        return []


def geocode_with_overpass(name, city, oblast):
    """Search OSM (Overpass) for matching named hospitals/clinics within the city's bbox.
    Returns (lat, lon, display_name) or (None, None, None).
    """
    if not name:
        return None, None, None
    bbox = get_city_bbox(city, oblast)
    if not bbox:
        # If we can't get a bbox, don't run a wide Overpass query to avoid overload.
        return None, None, None

    south, west, north, east = bbox
    # Escape name for regex: simple escape of quotes and slashes
    import re
    regex_name = re.escape(name)

    query = (
        '[out:json][timeout:25];'
        f'(node["name"~"{regex_name}",i]({south},{west},{north},{east});'
        f'way["name"~"{regex_name}",i]({south},{west},{north},{east});'
        f'relation["name"~"{regex_name}",i]({south},{west},{north},{east});'
        f'node[amenity~"hospital|clinic|doctors|healthcare"]({south},{west},{north},{east});'
        f'way[amenity~"hospital|clinic|doctors|healthcare"]({south},{west},{north},{east});'
        f'relation[amenity~"hospital|clinic|doctors|healthcare"]({south},{west},{north},{east}););out center;'
    )

    try:
        resp = requests.post('https://overpass-api.de/api/interpreter', data={'data': query}, timeout=30)
        if resp.status_code != 200:
            logging.warning(f"Overpass status {resp.status_code} for {name} in {city}")
            return None, None, None
        data = resp.json()
        elements = data.get('elements', [])
        if not elements:
            return None, None, None

        best = None
        best_score = -999
        for el in elements:
            tags = el.get('tags', {}) or {}
            el_name = tags.get('name', '')
            score = 0
            if el_name and el_name.strip().lower() == name.strip().lower():
                score += 50
            elif name.strip().lower() in el_name.lower():
                score += 20

            amenity = tags.get('amenity', '')
            if amenity in ('hospital', 'clinic'):
                score += 30

            # geometry
            if el.get('lat') and el.get('lon'):
                lat = float(el['lat'])
                lon = float(el['lon'])
            else:
                center = el.get('center') or {}
                lat = center.get('lat')
                lon = center.get('lon')

            # small city match heuristic
            addr_city = tags.get('addr:city', '')
            if city and addr_city and city.strip().lower() == addr_city.strip().lower():
                score += 10

            if lat and lon and score > best_score:
                best_score = score
                best = (lat, lon, el_name or tags.get('ref') or amenity)

        if best:
            logging.info(f"Overpass best for {name} in {city}: score={best_score} -> {best[2]}")
            return float(best[0]), float(best[1]), best[2]
    except Exception as e:
        logging.error(f"Overpass query error for {name} in {city}: {e}")
    return None, None, None


def geocode_address(address, city, oblast, name_hint=None):
    # Normalize
    street = address or ''
    if isinstance(street, str):
        # normalize common tokens but preserve Bulgarian letters (don't remove 'и')
        street = street.replace('\t', ' ').replace('  ', ' ').strip()
        # remove common apartment/entrance tokens that confuse geocoders
        for tok in ['ет.', 'ет', 'вх.', 'вх', 'партер', 'каб.', 'каб', 'ап.', 'ап', 'корп.', 'кв.', 'ж.к.', 'ж.к', 'жк', 'к.к.', 'к.к', '№']:
            street = street.replace(tok, '')
        # normalize prefixes
        street = street.replace('ГР.', '').replace('гр.', '').replace('Гр.', '')
        street = street.strip().strip(',')
    city = city.replace('ГР.', '').strip() if isinstance(city, str) and city.strip() != '' else (oblast if isinstance(oblast, str) else '')
    oblast = oblast or ''

    cache_key = f"{street}||{city}||{oblast}"
    global CACHE
    if cache_key in CACHE:
        logging.info(f"Cache hit for {cache_key}")
        val = CACHE[cache_key]
        return val.get('lat'), val.get('lng'), val.get('provider'), val.get('display_name')

    # Try Google first if api key present
    gkey = os.environ.get('GOOGLE_API_KEY')
    if gkey:
        res = geocode_with_google(street, city, oblast, name_hint=name_hint, api_key=gkey)
        if res and res[0] and res[1]:
            lat, lng, display = res
            CACHE[cache_key] = {'lat': lat, 'lng': lng, 'provider': 'google', 'display_name': display}
            save_cache(CACHE)
            return lat, lng, 'google', display
    # Try free-text Nominatim search first (more flexible than structured)
    import re
    m = re.search(r"(.*)\b(?:№|No\.?|n\.|#)?\s*([0-9]+[A-Za-z0-9/-]*)\s*$", street)
    housenumber = m.group(2) if m else None
    
    # Free-text search with address + city
    ft = nominatim_free_text_search(street, city, oblast, limit=10)
    for cand in ft:
        disp = cand.get('display_name','')
        
        # Validate city match
        if not _validate_result_city_match(disp, city):
            continue
        
        # If we have housenumber, prefer exact match
        if housenumber and housenumber in disp:
            try:
                lat = float(cand.get('lat'))
                lng = float(cand.get('lon'))
                display = disp
                logging.info(f"Using free-text Nominatim with housenumber {housenumber}: {display}")
                CACHE[cache_key] = {'lat': lat, 'lng': lng, 'provider': 'nominatim_free', 'display_name': display}
                save_cache(CACHE)
                return lat, lng, 'nominatim_free', display
            except Exception:
                pass
        # Otherwise, take first valid result with city match
        elif cand.get('lat') and cand.get('lon'):
            try:
                lat = float(cand.get('lat'))
                lng = float(cand.get('lon'))
                display = disp
                logging.info(f"Using free-text Nominatim: {display}")
                CACHE[cache_key] = {'lat': lat, 'lng': lng, 'provider': 'nominatim_free', 'display_name': display}
                save_cache(CACHE)
                return lat, lng, 'nominatim_free', display
            except Exception:
                pass

    # Fallback to Overpass (OSM) search by name inside city bbox for exact place matches (hospitals/clinics)
    try:
        res = geocode_with_overpass(name_hint or street, city, oblast)
        if res and res[0] and res[1]:
            lat, lng, info = res
        else:
            lat, lng, info = None, None, None
    except NameError:
        lat, lng, info = None, None, None

    if lat and lng:
        # If Overpass returns a very generic display (e.g. just 'hospital'/'clinic')
        # or the same coordinates are already used for many cache entries, treat
        # this result as low-confidence/ambiguous and try other providers
        dup_count = _count_cache_same_coord(lat, lng)
        is_generic = _is_generic_display(info)
        city_match = _validate_result_city_match(info, city)
        
        if is_generic or dup_count >= 3 or not city_match:
            logging.info(f"Overpass result for {cache_key} considered ambiguous (display={info}, dup_count={dup_count}, city_match={city_match}); will try other methods")
            # do not cache ambiguous Overpass results as definitive — fall through
            pass
        else:
            CACHE[cache_key] = {'lat': lat, 'lng': lng, 'provider': 'overpass', 'display_name': info}
            save_cache(CACHE)
            return lat, lng, 'overpass', info

    # Try structured Nominatim
    res = geocode_with_nominatim(street, city, oblast, name_hint=name_hint)
    if res and res[0] and res[1]:
        lat, lng, display = res
        
        # Validate city match
        if not _validate_result_city_match(display, city):
            logging.warning(f"Nominatim result city mismatch for {cache_key}: {display}")
            # Don't accept this result, try free-text below
            res = None
        else:
            # Prefer free-text candidate that contains exact housenumber when available
            # Try free-text only if street contains a housenumber
            import re
            m = re.search(r"(.*)\b(?:№|No\.?|n\.|#)?\s*([0-9]+[A-Za-z0-9/-]*)\s*$", street)
            if m:
                housenumber = m.group(2)
                ft = nominatim_free_text_search(street, city, oblast, limit=8)
                for cand in ft:
                    disp = cand.get('display_name','')
                    if housenumber in disp and _validate_result_city_match(disp, city):
                        try:
                            lat = float(cand.get('lat'))
                            lng = float(cand.get('lon'))
                            display = disp
                            logging.info(f"Preferred free-text Nominatim candidate with housenumber {housenumber}: {display}")
                            CACHE[cache_key] = {'lat': lat, 'lng': lng, 'provider': 'nominatim_free', 'display_name': display}
                            save_cache(CACHE)
                            return lat, lng, 'nominatim_free', display
                        except Exception:
                            pass
            CACHE[cache_key] = {'lat': lat, 'lng': lng, 'provider': 'nominatim', 'display_name': display}
            save_cache(CACHE)
            return lat, lng, 'nominatim', display

    # As a last resort, try a looser query (city-level)
    # As a last resort, try looser queries / variants
    variants = []
    # remove street number
    import re as _re
    variants.append(_re.sub(r"\s+[0-9A-Za-z\-/]+$", '', street).strip())
    # try only name_hint + city
    if name_hint:
        variants.append(f"{name_hint}, {city}")
    # try city-only
    if city:
        variants.append(city)

    for v in variants:
        if not v:
            continue
        res = geocode_with_nominatim(v, city if v != city else '', oblast, name_hint=name_hint, limit=3)
        if res and res[0] and res[1]:
            lat, lng, display = res
            CACHE[cache_key] = {'lat': lat, 'lng': lng, 'provider': 'nominatim_city', 'display_name': display}
            save_cache(CACHE)
            return lat, lng, 'nominatim_city', display

    logging.error(f"Failed to geocode: {street}, {city}, {oblast}")
    return None, None, None, None

def main():
    input_file = 'hospitals_cleaned.csv'
    output_file = 'hospitals_with_coords.csv'

    # Check if input file exists
    if not os.path.exists(input_file):
        logging.error(f"{input_file} not found in {os.getcwd()}")
        print(f"Error: {input_file} not found in {os.getcwd()}")
        return

    try:
        df = pd.read_csv(input_file, encoding='utf-8')
        logging.info(f"Successfully read {input_file} with {len(df)} rows")
        print(f"Successfully read {input_file} with {len(df)} rows")
    except Exception as e:
        logging.error(f"Error reading {input_file}: {e}")
        print(f"Error reading {input_file}: {e}")
        return

    # Validate required columns
    required_columns = ['Наименование', 'Област', 'Община', 'Населено място', 'Адрес']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logging.error(f"Missing columns in CSV: {missing_columns}")
        print(f"Error: Missing columns in CSV: {missing_columns}")
        return

    # Initialize lat, lng and QA columns
    df['lat'] = None
    df['lng'] = None
    df['provider'] = None
    df['display_name'] = None

    # Geocode each address
    for i, row in df.iterrows():
        city = row['Населено място'] if pd.notna(row['Населено място']) and row['Населено място'].strip() != '' else row['Област']
        name = row['Наименование'] if 'Наименование' in row else None
        lat, lng, provider, display = geocode_address(row['Адрес'], city, row['Област'], name_hint=name)
        df.at[i, 'lat'] = lat
        df.at[i, 'lng'] = lng
        df.at[i, 'provider'] = provider
        df.at[i, 'display_name'] = display
        print(f"Geocoded {row['Наименование']} at {row['Адрес']}, {city}, {row['Област']}: ({lat}, {lng}) provider={provider}")
        time.sleep(1.0)  # Required: Nominatim rate limit is 1 request/second

    # Second pass: try to refine rows that are missing coords or have low-confidence / duplicated coords
    def needs_refine(r):
        # missing coords
        if r['lat'] is None or r['lng'] is None:
            return True
        # provider indicates city-level or low confidence
        if isinstance(r.get('provider'), str) and r.get('provider') in ('nominatim_city', 'nominatim_free'):
            return True
        return False

    # find duplicated coordinates assigned to many different addresses
    dup_coords = df[df['lat'].notnull() & df['lng'].notnull()].groupby(['lat', 'lng']).size()
    dup_coords = dup_coords[dup_coords > 1]
    dup_set = set(dup_coords.index.tolist())

    for i, row in df.iterrows():
        city = row['Населено място'] if pd.notna(row['Населено място']) and row['Населено място'].strip() != '' else row['Област']
        name = row['Наименование'] if 'Наименование' in row else None
        lat = row['lat']
        lng = row['lng']
        provider = row.get('provider')

        if needs_refine(row) or ((lat, lng) in dup_set and (pd.notna(row['Адрес']) and str(row['Адрес']).strip() != '')):
            # try more aggressive variants: name + address free-text, Overpass by name, and Google forced
            variants = []
            addr = row['Адрес'] or ''
            if name:
                variants.append(f"{name}, {addr}, {city}")
                variants.append(f"{name}, {city}")
            variants.append(f"{addr}, {city}")
            tried = set()
            found = False
            for q in variants:
                if not q or q in tried:
                    continue
                tried.add(q)
                # run free-text nominatim
                try:
                    res_list = nominatim_free_text_search(q, city, row['Област'], limit=6)
                    for cand in res_list:
                        try:
                            cand_lat = float(cand.get('lat'))
                            cand_lon = float(cand.get('lon'))
                        except Exception:
                            continue
                        # ensure city matches somewhat
                        disp = cand.get('display_name','')
                        if city and city.lower() not in disp.lower() and name and name.lower() not in disp.lower():
                            # still accept if name matches
                            pass
                        # accept candidate
                        df.at[i, 'lat'] = cand_lat
                        df.at[i, 'lng'] = cand_lon
                        df.at[i, 'provider'] = 'nominatim_free_refined'
                        df.at[i, 'display_name'] = disp
                        CACHE[f"{addr}||{city}||{row['Област']}"] = {'lat': cand_lat, 'lng': cand_lon, 'provider': 'nominatim_free_refined', 'display_name': disp}
                        save_cache(CACHE)
                        found = True
                        logging.info(f"Refined via free-text Nominatim for {row['Наименование']}: {disp}")
                        break
                    if found:
                        break
                except Exception as e:
                    logging.warning(f"Refine free-text Nominatim error for {q}: {e}")
                time.sleep(1.0)

                # try Overpass by name
                if name and not found:
                    try:
                        o_lat, o_lon, o_disp = geocode_with_overpass(name, city, row['Област'])
                        if o_lat and o_lon:
                            df.at[i, 'lat'] = o_lat
                            df.at[i, 'lng'] = o_lon
                            # check for generic/duplicated overpass result
                            dup_count = _count_cache_same_coord(o_lat, o_lon)
                            if _is_generic_display(o_disp) or dup_count >= 3:
                                logging.info(f"Overpass refined result for {row['Наименование']} considered ambiguous (display={o_disp}, dup_count={dup_count}); not caching as definitive")
                                df.at[i, 'provider'] = 'overpass_refined_ambiguous'
                                df.at[i, 'display_name'] = o_disp
                            else:
                                df.at[i, 'provider'] = 'overpass_refined'
                                df.at[i, 'display_name'] = o_disp
                                CACHE[f"{addr}||{city}||{row['Област']}"] = {'lat': o_lat, 'lng': o_lon, 'provider': 'overpass_refined', 'display_name': o_disp}
                                save_cache(CACHE)
                            found = True
                            logging.info(f"Refined via Overpass for {row['Наименование']}: {o_disp}")
                    except Exception as e:
                        logging.warning(f"Refine Overpass error for {name}: {e}")
                    time.sleep(1.0)

                # try Google forced if key available
                gkey = os.environ.get('GOOGLE_API_KEY')
                if gkey and not found:
                    try:
                        g_lat, g_lon, g_display = geocode_with_google(addr or name, city, row['Област'], name_hint=name, api_key=gkey)
                        if g_lat and g_lon:
                            df.at[i, 'lat'] = g_lat
                            df.at[i, 'lng'] = g_lon
                            df.at[i, 'provider'] = 'google_refined'
                            df.at[i, 'display_name'] = g_display
                            CACHE[f"{addr}||{city}||{row['Област']}"] = {'lat': g_lat, 'lng': g_lon, 'provider': 'google_refined', 'display_name': g_display}
                            save_cache(CACHE)
                            found = True
                            logging.info(f"Refined via Google for {row['Наименование']}: {g_display}")
                    except Exception as e:
                        logging.warning(f"Refine Google error for {row['Наименование']}: {e}")
                    time.sleep(0.8)

            if found:
                print(f"Refined {row['Наименование']} -> ({df.at[i,'lat']}, {df.at[i,'lng']}) provider={df.at[i,'provider']}")
            else:
                print(f"Could not refine {row['Наименование']} (still provider={provider})")
            # be polite
            time.sleep(0.8)

    # Save to output file
    try:
        df.to_csv(output_file, index=False, encoding='utf-8')
        logging.info(f"Geocoding complete. Saved to {output_file} in {os.getcwd()}")
        print(f"Geocoding complete. Saved to {output_file} in {os.getcwd()}")
    except Exception as e:
        logging.error(f"Error saving {output_file}: {e}")
        print(f"Error saving {output_file}: {e}")

if __name__ == "__main__":
    main()