import "leaflet/dist/leaflet.css";
import { Marker, Popup, Tooltip } from "react-leaflet";
import L from "leaflet";

// Custom SVG-based divIcons so we get distinct depot/customer markers
// without importing external image files.
function createIcon(color, label, { size = 32, dashed = false } = {}) {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size + 10}" viewBox="0 0 ${size} ${size + 10}">
      <defs>
        <filter id="s" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="1" stdDeviation="1.5" flood-opacity="0.35"/>
        </filter>
      </defs>
      <circle cx="${size / 2}" cy="${size / 2}" r="${size / 2 - 2}"
        fill="${dashed ? "transparent" : color}"
        stroke="${color}" stroke-width="2.5"
        stroke-dasharray="${dashed ? "3,3" : "none"}"
        filter="url(#s)"/>
      <polygon points="${size / 2},${size + 6} ${size / 2 - 5},${size - 2} ${size / 2 + 5},${size - 2}"
        fill="${dashed ? "none" : color}" stroke="${dashed ? color : "none"}" />
      <text x="${size / 2}" y="${size / 2 + 1}" text-anchor="middle" dominant-baseline="central"
            fill="${dashed ? color : "#fff"}" font-size="${label.length > 2 ? 9 : 12}" font-weight="700" font-family="Inter,sans-serif">
        ${label}
      </text>
    </svg>`;

  return L.divIcon({
    html: svg,
    className: "custom-marker",
    iconSize: [size, size + 10],
    iconAnchor: [size / 2, size + 6],
    popupAnchor: [0, -(size / 2 + 6)],
    tooltipAnchor: [0, -(size / 2 + 8)],
  });
}

function LocationMarker({ location, onDragEnd, onRemove }) {
  const isDepot = location.type === "depot";
  // Multiple depots can be placed at once, but only one is used per
  // optimization run -- inactive depots render as a dashed outline so
  // it's visually obvious they're just saved candidates.
  const isInactiveDepot = isDepot && location.active === false;

  const color = isDepot ? "#18b9e8" : "#ff9f43";
  const label = isDepot ? "D" : `${location.displayIndex ?? location.id}`;
  const icon = createIcon(color, label, { dashed: isInactiveDepot });

  return (
    <Marker
      position={[location.latitude, location.longitude]}
      icon={icon}
      draggable
      eventHandlers={{
        dragend: (e) => {
          const { lat, lng } = e.target.getLatLng();
          onDragEnd(location.id, lat, lng);
        },
      }}
    >
      <Tooltip
        direction="top"
        offset={[0, -4]}
        className="route-location-label"
        permanent={false}
      >
        <strong>
          {isDepot
            ? isInactiveDepot
              ? `${location.name || "Depot"} (inactive)`
              : location.name || "Depot"
            : location.name || `Customer ${location.displayIndex ?? location.id}`}
        </strong>
      </Tooltip>
      <Popup>
        <div style={{ minWidth: 140 }}>
          <strong style={{ fontSize: 14 }}>
            {isDepot
              ? `🏭 ${location.name || "Depot"}${isInactiveDepot ? " (inactive)" : ""}`
              : `📦 ${location.name || "Customer " + (location.displayIndex ?? location.id)}`}
          </strong>
          <br />
          <span style={{ fontSize: 11, color: "#888" }}>
            {location.latitude.toFixed(5)}, {location.longitude.toFixed(5)}
          </span>
          {!isDepot && (
            <>
              <br />
              <span style={{ fontSize: 12 }}>Demand: {location.demand}</span>
            </>
          )}
          <br />
          <button
            onClick={() => onRemove(location.id)}
            style={{
              marginTop: 6,
              padding: "3px 10px",
              background: "#e74c62",
              color: "#fff",
              border: "none",
              borderRadius: 5,
              cursor: "pointer",
              fontSize: 11,
              fontWeight: 700,
            }}
          >
            Remove
          </button>
        </div>
      </Popup>
    </Marker>
  );
}

export default LocationMarker;
