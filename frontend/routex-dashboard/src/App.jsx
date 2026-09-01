import { useEffect, useState } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [algorithm, setAlgorithm] = useState("qpso");
  const [scenario, setScenario] = useState("medium");

  const [result, setResult] = useState(null);
  const [comparison, setComparison] = useState([]);

  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const [benchmarkResult, setBenchmarkResult] = useState(null);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);

  const [loading, setLoading] = useState(false);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [error, setError] = useState("");

  const loadComparison = async () => {
    setComparisonLoading(true);

    try {
      const response = await axios.get(
        `${API_URL}/results/comparison`
      );

      setComparison(response.data.comparison || []);
    } catch (err) {
      console.error(err);
      setError("Could not load algorithm comparison.");
    } finally {
      setComparisonLoading(false);
    }
  };

  const loadHistory = async () => {
  setHistoryLoading(true);

  try {
    const response = await axios.get(
      `${API_URL}/results?limit=10`
    );

    setHistory(response.data.results || []);
  } catch (err) {
    console.error(err);
    setError("Could not load optimization history.");
  } finally {
    setHistoryLoading(false);
  }
};

  useEffect(() => {
  loadComparison();
  loadHistory();
}, []);

const runOptimization = async () => {

  setLoading(true);

  setError("");

  setResult(null);

  try {

    const response = await axios.post(
      `${API_URL}/optimize`,
      {
        algorithm,
        scenario,
        seed: 42,
      }
    );

    setResult(response.data);

    // Refresh comparison after every optimization.
    await loadComparison();

    // Refresh results history after every optimization.
    await loadHistory();

  } catch (err) {

    console.error(err);

    setError(
      "Could not connect to RouteX backend. Make sure FastAPI is running."
    );

  } finally {

    setLoading(false);

  }

};

const runBenchmark = async () => {
  setBenchmarkLoading(true);
  setError("");
  setBenchmarkResult(null);

  try {
    const response = await axios.post(
      `${API_URL}/benchmark`,
      {
        seeds: 1,
        scenarios: [scenario],
        algorithms: ["greedy", "qpso", "hybrid"],
      }
    );

    setBenchmarkResult(response.data);

    // Refresh the existing dashboard sections.
    await loadComparison();
    await loadHistory();

  } catch (err) {
    console.error(err);

    setError(
      "Could not run algorithm comparison. Make sure FastAPI is running."
    );

  } finally {
    setBenchmarkLoading(false);
  }
};

const loadHistoricalResult = async (runId) => {
  try {
    setLoading(true);
    setError("");

    const response = await axios.get(
      `${API_URL}/results/${runId}`
    );

    setResult(response.data);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });

  } catch (err) {
    console.error(err);

    setError(
      "Could not load the selected optimization result."
    );

  } finally {
    setLoading(false);
  }
};
  const convergenceData =
    result?.convergence?.map((value, index) => ({
      iteration: index + 1,
      fitness: value,
    })) || [];

  // Only show comparison for the selected scenario.
  const scenarioComparison = comparison.filter(
    (item) => item.scenario === scenario
  );

  // Find the lowest fitness.
  const bestFitness =
    scenarioComparison.length > 0
      ? Math.min(
          ...scenarioComparison.map((item) => item.best_fitness)
        )
      : null;

  return (
    <div className="app">

      <header className="header">
        <div className="header-content">

          <div className="logo-mark">
            RX
          </div>

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
              <option value="greedy">
                Greedy
              </option>

              <option value="qpso">
                QPSO
              </option>

              <option value="hybrid">
                Hybrid QPSO
              </option>

            </select>

          </div>


          <div className="control">

            <label>Traffic Scenario</label>

            <select
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
            >

              <option value="low">
                Low Traffic
              </option>

              <option value="medium">
                Medium Traffic
              </option>

              <option value="high">
                High Traffic
              </option>

              <option value="big">
                Large Scenario
              </option>

            </select>

          </div>


          <button
            className="optimize-button"
            onClick={runOptimization}
            disabled={loading}
          >
            {loading
              ? "Optimizing..."
              : "Run Optimization"}
          </button>

          <button
            className="benchmark-button"
            onClick={runBenchmark}
            disabled={benchmarkLoading || loading}
          >
            {benchmarkLoading
              ? "Comparing Algorithms..."
              : "Compare All Algorithms"}
          </button>

        </section>


        {/* ERROR */}

        {error && (
          <div className="error">
            {error}
          </div>
        )}


        {/* OPTIMIZATION RESULT */}

        {result && (

          <section className="results">

            <div className="section-title">

              <div>

                <h2>
                  Optimization Result
                </h2>

                <p>
                  {result.algorithm} · {result.scenario}
                </p>

              </div>


              <div className="status">

                {result.feasible
                  ? "✓ Feasible"
                  : "✗ Infeasible"}

              </div>

            </div>


            {/* KPI CARDS */}

            <div className="cards">

              <div className="card">

                <span>Fitness</span>

                <strong>
                  {result.fitness}
                </strong>

              </div>


              <div className="card">

                <span>Total Distance</span>

                <strong>
                  {result.distance}
                </strong>

              </div>


              <div className="card">

                <span>Runtime</span>

                <strong>
                  {Number(result.runtime).toFixed(4)} s
                </strong>

              </div>


              <div className="card">

                <span>Vehicles Used</span>

                <strong>
                  {result.vehicles_used}
                </strong>

              </div>

            </div>


            {/* ROUTE */}
<div className="route-box">

  <div className="box-heading">
    <div>
      <h3>Optimized Route</h3>
      <p>Vehicle routing generated by the selected algorithm</p>
    </div>

    <span>
      {result.routes?.length || 0} vehicle(s)
    </span>
  </div>

  {result.routes?.map((route, index) => (
    <div className="visual-route" key={index}>

      <div className="vehicle-label">
        Vehicle {index + 1}
      </div>

      <div className="route-track">

        {route.map((node, nodeIndex) => (
          <div className="route-step" key={nodeIndex}>

            <div
              className={
                nodeIndex === 0 || nodeIndex === route.length - 1
                  ? "route-node depot"
                  : "route-node"
              }
            >
              {node}
            </div>

            {nodeIndex < route.length - 1 && (
              <div className="route-arrow">
                →
              </div>
            )}

          </div>
        ))}

      </div>

      <div className="route-summary">
        {route.length - 2} customer stop(s)
      </div>

    </div>
  ))}

</div>


            {/* CONVERGENCE */}

            <div className="chart-box">

              <div className="box-heading">

                <div>

                  <h3>
                    Convergence Analysis
                  </h3>

                  <p>
                    Fitness progression across optimization iterations
                  </p>

                </div>


                <span>

                  {result.iterations} iterations

                </span>

              </div>


              <div className="chart">

                <ResponsiveContainer
                  width="100%"
                  height={350}
                >

                  <LineChart
                    data={convergenceData}
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="iteration"
                    />

                    <YAxis />

                    <Tooltip />


                    <Line
                      type="monotone"
                      dataKey="fitness"
                      strokeWidth={3}
                    />

                  </LineChart>

                </ResponsiveContainer>

              </div>

            </div>

          </section>

        )}


        {/* ALGORITHM COMPARISON */}

        <section className="comparison-section">

          <div className="comparison-header">

            <div>

              <h2>
                Algorithm Comparison
              </h2>

              <p>
                Performance comparison for the selected traffic scenario
              </p>

            </div>


            <button
              className="refresh-button"
              onClick={loadComparison}
              disabled={comparisonLoading}
            >

              {comparisonLoading
                ? "Loading..."
                : "Refresh"}

            </button>

          </div>


          {scenarioComparison.length === 0 ? (

            <div className="empty-comparison">

              No comparison data available for this scenario.

              <br />

              Run multiple algorithms to generate comparison results.

            </div>

          ) : (

            <>

              {/* TABLE */}

              <div className="comparison-table-wrapper">

                <table className="comparison-table">

                  <thead>

                    <tr>

                      <th>
                        Algorithm
                      </th>

                      <th>
                        Best Fitness
                      </th>

                      <th>
                        Best Runtime
                      </th>

                      <th>
                        Runs
                      </th>

                      <th>
                        Status
                      </th>

                    </tr>

                  </thead>


                  <tbody>

                    {scenarioComparison.map((item, index) => (

                      <tr key={index}>

                        <td>

                          {item.algorithm}

                        </td>


                        <td>

                          {item.best_fitness}

                        </td>


                        <td>

                          {Number(
                            item.best_runtime
                          ).toFixed(6)} s

                        </td>


                        <td>

                          {item.runs}

                        </td>


                        <td>

                          {item.best_fitness === bestFitness
                            ? "🏆 Best"
                            : "-"}

                        </td>

                      </tr>

                    ))}

                  </tbody>

                </table>

              </div>


              {/* FITNESS BAR CHART */}

              <div className="comparison-chart">

                <h3>
                  Fitness Comparison
                </h3>


                <ResponsiveContainer
                  width="100%"
                  height={350}
                >

                  <BarChart
                    data={scenarioComparison}
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="algorithm"
                    />

                    <YAxis />

                    <Tooltip />

                    <Bar
                      dataKey="best_fitness"
                    />

                  </BarChart>

                </ResponsiveContainer>

              </div>


              {/* RUNTIME BAR CHART */}

              <div className="comparison-chart">

                <h3>
                  Runtime Comparison
                </h3>


                <ResponsiveContainer
                  width="100%"
                  height={350}
                >

                  <BarChart
                    data={scenarioComparison}
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="algorithm"
                    />

                    <YAxis />

                    <Tooltip />

                    <Bar
                      dataKey="best_runtime"
                    />

                  </BarChart>

                </ResponsiveContainer>

              </div>

            </>

          )}

        </section>
{/* BENCHMARK COMPARISON */}

{benchmarkResult && (
  <section className="benchmark-section">

    <div className="section-title">
      <div>
        <h2>Algorithm Comparison</h2>
        <p>
          {scenario} traffic scenario
        </p>
      </div>

      <div className="status">
        {benchmarkResult.total_runs} runs
      </div>
    </div>

    <div className="benchmark-table">

      <div className="benchmark-row benchmark-header">
        <span>Algorithm</span>
        <span>Best Fitness</span>
        <span>Mean Fitness</span>
        <span>Mean Runtime</span>
        <span>Improvement</span>
      </div>

      {benchmarkResult.summary?.map((item) => (
        <div
          className="benchmark-row"
          key={`${item.scenario}-${item.algorithm}`}
        >
          <strong>
            {item.algorithm}
          </strong>

          <span>
            {item.best_fitness}
          </span>

          <span>
            {item.mean_fitness}
          </span>

          <span>
            {item.mean_runtime}s
          </span>

          <span className="improvement">
            {item.improvement_vs_baseline_percent !== null
              ? `${item.improvement_vs_baseline_percent}%`
              : "Baseline"}
          </span>
        </div>
      ))}

    </div>

  </section>
)}

{/* RESULTS HISTORY */}
{/* RESULTS HISTORY */}

<section className="history-section">

  <div className="history-header">

    <div>
      <h2>Recent Optimization Runs</h2>

      <p>
        Previously saved optimization results
      </p>
    </div>

    <button
      className="refresh-button"
      onClick={loadHistory}
      disabled={historyLoading}
    >
      {historyLoading
        ? "Loading..."
        : "Refresh History"}
    </button>

  </div>

  {history.length === 0 ? (

    <div className="empty-comparison">
      No optimization history available yet.
    </div>

  ) : (

    <div className="history-list">

      {history.map((item) => (

        <button
          key={item.id}
          className="history-item"
          onClick={() => loadHistoricalResult(item.id)}
        >

          {/* RUN + ALGORITHM */}

          <div className="history-main">

            <div className="history-run">
              Run #{item.id}
            </div>

            <div className="history-algorithm">
              {item.algorithm}
            </div>

          </div>

          {/* DETAILS */}

          <div className="history-details">

            <div className="history-stat">
              <span>Scenario</span>
              <strong>
                {item.scenario}
              </strong>
            </div>

            <div className="history-stat">
              <span>Fitness</span>
              <strong>
                {item.fitness}
              </strong>
            </div>

            <div className="history-stat">
              <span>Runtime</span>
              <strong>
                {item.runtime !== null
                  ? `${Number(item.runtime).toFixed(4)} s`
                  : "N/A"}
              </strong>
            </div>

          </div>

          {/* ACTION */}

          <div className="history-action">
            View →
          </div>

        </button>

      ))}

    </div>

  )}

</section>
      </main>

    </div>
  );
}

export default App;
