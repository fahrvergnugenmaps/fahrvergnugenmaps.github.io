// Replace 'YOUR_MAPBOX_ACCESS_TOKEN' with your Mapbox access token
mapboxgl.accessToken = 'pk.eyJ1IjoidG9tYXNubjk4IiwiYSI6ImNseHI4MHg4ZzBrdXQyam9tbmR2Y2ZlZHQifQ.naW1BbxBbf20EERFLqREng';

const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v11',
    center: [-121.98685827727454, 37.360250540945366],
    zoom: 9
});

// Fetch points from the JSON file and add them to the map
fetch('points.json')
    .then(response => response.json())
    .then(geojson => {
        geojson.features.forEach(function(marker) {
            // Create a HTML element for each feature
            var el = document.createElement('div');
            el.className = 'marker';

            // Make a marker for each feature and add to the map
            new mapboxgl.Marker(el)
                .setLngLat(marker.geometry.coordinates)
                .setPopup(new mapboxgl.Popup({ offset: 25 }) // add popups
                    .setHTML('<h3>' + marker.properties.title + '</h3><p>' + marker.properties.description + '</p>'))
                .addTo(map);
        });
    })
    .catch(error => console.error('Error fetching GeoJSON:', error));
   