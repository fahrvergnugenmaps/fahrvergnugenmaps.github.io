import pandas as pd
import requests
import time
import json
from pathlib import Path

# Configuration
INPUT_CSV = 'input.csv'  # Your CSV file
OUTPUT_CSV = 'geocoded_output.csv'
MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoidG9tYXNubjk4IiwiYSI6ImNseHI3aHdzaTBqYmcyanEzaWJzdTdxcDYifQ.nljzyejSeSv3BpHyEi9x0w'  # Replace with your Mapbox token

def geocode_address(address, zip_code, token):
    """
    Geocode a single address using Mapbox Geocoding API
    """
    # Construct query - combine address with zip code for better accuracy
    query = f"{address}, {zip_code}"
    
    # URL encode the query
    import urllib.parse
    encoded_query = urllib.parse.quote(query)
    
    # Mapbox geocoding endpoint
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_query}.json"
    
    params = {
        'access_token': token,
        'limit': 1,  # Get only the best result
        'country': 'US',  # Limit to US addresses
        'types': 'address,poi'  # Prioritize address and point of interest results
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
                'full_response': json.dumps(feature)  # Store full response for debugging
            }
        else:
            return {
                'longitude': None,
                'latitude': None,
                'place_name': None,
                'relevance': None,
                'accuracy': None,
                'full_response': None
            }
            
    except requests.exceptions.RequestException as e:
        print(f"Error geocoding '{address}, {zip_code}': {e}")
        return {
            'longitude': None,
            'latitude': None,
            'place_name': None,
            'relevance': None,
            'accuracy': None,
            'full_response': None
        }

def main():
    # Read the CSV file
    print(f"Reading CSV file: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    
    print(f"Found {len(df)} records to geocode")
    
    # Add new columns for geocoding results
    df['longitude'] = None
    df['latitude'] = None
    df['place_name'] = None
    df['geocode_relevance'] = None
    df['geocode_accuracy'] = None
    df['geocode_full_response'] = None
    
    # Geocode each address
    successful = 0
    failed = 0
    
    for idx, row in df.iterrows():
        address = row['Location Address / Description']
        zip_code = row['Zip Code']
        
        if pd.isna(address) or pd.isna(zip_code):
            print(f"Row {idx}: Missing address or zip code")
            failed += 1
            continue
        
        print(f"Geocoding {idx+1}/{len(df)}: {address}, {zip_code}")
        
        # Geocode the address
        result = geocode_address(str(address), str(int(zip_code)), MAPBOX_ACCESS_TOKEN)
        
        # Update the dataframe
        df.at[idx, 'longitude'] = result['longitude']
        df.at[idx, 'latitude'] = result['latitude']
        df.at[idx, 'place_name'] = result['place_name']
        df.at[idx, 'geocode_relevance'] = result['relevance']
        df.at[idx, 'geocode_accuracy'] = result['accuracy']
        df.at[idx, 'geocode_full_response'] = result['full_response']
        
        if result['longitude'] is not None:
            successful += 1
            print(f"  ✓ Success: {result['latitude']:.4f}, {result['longitude']:.4f}")
        else:
            failed += 1
            print(f"  ✗ Failed to geocode")
        
        # Rate limiting - be nice to the API
        time.sleep(0.1)  # 100ms delay between requests
    
    # Save results
    print(f"\nGeocoding complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/len(df)*100:.1f}%")
    
    # Save to CSV
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nResults saved to: {OUTPUT_CSV}")
    
    # Create a summary
    summary_df = df[['SGO Report ID', 'Location Address / Description', 'Zip Code', 
                     'latitude', 'longitude', 'place_name', 'geocode_relevance']]
    
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