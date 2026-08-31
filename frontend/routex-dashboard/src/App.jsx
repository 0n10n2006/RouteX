import { useState } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import "./App.css";

function App() {
  const [algorithm, setAlgorithm] = useState("qpso");
  const [scenario, setScenario] = useState("medium");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runOptimization = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/optimize",
        {
          algorithm,
          scenario,
          seed: 42,
        }
      );

      setResult(response.data);
    } catch (err) {
      console.error(err);
      setError(
        "Could not connect to RouteX backend. Make sure FastAPI is running."
      );
    } finally {
      setLoading(false);
    }
  };

  // Convert backend convergence array into data Recharts understands.
  const convergenceData =
    result?.convergence?.map((value, index) => ({
      iteration: index + 1,
      fitness: value,
    })) || [];

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="logo-mark">RX</div>

          <div>
            <h1>RouteX</h1>
            <p>
              Quantum-Inspired Intelligent Traffic Route Optimization
            </p>
          </div>
        </div>
      </header>

      <main className="container">

        {/* CONTROLS */}
        <section className="controls">

          <div className="control">
            <label>Algorithm</label>

            <select
              value={algorithm}
              onChange={(e) => setAlgorithm(e.target.value)}
            >
              <option value="greedy">Greedy</option>
              <option value="qpso">QPSO</option>
              <option value="hybrid">Hybrid QPSO</option>
            </select>
          </div>

          <div className="control">
            <label>Traffic Scenario</label>

            <select
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
            >
              <option value="low">Low Traffic</option>
              <option value="medium">Medium Traffic</option>
              <option value="high">High Traffic</option>
              <option value="big">Large Scenario</option>
            </select>
          </div>

          <button
            className="optimize-button"
            onClick={runOptimization}
            disabled={loading}
          >
            {loading ? "Optimizing..." : "Run Optimization"}
          </button>

        </section>

        {/* ERROR */}
        {error && <div className="error">{error}</div>}

        {/* RESULTS */}
        {result && (
          <section className="results">

            <div className="section-title">
              <div>
                <h2>Optimization Result</h2>
                <p>
                  {result.algorithm} · {result.scenario}
                </p>
              </div>

              <div className="status">
                {result.feasible ? "✓ Feasible" : "✗ Infeasible"}
              </div>
            </div>

            {/* KPI CARDS */}
            <div className="cards">

              <div className="card">
                <span>Fitness</span>
                <strong>{result.fitness}</strong>
              </div>

              <div className="card">
                <span>Total Distance</span>
                <strong>{result.distance}</strong>
              </div>

              <div className="card">
                <span>Runtime</span>
                <strong>
                  {Number(result.runtime).toFixed(4)} s
                </strong>
              </div>

              <div className="card">
                <span>Vehicles Used</span>
                <strong>{result.vehicles_used}</strong>
              </div>

            </div>

            {/* ROUTE */}
            <div className="route-box">
              <div className="box-heading">
                <h3>Optimized Routes</h3>
                <span>
                  {result.routes?.length || 0} vehicle(s)
                </span>
              </div>

              {result.routes?.map((route, index) => (
                <div className="route-row" key={index}>
                  <div className="vehicle">
                    V{index + 1}
                  </div>

                  <div className="route-path">
                    {route.map((node, nodeIndex) => (
                      <span key={nodeIndex}>
                        <span className="node">
                          {node}
                        </span>

                        {nodeIndex < route.length - 1 && (
                          <span className="arrow">→</span>
                        )}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* CONVERGENCE GRAPH */}
            <div className="chart-box">

              <div className="box-heading">
                <div>
                  <h3>Convergence Analysis</h3>
                  <p>
                    Fitness progression across optimization iterations
                  </p>
                </div>

                <span>
                  {result.iterations} iterations
                </span>
              </div>

              <div className="chart">
                <ResponsiveContainer width="100%" height={350}>
                  <LineChart
                    data={convergenceData}
                    margin={{
                      top: 20,
                      right: 25,
                      left: 10,
                      bottom: 10,
                    }}
                  >
                    <CartesianGrid
                      stroke="#263454"
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="iteration"
                      stroke="#8292b5"
                      label={{
                        value: "Iteration",
                        position: "insideBottom",
                        offset: -5,
                        fill: "#8292b5",
                      }}
                    />

                    <YAxis
                      stroke="#8292b5"
                      label={{
                        value: "Fitness",
                        angle: -90,
                        position: "insideLeft",
                        fill: "#8292b5",
                      }}
                    />

                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#10182d",
                        border: "1px solid #304064",
                        borderRadius: "8px",
                        color: "#fff",
                      }}
                    />

                    <Line
                      type="monotone"
                      dataKey="fitness"
                      stroke="#35d0ff"
                      strokeWidth={3}
                      dot={{
                        r: 4,
                        fill: "#35d0ff",
                      }}
                      activeDot={{
                        r: 6,
                      }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

            </div>

          </section>
        )}

      </main>
    </div>
  );
}

export default App;