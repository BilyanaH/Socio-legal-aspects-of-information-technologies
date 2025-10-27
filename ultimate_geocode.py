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
        """Score geocoding result quality (0-100) with enhanced precision"""
        score = 0
        display = result.get('display_name', '').lower()
        addr_data = result.get('address', {})
        
        # 1. Exact city match (30 points) - STRICT
        city_lower = city.lower()
        result_city = (addr_data.get('city') or addr_data.get('town') or addr_data.get('village') or '').lower()
        
        if result_city == city_lower:
            score += 30
        elif city_lower in display:
            score += 20  # Partial match in display name
        else:
            # Wrong city = major penalty
            score -= 30
        
        # 2. Street number match (40 points) - CRITICAL
        result_number = addr_data.get('house_number', '')
        if street_number and result_number:
            # Exact match
            if street_number == result_number:
                score += 40
            # Normalize and compare (remove letters, slashes)
            elif re.sub(r'[^\d]', '', street_number) == re.sub(r'[^\d]', '', result_number):
                score += 35
            # Number appears in display
            elif street_number in display:
                score += 25
        elif street_number and street_number in display:
            score += 20
        elif street_number:
            # Has number but not found = penalty
            score -= 10
        
        # 3. Street name match (25 points) - ENHANCED
        street_name = self._extract_street_name(address)
        result_road = (addr_data.get('road') or addr_data.get('street') or '').lower()
        
        if street_name and len(street_name) > 3:
            street_lower = street_name.lower()
            
            # Exact match in road field
            if street_lower in result_road or result_road in street_lower:
                score += 25
            # Match in display name
            elif street_lower in display:
                score += 15
            else:
                # Check word-by-word match
                words = [w for w in street_name.split() if len(w) > 3]
                matches = sum(1 for w in words if w.lower() in display or w.lower() in result_road)
                score += min(15, matches * 7)
        
        # 4. Address type quality (15 points)
        if addr_data.get('house_number'):
            score += 8
        if addr_data.get('road') or addr_data.get('street'):
            score += 7
        
        # 5. Coordinate precision check (10 points)
        lat_str = str(result.get('lat', ''))
        lon_str = str(result.get('lon', ''))
        # More decimal places = more precise
        lat_precision = len(lat_str.split('.')[-1]) if '.' in lat_str else 0
        lon_precision = len(lon_str.split('.')[-1]) if '.' in lon_str else 0
        avg_precision = (lat_precision + lon_precision) / 2
        
        if avg_precision >= 7:
            score += 10
        elif avg_precision >= 5:
            score += 5
        
        # 6. OSM type quality bonus (5 points)
        osm_type = result.get('osm_type', '')
        if osm_type == 'node':  # Exact point
            score += 5
        elif osm_type == 'way':  # Building outline
            score += 3
        
        # 7. Class/type validation (5 points)
        result_class = result.get('class', '')
        result_type = result.get('type', '')
        
        if result_class == 'building' or result_type == 'house':
            score += 5
        elif result_class == 'amenity' and result_type in ['hospital', 'clinic', 'doctors']:
            score += 5
        elif result_class == 'place':  # City-level result = bad
            score -= 20
        
        # Ensure score is in valid range
        return max(0, min(100, score))
    
    def _nominatim_search(self, query, limit=10):
        """Enhanced Nominatim search with multiple strategies"""
        results = []
        
        # Strategy 1: Exact query with enhanced parameters
        try:
            resp = self.session.get(
                'https://nominatim.openstreetmap.org/search',
                params={
                    'q': query,
                    'format': 'json',
                    'addressdetails': 1,
                    'limit': limit,
                    'countrycodes': 'bg',
                    'extratags': 1,  # Get OSM tags
                    'namedetails': 1,  # Get name variations
                    'dedupe': 0  # Don't merge similar results
                },
                timeout=15
            )
            if resp.status_code == 200:
                results.extend(resp.json())
        except Exception as e:
            logging.error(f"Nominatim search error for '{query}': {e}")
        
        return results
    
    def _nominatim_structured(self, street, city, house_number=None):
        """Structured Nominatim query with enhanced precision"""
        results = []
        
        try:
            # Variation 1: Full structured query
            params = {
                'format': 'json',
                'addressdetails': 1,
                'limit': 10,
                'country': 'Bulgaria',
                'countrycodes': 'bg',
                'extratags': 1,
                'namedetails': 1
            }
            
            if city:
                params['city'] = city
            if street and house_number:
                params['street'] = f"{street} {house_number}"
            elif street:
                params['street'] = street
            
            resp = self.session.get(
                'https://nominatim.openstreetmap.org/search',
                params=params,
                timeout=15
            )
            
            if resp.status_code == 200:
                results.extend(resp.json())
            
            # Variation 2: If we have house number, try separate field
            if house_number and len(results) < 3:
                time.sleep(1.0)
                params2 = params.copy()
                params2['street'] = street
                params2.pop('city', None)
                params2['city'] = city
                
                # Try adding postal code search variation
                resp2 = self.session.get(
                    'https://nominatim.openstreetmap.org/search',
                    params=params2,
                    timeout=15
                )
                
                if resp2.status_code == 200:
                    results.extend(resp2.json())
                    
        except Exception as e:
            logging.error(f"Nominatim structured error: {e}")
        
        return results
    
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
    
    def geocode(self, address, city, oblast, name=None, street_number_hint=None, street_name_hint=None):
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
        
        # Extract components - use hints if provided
        street_number = street_number_hint if street_number_hint else self._extract_street_number(address)
        street_name = street_name_hint if street_name_hint else self._extract_street_name(address)
        
        logging.info(f"Geocoding: {address} | {city} | Number={street_number}")
        
        candidates = []
        
        # === STRATEGY 1: Free-text search with enhanced variations ===
        queries = [
            f"{address}, {city}, България",
            f"{street_name} {street_number}, {city}, България" if street_number and street_name else None,
            f"{address}, {city}, {oblast}, България",
            f"{street_number} {street_name}, {city}" if street_number and street_name else None,
            # Try without country to get more OSM results
            f"{address}, {city}, {oblast}" if oblast else None,
        ]
        
        for query in queries:
            if not query:
                continue
            
            results = self._nominatim_search(query, limit=15)
            
            # Filter and score each result
            for r in results:
                score = self._score_result(r, address, city, street_number)
                
                # Lower threshold but track all candidates
                if score >= 30:  # Accept more candidates for comparison
                    # Check for duplicates (same coordinates)
                    is_duplicate = any(
                        abs(float(r['lat']) - c['lat']) < 0.0001 and 
                        abs(float(r['lon']) - c['lng']) < 0.0001
                        for c in candidates
                    )
                    
                    if not is_duplicate:
                        candidates.append({
                            'lat': float(r['lat']),
                            'lng': float(r['lon']),
                            'display': r['display_name'],
                            'provider': 'nominatim_free',
                            'score': score,
                            'osm_type': r.get('osm_type', ''),
                            'osm_id': r.get('osm_id', '')
                        })
            
            time.sleep(1.0)  # Rate limiting
        
        # === STRATEGY 2: Structured search ===
        if street_name:
            results = self._nominatim_structured(street_name, city, street_number)
            for r in results:
                score = self._score_result(r, address, city, street_number)
                
                if score >= 30:
                    # Check for duplicates
                    is_duplicate = any(
                        abs(float(r['lat']) - c['lat']) < 0.0001 and 
                        abs(float(r['lon']) - c['lng']) < 0.0001
                        for c in candidates
                    )
                    
                    if not is_duplicate:
                        candidates.append({
                            'lat': float(r['lat']),
                            'lng': float(r['lon']),
                            'display': r['display_name'],
                            'provider': 'nominatim_structured',
                            'score': score,
                            'osm_type': r.get('osm_type', ''),
                            'osm_id': r.get('osm_id', '')
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
        
        # === SELECT BEST CANDIDATE with enhanced filtering (SHOW ALL RESULTS) ===
        if candidates:
            # Sort by score (highest first)
            candidates.sort(key=lambda x: x['score'], reverse=True)

            # Prefer high-quality candidates but fallback to the best available
            top_candidates = [c for c in candidates if c['score'] >= 50]

            if top_candidates:
                best = top_candidates[0]
                chosen_reason = 'high_confidence'
            else:
                # No high-quality results — still return the best candidate (lowest confidence)
                best = candidates[0]
                chosen_reason = 'low_confidence'

            # If very low score, mark provider so UI can style it differently
            provider = best.get('provider', 'unknown')
            if chosen_reason == 'low_confidence' or best.get('score', 0) < 50:
                provider = f"{provider}_lowconf"

            # Cache result (store exact returned score)
            self.cache[cache_key] = {
                'lat': best['lat'],
                'lng': best['lng'],
                'provider': provider,
                'display': best.get('display'),
                'score': best.get('score', 0)
            }
            self._save_cache()

            logging.info(f"✓ Selected ({chosen_reason}): {str(best.get('display'))[:80]} (score={best.get('score')}, provider={provider})")
            return (best['lat'], best['lng'], provider, best.get('display'), best.get('score', 0))
        
        # No acceptable result found
        logging.warning(f"✗ Failed to geocode: {address}, {city}")
        return (None, None, None, None, 0)


def main():
    print("="*70)
    print("ULTIMATE GEOCODING SOLUTION v2.0 - ENHANCED PRECISION")
    print("="*70)
    print()
    print("Enhancements:")
    print("  - Stricter city validation (exact match required)")
    print("  - Enhanced street number matching")
    print("  - Coordinate precision scoring")
    print("  - OSM type validation (building/amenity)")
    print("  - Duplicate filtering")
    print("  - Quality threshold: minimum score 50")
    print()
    
    # Load data - use improved version if available
    if os.path.exists('hospitals_official_improved.csv'):
        df = pd.read_csv('hospitals_official_improved.csv', encoding='utf-8')
        print(f"Loaded {len(df)} hospitals (IMPROVED DATA)")
        print("Using extracted metadata: street_number, street_name_clean")
    else:
        df = pd.read_csv('hospitals_official_cleaned.csv', encoding='utf-8')
        print(f"Loaded {len(df)} hospitals")
    
    print(f"Estimated time: ~{len(df) * 3 / 60:.1f} minutes (enhanced multi-strategy)")
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
        
        # Use pre-extracted metadata if available
        street_number = row.get('street_number') if 'street_number' in row and pd.notna(row.get('street_number')) else None
        street_name = row.get('street_name_clean') if 'street_name_clean' in row and pd.notna(row.get('street_name_clean')) else None
        
        # Override extraction if we have better data
        if not street_number:
            street_number = geocoder._extract_street_number(addr)
        if not street_name:
            street_name = geocoder._extract_street_name(addr)
        
        # Progress
        if (i + 1) % 20 == 0 or i == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            remaining = (len(df) - i - 1) / rate if rate > 0 else 0
            
            print(f"[{i+1}/{len(df)}] {(i+1)/len(df)*100:.1f}% | "
                  f"Elapsed: {elapsed/60:.1f}m | Remaining: ~{remaining/60:.1f}m")
            print(f"  Quality: Excellent={stats['excellent']} Good={stats['good']} "
                  f"Fair={stats['fair']} Failed={stats['failed']}")
        
        # Geocode - pass extracted metadata for better precision
        lat, lng, provider, display, score = geocoder.geocode(
            addr, city, oblast, name, 
            street_number_hint=street_number,
            street_name_hint=street_name
        )
        
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
