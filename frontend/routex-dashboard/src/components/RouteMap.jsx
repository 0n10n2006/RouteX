import { MapContainer, TileLayer, GeoJSON, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const KOTHRUD_CENTER = [18.5095, 73.7982];

function RouteMap({ geometry }) {
  if (!geometry) {
    return (
      <div className="route-map-empty">
        <div>
          <strong>No route geometry available</strong>
          <p>Run the Kothrud OSM scenario to display the optimized route.</p>
        </div>
      </div>
    );
  }

  const locations = geometry.locations || [];

  return (
    <div className="route-map-container">
      <MapContainer
        center={KOTHRUD_CENTER}
        zoom={15}
        scrollWheelZoom={true}
        className="route-map"
      >
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <GeoJSON
          data={{
            type: "FeatureCollection",
            features: geometry.features || [],
          }}
          style={{
            weight: 6,
          }}
        />

        {locations.map((location) => (
          <CircleMarker
            key={location.id}
            center={[location.latitude, location.longitude]}
            radius={7}
          >
            <Popup>
              <strong>{location.name}</strong>
              <br />
              Location {location.id}
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}

export default RouteMap;