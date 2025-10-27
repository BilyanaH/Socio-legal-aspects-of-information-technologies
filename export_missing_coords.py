import pandas as pd
import os

infile = 'hospitals_with_coords.csv'
outfile = 'missing_coords.csv'

df = pd.read_csv(infile, encoding='utf-8')
# Consider missing if lat or lng is null/empty or provider is null
mask = df['lat'].isnull() | df['lng'].isnull() | df['provider'].isnull()
missing = df[mask]
print(f'Total rows: {len(df)}, missing: {len(missing)}')
if len(missing) > 0:
    missing.to_csv(outfile, index=False, encoding='utf-8')
    print(f'Wrote {len(missing)} rows to {outfile}')
else:
    print('No missing rows found')
