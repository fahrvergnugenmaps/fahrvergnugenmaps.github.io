import pandas as pd
import json
import os
import sys
from datetime import datetime

def process_csv_to_html(input_csv_path, output_html_path=None, mapbox_token=None):
    """
    Process CSV file using pandas and generate HTML with embedded data
    
    Args:
        input_csv_path: Path to the CSV file
        output_html_path: Path for output HTML file (optional)
        mapbox_token: Your Mapbox access token (optional - will prompt if not provided)
    """
    
    # Read CSV file
    print(f"📂 Reading CSV file: {input_csv_path}")
    try:
        df = pd.read_csv(input_csv_path)
    except FileNotFoundError:
        print(f"❌ Error: File '{input_csv_path}' not found")
        return
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return
    
    print(f"✅ Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"📊 Columns found: {', '.join(df.columns)}")
    
    # Try to identify relevant columns (case-insensitive)
    column_mapping = {}
    
    for col in df.columns:
        col_lower = col.lower().strip()
        
        # Find longitude columns
        if 'longitude' in col_lower or 'lon' in col_lower:
            column_mapping['longitude'] = col
            print(f"   Found longitude column: '{col}'")
        
        # Find latitude columns
        elif 'latitude' in col_lower or 'lat' in col_lower:
            column_mapping['latitude'] = col
            print(f"   Found latitude column: '{col}'")
        
        # Find address columns
        elif 'address' in col_lower or 'description' in col_lower:
            column_mapping['address'] = col
            print(f"   Found address column: '{col}'")
        
        # Find location name columns
        elif 'location' in col_lower and 'name' not in col_lower:
            column_mapping['location_name'] = col
            print(f"   Found location column: '{col}'")
        
        # Find ID columns
        elif 'id' in col_lower or 'report' in col_lower:
            column_mapping['id'] = col
            print(f"   Found ID column: '{col}'")
        
        # Find date columns
        elif 'date' in col_lower or 'incident' in col_lower:
            column_mapping['date'] = col
            print(f"   Found date column: '{col}'")
    
    # Check for required columns
    if 'longitude' not in column_mapping:
        print("❌ ERROR: Could not find longitude column")
        print("   Looking for columns containing: 'longitude' or 'lon'")
        return
    
    if 'latitude' not in column_mapping:
        print("❌ ERROR: Could not find latitude column")
        print("   Looking for columns containing: 'latitude' or 'lat'")
        return
    
    # Set default values for optional columns
    if 'address' not in column_mapping:
        column_mapping['address'] = df.columns[0]  # Use first column as fallback
        print(f"⚠️  Using '{column_mapping['address']}' as address column")
    
    if 'location_name' not in column_mapping:
        column_mapping['location_name'] = 'Unknown Location'
        print("⚠️  No location name column found, using placeholder")
    
    if 'id' not in column_mapping:
        column_mapping['id'] = 'ID'
        print("⚠️  No ID column found, using row numbers")
    
    # Process data
    locations = []
    skipped_rows = 0
    
    print("\n🔍 Processing data...")
    
    for idx, row in df.iterrows():
        try:
            # Get coordinates
            lon_val = row[column_mapping['longitude']]
            lat_val = row[column_mapping['latitude']]
            
            # Convert to float, handle missing values
            try:
                lon = float(lon_val)
                lat = float(lat_val)
            except (ValueError, TypeError):
                skipped_rows += 1
                continue
            
            # Skip if coordinates are NaN or zero
            if pd.isna(lon) or pd.isna(lat) or lon == 0 or lat == 0:
                skipped_rows += 1
                continue
            
            # Create location object
            location = {
                'id': str(row.get(column_mapping['id'], f"row_{idx}")),
                'lon': lon,
                'lat': lat,
                'address': str(row.get(column_mapping['address'], 'No address')),
                'location_name': str(row.get(column_mapping['location_name'], 'Unknown Location')),
                'date': str(row.get(column_mapping.get('date', ''), '')) if column_mapping.get('date') else '',
                'row_data': {}
            }
            
            # Store all column values
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    location['row_data'][col] = ''
                else:
                    location['row_data'][col] = str(val)
            
            locations.append(location)
            
        except Exception as e:
            skipped_rows += 1
            continue
    
    print(f"✅ Successfully processed {len(locations)} locations")
    if skipped_rows > 0:
        print(f"⚠️  Skipped {skipped_rows} rows due to missing/invalid data")
    
    if len(locations) == 0:
        print("❌ ERROR: No valid locations found with coordinates")
        return
    
    # Get Mapbox token
    if not mapbox_token:
        mapbox_token = input("\n🔑 Enter your Mapbox access token (get one at mapbox.com): ").strip()
        if not mapbox_token:
            print("⚠️  Using demo token (may have limited functionality)")
            mapbox_token = 'pk.eyJ1IjoiZXhhbXBsZXVzZXIiLCJhIjoiY2x0b2JjM2xkMDVzYjJqb2I1a25oa3B6NyJ9.dummy_token'
    
    # Set output path
    if not output_html_path:
        base_name = os.path.splitext(input_csv_path)[0]
        output_html_path = f"{base_name}_map.html"
    
    # Generate HTML
    print(f"\n🛠️  Generating HTML file: {output_html_path}")
    generate_html(locations, output_html_path, os.path.basename(input_csv_path), mapbox_token)
    
    print(f"\n🎉 Success! HTML file generated: {output_html_path}")
    print(f"📊 Total locations: {len(locations)}")
    print(f"📍 Open {output_html_path} in your web browser to view the map")

def generate_html(locations, output_path, csv_filename, mapbox_token):
    """
    Generate HTML file with embedded location data
    """
    # Convert locations to JSON for embedding
    locations_json = json.dumps(locations, indent=2)
    
    # Calculate bounds for initial map view
    if locations:
        lons = [loc['lon'] for loc in locations]
        lats = [loc['lat'] for loc in locations]
        center_lon = sum(lons) / len(lons)
        center_lat = sum(lats) / len(lats)
    else:
        center_lon, center_lat = -98.5795, 39.8283  # Center of US
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSV Map: {csv_filename}</title>
    <script src="https://api.mapbox.com/mapbox-gl-js/v2.14.1/mapbox-gl.js"></script>
    <link href="https://api.mapbox.com/mapbox-gl-js/v2.14.1/mapbox-gl.css" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        
        #map {{ 
            position: fixed; 
            top: 0; 
            left: 0; 
            right: 0; 
            bottom: 0; 
        }}
        
        .sidebar {{
            position: fixed;
            top: 20px;
            left: 20px;
            width: 350px;
            max-height: calc(100vh - 40px);
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            padding: 20px;
            overflow-y: auto;
            z-index: 1000;
        }}
        
        .sidebar h2 {{
            margin: 0 0 15px 0;
            color: #333;
            font-size: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #0066cc;
        }}
        
        .stats {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }}
        
        .stat-item {{
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            font-size: 14px;
        }}
        
        .stat-value {{
            font-weight: 600;
            color: #0066cc;
        }}
        
        .controls {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin: 20px 0;
        }}
        
        button {{
            background: #0066cc;
            color: white;
            border: none;
            padding: 12px 15px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }}
        
        button:hover {{
            background: #0052a3;
            transform: translateY(-1px);
        }}
        
        button:active {{
            transform: translateY(0);
        }}
        
        .details-panel {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            right: 20px;
            max-height: 300px;
            background: rgba(255, 255, 255, 0.98);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            z-index: 1000;
            display: none;
            overflow-y: auto;
        }}
        
        .details-header {{
            background: #0066cc;
            color: white;
            padding: 15px 20px;
            border-radius: 12px 12px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .details-content {{
            padding: 20px;
        }}
        
        .location-card {{
            background: white;
            border-left: 4px solid #0066cc;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            font-size: 12px;
        }}
        
        .data-table th, .data-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        
        .data-table th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        
        .data-table tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        
        .marker {{
            background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="%230066cc" d="M12 0C7.2 0 3 4.2 3 9c0 5.3 9 15 9 15s9-9.7 9-15c0-4.8-42-9-9-9zm0 13c-2.2 0-4-1.8-4-4s1.8-4 4-4 4 1.8 4 4-1.8 4-4 4z"/></svg>');
            background-size: cover;
            width: 24px;
            height: 24px;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        
        .marker:hover {{
            transform: scale(1.2);
        }}
        
        .mapboxgl-popup {{
            max-width: 300px;
        }}
        
        .mapboxgl-popup-content {{
            padding: 15px;
            border-radius: 8px;
        }}
        
        .notification {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #0066cc;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 2000;
            display: none;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="sidebar">
        <h2>📍 CSV Location Map</h2>
        <div class="stats">
            <div class="stat-item">
                <span>File:</span>
                <span class="stat-value">{csv_filename}</span>
            </div>
            <div class="stat-item">
                <span>Total Locations:</span>
                <span class="stat-value" id="location-count">{len(locations)}</span>
            </div>
            <div class="stat-item">
                <span>Generated:</span>
                <span class="stat-value">{datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
            </div>
        </div>
        
        <div class="controls">
            <button onclick="fitToBounds()">📍 Fit to All Locations</button>
            <button onclick="exportData()">💾 Export as JSON</button>
            <button onclick="showAllData()">📊 Show All Data Table</button>
            <button onclick="toggleClusters()">⚙️ Toggle Clustering</button>
        </div>
        
        <div style="margin-top: 20px; font-size: 12px; color: #666;">
            <p><strong>Instructions:</strong></p>
            <p>• Click on any marker to see details</p>
            <p>• Use mouse to zoom and pan</p>
            <p>• Clustering helps with large datasets</p>
        </div>
    </div>
    
    <div class="details-panel" id="detailsPanel">
        <div class="details-header">
            <h3 style="margin: 0; font-size: 16px;">Location Details</h3>
            <button onclick="closeDetails()" style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 5px 10px; border-radius: 4px; cursor: pointer;">✕ Close</button>
        </div>
        <div class="details-content" id="detailsContent">
            <!-- Details will be inserted here -->
        </div>
    </div>
    
    <div class="notification" id="notification"></div>

    <script>
        // Embedded data
        const locations = {locations_json};
        
        // Mapbox setup
        mapboxgl.accessToken = '{mapbox_token}';
        
        let map;
        let markers = [];
        let useClustering = false;
        
        // Initialize map
        function initMap() {{
            map = new mapboxgl.Map({{
                container: 'map',
                style: 'mapbox://styles/mapbox/light-v11',
                center: [{center_lon}, {center_lat}],
                zoom: 4
            }});
            
            // Add controls
            map.addControl(new mapboxgl.NavigationControl());
            map.addControl(new mapboxgl.GeolocateControl({{
                positionOptions: {{
                    enableHighAccuracy: true
                }},
                trackUserLocation: true
            }}));
            
            // Load markers after map is ready
            map.on('load', () => {{
                plotMarkers();
                fitToBounds();
            }});
        }}
        
        function plotMarkers() {{
            // Clear existing markers
            markers.forEach(marker => marker.remove());
            markers = [];
            
            locations.forEach(location => {{
                // Create marker element
                const el = document.createElement('div');
                el.className = 'marker';
                el.title = location.location_name;
                
                // Create marker
                const marker = new mapboxgl.Marker(el)
                    .setLngLat([location.lon, location.lat])
                    .addTo(map);
                
                // Add click handler
                el.addEventListener('click', (e) => {{
                    e.stopPropagation();
                    showLocationDetails(location);
                }});
                
                // Add popup
                const popup = new mapboxgl.Popup({{
                    offset: 25,
                    closeButton: false
                }}).setHTML(`<h3>${{location.location_name}}</h3>
                    <p><strong>Address:</strong> ${{location.address}}</p>
                    <p><strong>Date:</strong> ${{location.date || 'Not specified'}}</p>
                    <p><strong>Coordinates:</strong> ${{location.lat.toFixed(6)}}, ${{location.lon.toFixed(6)}}</p>
                    <p style="margin-top: 8px; font-size: 12px; color: #666;">Click marker for full details</p>`);
                
                marker.setPopup(popup);
                markers.push(marker);
            }});
            
            showNotification(`Loaded ${{locations.length}} locations`);
        }}
        
        function showLocationDetails(location) {{
            const detailsPanel = document.getElementById('detailsPanel');
            const detailsContent = document.getElementById('detailsContent');
            
            // Build details HTML
            let html = `
                <div class="location-card">
                    <h4>${{location.location_name}}</h4>
                    <p><strong>ID:</strong> ${{location.id}}</p>
                    <p><strong>Address:</strong> ${{location.address}}</p>
                    <p><strong>Date:</strong> ${{location.date || 'Not specified'}}</p>
                    <p><strong>Coordinates:</strong> ${{location.lat.toFixed(6)}}°, ${{location.lon.toFixed(6)}}°</p>
                </div>
                
                <h4 style="margin-top: 20px;">All Data Fields:</h4>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Field</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>`;
            
            // Add all data fields
            for (const [key, value] of Object.entries(location.row_data)) {{
                html += `<tr>
                    <td><strong>${{key}}</strong></td>
                    <td>${{value}}</td>
                </tr>`;
            }}
            
            html += `</tbody></table>`;
            
            detailsContent.innerHTML = html;
            detailsPanel.style.display = 'block';
            
            // Fly to location
            map.flyTo({{
                center: [location.lon, location.lat],
                zoom: 14,
                essential: true
            }});
        }}
        
        function closeDetails() {{
            document.getElementById('detailsPanel').style.display = 'none';
        }}
        
        function fitToBounds() {{
            if (locations.length === 0) return;
            
            const bounds = new mapboxgl.LngLatBounds();
            locations.forEach(location => {{
                bounds.extend([location.lon, location.lat]);
            }});
            
            map.fitBounds(bounds, {{
                padding: 50,
                maxZoom: 10
            }});
            
            showNotification('Zoomed to show all locations');
        }}
        
        function exportData() {{
            const dataStr = JSON.stringify(locations, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
            
            const exportFileDefaultName = '${{csv_filename}}_data.json';
            
            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileDefaultName);
            linkElement.click();
            
            showNotification('Data exported as JSON');
        }}
        
        function showAllData() {{
            let html = '<h3>All Location Data</h3>';
            html += '<table class="data-table">';
            html += '<thead><tr><th>ID</th><th>Location</th><th>Address</th><th>Latitude</th><th>Longitude</th></tr></thead><tbody>';
            
            locations.forEach(location => {{
                html += `<tr>
                    <td>${{location.id}}</td>
                    <td>${{location.location_name}}</td>
                    <td>${{location.address}}</td>
                    <td>${{location.lat.toFixed(4)}}</td>
                    <td>${{location.lon.toFixed(4)}}</td>
                </tr>`;
            }});
            
            html += '</tbody></table>';
            
            document.getElementById('detailsContent').innerHTML = html;
            document.getElementById('detailsPanel').style.display = 'block';
        }}
        
        function toggleClusters() {{
            useClustering = !useClustering;
            showNotification(`Clustering ${{useClustering ? 'enabled' : 'disabled'}}`);
            // Note: For true clustering, you'd need to implement cluster markers
        }}
        
        function showNotification(message) {{
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.style.display = 'block';
            
            setTimeout(() => {{
                notification.style.display = 'none';
            }}, 3000);
        }}
        
        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', initMap);
    </script>
</body>
</html>"""
    
    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    """
    Main function to run the script
    """
    print("=" * 60)
    print("📊 CSV to Map Converter")
    print("=" * 60)
    
    # Get input file
    if len(sys.argv) > 1:
        input_csv = sys.argv[1]
    else:
        input_csv = input("Enter path to CSV file: ").strip()
    
    # Check if file exists
    if not os.path.exists(input_csv):
        print(f"❌ Error: File '{input_csv}' not found")
        sys.exit(1)
    
    # Optional Mapbox token as second argument
    mapbox_token = None
    if len(sys.argv) > 2:
        mapbox_token = sys.argv[2]
    
    # Optional output path as third argument
    output_html = None
    if len(sys.argv) > 3:
        output_html = sys.argv[3]
    
    # Process the CSV
    process_csv_to_html(input_csv, output_html, mapbox_token)

if __name__ == "__main__":
    main()