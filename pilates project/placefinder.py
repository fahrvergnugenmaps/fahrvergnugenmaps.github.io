#!/usr/bin/env python3
"""
Pilates Studio Finder for San Francisco Bay Area
Uses Google Maps API to find Pilates studios and save as GeoJSON
"""

import time
import json
import argparse
from typing import List, Dict, Any
import googlemaps
from datetime import datetime

class PilatesStudioFinder:
    def __init__(self, api_key: str):
        """
        Initialize the Pilates studio finder with Google Maps API key
        
        Args:
            api_key: Your Google Maps API key
        """
        self.gmaps = googlemaps.Client(key=api_key)
        
        # Define Bay Area bounding box and major cities
        self.bay_area_cities = [
            {"name": "San Francisco", "lat": 37.7749, "lng": -122.4194},
            {"name": "Oakland", "lat": 37.8044, "lng": -122.2711},
            {"name": "San Jose", "lat": 37.3382, "lng": -121.8863},
            {"name": "Berkeley", "lat": 37.8715, "lng": -122.2727},
            {"name": "Palo Alto", "lat": 37.4419, "lng": -122.1430},
            {"name": "Mountain View", "lat": 37.3861, "lng": -122.0839},
            {"name": "Sunnyvale", "lat": 37.3688, "lng": -122.0363},
            {"name": "Santa Clara", "lat": 37.3541, "lng": -121.9552},
            {"name": "Fremont", "lat": 37.5485, "lng": -121.9886},
            {"name": "Hayward", "lat": 37.6688, "lng": -122.0808},
            {"name": "Richmond", "lat": 37.9358, "lng": -122.3477},
            {"name": "Walnut Creek", "lat": 37.9101, "lng": -122.0652},
            {"name": "San Mateo", "lat": 37.5630, "lng": -122.3255},
            {"name": "Redwood City", "lat": 37.4852, "lng": -122.2364},
            {"name": "Santa Rosa", "lat": 38.4405, "lng": -122.7144},
            {"name": "Napa", "lat": 38.2975, "lng": -122.2869},
            {"name": "Novato", "lat": 38.1074, "lng": -122.5697},
        ]
        
        # Search keywords for Pilates studios
        self.search_queries = [
            "Pilates studio",
            "Pilates",
            "Pilates reformer",
            "Classical Pilates",
            "Contemporary Pilates"
        ]
        
        self.found_places = {}  # Use dict with place_id as key to avoid duplicates
        
    def search_area(self, location: Dict[str, float], radius: int = 5000) -> List[Dict]:
        """
        Search for Pilates studios in a specific area
        
        Args:
            location: Dict with 'lat' and 'lng' keys
            radius: Search radius in meters (default 5000)
            
        Returns:
            List of place results
        """
        all_results = []
        
        for query in self.search_queries:
            try:
                print(f"  Searching for '{query}' near {location['name']}...")
                
                # Perform the search
                results = self.gmaps.places(
                    query=query,
                    location=(location['lat'], location['lng']),
                    radius=radius
                )
                
                # Process results
                for result in results.get('results', []):
                    place_id = result['place_id']
                    
                    # Skip if we already found this place
                    if place_id in self.found_places:
                        continue
                    
                    # Get additional details
                    place_details = self.get_place_details(place_id)
                    
                    # Combine basic info with details
                    place_info = {
                        **result,
                        'details': place_details
                    }
                    
                    self.found_places[place_id] = place_info
                    all_results.append(place_info)
                    
                    print(f"    Found: {result.get('name')} - {result.get('formatted_address', 'No address')}")
                
                # Handle pagination if there are more results
                while 'next_page_token' in results:
                    time.sleep(2)  # Required delay between pagination requests
                    results = self.gmaps.places_page(results['next_page_token'])
                    
                    for result in results.get('results', []):
                        place_id = result['place_id']
                        
                        if place_id in self.found_places:
                            continue
                            
                        place_details = self.get_place_details(place_id)
                        place_info = {
                            **result,
                            'details': place_details
                        }
                        
                        self.found_places[place_id] = place_info
                        all_results.append(place_info)
                        
                        print(f"    Found: {result.get('name')} - {result.get('formatted_address', 'No address')}")
                
                # Small delay to avoid hitting rate limits
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  Error searching {location['name']}: {e}")
                
        return all_results
    
    def get_place_details(self, place_id: str) -> Dict:
        """
        Get additional details for a place
        
        Args:
            place_id: Google Maps place ID
            
        Returns:
            Dict with place details
        """
        try:
            details = self.gmaps.place(
                place_id,
                fields=['name', 'formatted_phone_number', 'website', 
                       'opening_hours', 'rating', 'user_ratings_total', 
                       'price_level', 'reviews']
            )
            return details.get('result', {})
        except Exception as e:
            print(f"    Error getting details for {place_id}: {e}")
            return {}
    
    def search_bay_area(self) -> List[Dict]:
        """
        Search for Pilates studios throughout the Bay Area
        
        Returns:
            List of all found places
        """
        print("🔍 Searching for Pilates studios in the Bay Area...")
        print("=" * 60)
        
        all_studios = []
        
        for city in self.bay_area_cities:
            print(f"\n📍 Searching {city['name']}...")
            results = self.search_area(city, radius=8000)  # 8km radius
            all_studios.extend(results)
            
        print(f"\n✅ Found {len(all_studios)} unique Pilates studios")
        
        return all_studios
    
    def convert_to_geojson(self, studios: List[Dict]) -> Dict:
        """
        Convert studio data to GeoJSON format
        
        Args:
            studios: List of studio data from Google Maps
            
        Returns:
            GeoJSON FeatureCollection
        """
        features = []
        
        for studio in studios:
            # Get coordinates
            geometry = studio.get('geometry', {})
            location = geometry.get('location', {})
            
            if not location:
                continue
                
            # Extract useful information from details
            details = studio.get('details', {})
            
            # Create properties dictionary
            properties = {
                'name': studio.get('name', 'Unknown'),
                'address': studio.get('formatted_address', ''),
                'place_id': studio.get('place_id', ''),
                'rating': studio.get('rating', None),
                'user_ratings_total': studio.get('user_ratings_total', 0),
                'phone': details.get('formatted_phone_number', ''),
                'website': details.get('website', ''),
                'price_level': details.get('price_level', None),
                'business_status': studio.get('business_status', ''),
                'types': studio.get('types', []),
            }
            
            # Add opening hours if available
            if 'opening_hours' in details:
                properties['opening_hours'] = details['opening_hours'].get('weekday_text', [])
                properties['open_now'] = details['opening_hours'].get('open_now', False)
            
            # Create feature
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [location['lng'], location['lat']]  # GeoJSON uses [lng, lat]
                },
                'properties': properties
            }
            
            features.append(feature)
        
        # Create FeatureCollection
        geojson = {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'generated': datetime.now().isoformat(),
                'count': len(features),
                'source': 'Google Maps API',
                'search_area': 'San Francisco Bay Area'
            }
        }
        
        return geojson
    
    def save_geojson(self, geojson: Dict, filename: str = 'pilates_studios_bay_area.geojson'):
        """
        Save GeoJSON data to file
        
        Args:
            geojson: GeoJSON data
            filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(geojson, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Saved {geojson['metadata']['count']} studios to {filename}")
        except Exception as e:
            print(f"Error saving file: {e}")
    
    def print_summary(self, studios: List[Dict]):
        """
        Print a summary of found studios
        
        Args:
            studios: List of studio data
        """
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        
        # Count by city
        city_counts = {}
        for studio in studios:
            address = studio.get('formatted_address', '')
            # Simple city extraction (not perfect but gives an idea)
            for city in self.bay_area_cities:
                if city['name'] in address:
                    city_counts[city['name']] = city_counts.get(city['name'], 0) + 1
                    break
        
        print("\n🏙️  Studios by city:")
        for city, count in sorted(city_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {city}: {count}")
        
        # Rating statistics
        ratings = [s.get('rating') for s in studios if s.get('rating')]
        if ratings:
            print(f"\n⭐ Average rating: {sum(ratings)/len(ratings):.2f} ({len(ratings)} rated)")
        
        # Price level distribution
        price_levels = [s.get('price_level') for s in studios if s.get('price_level')]
        if price_levels:
            print("\n💰 Price level distribution:")
            for level in range(1, 5):
                count = price_levels.count(level)
                if count:
                    print(f"  {'$' * level}: {count} studios")


def main():
    parser = argparse.ArgumentParser(description='Find Pilates studios in the Bay Area')
    parser.add_argument('--api-key', required=True, help='Google Maps API key')
    parser.add_argument('--output', default='pilates_studios_bay_area.geojson', 
                       help='Output GeoJSON filename')
    parser.add_argument('--radius', type=int, default=8000, 
                       help='Search radius in meters (default: 8000)')
    
    args = parser.parse_args()
    
    # Initialize finder
    finder = PilatesStudioFinder(args.api_key)
    
    # Search for studios
    print("🧘 Starting Pilates studio search in the Bay Area...")
    studios = finder.search_bay_area()
    
    if studios:
        # Convert to GeoJSON
        geojson = finder.convert_to_geojson(studios)
        
        # Save to file
        finder.save_geojson(geojson, args.output)
        
        # Print summary
        finder.print_summary(studios)
        
        print(f"\n✨ Done! Found {len(studios)} Pilates studios")
    else:
        print("❌ No studios found")

if __name__ == "__main__":
    main()