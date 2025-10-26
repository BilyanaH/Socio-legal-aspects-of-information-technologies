import requests
import time
import pandas as pd
import os
import sys
import logging

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

def transliterate_cyrillic(text):
    """Transliterate Cyrillic to Latin for Nominatim compatibility."""
    cyrillic_to_latin = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ж': 'zh', 'з': 'z',
        'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p',
        'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'щ': 'sht', 'ъ': 'a', 'ь': '', 'ю': 'yu', 'я': 'ya'
    }
    text = text.lower()
    result = ''
    for char in text:
        result += cyrillic_to_latin.get(char, char)
    return result

def geocode_address(address, city, oblast, retries=5):
    # Normalize address: remove 'ет.', 'ГР.', '№', 'и', 'Д-р', extra spaces
    address = (address.replace('ет.', '')
                     .replace('ГР.', '')
                     .replace('№', '')
                     .replace('и', '')
                     .replace('Д-р', '')
                     .replace('  ', ' ')
                     .strip())
    city = city.replace('ГР.', '').strip() if city else oblast
    oblast = oblast.strip()
    
    # Try multiple query formats: Cyrillic and transliterated Latin
    queries = [
        f"{address}, {city}, {oblast}, Bulgaria",           # Full Cyrillic
        f"{address}, {city}, Bulgaria",                     # Cyrillic without oblast
        f"{city}, {oblast}, Bulgaria",                      # City-level Cyrillic
        f"{city}, Bulgaria",                                # City only Cyrillic
        f"{transliterate_cyrillic(address)}, {transliterate_cyrillic(city)}, Bulgaria",  # Full Latin
        f"{transliterate_cyrillic(city)}, Bulgaria"         # City only Latin
    ]
    
    for query in queries:
        for attempt in range(retries):
            try:
                headers = {'User-Agent': 'CourseProject/1.0 (your_email@example.com)'}  # Replace with your email
                response = requests.get(f"https://nominatim.openstreetmap.org/search?format=json&q={query}", headers=headers)
                if response.status_code != 200:
                    logging.error(f"Attempt {attempt + 1}/{retries}: Status {response.status_code} for {query}")
                    if attempt < retries - 1:
                        time.sleep(5)
                    continue
                data = response.json()
                if data:
                    lat, lng = data[0]['lat'], data[0]['lon']
                    logging.info(f"Geocoded {query}: ({lat}, {lng})")
                    return lat, lng
                logging.warning(f"No coordinates found for: {query}")
            except Exception as e:
                logging.error(f"Attempt {attempt + 1}/{retries}: Error geocoding {query}: {e}")
                if attempt < retries - 1:
                    time.sleep(5)
        # Try next query format if current one fails
    logging.error(f"Failed after {retries} attempts for all queries: {address}, {city}, {oblast}")
    return None, None

def main():
    input_file = 'hospitals.csv'
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

    # Initialize lat and lng columns
    df['lat'] = None
    df['lng'] = None

    # Geocode each address
    for i, row in df.iterrows():
        city = row['Населено място'] if pd.notna(row['Населено място']) and row['Населено място'].strip() != '' else row['Област']
        lat, lng = geocode_address(row['Адрес'], city, row['Област'])
        df.at[i, 'lat'] = lat
        df.at[i, 'lng'] = lng
        print(f"Geocoded {row['Наименование']} at {row['Адрес']}, {city}, {row['Област']}: ({lat}, {lng})")
        time.sleep(1.5)  # Longer delay to avoid rate limits

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