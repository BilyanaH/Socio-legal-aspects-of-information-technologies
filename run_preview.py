import os
import pandas as pd
from geocode_hospitals import geocode_address

# Configuration
N = 70
input_file = 'hospitals.csv'
output_file = 'hospitals_with_coords_preview.csv'
review_file = 'to_review_preview.csv'

# Force Nominatim-only mode
os.environ['FORCE_NOMINATIM'] = '1'

# Read input
if not os.path.exists(input_file):
    print(f"Input file {input_file} not found")
    raise SystemExit(1)

DF = pd.read_csv(input_file, encoding='utf-8')
print(f"Read {len(DF)} rows from {input_file}")
DFp = DF.head(N).copy()

# Ensure columns
DFp['lat'] = None
DFp['lng'] = None
DFp['provider'] = None
DFp['display_name'] = None
DFp['needs_review'] = False

for i, row in DFp.iterrows():
    city = row['Населено място'] if pd.notna(row['Населено място']) and row['Населено място'].strip() != '' else row['Област']
    name = row['Наименование'] if 'Наименование' in row else None
    lat, lng, provider, display = geocode_address(row['Адрес'], city, row['Област'], name_hint=name)
    DFp.at[i, 'lat'] = lat
    DFp.at[i, 'lng'] = lng
    DFp.at[i, 'provider'] = provider
    DFp.at[i, 'display_name'] = display
    if provider in (None, 'overpass', 'nominatim_city') or lat is None:
        DFp.at[i, 'needs_review'] = True
    print(f"{i+1}: {row.get('Наименование','')} -> ({lat}, {lng}) provider={provider}")

# Save outputs
DFp.to_csv(output_file, index=False, encoding='utf-8')
DFp[DFp['needs_review']].to_csv(review_file, index=False, encoding='utf-8')

print(f"Preview complete: wrote {output_file} ({len(DFp)} rows) and {review_file} ({DFp['needs_review'].sum()} rows needs review)")
