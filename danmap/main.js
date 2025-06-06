console.log('foo');

mapboxgl.accessToken = 'pk.eyJ1IjoidG9tYXNubjk4IiwiYSI6ImNseHI4MHg4ZzBrdXQyam9tbmR2Y2ZlZHQifQ.naW1BbxBbf20EERFLqREng';
const geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [-121.99086461286373, 37.408798455507124]
            },
            "properties": {
            	"type": "a",
                "title": "a",
                "description": "Performed content analysis, validation, cleansing, and collection. Created and published regularly scheduled and ad hoc reports."
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [-121.94056278133901, 37.47480348449061]
            },
            "properties": {
            	"type": "cbat",
                "title": "cbat",
                "description": "Created, maintained and reviewed map data to assist functionality of autonomous vehicles. Performed large scale audits of existing maps."
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [-122.2724378471316, 37.5680079516563]
            },
            "properties": {
            	"type": "cte",
                "title": "cte",
                "description": "Created, maintained and reviewed map data to assist functionality of autonomous vehicles. Took ownership of map health reports. Created scripts to automate regular tasks and reduce Cartographer burden."
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [-122.0528909204977, 37.38741730182734]
            },
            "properties": {
            	"type": "emg",
                "title": "emg",
                "description": "Created training maps for on-vehicle map model. Created and reviewed map data to assist functionality of autonomous vehicles."
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [-122.05981694194026, 36.99869900860264]
            },
            "properties": {
            	"type": "g",
                "title": "g",
                "description": "2016-2020 Environmental Studies BA, GIS Concentration"
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [-122.05705446913795, 36.95975300013402]
            },
            "properties": {
            	"type": "kl",
                "title": "kl",
                "description": "Performed GIS analysis on a parcel map to find usable land for Accessory Dwelling Units. Prepared key reports for investors and stakeholders."
            }
        }
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