import time
import pandas as pd
import geocode_hospitals as gh

infile = 'hospitals_with_coords.csv'
outfile = 'hospitals_with_coords.csv'

print('Loading', infile)
df = pd.read_csv(infile, encoding='utf-8')

updated = 0
for i, row in df.iterrows():
    lat = row.get('lat')
    lng = row.get('lng')
    provider = row.get('provider')
    # treat missing or null provider/coords as needing geocode
    if pd.isna(lat) or pd.isna(lng) or pd.isna(provider) or str(provider).strip() == '':
        addr = row['Адрес'] if 'Адрес' in row else ''
        city = row['Населено място'] if pd.notna(row['Населено място']) and str(row['Населено място']).strip() != '' else row['Област']
        name = row['Наименование'] if 'Наименование' in row else None
        print(f"Geocoding missing row {i}: {name} / {addr} / {city}")
        try:
            res = gh.geocode_address(addr, city, row['Област'], name_hint=name)
            if res and res[0] and res[1]:
                lat, lng, provider, display = res
                df.at[i, 'lat'] = lat
                df.at[i, 'lng'] = lng
                df.at[i, 'provider'] = provider
                df.at[i, 'display_name'] = display
                updated += 1
                print(f" -> Found: ({lat}, {lng}) via {provider}")
            else:
                print(" -> Still not found")
        except Exception as e:
            print('Error geocoding row', i, e)
        time.sleep(1.2)

if updated:
    df.to_csv(outfile, index=False, encoding='utf-8')
    print(f'Updated {updated} rows and saved to {outfile}')
else:
    print('No updates made')
