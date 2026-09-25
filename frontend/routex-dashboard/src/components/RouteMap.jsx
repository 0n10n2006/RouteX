import { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  CircleMarker,
  Popup,
  Tooltip,
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

const VEHICLE_COLOURS = ["#42d9ff", "#ff9f43", "#a78bfa", "#34d399"];

// Fallback center used only if a run somehow has no locations at all.
const DEFAULT_CENTER = [18.5095, 73.7982];

function RecenterMap({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds && bounds.length > 0) {
      try {
        map.fitBounds(bounds, { padding: [40, 40] });
      } catch (e) {
        console.error("fitBounds error:", e);
      }
    }
  }, [map, bounds]);
  return null;
}

function RouteMap({ geometry }) {
  if (!geometry) {
    return (
      <div className="route-map-empty">
        <div>
          <strong>No route geometry available</strong>
          <p>Run an OSM-backed scenario to display the optimized route.</p>
        </div>
      </div>
    );
  }

  const locations = geometry.locations || [];

  // Fit the map to whichever locations came back, or extract from coordinates
  const bounds =
    locations.length > 0
      ? locations.map((location) => [location.latitude, location.longitude])
      : (geometry.features || []).flatMap((f) =>
          (f.geometry?.coordinates || []).map((c) => [c[1], c[0]])
        );

  const validBounds = bounds.length > 0 ? bounds : null;
  const features = geometry.features || [];

  return (
    <div className="route-map-container">
      <MapContainer
        key={`map-${geometry.run_id || "geom"}-${locations.length}-${validBounds?.[0]?.[0] || 0}`}
        {...(validBounds
          ? { bounds: validBounds, boundsOptions: { padding: [40, 40] } }
          : { center: DEFAULT_CENTER, zoom: 17 })}
        scrollWheelZoom={true}
        className="route-map dark-tiles"
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {validBounds && <RecenterMap bounds={validBounds} />}

        {features.length > 0 && (
          <GeoJSON
            key={`geojson-${geometry.run_id || "route"}-${JSON.stringify(
              features.map((f) => f.geometry?.coordinates?.length)
            )}`}
            data={{
              type: "FeatureCollection",
              features: features,
            }}
            style={(feature) => ({
              color:
                VEHICLE_COLOURS[
                  ((feature?.properties?.vehicle_index || 1) - 1) %
                    VEHICLE_COLOURS.length
                ],
              weight: 6,
              opacity: 0.9,
            })}
          />
        )}

        {locations.map((location) => {
  const isDepot = location.id === 0;
  const label = isDepot ? "D0" : `C${location.id}`;

  return (
    <CircleMarker
      key={location.id}
      center={[location.latitude, location.longitude]}
      radius={isDepot ? 9 : 7}
      pathOptions={{
        weight: 2,
        fillOpacity: 1,
      }}
    >
      <Tooltip
        permanent
        direction="top"
        offset={[0, -10]}
        className="route-location-label"
      >
        <strong>{label}</strong>
      </Tooltip>

      <Popup>
        <strong>
          {isDepot ? "Depot 0" : `Customer ${location.id}`}
        </strong>
        <br />
        {location.name}
        <br />
        Location {location.id}
      </Popup>
    </CircleMarker>
  );
})}
      </MapContainer>
    </div>
  );
}

export default RouteMap;
