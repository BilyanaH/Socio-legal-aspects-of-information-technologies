"""Generate a manual review CSV for problematic geocodes.

Reads either `to_review.csv` (if present) or `hospitals_with_coords.csv` and
filters rows with low-confidence providers or missing coordinates. Produces
`manual_review.csv` with helpful columns and links (Google Maps & OSM).

If libpostal is installed, address components are parsed and included.
"""
import os
import sys
import urllib.parse
import pandas as pd


def try_libpostal_parse(addr):
    try:
        from postal.parser import parse_address
    except Exception:
        return None
    try:
        parts = parse_address(addr)
        return {k: v for v, k in parts}
    except Exception:
        return None


def google_maps_link(lat, lon, address=None):
    if pd.notna(lat) and pd.notna(lon):
        return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    if address:
        q = urllib.parse.quote_plus(address)
        return f"https://www.google.com/maps/search/?api=1&query={q}"
    return ''


def osm_link(lat, lon, address=None):
    if pd.notna(lat) and pd.notna(lon):
        return f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=19/{lat}/{lon}"
    if address:
        q = urllib.parse.quote_plus(address)
        return f"https://www.openstreetmap.org/search?query={q}"
    return ''


def suggested_osm_change(row):
    # Template suggestion to help a human editor
    addr = row.get('Адрес', '')
    name = row.get('Наименование', '')
    parts = []
    if pd.isna(row.get('lat')) or pd.isna(row.get('lng')):
        parts.append('No coordinates — find building/entrance and add addr:street / addr:housenumber')
    else:
        parts.append('Verify that this point matches the entrance; if not, add separate node for entrance')
    parts.append(f"Suggested tags: name={name}")
    if addr:
        parts.append(f"Address from source: {addr}")
    parts.append('If address split across multiple buildings, consider creating separate OSM nodes/entrances')
    return ' | '.join(parts)


def main():
    # Choose input file
    if os.path.exists('to_review.csv'):
        df = pd.read_csv('to_review.csv', encoding='utf-8')
    elif os.path.exists('hospitals_with_coords.csv'):
        df = pd.read_csv('hospitals_with_coords.csv', encoding='utf-8')
    else:
        print('No input file found (to_review.csv or hospitals_with_coords.csv). Run geocoding first.')
        return

    # Normalize some expected columns if missing
    for col in ['Наименование', 'Област', 'Населено място', 'Адрес', 'provider', 'display_name', 'lat', 'lng']:
        if col not in df.columns:
            df[col] = None

    # Filter rows needing review: missing lat/lng or provider less confident
    low_conf_providers = set(['overpass', 'nominatim_city', None])
    needs = df[df['lat'].isna() | df['lng'].isna() | df['provider'].isin(['overpass', 'nominatim_city'])]

    if needs.empty:
        print('No rows flagged for review.')
        return

    out_rows = []
    for _, r in needs.iterrows():
        lat = r.get('lat')
        lon = r.get('lng')
        address = ', '.join([str(r.get('Адрес') or ''), str(r.get('Населено място') or ''), str(r.get('Област') or '')]).strip(', ')
        gm = google_maps_link(lat, lon, address=address)
        osm = osm_link(lat, lon, address=address)
        parsed = try_libpostal_parse(r.get('Адрес') or '')
        parsed_str = ''
        if parsed:
            parsed_str = ';'.join(f"{k}={v}" for k, v in parsed.items())

        out_rows.append({
            'Наименование': r.get('Наименование'),
            'Адрес': r.get('Адрес'),
            'Населено място': r.get('Населено място'),
            'Област': r.get('Област'),
            'provider': r.get('provider'),
            'display_name': r.get('display_name'),
            'lat': lat,
            'lng': lon,
            'google_maps_link': gm,
            'osm_link': osm,
            'parsed_address_parts': parsed_str,
            'suggested_osm_change': suggested_osm_change(r)
        })

    out = pd.DataFrame(out_rows)
    out_file = 'manual_review.csv'
    out.to_csv(out_file, index=False, encoding='utf-8')
    print(f'Wrote {len(out)} rows to {out_file}')


if __name__ == '__main__':
    main()
