// Replace 'YOUR_MAPBOX_ACCESS_TOKEN' with your Mapbox access token
mapboxgl.accessToken = 'pk.eyJ1IjoidG9tYXNubjk4IiwiYSI6ImNseHI4MHg4ZzBrdXQyam9tbmR2Y2ZlZHQifQ.naW1BbxBbf20EERFLqREng';

// Initialize the map
var map = new mapboxgl.Map({
  container: 'map', // container id specified in the HTML
  style: 'mapbox://styles/mapbox/streets-v11', // style URL
  center: [-121.98685827727454,37.360250540945366], // starting position [lng, lat]
  zoom: 9 // starting zoom
});