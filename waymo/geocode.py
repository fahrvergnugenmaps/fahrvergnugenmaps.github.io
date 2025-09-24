import requests

def geocode_address(address, mapbox_token):
    """Geocode an address using Mapbox API and return coordinates."""
    base_url = "https://api.mapbox.com/geocoding/v5/mapbox.places"
    
    # Encode the address for URL (replace spaces with %20)
    encoded_address = requests.utils.quote(address)
    
    # Construct the API request URL
    url = f"{base_url}/{encoded_address}.json?access_token={mapbox_token}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()
        
        if data.get("features"):
            # Extract first result's coordinates [longitude, latitude]
            print(data)
            longitude, latitude = data["features"][0]["center"]
            return {"latitude": latitude, "longitude": longitude}
        else:
            return {"error": "No results found"}
    
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}

# Example Usage
if __name__ == "__main__":
    MAPBOX_TOKEN = "pk.eyJ1IjoidG9tYXNubjk4IiwiYSI6ImNtYWhzMHpsdTA2MTUyb3E1dHBzNTJmOGsifQ.4OQZndB_QZgm6ILYTGkiIQ"  # Replace with your token
    address = "19th Street & Tennessee Street, San Francisco, CA"
    
    result = geocode_address(address, MAPBOX_TOKEN)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Address: {address}")
        print(f"Coordinates (Lat, Lng): {result['latitude']}, {result['longitude']}")