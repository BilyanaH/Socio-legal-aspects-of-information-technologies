import geocode_hospitals as gh

q = 'МЦ Медика Албена, Албена, Балчик'
print('Running free-text search for:', q)
res = gh.nominatim_free_text_search(q, 'Албена', 'Балчик', limit=5)
print('Found', len(res), 'results')
if res:
    for r in res:
        print('-', r.get('display_name'), r.get('lat'), r.get('lon'))
