import pandas as pd
import requests
import time
import json
from pathlib import Path

# Configuration
INPUT_CSV = 'input.csv'  # Your CSV file
OUTPUT_CSV = 'geocoded_output.csv'
MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoidG9tYXNubjk4IiwiYSI6ImNseHI3aHdzaTBqYmcyanEzaWJzdTdxcDYifQ.nljzyejSeSv3BpHyEi9x0w'  # Replace with your Mapbox token

def geocode_address(address, zip_code, location, token):
    """
    Geocode a single address using Mapbox Geocoding API
    """
    # NEW: Combine address with location column if available
    # Prioritize location column, fall back to address
    if pd.notna(location) and str(location).strip():
        # Use location column as primary query
        query = str(location).strip()
        # Optionally append zip code for better accuracy
        if pd.notna(zip_code) and str(zip_code).strip():
            query = f"{query}, {str(int(zip_code))}"
    elif pd.notna(address) and str(address).strip():
        # Fall back to address column
        query = str(address).strip()
        if pd.notna(zip_code) and str(zip_code).strip():
            query = f"{query}, {str(int(zip_code))}"
    else:
        return {
            'longitude': None,
            'latitude': None,
            'place_name': None,
            'relevance': None,
            'accuracy': None,
            'full_response': None
        }
    
    # URL encode the query
    import urllib.parse
    encoded_query = urllib.parse.quote(query)
    
    # Mapbox geocoding endpoint
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_query}.json"
    
    params = {
        'access_token': token,
        'limit': 1,  # Get only the best result
        'country': 'US',  # Limit to US addresses
        'types': 'address,poi,place'  # Prioritize address, point of interest, and place results
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['features']:
            # Extract relevant information from the best match
            feature = data['features'][0]
            return {
                'longitude': feature['center'][0],
                'latitude': feature['center'][1],
                'place_name': feature['place_name'],
                'relevance': feature['relevance'],
                'accuracy': feature.get('properties', {}).get('accuracy', 'unknown'),
                'full_response': json.dumps(feature),  # Store full response for debugging
                'query_used': query  # NEW: Track which query was used
            }
        else:
            return {
                'longitude': None,
                'latitude': None,
                'place_name': None,
                'relevance': None,
                'accuracy': None,
                'full_response': None,
                'query_used': query  # NEW: Track which query was used
            }
            
    except requests.exceptions.RequestException as e:
        print(f"Error geocoding '{query}': {e}")
        return {
            'longitude': None,
            'latitude': None,
            'place_name': None,
            'relevance': None,
            'accuracy': None,
            'full_response': None,
            'query_used': query  # NEW: Track which query was used
        }

def main():
    # Read the CSV file
    print(f"Reading CSV file: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    
    print(f"Found {len(df)} records to geocode")
    
    # NEW: Check if location column exists
    location_col = None
    possible_location_cols = ['Location', 'location', 'loc', 'LOCATION']
    
    for col in possible_location_cols:
        if col in df.columns:
            location_col = col
            print(f"Found location column: '{location_col}'")
            break
    
    if location_col is None:
        print("Warning: No location column found. Will use address column only.")
        # Add empty location column to avoid errors
        df['Location'] = None
        location_col = 'Location'
    
    # Add new columns for geocoding results
    df['longitude'] = None
    df['latitude'] = None
    df['place_name'] = None
    df['geocode_relevance'] = None
    df['geocode_accuracy'] = None
    df['geocode_full_response'] = None
    df['geocode_query_used'] = None  # NEW: Track which query was used
    
    # Geocode each address
    successful = 0
    failed = 0
    
    for idx, row in df.iterrows():
        address = row['Location Address / Description']
        zip_code = row['Zip Code']
        location = row[location_col]  # NEW: Get location column value
        
        if pd.isna(address) and pd.isna(location):
            print(f"Row {idx}: Missing both address and location")
            failed += 1
            continue
        
        # Determine which field(s) to show in log
        log_info = []
        if pd.notna(location):
            log_info.append(f"Location: {location}")
        if pd.notna(address):
            log_info.append(f"Address: {address}")
        if pd.notna(zip_code):
            log_info.append(f"ZIP: {zip_code}")
        
        print(f"Geocoding {idx+1}/{len(df)}: {', '.join(log_info)}")
        
        # Geocode the address/location
        result = geocode_address(
            str(address) if pd.notna(address) else None,
            str(int(zip_code)) if pd.notna(zip_code) else None,
            location,
            MAPBOX_ACCESS_TOKEN
        )
        
        # Update the dataframe
        df.at[idx, 'longitude'] = result['longitude']
        df.at[idx, 'latitude'] = result['latitude']
        df.at[idx, 'place_name'] = result['place_name']
        df.at[idx, 'geocode_relevance'] = result['relevance']
        df.at[idx, 'geocode_accuracy'] = result['accuracy']
        df.at[idx, 'geocode_full_response'] = result['full_response']
        df.at[idx, 'geocode_query_used'] = result['query_used']  # NEW: Store query used
        
        if result['longitude'] is not None:
            successful += 1
            print(f"  ✓ Success: {result['latitude']:.4f}, {result['longitude']:.4f}")
            if 'query_used' in result:
                print(f"  Query used: {result['query_used']}")
        else:
            failed += 1
            print(f"  ✗ Failed to geocode")
            if 'query_used' in result:
                print(f"  Query attempted: {result['query_used']}")
        
        # Rate limiting - be nice to the API
        time.sleep(0.1)  # 100ms delay between requests
    
    # Save results
    print(f"\nGeocoding complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/len(df)*100:.1f}%")
    
    # NEW: Show query usage statistics
    if 'geocode_query_used' in df.columns:
        query_sources = df['geocode_query_used'].dropna()
        if len(query_sources) > 0:
            location_queries = query_sources[query_sources.str.contains(r'^\s*[^,]+\s*,\s*\d{5}')].count()
            address_queries = len(query_sources) - location_queries
            print(f"\nQuery source statistics:")
            print(f"  Location-based queries: {location_queries}")
            print(f"  Address-based queries: {address_queries}")
    
    # Save to CSV
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nResults saved to: {OUTPUT_CSV}")
    
    # Create a summary
    summary_cols = ['SGO Report ID', 'Location Address / Description', location_col, 'Zip Code', 
                    'latitude', 'longitude', 'place_name', 'geocode_relevance']
    
    # Add query used column if it exists
    if 'geocode_query_used' in df.columns:
        summary_cols.append('geocode_query_used')
    
    summary_df = df[summary_cols]
    
    # Save a simplified version without the full JSON response
    simplified_csv = 'geocoded_simplified.csv'
    summary_df.to_csv(simplified_csv, index=False)
    print(f"Simplified results saved to: {simplified_csv}")
    
    # Show sample of results
    print("\nSample of geocoded results:")
    print(summary_df.head(10).to_string())
    
    # Statistics
    print(f"\nGeocoding Statistics:")
    print(f"Records with coordinates: {df['latitude'].notna().sum()}")
    print(f"Average relevance score: {df['geocode_relevance'].mean():.3f}")

if __name__ == "__main__":
    # Check for Mapbox token
    if MAPBOX_ACCESS_TOKEN == 'YOUR_MAPBOX_ACCESS_TOKEN_HERE':
        print("ERROR: Please replace 'YOUR_MAPBOX_ACCESS_TOKEN_HERE' with your actual Mapbox access token")
        print("Get a token from: https://account.mapbox.com/access-tokens/")
    else:
        main()