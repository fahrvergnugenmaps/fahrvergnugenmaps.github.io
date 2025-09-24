console.log('foo');

mapboxgl.accessToken = 'pk.eyJ1IjoidG9tYXNubjk4IiwiYSI6ImNseHI4MHg4ZzBrdXQyam9tbmR2Y2ZlZHQifQ.naW1BbxBbf20EERFLqREng';
const geojson = {
    "type": "FeatureCollection",
    "features": [
        
    ]
};

const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v11',
    center: [-121.98322731088342, 37.292166637386245],
    zoom: 8.5
});

console.log('Adding markers from GeoJSON data...');
geojson.features.forEach(function(marker) {
    console.log('Adding marker:', marker);

    var el = document.createElement('div');
    el.className = 'marker';
	console.log('made it')

    if (marker.properties.type === "A") {
    	console.log('found apple')
        el.classList.add('a');
    } else if (marker.properties.type === "CBAT") {
        el.classList.add('cbat');
    } else if (marker.properties.type === "CTE") {
        el.classList.add('cte');
    } else if (marker.properties.type === "EMG") {
        el.classList.add('emg');
    } else if (marker.properties.type === "G") {
        el.classList.add('g');
    } else if (marker.properties.type === "KL") {
        el.classList.add('kl');
    }

    new mapboxgl.Marker(el)
        .setLngLat(marker.geometry.coordinates)
        .setPopup(new mapboxgl.Popup({ offset: 25 }) 
            .setHTML('<h3>' + marker.properties.title + '</h3><p>' + marker.properties.description + '</p>'))
        .addTo(map);
});