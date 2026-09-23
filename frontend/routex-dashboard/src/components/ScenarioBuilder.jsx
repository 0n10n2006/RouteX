import { useState, useCallback, useRef, useMemo, useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  useMapEvents,
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import axios from "axios";
import LocationMarker from "./LocationMarker";
import SearchBox from "./SearchBox";

const API_URL = import.meta.env.VITE_API_URL || "/api";

const ALGORITHMS = [
  ["greedy", "Greedy"],
  ["ga", "Genetic Algorithm (GA)"],
  ["pso", "Particle Swarm (PSO)"],
  ["qpso", "QPSO"],
  ["hybrid", "Hybrid QPSO"],
];

const DEFAULT_CENTER = [28.6139, 77.209]; // New Delhi

// Fly the map to given coords
function FlyTo({ center, zoom }) {
  const map = useMap();
  if (center) map.flyTo(center, zoom || 14, { duration: 1.2 });
  return null;
}

// Click handler on the map surface
function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click: (e) => onMapClick(e.latlng),
  });
  return null;
}

// Fit bounds helper
function FitBounds({ locations }) {
  const map = useMap();
  if (locations.length > 1) {
    const bounds = locations.map((l) => [l.latitude, l.longitude]);
    map.fitBounds(bounds, { padding: [60, 60], maxZoom: 16 });
  } else if (locations.length === 1) {
    map.flyTo([locations[0].latitude, locations[0].longitude], 15, {
      duration: 0.8,
    });
  }
  return null;
}

let nextId = 1;

function ScenarioBuilder({ onResult }) {
  const [locations, setLocations] = useState([]);
  const [vehicles, setVehicles] = useState([
    { id: 1, capacity: 10 },
    { id: 2, capacity: 10 },
  ]);
  const [algorithm, setAlgorithm] = useState("qpso");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [flyTarget, setFlyTarget] = useState(null);
  const [routeGeometry, setRouteGeometry] = useState(null);
  const [result, setResult] = useState(null);
  const fileInputRef = useRef(null);
  const nextVehicleId = useRef(3);

  const [permanentDepots, setPermanentDepots] = useState([]);
  
  const hasDepot = locations.some((l) => l.type === "depot");
  const customers = locations.filter((l) => l.type === "customer");
  
  // Load permanent depots on mount
  useEffect(() => {
    const fetchDepots = async () => {
      try {
        const res = await axios.get(`${API_URL}/depots`);
        setPermanentDepots(res.data.depots);
      } catch (err) {
        // Not logged in or error
      }
    };
    fetchDepots();
  }, []);
  
  const saveDepot = async (loc) => {
    try {
      const res = await axios.post(`${API_URL}/depots`, {
        name: loc.name || "My Depot",
        latitude: loc.latitude,
        longitude: loc.longitude
      });
      setPermanentDepots(prev => [...prev, res.data]);
      alert("Depot saved permanently!");
    } catch (err) {
      alert("Failed to save depot. Are you logged in?");
    }
  };
  
  const loadDepot = (depot) => {
    setLocations(prev => {
      const withoutDepot = prev.filter(l => l.type !== "depot");
      return [...withoutDepot, {
        id: nextId++,
        name: depot.name,
        latitude: depot.latitude,
        longitude: depot.longitude,
        type: "depot",
        demand: 0
      }];
    });
    setFlyTarget({ center: [depot.latitude, depot.longitude], zoom: 15 });
  };

  const handleMapClick = useCallback(
    (latlng) => {
      const type = hasDepot ? "customer" : "depot";
      const id = nextId++;
      setLocations((prev) => [
        ...prev,
        {
          id,
          name: type === "depot" ? "Depot" : "",
          latitude: latlng.lat,
          longitude: latlng.lng,
          type,
          demand: type === "customer" ? 2 : 0,
        },
      ]);
      setRouteGeometry(null);
      setResult(null);
    },
    [hasDepot]
  );

  const handleDragEnd = useCallback((id, lat, lng) => {
    setLocations((prev) =>
      prev.map((l) =>
        l.id === id ? { ...l, latitude: lat, longitude: lng } : l
      )
    );
    setRouteGeometry(null);
    setResult(null);
  }, []);

  const handleRemove = useCallback((id) => {
    setLocations((prev) => prev.filter((l) => l.id !== id));
    setRouteGeometry(null);
    setResult(null);
  }, []);

  const updateLocation = useCallback((id, field, value) => {
    setLocations((prev) =>
      prev.map((l) => (l.id === id ? { ...l, [field]: value } : l))
    );
  }, []);

  const handleSearch = useCallback((place) => {
    setFlyTarget({
      center: [place.latitude, place.longitude],
      zoom: place.boundingbox ? 14 : 15,
    });
    // Clear fly target after animation
    setTimeout(() => setFlyTarget(null), 1500);
  }, []);

  const addVehicle = () => {
    setVehicles((prev) => [
      ...prev,
      { id: nextVehicleId.current++, capacity: 10 },
    ]);
  };

  const removeVehicle = (id) => {
    setVehicles((prev) => prev.filter((v) => v.id !== id));
  };

  const updateVehicleCapacity = (id, capacity) => {
    setVehicles((prev) =>
      prev.map((v) =>
        v.id === id
          ? { ...v, capacity: Math.max(1, parseInt(capacity) || 1) }
          : v
      )
    );
  };

  const clearAll = () => {
    setLocations([]);
    setRouteGeometry(null);
    setResult(null);
    setError("");
  };

  // JSON import/export
  const exportJSON = () => {
    const data = JSON.stringify({ locations, vehicles }, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "routex-scenario.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const importJSON = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const data = JSON.parse(ev.target.result);
        if (data.locations && Array.isArray(data.locations)) {
          setLocations(data.locations);
          nextId = Math.max(...data.locations.map((l) => l.id), nextId) + 1;
        }
        if (data.vehicles && Array.isArray(data.vehicles)) {
          setVehicles(data.vehicles);
          nextVehicleId.current =
            Math.max(...data.vehicles.map((v) => v.id), 0) + 1;
        }
        setRouteGeometry(null);
        setResult(null);
        setError("");
      } catch {
        setError("Invalid JSON file.");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  const runOptimization = async () => {
    if (!hasDepot || customers.length === 0 || vehicles.length === 0) {
      setError(
        "Place at least 1 depot and 1 customer, and add at least 1 vehicle."
      );
      return;
    }

    setLoading(true);
    setError("");
    setRouteGeometry(null);
    setResult(null);

    try {
      const res = await axios.post(`${API_URL}/optimize/custom`, {
        locations: locations.map((l) => ({
          id: l.id,
          name: l.name,
          latitude: l.latitude,
          longitude: l.longitude,
          type: l.type,
          demand: l.demand || 1,
        })),
        vehicles: vehicles.map((v) => ({ id: v.id, capacity: v.capacity })),
        algorithm,
        seed: 42,
      });

      const optimizationResult = res.data;
      setResult(optimizationResult);

      if (optimizationResult.geometry) {
        setRouteGeometry(optimizationResult.geometry);
      }

      if (onResult) onResult(optimizationResult);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Optimization failed. Check that the backend is running and locations are on reachable roads."
      );
    } finally {
      setLoading(false);
    }
  };

  // Vehicle colors for route rendering
  const VEHICLE_COLOURS = ["#42d9ff", "#ff9f43", "#a78bfa", "#34d399", "#f472b6", "#fbbf24"];

  // Customer display indices (1-based, ordered by addition)
  const customerIndices = useMemo(() => {
    const map = {};
    let idx = 1;
    for (const l of locations) {
      if (l.type === "customer") map[l.id] = idx++;
    }
    return map;
  }, [locations]);

  return (
    <div className="view">
      <div className="page-header">
        <div>
          <span className="page-eyebrow">SCENARIO BUILDER</span>
          <h1>Custom Locations</h1>
          <p>
            Click the map to place a depot and customer locations anywhere in
            the world. The optimizer will download real road data automatically.
          </p>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <span>!</span>
          {error}
          <button onClick={() => setError("")}>×</button>
        </div>
      )}

      <div className="builder-layout">
        {/* MAP */}
        <div className="builder-map-wrapper">
          <div className="builder-search-overlay">
            <SearchBox onSelect={handleSearch} />
          </div>

          <div className="builder-map-hint">
            {!hasDepot
              ? "Click the map to place your depot"
              : "Click to add customer locations"}
          </div>

          <MapContainer
            center={DEFAULT_CENTER}
            zoom={5}
            scrollWheelZoom={true}
            className="builder-map"
          >
            <TileLayer
              attribution="&copy; OpenStreetMap contributors &copy; CartoDB"
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />

            <MapClickHandler onMapClick={handleMapClick} />

            {flyTarget && (
              <FlyTo center={flyTarget.center} zoom={flyTarget.zoom} />
            )}

            {locations.length > 0 && <FitBounds locations={locations} />}

            {locations.map((loc) => (
              <LocationMarker
                key={loc.id}
                location={{
                  ...loc,
                  displayIndex: customerIndices[loc.id],
                }}
                onDragEnd={handleDragEnd}
                onRemove={handleRemove}
              />
            ))}

            {routeGeometry && (
              <GeoJSON
                key={result?.run_id || "route"}
                data={{
                  type: "FeatureCollection",
                  features: routeGeometry.features || [],
                }}
                style={(feature) => ({
                  color:
                    VEHICLE_COLOURS[
                      ((feature?.properties?.vehicle_index || 1) - 1) %
                        VEHICLE_COLOURS.length
                    ],
                  weight: 5,
                  opacity: 0.85,
                })}
              />
            )}
          </MapContainer>
        </div>

        {/* CONFIG PANEL */}
        <div className="builder-panel">
          {/* LOCATIONS */}
          <div className="builder-section">
            <div className="builder-section-header">
              <span className="micro-label">LOCATIONS</span>
              <div className="flex gap-2">
                {permanentDepots.length > 0 && !hasDepot && (
                  <select 
                    className="text-xs bg-black/20 border border-border/20 rounded px-1"
                    onChange={(e) => {
                      const d = permanentDepots.find(x => x.id.toString() === e.target.value);
                      if (d) loadDepot(d);
                      e.target.value = "";
                    }}
                    defaultValue=""
                  >
                    <option value="" disabled>Load Depot...</option>
                    {permanentDepots.map(d => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                )}
                <span className="builder-count">
                  {locations.length} placed
                </span>
              </div>
            </div>

            {locations.length === 0 ? (
              <div className="builder-empty-hint">
                Click the map to start placing locations
              </div>
            ) : (
              <div className="location-list">
                {locations.map((loc) => {
                  const isDepot = loc.type === "depot";
                  return (
                    <div
                      key={loc.id}
                      className={`location-item ${isDepot ? "depot" : ""}`}
                    >
                      <div className="location-item-header">
                        <span
                          className={`location-type-badge ${
                            isDepot ? "depot-badge" : "customer-badge"
                          }`}
                        >
                          {isDepot ? "D" : `C${customerIndices[loc.id] ?? ""}`}
                        </span>

                        <input
                          className="location-name-input"
                          value={loc.name}
                          placeholder={
                            isDepot
                              ? "Depot name"
                              : `Customer ${customerIndices[loc.id] ?? ""}`
                          }
                          onChange={(e) =>
                            updateLocation(loc.id, "name", e.target.value)
                          }
                        />

                        <div className="flex gap-1 ml-auto">
                          {isDepot && (
                            <button
                              className="text-xs text-primary hover:underline px-1"
                              onClick={() => saveDepot(loc)}
                              title="Save as permanent depot"
                            >
                              Save
                            </button>
                          )}
                          <button
                            className="location-remove-btn"
                            onClick={() => handleRemove(loc.id)}
                            title="Remove location"
                          >
                            ×
                          </button>
                        </div>
                      </div>

                      <div className="location-item-details">
                        <span className="location-coords">
                          {loc.latitude.toFixed(4)}, {loc.longitude.toFixed(4)}
                        </span>

                        {!isDepot && (
                          <div className="location-demand">
                            <label>Demand</label>
                            <input
                              type="number"
                              min="1"
                              max="100"
                              value={loc.demand}
                              onChange={(e) =>
                                updateLocation(
                                  loc.id,
                                  "demand",
                                  Math.max(
                                    1,
                                    parseInt(e.target.value) || 1
                                  )
                                )
                              }
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* VEHICLES */}
          <div className="builder-section">
            <div className="builder-section-header">
              <span className="micro-label">FLEET</span>
              <button className="builder-add-btn" onClick={addVehicle}>
                + Vehicle
              </button>
            </div>

            <div className="vehicle-list">
              {vehicles.map((v, i) => (
                <div key={v.id} className="vehicle-item">
                  <span className="vehicle-label">Vehicle {i + 1}</span>
                  <div className="vehicle-capacity">
                    <label>Cap.</label>
                    <input
                      type="number"
                      min="1"
                      max="1000"
                      value={v.capacity}
                      onChange={(e) =>
                        updateVehicleCapacity(v.id, e.target.value)
                      }
                    />
                  </div>
                  {vehicles.length > 1 && (
                    <button
                      className="vehicle-remove-btn"
                      onClick={() => removeVehicle(v.id)}
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* ALGORITHM + RUN */}
          <div className="builder-section">
            <div className="builder-section-header">
              <span className="micro-label">ALGORITHM</span>
            </div>

            <select
              className="dark-select"
              value={algorithm}
              onChange={(e) => setAlgorithm(e.target.value)}
            >
              {ALGORITHMS.map(([val, label]) => (
                <option key={val} value={val}>
                  {label}
                </option>
              ))}
            </select>

            <button
              className="primary-button full-width"
              onClick={runOptimization}
              disabled={loading || !hasDepot || customers.length === 0}
              style={{ marginTop: 12 }}
            >
              {loading ? "Optimizing…" : "Optimize Routes"}
              <span className="button-arrow">→</span>
            </button>
          </div>

          {/* IMPORT / EXPORT / CLEAR */}
          <div className="builder-section">
            <div className="builder-section-header">
              <span className="micro-label">DATA</span>
            </div>
            <div className="builder-actions-row">
              <button className="secondary-button" onClick={exportJSON}>
                Export JSON
              </button>
              <button
                className="secondary-button"
                onClick={() => fileInputRef.current?.click()}
              >
                Import JSON
              </button>
              <button
                className="secondary-button danger-outline"
                onClick={clearAll}
              >
                Clear All
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".json"
                style={{ display: "none" }}
                onChange={importJSON}
              />
            </div>
          </div>

          {/* RESULT SUMMARY */}
          {result && (
            <div className="builder-section builder-result">
              <div className="builder-section-header">
                <span className="micro-label">RESULT</span>
                <span
                  className={
                    result.feasible
                      ? "status-badge success"
                      : "status-badge danger"
                  }
                >
                  {result.feasible ? "✓ FEASIBLE" : "✕ INFEASIBLE"}
                </span>
              </div>

              <div className="builder-result-grid">
                <div>
                  <span>FITNESS</span>
                  <strong>
                    {result.fitness != null
                      ? Number(result.fitness).toFixed(2)
                      : "—"}
                  </strong>
                </div>
                <div>
                  <span>DISTANCE</span>
                  <strong>
                    {result.distance != null
                      ? Number(result.distance).toFixed(1) + " m"
                      : "—"}
                  </strong>
                </div>
                <div>
                  <span>TRAVEL TIME</span>
                  <strong>
                    {result.travel_time != null
                      ? Number(result.travel_time).toFixed(1) + " s"
                      : "—"}
                  </strong>
                </div>
                <div>
                  <span>VEHICLES</span>
                  <strong>{result.vehicles_used ?? "—"}</strong>
                </div>
              </div>

              {result.routes && (
                <div className="builder-routes">
                  {result.routes.map((route, i) => (
                    <div key={i} className="builder-route-row">
                      <span
                        className="builder-route-dot"
                        style={{
                          background:
                            VEHICLE_COLOURS[i % VEHICLE_COLOURS.length],
                        }}
                      />
                      <span className="builder-route-label">
                        V{i + 1}
                      </span>
                      <span className="builder-route-stops">
                        {route.join(" → ")}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ScenarioBuilder;
