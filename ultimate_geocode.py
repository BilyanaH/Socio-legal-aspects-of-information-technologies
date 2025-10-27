# -*- coding: utf-8 -*-
"""
ULTIMATE GEOCODING SOLUTION
Combines multiple strategies for maximum accuracy:
1. Enhanced address preprocessing
2. Multi-pass geocoding with fallbacks
3. Result validation and scoring
4. Smart caching with quality indicators
"""
import pandas as pd
import requests
import time
import json
import os
import re
import logging
from urllib.parse import quote

logging.basicConfig(
    filename='ultimate_geocode.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

class UltimateGeocoder:
    def __init__(self):
        self.cache = self._load_cache()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'HospitalGeocoder/2.0'})
        
    def _load_cache(self):
        if os.path.exists('ultimate_cache.json'):
            with open('ultimate_cache.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        with open('ultimate_cache.json', 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def _extract_street_number(self, address):
        """Extract street number from address"""
        # Match patterns like "123", "123А", "123-125", "123/1"
        match = re.search(r'\b(\d+[А-Яа-яA-Za-z]?(?:[-/]\d+[А-Яа-яA-Za-z]?)?)\s*$', address)
        return match.group(1) if match else None
    
    def _extract_street_name(self, address):
        """Extract clean street name without number"""
        # Remove prefixes
        addr = address.replace('ул.', '').replace('бул.', '').replace('жк', '').strip()
        # Remove number
        addr = re.sub(r'\s+\d+.*$', '', addr).strip()
        return addr
    
    def _score_result(self, result, address, city, street_number):
        """Score geocoding result quality (0-100)"""
        score = 0
        display = result.get('display_name', '').lower()
        
        # 1. City match (30 points)
        if city.lower() in display:
            score += 30
        
        # 2. Street number match (40 points) - CRITICAL
        if street_number and street_number in display:
            score += 40
        elif street_number:
            # Partial number match
            num_base = re.sub(r'[А-Яа-яA-Za-z/-]', '', street_number)
            if num_base and num_base in display:
                score += 20
        
        # 3. Street name match (20 points)
        street_name = self._extract_street_name(address)
        if street_name and len(street_name) > 3:
            # Check if key words from street name appear
            words = [w for w in street_name.split() if len(w) > 3]
            matches = sum(1 for w in words if w.lower() in display)
            score += min(20, matches * 10)
        
        # 4. Address type quality (10 points)
        addr_data = result.get('address', {})
        if addr_data.get('house_number'):
            score += 5
        if addr_data.get('road'):
            score += 5
        
        return score
    
    def _nominatim_search(self, query, limit=10):
        """Enhanced Nominatim search with multiple strategies"""
        results = []
        
        # Strategy 1: Exact query
        try:
            resp = self.session.get(
                'https://nominatim.openstreetmap.org/search',
                params={
                    'q': query,
                    'format': 'json',
                    'addressdetails': 1,
                    'limit': limit,
                    'countrycodes': 'bg'
                },
                timeout=15
            )
            if resp.status_code == 200:
                results.extend(resp.json())
        except Exception as e:
            logging.error(f"Nominatim search error for '{query}': {e}")
        
        return results
    
    def _nominatim_structured(self, street, city, house_number=None):
        """Structured Nominatim query"""
        try:
            params = {
                'format': 'json',
                'addressdetails': 1,
                'limit': 5,
                'country': 'Bulgaria',
                'countrycodes': 'bg'
            }
            
            if city:
                params['city'] = city
            if street:
                params['street'] = street
            if house_number:
                params['street'] = f"{street} {house_number}"
            
            resp = self.session.get(
                'https://nominatim.openstreetmap.org/search',
                params=params,
                timeout=15
            )
            
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logging.error(f"Nominatim structured error: {e}")
        
        return []
    
    def _overpass_search(self, name, city):
        """Search OpenStreetMap for hospital/clinic by name"""
        try:
            # Build Overpass query
            query = f"""
            [out:json][timeout:25];
            area["name"="{city}"]["place"~"city|town"]["admin_level"="8"]->.searchArea;
            (
                nwr["name"~"{re.escape(name)}",i]["amenity"~"hospital|clinic|doctors"](area.searchArea);
                nwr["name"~"МБАЛ|болница",i]["amenity"~"hospital|clinic"](area.searchArea);
            );
            out center;
            """
            
            resp = self.session.post(
                'https://overpass-api.de/api/interpreter',
                data={'data': query},
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                elements = data.get('elements', [])
                
                if elements:
                    # Score by name similarity
                    best = None
                    best_score = 0
                    
                    for el in elements:
                        tags = el.get('tags', {})
                        el_name = tags.get('name', '')
                        
                        # Simple scoring
                        score = 0
                        if name.lower() in el_name.lower():
                            score += 50
                        if tags.get('amenity') == 'hospital':
                            score += 30
                        
                        if score > best_score:
                            best_score = score
                            best = el
                    
                    if best and best_score >= 30:
                        if 'lat' in best and 'lon' in best:
                            lat, lon = best['lat'], best['lon']
                        elif 'center' in best:
                            lat, lon = best['center']['lat'], best['center']['lon']
                        else:
                            return None
                        
                        return {
                            'lat': lat,
                            'lon': lon,
                            'display_name': best.get('tags', {}).get('name', 'Unknown'),
                            'score': best_score
                        }
        except Exception as e:
            logging.warning(f"Overpass search error for '{name}' in {city}: {e}")
        
        return None
    
    def geocode(self, address, city, oblast, name=None):
        """
        Ultimate geocoding with multi-strategy approach
        Returns: (lat, lng, provider, display_name, quality_score)
        """
        # Cache key
        cache_key = f"{address}||{city}||{oblast}"
        
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            return (cached['lat'], cached['lng'], cached['provider'], 
                   cached['display'], cached.get('score', 50))
        
        # Extract components
        street_number = self._extract_street_number(address)
        street_name = self._extract_street_name(address)
        
        logging.info(f"Geocoding: {address} | {city} | Number={street_number}")
        
        candidates = []
        
        # === STRATEGY 1: Free-text search with variations ===
        queries = [
            f"{address}, {city}, България",
            f"{street_name} {street_number}, {city}, България" if street_number else None,
            f"{address}, {city}, {oblast}, България",
        ]
        
        for query in queries:
            if not query:
                continue
            
            results = self._nominatim_search(query, limit=10)
            for r in results:
                score = self._score_result(r, address, city, street_number)
                if score >= 40:  # Minimum acceptable score
                    candidates.append({
                        'lat': float(r['lat']),
                        'lng': float(r['lon']),
                        'display': r['display_name'],
                        'provider': 'nominatim_free',
                        'score': score
                    })
            
            time.sleep(1.0)  # Rate limiting
        
        # === STRATEGY 2: Structured search ===
        if street_name:
            results = self._nominatim_structured(street_name, city, street_number)
            for r in results:
                score = self._score_result(r, address, city, street_number)
                if score >= 40:
                    candidates.append({
                        'lat': float(r['lat']),
                        'lng': float(r['lon']),
                        'display': r['display_name'],
                        'provider': 'nominatim_structured',
                        'score': score
                    })
            
            time.sleep(1.0)
        
        # === STRATEGY 3: Overpass by hospital name ===
        if name and len(candidates) < 2:
            overpass_result = self._overpass_search(name, city)
            if overpass_result:
                candidates.append({
                    'lat': float(overpass_result['lat']),
                    'lng': float(overpass_result['lon']),
                    'display': overpass_result['display_name'],
                    'provider': 'overpass',
                    'score': overpass_result['score'] + 20  # Bonus for exact POI match
                })
            
            time.sleep(1.0)
        
        # === SELECT BEST CANDIDATE ===
        if candidates:
            # Sort by score (highest first)
            candidates.sort(key=lambda x: x['score'], reverse=True)
            best = candidates[0]
            
            # Cache result
            self.cache[cache_key] = {
                'lat': best['lat'],
                'lng': best['lng'],
                'provider': best['provider'],
                'display': best['display'],
                'score': best['score']
            }
            self._save_cache()
            
            logging.info(f"✓ Found: {best['display']} (score={best['score']}, provider={best['provider']})")
            return (best['lat'], best['lng'], best['provider'], best['display'], best['score'])
        
        # No acceptable result found
        logging.warning(f"✗ Failed to geocode: {address}, {city}")
        return (None, None, None, None, 0)


def main():
    print("="*70)
    print("ULTIMATE GEOCODING SOLUTION")
    print("="*70)
    print()
    
    # Load data
    df = pd.read_csv('hospitals_official_cleaned.csv', encoding='utf-8')
    print(f"Loaded {len(df)} hospitals")
    print(f"Estimated time: ~{len(df) * 2.5 / 60:.1f} minutes (multi-strategy approach)")
    print()
    
    # Initialize geocoder
    geocoder = UltimateGeocoder()
    
    # Add result columns
    for col in ['lat', 'lng', 'provider', 'display_name', 'quality_score']:
        if col not in df.columns:
            df[col] = None
    
    # Statistics
    stats = {
        'excellent': 0,  # score >= 80
        'good': 0,       # score >= 60
        'fair': 0,       # score >= 40
        'failed': 0      # score < 40 or None
    }
    
    # Geocode all
    start = time.time()
    
    for i, row in df.iterrows():
        addr = str(row.get('Адрес') or '').strip()
        city = str(row.get('Населено място') or '').strip()
        oblast = str(row.get('Област') or '').strip()
        name = str(row.get('Наименование') or '').strip()
        
        # Progress
        if (i + 1) % 20 == 0 or i == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            remaining = (len(df) - i - 1) / rate if rate > 0 else 0
            
            print(f"[{i+1}/{len(df)}] {(i+1)/len(df)*100:.1f}% | "
                  f"Elapsed: {elapsed/60:.1f}m | Remaining: ~{remaining/60:.1f}m")
            print(f"  Quality: Excellent={stats['excellent']} Good={stats['good']} "
                  f"Fair={stats['fair']} Failed={stats['failed']}")
        
        # Geocode
        lat, lng, provider, display, score = geocoder.geocode(addr, city, oblast, name)
        
        df.at[i, 'lat'] = lat
        df.at[i, 'lng'] = lng
        df.at[i, 'provider'] = provider
        df.at[i, 'display_name'] = display
        df.at[i, 'quality_score'] = score
        
        # Update stats
        if score >= 80:
            stats['excellent'] += 1
        elif score >= 60:
            stats['good'] += 1
        elif score >= 40:
            stats['fair'] += 1
        else:
            stats['failed'] += 1
    
    # Save results
    output = 'hospitals_ultimate_coords.csv'
    df.to_csv(output, index=False, encoding='utf-8')
    
    # Final report
    total_time = time.time() - start
    success_rate = (stats['excellent'] + stats['good'] + stats['fair']) / len(df) * 100
    
    print()
    print("="*70)
    print("GEOCODING COMPLETE")
    print("="*70)
    print(f"Total hospitals: {len(df)}")
    print(f"  ★★★ Excellent (80-100): {stats['excellent']} ({stats['excellent']/len(df)*100:.1f}%)")
    print(f"  ★★  Good (60-79): {stats['good']} ({stats['good']/len(df)*100:.1f}%)")
    print(f"  ★   Fair (40-59): {stats['fair']} ({stats['fair']/len(df)*100:.1f}%)")
    print(f"  ✗   Failed (<40): {stats['failed']} ({stats['failed']/len(df)*100:.1f}%)")
    print(f"\nOverall success rate: {success_rate:.1f}%")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Average: {total_time/len(df):.2f} seconds per hospital")
    print(f"\nOutput: {output}")
    print("="*70)
    
    # Export by quality
    excellent = df[df['quality_score'] >= 80]
    if len(excellent) > 0:
        excellent.to_csv('hospitals_excellent.csv', index=False, encoding='utf-8')
        print(f"Excellent quality: hospitals_excellent.csv ({len(excellent)} rows)")
    
    failed = df[df['quality_score'] < 40]
    if len(failed) > 0:
        failed.to_csv('hospitals_needs_manual.csv', index=False, encoding='utf-8')
        print(f"Needs manual review: hospitals_needs_manual.csv ({len(failed)} rows)")

if __name__ == '__main__':
    main()
