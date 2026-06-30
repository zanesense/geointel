const map = L.map("map").setView([20,0],2);

L.tileLayer(
  "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
  { maxZoom:19 }
).addTo(map);

const markers = L.layerGroup().addTo(map);

function addMarker(lat, lon, label) {
  markers.clearLayers();
  L.circleMarker([lat, lon], {
    radius:8,
    color:"#38bdf8",
    fillOpacity:0.9
  }).addTo(markers).bindPopup(label).openPopup();
}
