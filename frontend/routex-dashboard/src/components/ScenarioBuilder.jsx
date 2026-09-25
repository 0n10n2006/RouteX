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
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
} from "recharts";
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

const ALGO_COLORS = {
  greedy: "#6b7280",
  ga: "#f59e0b",
  pso: "#3b82f6",
  qpso: "#8b5cf6",
  hybrid: "#10b981",
};

const ALGO_SHORT = {
  "Greedy (classical baseline)": "Greedy",
  GA: "GA",
  PSO: "PSO",
  QPSO: "QPSO",
  "Hybrid QPSO + 2-opt": "Hybrid",
};

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
  const [useLiveTraffic, setUseLiveTraffic] = useState(false);
  const [loading, setLoading] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);
  const [error, setError] = useState("");
  const [flyTarget, setFlyTarget] = useState(null);
  const [routeGeometry, setRouteGeometry] = useState(null);
  const [result, setResult] = useState(null);
  const fileInputRef = useRef(null);
  const nextVehicleId = useRef(3);

  const [permanentDepots, setPermanentDepots] = useState([]);
  const [forceDepotMode, setForceDepotMode] = useState(false);
  const [savedDepotId, setSavedDepotId] = useState(null);

  // Compare-all state
  const [compareResults, setCompareResults] = useState(null);
  const [selectedAlgo, setSelectedAlgo] = useState("");

  const depots = locations.filter((l) => l.type === "depot");
  const activeDepot = depots.find((l) => l.active) || depots[0] || null;
  const hasDepot = depots.length > 0;
  const customers = locations.filter((l) => l.type === "customer");

  // Load permanent depots on mount
  useEffect(() => {
    const fetchDepots = async () => {
      try {
        const res = await axios.get(`${API_URL}/depots`);
        setPermanentDepots(res.data.depots);
      } catch {
        // Not logged in, or the depots endpoint isn't reachable yet --
        // either way, the builder still works without saved depots.
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
      setSavedDepotId(loc.id);
      setTimeout(() => {
        setSavedDepotId((id) => (id === loc.id ? null : id));
      }, 2000);
    } catch {
      setError("Failed to save depot. Are you logged in?");
    }
  };

  // Loads a saved depot onto the map as a new depot candidate (it does not
  // replace any depot already placed) and makes it the active one.
  const loadDepot = (depot) => {
    setLocations((prev) => {
      const deactivated = prev.map((l) =>
        l.type === "depot" ? { ...l, active: false } : l
      );
      return [
        ...deactivated,
        {
          id: nextId++,
          name: depot.name,
          latitude: depot.latitude,
          longitude: depot.longitude,
          type: "depot",
          demand: 0,
          active: true,
        },
      ];
    });
    setFlyTarget({ center: [depot.latitude, depot.longitude], zoom: 15 });
  };

  // Marks a single depot as the one used for the next optimization run.
  const setActiveDepot = useCallback((id) => {
    setLocations((prev) =>
      prev.map((l) =>
        l.type === "depot" ? { ...l, active: l.id === id } : l
      )
    );
    setRouteGeometry(null);
    setResult(null);
    setCompareResults(null);
  }, []);

  const handleMapClick = useCallback(
    (latlng) => {
      const placingDepot = !hasDepot || forceDepotMode;
      const type = placingDepot ? "depot" : "customer";
      const id = nextId++;

      setLocations((prev) => {
        const isFirstDepot =
          type === "depot" && !prev.some((l) => l.type === "depot");

        return [
          ...prev,
          {
            id,
            name: type === "depot" ? "Depot" : "",
            latitude: latlng.lat,
            longitude: latlng.lng,
            type,
            demand: type === "customer" ? 2 : 0,
            active: type === "depot" ? isFirstDepot : undefined,
          },
        ];
      });

      if (type === "depot") setForceDepotMode(false);
      setRouteGeometry(null);
      setResult(null);
      setCompareResults(null);
    },
    [hasDepot, forceDepotMode]
  );

  const handleDragEnd = useCallback((id, lat, lng) => {
    setLocations((prev) =>
      prev.map((l) =>
        l.id === id ? { ...l, latitude: lat, longitude: lng } : l
      )
    );
    setRouteGeometry(null);
    setResult(null);
    setCompareResults(null);
  }, []);

  const handleRemove = useCallback((id) => {
    setLocations((prev) => {
      const removed = prev.find((l) => l.id === id);
      let next = prev.filter((l) => l.id !== id);

      // If the active depot was removed, promote the next remaining
      // depot (if any) so there's always an active depot to run with.
      if (removed?.type === "depot" && removed.active) {
        const promotedId = next.find((l) => l.type === "depot")?.id;
        if (promotedId != null) {
          next = next.map((l) =>
            l.id === promotedId ? { ...l, active: true } : l
          );
        }
      }

      return next;
    });
    setRouteGeometry(null);
    setResult(null);
    setCompareResults(null);
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
    setCompareResults(null);
    setSelectedAlgo("");
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
          let importedLocations = data.locations;

          // Older exports (or hand-written files) may not have an
          // `active` flag on their depots -- make sure exactly one
          // depot ends up active so optimization can run immediately.
          const importedDepots = importedLocations.filter(
            (l) => l.type === "depot"
          );
          if (
            importedDepots.length > 0 &&
            !importedDepots.some((d) => d.active)
          ) {
            let promoted = false;
            importedLocations = importedLocations.map((l) => {
              if (l.type === "depot" && !promoted) {
                promoted = true;
                return { ...l, active: true };
              }
              return l;
            });
          }

          setLocations(importedLocations);
          nextId =
            Math.max(...importedLocations.map((l) => l.id), nextId) + 1;
        }
        if (data.vehicles && Array.isArray(data.vehicles)) {
          setVehicles(data.vehicles);
          nextVehicleId.current =
            Math.max(...data.vehicles.map((v) => v.id), 0) + 1;
        }
        setRouteGeometry(null);
        setResult(null);
        setCompareResults(null);
        setError("");
      } catch {
        setError("Invalid JSON file.");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  const buildPayloadLocations = () => {
    const runLocations = [activeDepot, ...customers];
    return runLocations.map((l) => ({
      id: l.id,
      name: l.name,
      latitude: l.latitude,
      longitude: l.longitude,
      type: l.type,
      demand: l.demand || 1,
    }));
  };

  const runOptimization = async () => {
    if (!activeDepot || customers.length === 0 || vehicles.length === 0) {
      setError(
        "Place at least 1 active depot and 1 customer, and add at least 1 vehicle."
      );
      return;
    }

    setLoading(true);
    setError("");
    setRouteGeometry(null);
    setResult(null);
    setCompareResults(null);

    try {
      const res = await axios.post(`${API_URL}/optimize/custom`, {
        locations: buildPayloadLocations(),
        vehicles: vehicles.map((v) => ({ id: v.id, capacity: v.capacity })),
        algorithm,
        seed: 42,
        use_live_traffic: useLiveTraffic,
      });

      const optimizationResult = res.data;
      setResult(optimizationResult);

      if (optimizationResult.geometry) {
        setRouteGeometry(optimizationResult.geometry);
      } else if (optimizationResult.routes) {
        const runLocations = [activeDepot, ...customers];
        const locMap = {};
        runLocations.forEach((l, idx) => {
          locMap[idx] = [l.longitude, l.latitude];
        });
        const features = (optimizationResult.routes || [])
          .filter((r) => Array.isArray(r) && r.length >= 2)
          .map((route, vIdx) => ({
            type: "Feature",
            properties: { vehicle_index: vIdx + 1, route },
            geometry: {
              type: "LineString",
              coordinates: route.map((id) => locMap[id]).filter(Boolean),
            },
          }))
          .filter((f) => f.geometry.coordinates.length >= 2);

        if (features.length > 0) {
          setRouteGeometry({ type: "FeatureCollection", features });
        }
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

  // Run ALL algorithms
  const runCompareAll = async () => {
    if (!activeDepot || customers.length === 0 || vehicles.length === 0) {
      setError(
        "Place at least 1 active depot and 1 customer, and add at least 1 vehicle."
      );
      return;
    }

    setCompareLoading(true);
    setError("");
    setRouteGeometry(null);
    setResult(null);
    setCompareResults(null);
    setSelectedAlgo("");

    try {
      const res = await axios.post(`${API_URL}/optimize/custom/compare`, {
        locations: buildPayloadLocations(),
        vehicles: vehicles.map((v) => ({ id: v.id, capacity: v.capacity })),
        seed: 42,
        use_live_traffic: useLiveTraffic,
      });

      const results = res.data;
      setCompareResults(results);

      // Default to best algorithm's route on map
      if (results.length > 0) {
        const best = results.reduce((a, b) =>
          (a.fitness ?? Infinity) < (b.fitness ?? Infinity) ? a : b
        );
        setSelectedAlgo(best.algorithm);
        if (best.geometry) setRouteGeometry(best.geometry);
        setResult(best);
      }

      if (onResult && results.length > 0) onResult(results[0]);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Comparison failed. Check that the backend is running."
      );
    } finally {
      setCompareLoading(false);
    }
  };

  // Switch displayed algorithm route on map
  const handleAlgoSwitch = (algoName) => {
    setSelectedAlgo(algoName);
    const r = compareResults?.find((r) => r.algorithm === algoName);
    if (r) {
      setResult(r);
      if (r.geometry) setRouteGeometry(r.geometry);
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

  // Build comparison chart data
  const comparisonChartData = useMemo(() => {
    if (!compareResults) return [];
    return compareResults.map((r) => ({
      algorithm: ALGO_SHORT[r.algorithm] || r.algorithm,
      fitness: r.fitness != null ? Number(r.fitness) : 0,
      distance: r.distance != null ? Number(r.distance) : 0,
      runtime: r.runtime != null ? Number((r.runtime * 1000).toFixed(1)) : 0,
      fullName: r.algorithm,
    }));
  }, [compareResults]);

  // Build convergence chart data (QPSO & Hybrid only)
  const convergenceData = useMemo(() => {
    if (!compareResults) return [];
    const qpsoResult = compareResults.find((r) =>
      r.algorithm === "QPSO"
    );
    const hybridResult = compareResults.find((r) =>
      r.algorithm === "Hybrid QPSO + 2-opt"
    );

    const qpsoConv = qpsoResult?.convergence || [];
    const hybridConv = hybridResult?.convergence || [];
    const maxLen = Math.max(qpsoConv.length, hybridConv.length);

    if (maxLen === 0) return [];

    const data = [];
    for (let i = 0; i < maxLen; i++) {
      const point = { iteration: i + 1 };
      if (i < qpsoConv.length && qpsoConv[i] != null)
        point.QPSO = Number(qpsoConv[i]);
      if (i < hybridConv.length && hybridConv[i] != null)
        point["Hybrid QPSO"] = Number(hybridConv[i]);
      data.push(point);
    }
    return data;
  }, [compareResults]);

  const isAnyLoading = loading || compareLoading;

  return (
    <div className="view">
      <div className="page-header">
        <div>
          <span className="page-eyebrow">SCENARIO BUILDER</span>
          <h1>Custom Locations</h1>
          <p>
            Click the map to place a depot and customer locations anywhere in
            the world. You can place multiple depots and choose which one is
            active for each run — the optimizer downloads real road data
            automatically.
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
            {forceDepotMode
              ? "Click the map to place another depot"
              : !hasDepot
              ? "Click the map to place your depot"
              : "Click to add customer locations"}
          </div>

          {/* Algorithm route switcher dropdown (when compare results exist) */}
          {compareResults && compareResults.length > 1 && (
            <div className="map-algo-switcher">
              <select
                value={selectedAlgo}
                onChange={(e) => handleAlgoSwitch(e.target.value)}
                className="dark-select"
              >
                {compareResults.map((r) => (
                  <option key={r.algorithm} value={r.algorithm}>
                    {ALGO_SHORT[r.algorithm] || r.algorithm} — Fitness:{" "}
                    {r.fitness != null ? Number(r.fitness).toFixed(1) : "—"}
                  </option>
                ))}
              </select>
            </div>
          )}

          <MapContainer
            center={DEFAULT_CENTER}
            zoom={5}
            scrollWheelZoom={true}
            className="builder-map dark-tiles"
          >
            <TileLayer
              attribution="&copy; OpenStreetMap contributors"
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
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
                key={`route-${result?.run_id || "custom"}-${result?.algorithm || ""}-${JSON.stringify(
                  (routeGeometry.features || []).map((f) => f.geometry?.coordinates?.length)
                )}`}
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
              <div className="flex gap-2 items-center">
                {permanentDepots.length > 0 && (
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
                <button
                  className="builder-add-btn"
                  onClick={() => setForceDepotMode(true)}
                  disabled={forceDepotMode}
                  title="Place another depot on the map"
                >
                  + Depot
                </button>
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
                  const isActiveDepot = isDepot && loc.active;
                  return (
                    <div
                      key={loc.id}
                      className={`location-item ${isDepot ? "depot" : ""} ${
                        isDepot && !isActiveDepot ? "depot-inactive" : ""
                      }`}
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

                        <div className="flex gap-1 ml-auto items-center">
                          {isDepot && depots.length > 1 && (
                            isActiveDepot ? (
                              <span className="status-badge success depot-active-badge">
                                ACTIVE
                              </span>
                            ) : (
                              <button
                                className="text-xs text-primary hover:underline px-1"
                                onClick={() => setActiveDepot(loc.id)}
                                title="Use this depot for the next run"
                              >
                                Set Active
                              </button>
                            )
                          )}
                          {isDepot && (
                            <button
                              className="text-xs text-primary hover:underline px-1"
                              onClick={() => saveDepot(loc)}
                              title="Save as permanent depot"
                            >
                              {savedDepotId === loc.id ? "Saved ✓" : "Save"}
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

            <div style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                id="liveTrafficToggle"
                checked={useLiveTraffic}
                onChange={(e) => setUseLiveTraffic(e.target.checked)}
              />
              <label htmlFor="liveTrafficToggle" style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                Use Live Traffic (TomTom)
              </label>
            </div>

            <button
              className="primary-button full-width"
              onClick={runOptimization}
              disabled={isAnyLoading || !activeDepot || customers.length === 0}
              style={{ marginTop: 12 }}
            >
              {loading ? "Optimizing…" : "Optimize Routes"}
              <span className="button-arrow">→</span>
            </button>

            <button
              className="compare-all-button full-width"
              onClick={runCompareAll}
              disabled={isAnyLoading || !activeDepot || customers.length === 0}
              style={{ marginTop: 8 }}
            >
              {compareLoading ? (
                <span className="compare-loading-text">
                  <span className="spinner-inline" />
                  Running All Algorithms…
                </span>
              ) : (
                <>
                  ⚡ Compare All Algorithms
                </>
              )}
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

          {/* RESULT SUMMARY (single algo) */}
          {result && !compareResults && (
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

          {/* COMPARE RESULTS TABLE */}
          {compareResults && (
            <div className="builder-section builder-result">
              <div className="builder-section-header">
                <span className="micro-label">COMPARISON RESULTS</span>
                <span className="builder-count">
                  {compareResults.length} algorithms
                </span>
              </div>

              <div className="compare-table-wrapper">
                <table className="compare-table">
                  <thead>
                    <tr>
                      <th>Algorithm</th>
                      <th>Fitness</th>
                      <th>Distance</th>
                      <th>Time (ms)</th>
                      <th>Vehicles</th>
                    </tr>
                  </thead>
                  <tbody>
                    {compareResults.map((r) => {
                      const isBest =
                        r.fitness != null &&
                        r.fitness ===
                          Math.min(
                            ...compareResults
                              .filter((x) => x.fitness != null)
                              .map((x) => x.fitness)
                          );
                      const isSelected = r.algorithm === selectedAlgo;
                      return (
                        <tr
                          key={r.algorithm}
                          className={`${isBest ? "best-row" : ""} ${
                            isSelected ? "selected-row" : ""
                          }`}
                          onClick={() => handleAlgoSwitch(r.algorithm)}
                          style={{ cursor: "pointer" }}
                        >
                          <td>
                            <span className="algo-dot" style={{
                              background: ALGO_COLORS[
                                Object.entries(ALGO_SHORT).find(
                                  ([k]) => k === r.algorithm
                                )?.[1]?.toLowerCase()
                              ] || "#8b5cf6",
                            }} />
                            {ALGO_SHORT[r.algorithm] || r.algorithm}
                            {isBest && <span className="best-badge">BEST</span>}
                          </td>
                          <td>{r.fitness != null ? Number(r.fitness).toFixed(2) : "—"}</td>
                          <td>{r.distance != null ? Number(r.distance).toFixed(1) : "—"}</td>
                          <td>{r.runtime != null ? (r.runtime * 1000).toFixed(1) : "—"}</td>
                          <td>{r.vehicles_used ?? "—"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Selected algorithm route detail */}
              {result && result.routes && (
                <div className="builder-routes" style={{ marginTop: 12 }}>
                  <div className="micro-label" style={{ marginBottom: 6 }}>
                    {ALGO_SHORT[result.algorithm] || result.algorithm} Routes
                  </div>
                  {result.routes.map((route, i) => (
                    <div key={i} className="builder-route-row">
                      <span
                        className="builder-route-dot"
                        style={{
                          background:
                            VEHICLE_COLOURS[i % VEHICLE_COLOURS.length],
                        }}
                      />
                      <span className="builder-route-label">V{i + 1}</span>
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

      {/* ──── CHARTS SECTION (below the builder) ──── */}
      {compareResults && compareResults.length > 0 && (
        <div className="compare-charts-section">
          {/* FITNESS COMPARISON BAR CHART */}
          <div className="compare-chart-card">
            <h3>Algorithm Fitness Comparison</h3>
            <p className="chart-subtitle">Lower fitness = better solution</p>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={comparisonChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis
                  dataKey="algorithm"
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                />
                <YAxis
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                  label={{
                    value: "Fitness Score",
                    angle: -90,
                    position: "insideLeft",
                    style: { fill: "#64748b", fontSize: 12 },
                  }}
                />
                <Tooltip
                  contentStyle={{
                    background: "rgba(15, 23, 42, 0.95)",
                    border: "1px solid rgba(139, 92, 246, 0.3)",
                    borderRadius: 8,
                    color: "#e2e8f0",
                  }}
                  formatter={(value) => [Number(value).toFixed(2), "Fitness"]}
                />
                <Bar
                  dataKey="fitness"
                  radius={[6, 6, 0, 0]}
                  fill="#8b5cf6"
                  fillOpacity={0.85}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* RUNTIME COMPARISON BAR CHART */}
          <div className="compare-chart-card">
            <h3>Algorithm Runtime Comparison</h3>
            <p className="chart-subtitle">Execution time in milliseconds</p>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={comparisonChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis
                  dataKey="algorithm"
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                />
                <YAxis
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                  label={{
                    value: "Runtime (ms)",
                    angle: -90,
                    position: "insideLeft",
                    style: { fill: "#64748b", fontSize: 12 },
                  }}
                />
                <Tooltip
                  contentStyle={{
                    background: "rgba(15, 23, 42, 0.95)",
                    border: "1px solid rgba(16, 185, 129, 0.3)",
                    borderRadius: 8,
                    color: "#e2e8f0",
                  }}
                  formatter={(value) => [Number(value).toFixed(1) + " ms", "Runtime"]}
                />
                <Bar
                  dataKey="runtime"
                  radius={[6, 6, 0, 0]}
                  fill="#10b981"
                  fillOpacity={0.85}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* CONVERGENCE CHART (QPSO & Hybrid QPSO) */}
          {convergenceData.length > 0 && (
            <div className="compare-chart-card convergence-chart-card">
              <h3>QPSO Convergence Analysis</h3>
              <p className="chart-subtitle">
                Fitness value over iterations — shows how each quantum-inspired
                algorithm converges to its solution
              </p>
              <ResponsiveContainer width="100%" height={360}>
                <LineChart
                  data={convergenceData}
                  margin={{ top: 20, right: 30, left: 20, bottom: 10 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(255,255,255,0.06)"
                  />
                  <XAxis
                    dataKey="iteration"
                    tick={{ fill: "#94a3b8", fontSize: 12 }}
                    axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                    label={{
                      value: "Iteration",
                      position: "insideBottom",
                      offset: -5,
                      style: { fill: "#64748b", fontSize: 12 },
                    }}
                  />
                  <YAxis
                    tick={{ fill: "#94a3b8", fontSize: 12 }}
                    axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                    domain={[
                      (dataMin) =>
                        Math.floor(
                          dataMin - Math.max(Math.abs(dataMin) * 0.05, 1)
                        ),
                      (dataMax) =>
                        Math.ceil(
                          dataMax + Math.max(Math.abs(dataMax) * 0.05, 1)
                        ),
                    ]}
                    label={{
                      value: "Fitness (lower = better)",
                      angle: -90,
                      position: "insideLeft",
                      style: { fill: "#64748b", fontSize: 12 },
                    }}
                    tickFormatter={(v) =>
                      v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v.toFixed(0)
                    }
                  />
                  <Tooltip
                    contentStyle={{
                      background: "rgba(15, 23, 42, 0.95)",
                      border: "1px solid rgba(139, 92, 246, 0.3)",
                      borderRadius: 8,
                      color: "#e2e8f0",
                    }}
                    formatter={(value, name) => [
                      Number(value).toFixed(2),
                      name,
                    ]}
                    labelFormatter={(label) => `Iteration ${label}`}
                  />
                  <Legend
                    wrapperStyle={{ color: "#94a3b8", fontSize: 13 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="QPSO"
                    stroke="#8b5cf6"
                    strokeWidth={2.5}
                    dot={false}
                    activeDot={{ r: 4, fill: "#8b5cf6" }}
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="Hybrid QPSO"
                    stroke="#10b981"
                    strokeWidth={2.5}
                    dot={false}
                    activeDot={{ r: 4, fill: "#10b981" }}
                    connectNulls
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ScenarioBuilder;
