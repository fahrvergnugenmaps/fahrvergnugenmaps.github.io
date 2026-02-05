import pandas as pd
import json
from pathlib import Path

def create_map_html(csv_file, output_html='map.html', mapbox_token=None):
    """
    Create an HTML file with a Mapbox map showing all geocoded locations as pins.
    
    Parameters:
    - csv_file: Path to the geocoded CSV file
    - output_html: Output HTML file path
    - mapbox_token: Your Mapbox access token (defaults to the one in your geocoding script)
    """
    
    # Use the same token as your geocoding script if not provided
    if mapbox_token is None:
        mapbox_token = 'pk.eyJ1IjoidG9tYXNubjk4IiwiYSI6ImNseHI4MHg4ZzBrdXQyam9tbmR2Y2ZlZHQifQ.naW1BbxBbf20EERFLqREng'
    
    # Read the CSV file
    print(f"Reading CSV file: {csv_file}")
    df = pd.read_csv(csv_file)
    
    # Check for required columns
    required_cols = ['latitude', 'longitude']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"Error: CSV is missing required columns: {missing_cols}")
        print(f"Available columns: {list(df.columns)}")
        return
    
    # Filter out rows without coordinates
    geocoded_df = df.dropna(subset=['latitude', 'longitude'])
    
    if len(geocoded_df) == 0:
        print("Error: No geocoded locations found in the CSV.")
        return
    
    print(f"Found {len(geocoded_df)} geocoded locations out of {len(df)} total rows")
    
    # Calculate average relevance if column exists
    if 'geocode_relevance' in geocoded_df.columns:
        avg_relevance = f"{geocoded_df['geocode_relevance'].mean():.2f}"
    else:
        avg_relevance = 'N/A'
    
    # Prepare data for the map
    features = []
    for idx, row in geocoded_df.iterrows():
        # Get popup content
        popup_content = []
        
        # Add available information to popup
        if 'SGO Report ID' in df.columns and pd.notna(row['SGO Report ID']):
            popup_content.append(f"<strong>Report ID:</strong> {row['SGO Report ID']}")
        
        if 'Location Address / Description' in df.columns and pd.notna(row['Location Address / Description']):
            popup_content.append(f"<strong>Address:</strong> {row['Location Address / Description']}")
        
        # Check for location column (from your updated script)
        location_cols = [col for col in df.columns if 'location' in col.lower() and col != 'Location Address / Description']
        if location_cols and pd.notna(row[location_cols[0]]):
            popup_content.append(f"<strong>Location:</strong> {row[location_cols[0]]}")
        
        if 'Zip Code' in df.columns and pd.notna(row['Zip Code']):
            popup_content.append(f"<strong>ZIP Code:</strong> {row['Zip Code']}")
        
        if 'place_name' in df.columns and pd.notna(row['place_name']):
            popup_content.append(f"<strong>Geocoded as:</strong> {row['place_name']}")
        
        if 'geocode_relevance' in df.columns and pd.notna(row['geocode_relevance']):
            popup_content.append(f"<strong>Relevance score:</strong> {row['geocode_relevance']:.2f}")
        
        if 'geocode_query_used' in df.columns and pd.notna(row['geocode_query_used']):
            popup_content.append(f"<strong>Query used:</strong> {row['geocode_query_used']}")
        
        # Create feature for GeoJSON
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row['longitude']), float(row['latitude'])]
            },
            "properties": {
                "id": idx,
                "popupContent": "<br>".join(popup_content) if popup_content else f"Location {idx}",
                "relevance": float(row['geocode_relevance']) if 'geocode_relevance' in df.columns and pd.notna(row['geocode_relevance']) else 1.0
            }
        }
        features.append(feature)
    
    # Create GeoJSON data
    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # Convert to JSON string
    geojson_str = json.dumps(geojson_data)
    
    # Calculate center of all points for initial map view
    avg_lat = geocoded_df['latitude'].mean()
    avg_lon = geocoded_df['longitude'].mean()
    
    # Calculate bounds for fitting map to all points
    min_lat = geocoded_df['latitude'].min()
    max_lat = geocoded_df['latitude'].max()
    min_lon = geocoded_df['longitude'].min()
    max_lon = geocoded_df['longitude'].max()
    
    # Create HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Geocoded Locations Map</title>
        <script src='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js'></script>
        <link href='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css' rel='stylesheet' />
        <style>
            body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
            #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
            #sidebar {{
                position: absolute;
                top: 20px;
                left: 20px;
                background: white;
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                max-width: 300px;
                z-index: 1000;
            }}
            #controls {{
                position: absolute;
                top: 20px;
                right: 20px;
                background: white;
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                z-index: 1000;
            }}
            h1 {{ margin: 0 0 10px 0; font-size: 18px; }}
            p {{ margin: 0 0 10px 0; font-size: 14px; }}
            .legend {{ display: flex; align-items: center; margin-bottom: 5px; }}
            .legend-color {{ width: 20px; height: 20px; margin-right: 10px; border-radius: 50%; }}
            .legend-text {{ font-size: 12px; }}
            button {{
                padding: 8px 12px;
                margin: 5px 0;
                background: #4264fb;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                font-size: 14px;
                width: 100%;
            }}
            button:hover {{ background: #3151e0; }}
            .mapboxgl-popup {{
                max-width: 300px;
                font: 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;
            }}
            .mapboxgl-popup-content {{
                padding: 15px;
            }}
        </style>
    </head>
    <body>
        <div id="sidebar">
            <h1>📍 Geocoded Locations</h1>
            <p>Total locations: <strong>{len(geocoded_df)}</strong></p>
            <p>Average relevance: <strong>{avg_relevance}</strong></p>
            
            <div class="legend">
                <div class="legend-color" style="background-color: #ff6b6b;"></div>
                <div class="legend-text">High relevance (&gt; 0.8)</div>
            </div>
            <div class="legend">
                <div class="legend-color" style="background-color: #ffd166;"></div>
                <div class="legend-text">Medium relevance (0.5-0.8)</div>
            </div>
            <div class="legend">
                <div class="legend-color" style="background-color: #06d6a0;"></div>
                <div class="legend-text">Low relevance (&lt; 0.5)</div>
            </div>
        </div>
        
        <div id="controls">
            <button id="fit-bounds">Fit to All Locations</button>
            <button id="reset-view">Reset View</button>
            <button id="toggle-clusters">Toggle Clustering</button>
            <button id="download-data">Download GeoJSON</button>
        </div>
        
        <div id="map"></div>
        
        <script>
            // Set your Mapbox access token
            mapboxgl.accessToken = '{mapbox_token}';
            
            // Initialize map
            const map = new mapboxgl.Map({{
                container: 'map',
                style: 'mapbox://styles/mapbox/streets-v12',
                center: [{avg_lon}, {avg_lat}],
                zoom: 10
            }});
            
            // GeoJSON data
            const geojsonData = {geojson_str};
            
            // Store original bounds
            const bounds = [[{min_lon}, {min_lat}], [{max_lon}, {max_lat}]];
            
            // Wait for map to load
            map.on('load', () => {{
                
                // Add source
                map.addSource('locations', {{
                    'type': 'geojson',
                    'data': geojsonData,
                    'cluster': true,
                    'clusterMaxZoom': 14,
                    'clusterRadius': 50
                }});
                
                // Add clusters layer
                map.addLayer({{
                    id: 'clusters',
                    type: 'circle',
                    source: 'locations',
                    filter: ['has', 'point_count'],
                    paint: {{
                        'circle-color': '#4264fb',
                        'circle-radius': [
                            'step',
                            ['get', 'point_count'],
                            20,
                            100,
                            30,
                            750,
                            40
                        ],
                        'circle-opacity': 0.8
                    }}
                }});
                
                // Add cluster count layer
                map.addLayer({{
                    id: 'cluster-count',
                    type: 'symbol',
                    source: 'locations',
                    filter: ['has', 'point_count'],
                    layout: {{
                        'text-field': '{{point_count_abbreviated}}',
                        'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
                        'text-size': 12
                    }},
                    paint: {{
                        'text-color': '#ffffff'
                    }}
                }});
                
                // Add individual points layer
                map.addLayer({{
                    id: 'unclustered-point',
                    type: 'circle',
                    source: 'locations',
                    filter: ['!', ['has', 'point_count']],
                    paint: {{
                        'circle-color': [
                            'case',
                            ['>', ['get', 'relevance'], 0.8], '#ff6b6b',  // High relevance - red
                            ['>=', ['get', 'relevance'], 0.5], '#ffd166',  // Medium relevance - yellow
                            '#06d6a0'  // Low relevance - green
                        ],
                        'circle-radius': 8,
                        'circle-stroke-width': 2,
                        'circle-stroke-color': '#ffffff'
                    }}
                }});
                
                // Add popups on click
                map.on('click', 'unclustered-point', (e) => {{
                    const coordinates = e.features[0].geometry.coordinates.slice();
                    const properties = e.features[0].properties;
                    
                    // Ensure the popup appears in the correct place
                    while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {{
                        coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
                    }}
                    
                    new mapboxgl.Popup()
                        .setLngLat(coordinates)
                        .setHTML(properties.popupContent)
                        .addTo(map);
                }});
                
                // Add popups for clusters
                map.on('click', 'clusters', (e) => {{
                    const features = map.queryRenderedFeatures(e.point, {{
                        layers: ['clusters']
                    }});
                    const clusterId = features[0].properties.cluster_id;
                    const source = map.getSource('locations');
                    
                    source.getClusterExpansionZoom(clusterId, (err, zoom) => {{
                        if (err) return;
                        
                        map.easeTo({{
                            center: features[0].geometry.coordinates,
                            zoom: zoom
                        }});
                    }});
                }});
                
                // Change cursor on hover
                map.on('mouseenter', 'clusters', () => {{
                    map.getCanvas().style.cursor = 'pointer';
                }});
                
                map.on('mouseleave', 'clusters', () => {{
                    map.getCanvas().style.cursor = '';
                }});
                
                map.on('mouseenter', 'unclustered-point', () => {{
                    map.getCanvas().style.cursor = 'pointer';
                }});
                
                map.on('mouseleave', 'unclustered-point', () => {{
                    map.getCanvas().style.cursor = '';
                }});
            }});
            
            // Control buttons
            document.getElementById('fit-bounds').addEventListener('click', () => {{
                map.fitBounds(bounds, {{ padding: 50 }});
            }});
            
            document.getElementById('reset-view').addEventListener('click', () => {{
                map.flyTo({{
                    center: [{avg_lon}, {avg_lat}],
                    zoom: 10,
                    essential: true
                }});
            }});
            
            document.getElementById('toggle-clusters').addEventListener('click', () => {{
                const clustersVisible = map.getLayoutProperty('clusters', 'visibility');
                const newVisibility = clustersVisible === 'visible' ? 'none' : 'visible';
                
                map.setLayoutProperty('clusters', 'visibility', newVisibility);
                map.setLayoutProperty('cluster-count', 'visibility', newVisibility);
                
                // Update button text
                document.getElementById('toggle-clusters').textContent = 
                    newVisibility === 'visible' ? 'Hide Clusters' : 'Show Clusters';
            }});
            
            document.getElementById('download-data').addEventListener('click', () => {{
                const dataStr = JSON.stringify(geojsonData, null, 2);
                const dataBlob = new Blob([dataStr], {{ type: 'application/json' }});
                const url = URL.createObjectURL(dataBlob);
                
                const link = document.createElement('a');
                link.href = url;
                link.download = 'geocoded_locations.geojson';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
            }});
            
            // Add navigation controls
            map.addControl(new mapboxgl.NavigationControl());
            
            // Add scale control
            map.addControl(new mapboxgl.ScaleControl());
            
            // Add geolocate control
            map.addControl(new mapboxgl.GeolocateControl({{
                positionOptions: {{
                    enableHighAccuracy: true
                }},
                trackUserLocation: true,
                showUserLocation: true
            }}));
            
            // Add fullscreen control
            map.addControl(new mapboxgl.FullscreenControl());
        </script>
    </body>
    </html>
    """
    
    # Write HTML file
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Map HTML created: {output_html}")
    print(f"Open this file in your browser to view the interactive map")
    
    # Print summary statistics
    if 'geocode_relevance' in geocoded_df.columns:
        high_rel = len(geocoded_df[geocoded_df['geocode_relevance'] > 0.8])
        med_rel = len(geocoded_df[(geocoded_df['geocode_relevance'] >= 0.5) & (geocoded_df['geocode_relevance'] <= 0.8)])
        low_rel = len(geocoded_df[geocoded_df['geocode_relevance'] < 0.5])
        
        print(f"\nRelevance distribution:")
        print(f"  High relevance (>0.8): {high_rel} locations")
        print(f"  Medium relevance (0.5-0.8): {med_rel} locations")
        print(f"  Low relevance (<0.5): {low_rel} locations")

def main():
    # Configuration
    CSV_FILE = 'geocoded_output.csv'  # Your geocoded output file
    OUTPUT_HTML = 'locations_map.html'
    
    # Optional: Provide a different Mapbox token if needed
    MAPBOX_TOKEN = None  # Uses default from your script
    
    # Create the map
    create_map_html(CSV_FILE, OUTPUT_HTML, MAPBOX_TOKEN)
    
    # Also check for simplified file
    simplified_csv = 'geocoded_simplified.csv'
    if Path(simplified_csv).exists():
        print(f"\nFound simplified file, creating another map...")
        create_map_html(simplified_csv, 'locations_map_simplified.html', MAPBOX_TOKEN)

if __name__ == "__main__":
    main()