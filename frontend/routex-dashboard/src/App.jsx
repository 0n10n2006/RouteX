import { useEffect, useMemo, useState } from "react";
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

  const [benchmarkResult, setBenchmarkResult] = useState(null);

  const [loading, setLoading] = useState(false);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);

  const [error, setError] = useState("");
  const [activeView, setActiveView] = useState("dashboard");

  const loadComparison = async () => {
    setComparisonLoading(true);

    try {
      const response = await axios.get(`${API_URL}/results/comparison`);
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
      const response = await axios.get(`${API_URL}/results?limit=10`);
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

    try {
      const response = await axios.post(`${API_URL}/optimize`, {
        algorithm,
        scenario,
        seed: 42,
      });

      setResult(response.data);
      setActiveView("optimization");

      await loadComparison();
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

    try {
      const response = await axios.post(`${API_URL}/benchmark`, {
        seeds: 1,
        scenarios: [scenario],
        algorithms: ["greedy", "qpso", "hybrid"],
      });

      setBenchmarkResult(response.data);
      setActiveView("comparison");

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

      const response = await axios.get(`${API_URL}/results/${runId}`);

      setResult(response.data);
      setActiveView("optimization");
    } catch (err) {
      console.error(err);
      setError("Could not load the selected optimization result.");
    } finally {
      setLoading(false);
    }
  };

  const convergenceData = useMemo(
    () =>
      result?.convergence?.map((value, index) => ({
        iteration: index + 1,
        fitness: value,
      })) || [],
    [result]
  );

  const scenarioComparison = comparison.filter(
    (item) => item.scenario === scenario
  );

  const bestFitness =
    scenarioComparison.length > 0
      ? Math.min(
          ...scenarioComparison.map((item) => item.best_fitness)
        )
      : null;

  const navigate = (view) => {
    setActiveView(view);
    setError("");
  };

  return (
    <div className="app-shell">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">RX</div>

          <div className="brand-text">
            <strong>RouteX</strong>
            <span>TRAFFIC OPTIMIZER</span>
          </div>
        </div>

        <div className="sidebar-section-label">NAVIGATION</div>

        <nav className="sidebar-nav">
          <button
            className={`nav-item ${
              activeView === "dashboard" ? "active" : ""
            }`}
            onClick={() => navigate("dashboard")}
          >
            <span className="nav-icon">▦</span>
            <span>Dashboard</span>
          </button>

          <button
            className={`nav-item ${
              activeView === "optimization" ? "active" : ""
            }`}
            onClick={() => navigate("optimization")}
          >
            <span className="nav-icon">◇</span>
            <span>Optimization</span>
          </button>

          <button
            className={`nav-item ${
              activeView === "comparison" ? "active" : ""
            }`}
            onClick={() => navigate("comparison")}
          >
            <span className="nav-icon">▥</span>
            <span>Comparison</span>
          </button>

          <button
            className={`nav-item ${
              activeView === "history" ? "active" : ""
            }`}
            onClick={() => navigate("history")}
          >
            <span className="nav-icon">◷</span>
            <span>Run History</span>
          </button>
        </nav>

        <div className="sidebar-bottom">
          <div className="system-card">
            <div className="system-card-title">SYSTEM STATUS</div>

            <div className="system-status">
              <span className="status-dot"></span>
              <span>RouteX API</span>
              <strong>READY</strong>
            </div>

            <div className="system-endpoint">
              127.0.0.1:8000
            </div>
          </div>

          <div className="sidebar-footer">
            SIH • Route Optimization
          </div>
        </div>
      </aside>

      {/* MAIN */}
      <main className="main-content">
        <header className="topbar">
          <div>
            <span className="topbar-label">ROUTEX / OPERATIONS</span>
          </div>

          <div className="topbar-status">
            <span className="status-dot"></span>
            Backend Connected
          </div>
        </header>

        <div className="page-content">
          {error && (
            <div className="error-banner">
              <span>!</span>
              {error}
              <button onClick={() => setError("")}>×</button>
            </div>
          )}

          {/* DASHBOARD */}
          {activeView === "dashboard" && (
            <DashboardView
              result={result}
              history={history}
              comparison={scenarioComparison}
              loading={loading}
              algorithm={algorithm}
              scenario={scenario}
              setAlgorithm={setAlgorithm}
              setScenario={setScenario}
              runOptimization={runOptimization}
              navigate={navigate}
              convergenceData={convergenceData}
              bestFitness={bestFitness}
              loadHistoricalResult={loadHistoricalResult}
            />
          )}

          {/* OPTIMIZATION */}
          {activeView === "optimization" && (
            <OptimizationView
              result={result}
              loading={loading}
              algorithm={algorithm}
              scenario={scenario}
              setAlgorithm={setAlgorithm}
              setScenario={setScenario}
              runOptimization={runOptimization}
              convergenceData={convergenceData}
            />
          )}

          {/* COMPARISON */}
          {activeView === "comparison" && (
            <ComparisonView
              scenario={scenario}
              setScenario={setScenario}
              scenarioComparison={scenarioComparison}
              bestFitness={bestFitness}
              comparisonLoading={comparisonLoading}
              loadComparison={loadComparison}
              benchmarkResult={benchmarkResult}
              benchmarkLoading={benchmarkLoading}
              runBenchmark={runBenchmark}
            />
          )}

          {/* HISTORY */}
          {activeView === "history" && (
            <HistoryView
              history={history}
              historyLoading={historyLoading}
              loadHistory={loadHistory}
              loadHistoricalResult={loadHistoricalResult}
            />
          )}
        </div>
      </main>
    </div>
  );
}

/* =========================================================
   DASHBOARD
========================================================= */

function DashboardView({
  result,
  history,
  comparison,
  loading,
  algorithm,
  scenario,
  setAlgorithm,
  setScenario,
  runOptimization,
  navigate,
  convergenceData,
  bestFitness,
  loadHistoricalResult,
}) {
  return (
    <div className="view">
      <PageHeader
        eyebrow="LIVE OPERATIONS"
        title="Dashboard"
        subtitle="Monitor RouteX optimization performance and traffic routing."
      />

      {/* QUICK CONTROL */}
      <section className="panel control-panel">
        <div className="panel-heading">
          <div>
            <span className="micro-label">OPTIMIZATION CONTROL</span>
            <h2>Run a new optimization</h2>
          </div>

          <span className="ready-badge">
            <span className="status-dot"></span>
            READY
          </span>
        </div>

        <div className="control-grid">
          <SelectField
            label="ALGORITHM"
            value={algorithm}
            onChange={setAlgorithm}
            options={[
              ["greedy", "Greedy"],
              ["qpso", "QPSO"],
              ["hybrid", "Hybrid QPSO"],
            ]}
          />

          <SelectField
            label="TRAFFIC SCENARIO"
            value={scenario}
            onChange={setScenario}
            options={[
              ["low", "Low Traffic"],
              ["medium", "Medium Traffic"],
              ["high", "High Traffic"],
              ["big", "Large Scenario"],
            ]}
          />

          <button
            className="primary-button"
            onClick={runOptimization}
            disabled={loading}
          >
            {loading ? "Optimizing..." : "Run Optimization"}
            <span className="button-arrow">→</span>
          </button>
        </div>
      </section>

      {/* KPI */}
      <div className="kpi-grid">
        <KpiCard
          label="FITNESS"
          value={result?.fitness ?? "—"}
          icon="◈"
          accent="cyan"
        />

        <KpiCard
          label="TOTAL DISTANCE"
          value={result?.distance ?? "—"}
          unit={result ? "units" : ""}
          icon="↗"
          accent="blue"
        />

        <KpiCard
          label="RUNTIME"
          value={
            result?.runtime !== undefined
              ? Number(result.runtime).toFixed(4)
              : "—"
          }
          unit={result ? "sec" : ""}
          icon="◷"
          accent="purple"
        />

        <KpiCard
          label="VEHICLES USED"
          value={result?.vehicles_used ?? "—"}
          icon="▱"
          accent="green"
        />
      </div>

      {!result ? (
        <section className="empty-state large">
          <div className="empty-icon">◇</div>
          <h2>No optimization loaded</h2>
          <p>
            Select an algorithm and traffic scenario above to generate a
            RouteX optimization result.
          </p>
        </section>
      ) : (
        <div className="dashboard-grid">
          {/* RESULT SUMMARY */}
          <section className="panel result-summary">
            <div className="panel-heading">
              <div>
                <span className="micro-label">LATEST RESULT</span>
                <h2>Optimization Result</h2>
              </div>

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

            <div className="result-meta-grid">
              <div>
                <span>ALGORITHM</span>
                <strong>{result.algorithm}</strong>
              </div>

              <div>
                <span>SCENARIO</span>
                <strong>{result.scenario}</strong>
              </div>

              <div>
                <span>ITERATIONS</span>
                <strong>{result.iterations}</strong>
              </div>
            </div>

            <button
              className="secondary-button full-width"
              onClick={() => navigate("optimization")}
            >
              View Full Optimization
              <span>→</span>
            </button>
          </section>

          {/* MINI CONVERGENCE */}
          <section className="panel chart-panel">
            <div className="panel-heading">
              <div>
                <span className="micro-label">PERFORMANCE</span>
                <h2>Convergence</h2>
              </div>

              <span className="chart-caption">
                {result.iterations} iterations
              </span>
            </div>

            <div className="mini-chart">
              <ResponsiveContainer width="100%" height={210}>
                <LineChart data={convergenceData}>
                  <CartesianGrid
                    stroke="#253252"
                    strokeDasharray="3 3"
                  />
                  <XAxis
                    dataKey="iteration"
                    tick={{ fill: "#7182a5", fontSize: 10 }}
                  />
                  <YAxis
                    tick={{ fill: "#7182a5", fontSize: 10 }}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "#111a31",
                      border: "1px solid #304065",
                      borderRadius: "8px",
                      color: "#fff",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="fitness"
                    stroke="#42d9ff"
                    strokeWidth={3}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>
        </div>
      )}

      {/* QUICK COMPARISON */}
      {comparison.length > 0 && (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="micro-label">ALGORITHM PERFORMANCE</span>
              <h2>Current Scenario Comparison</h2>
            </div>

            <button
              className="text-button"
              onClick={() => navigate("comparison")}
            >
              View Comparison →
            </button>
          </div>

          <ComparisonTable
            data={comparison}
            bestFitness={bestFitness}
          />
        </section>
      )}

      {/* RECENT RUNS */}
      {history.length > 0 && (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="micro-label">RECENT ACTIVITY</span>
              <h2>Latest Optimization Runs</h2>
            </div>

            <button
              className="text-button"
              onClick={() => navigate("history")}
            >
              View All →
            </button>
          </div>

          <div className="compact-history">
            {history.slice(0, 4).map((item) => (
              <button
                className="compact-history-row"
                key={item.id}
                onClick={() => loadHistoricalResult(item.id)}
              >
                <span className="run-id">#{item.id}</span>
                <strong>{item.algorithm}</strong>
                <span>{item.scenario}</span>
                <span>{item.fitness}</span>
                <span>→</span>
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

/* =========================================================
   OPTIMIZATION VIEW
========================================================= */

function OptimizationView({
  result,
  loading,
  algorithm,
  scenario,
  setAlgorithm,
  setScenario,
  runOptimization,
  convergenceData,
}) {
  return (
    <div className="view">
      <PageHeader
        eyebrow="OPTIMIZATION ENGINE"
        title="Optimization"
        subtitle="Configure and execute intelligent vehicle routing."
      />

      <section className="panel control-panel">
        <div className="panel-heading">
          <div>
            <span className="micro-label">CONFIGURATION</span>
            <h2>Optimization Parameters</h2>
          </div>

          <span className="seed-label">SEED: 42</span>
        </div>

        <div className="control-grid optimization-controls">
          <SelectField
            label="ALGORITHM"
            value={algorithm}
            onChange={setAlgorithm}
            options={[
              ["greedy", "Greedy"],
              ["qpso", "QPSO"],
              ["hybrid", "Hybrid QPSO"],
            ]}
          />

          <SelectField
            label="TRAFFIC SCENARIO"
            value={scenario}
            onChange={setScenario}
            options={[
              ["low", "Low Traffic"],
              ["medium", "Medium Traffic"],
              ["high", "High Traffic"],
              ["big", "Large Scenario"],
            ]}
          />

          <button
            className="primary-button"
            onClick={runOptimization}
            disabled={loading}
          >
            {loading ? "Optimizing..." : "Run Optimization"}
            <span>→</span>
          </button>
        </div>
      </section>

      {!result ? (
        <section className="empty-state">
          <div className="empty-icon">◇</div>
          <h2>Ready to optimize</h2>
          <p>
            Choose an algorithm and traffic scenario, then run the
            optimization engine.
          </p>
        </section>
      ) : (
        <>
          <div className="kpi-grid">
            <KpiCard
              label="FITNESS"
              value={result.fitness}
              icon="◈"
              accent="cyan"
            />

            <KpiCard
              label="TOTAL DISTANCE"
              value={result.distance}
              icon="↗"
              accent="blue"
            />

            <KpiCard
              label="RUNTIME"
              value={Number(result.runtime).toFixed(4)}
              unit="sec"
              icon="◷"
              accent="purple"
            />

            <KpiCard
              label="VEHICLES USED"
              value={result.vehicles_used}
              icon="▱"
              accent="green"
            />
          </div>

          <section className="panel">
            <div className="panel-heading">
              <div>
                <span className="micro-label">ROUTING OUTPUT</span>
                <h2>Optimized Route</h2>
                <p>
                  Vehicle routing generated by the selected algorithm.
                </p>
              </div>

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

            <div className="route-list">
              {result.routes?.map((route, index) => (
                <div className="route-row" key={index}>
                  <div className="vehicle-info">
                    <span className="vehicle-icon">▱</span>
                    <div>
                      <strong>Vehicle {index + 1}</strong>
                      <span>{Math.max(route.length - 2, 0)} customer stops</span>
                    </div>
                  </div>

                  <div className="route-track">
                    {route.map((node, nodeIndex) => (
                      <div className="route-step" key={nodeIndex}>
                        <span
                          className={
                            nodeIndex === 0 ||
                            nodeIndex === route.length - 1
                              ? "route-node depot"
                              : "route-node"
                          }
                        >
                          {node}
                        </span>

                        {nodeIndex < route.length - 1 && (
                          <span className="route-arrow">→</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="panel chart-panel">
            <div className="panel-heading">
              <div>
                <span className="micro-label">OPTIMIZATION PROCESS</span>
                <h2>Convergence Analysis</h2>
                <p>Fitness progression across optimization iterations.</p>
              </div>

              <span className="chart-caption">
                {result.iterations} iterations
              </span>
            </div>

            <div className="large-chart">
              <ResponsiveContainer width="100%" height={330}>
                <LineChart data={convergenceData}>
                  <CartesianGrid
                    stroke="#253252"
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="iteration"
                    tick={{ fill: "#7182a5", fontSize: 11 }}
                    axisLine={{ stroke: "#304065" }}
                  />

                  <YAxis
                    tick={{ fill: "#7182a5", fontSize: 11 }}
                    axisLine={{ stroke: "#304065" }}
                  />

                  <Tooltip
                    contentStyle={{
                      background: "#111a31",
                      border: "1px solid #304065",
                      borderRadius: "8px",
                      color: "#fff",
                    }}
                  />

                  <Line
                    type="monotone"
                    dataKey="fitness"
                    stroke="#42d9ff"
                    strokeWidth={3}
                    dot={false}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

/* =========================================================
   COMPARISON VIEW
========================================================= */

function ComparisonView({
  scenario,
  setScenario,
  scenarioComparison,
  bestFitness,
  comparisonLoading,
  loadComparison,
  benchmarkResult,
  benchmarkLoading,
  runBenchmark,
}) {
  return (
    <div className="view">
      <PageHeader
        eyebrow="PERFORMANCE ANALYTICS"
        title="Algorithm Comparison"
        subtitle="Compare optimization strategies for different traffic scenarios."
      />

      <section className="panel comparison-controls">
        <div>
          <span className="micro-label">SCENARIO FILTER</span>

          <select
            className="dark-select"
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
          >
            <option value="low">Low Traffic</option>
            <option value="medium">Medium Traffic</option>
            <option value="high">High Traffic</option>
            <option value="big">Large Scenario</option>
          </select>
        </div>

        <div className="comparison-actions">
          <button
            className="secondary-button"
            onClick={loadComparison}
            disabled={comparisonLoading}
          >
            {comparisonLoading ? "Loading..." : "Refresh"}
          </button>

          <button
            className="primary-button"
            onClick={runBenchmark}
            disabled={benchmarkLoading}
          >
            {benchmarkLoading
              ? "Comparing..."
              : "Compare All Algorithms"}
            <span>→</span>
          </button>
        </div>
      </section>

      {scenarioComparison.length === 0 ? (
        <section className="empty-state">
          <div className="empty-icon">▥</div>
          <h2>No comparison data</h2>
          <p>
            Run multiple algorithms or use Compare All Algorithms to
            generate comparison results.
          </p>
        </section>
      ) : (
        <>
          <section className="panel">
            <div className="panel-heading">
              <div>
                <span className="micro-label">RESULTS</span>
                <h2>{scenario} traffic</h2>
              </div>
            </div>

            <ComparisonTable
              data={scenarioComparison}
              bestFitness={bestFitness}
            />
          </section>

          <div className="two-column">
            <section className="panel chart-panel">
              <div className="panel-heading">
                <div>
                  <span className="micro-label">FITNESS</span>
                  <h2>Fitness Comparison</h2>
                </div>
              </div>

              <div className="chart-medium">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={scenarioComparison}>
                    <CartesianGrid
                      stroke="#253252"
                      strokeDasharray="3 3"
                    />
                    <XAxis
                      dataKey="algorithm"
                      tick={{ fill: "#8b9abd", fontSize: 11 }}
                    />
                    <YAxis
                      tick={{ fill: "#8b9abd", fontSize: 11 }}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "#111a31",
                        border: "1px solid #304065",
                        borderRadius: "8px",
                        color: "#fff",
                      }}
                    />
                    <Bar
                      dataKey="best_fitness"
                      fill="#42d9ff"
                      radius={[5, 5, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className="panel chart-panel">
              <div className="panel-heading">
                <div>
                  <span className="micro-label">EXECUTION</span>
                  <h2>Runtime Comparison</h2>
                </div>
              </div>

              <div className="chart-medium">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={scenarioComparison}>
                    <CartesianGrid
                      stroke="#253252"
                      strokeDasharray="3 3"
                    />
                    <XAxis
                      dataKey="algorithm"
                      tick={{ fill: "#8b9abd", fontSize: 11 }}
                    />
                    <YAxis
                      tick={{ fill: "#8b9abd", fontSize: 11 }}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "#111a31",
                        border: "1px solid #304065",
                        borderRadius: "8px",
                        color: "#fff",
                      }}
                    />
                    <Bar
                      dataKey="best_runtime"
                      fill="#9277ff"
                      radius={[5, 5, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>
          </div>
        </>
      )}

      {benchmarkResult && (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="micro-label">BENCHMARK</span>
              <h2>Benchmark Summary</h2>
            </div>

            <span className="status-badge info">
              {benchmarkResult.total_runs} RUNS
            </span>
          </div>

          <div className="benchmark-table">
            <div className="benchmark-row benchmark-header">
              <span>ALGORITHM</span>
              <span>BEST FITNESS</span>
              <span>MEAN FITNESS</span>
              <span>MEAN RUNTIME</span>
              <span>IMPROVEMENT</span>
            </div>

            {benchmarkResult.summary?.map((item) => (
              <div
                className="benchmark-row"
                key={`${item.scenario}-${item.algorithm}`}
              >
                <strong>{item.algorithm}</strong>

                <span>{item.best_fitness}</span>

                <span>{item.mean_fitness}</span>

                <span>{item.mean_runtime}s</span>

                <span
                  className={
                    item.improvement_vs_baseline_percent !== null
                      ? "positive"
                      : "muted"
                  }
                >
                  {item.improvement_vs_baseline_percent !== null
                    ? `${item.improvement_vs_baseline_percent}%`
                    : "Baseline"}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

/* =========================================================
   HISTORY VIEW
========================================================= */

function HistoryView({
  history,
  historyLoading,
  loadHistory,
  loadHistoricalResult,
}) {
  return (
    <div className="view">
      <PageHeader
        eyebrow="OPTIMIZATION RECORDS"
        title="Run History"
        subtitle="Previously saved RouteX optimization results."
        action={
          <button
            className="secondary-button"
            onClick={loadHistory}
            disabled={historyLoading}
          >
            {historyLoading ? "Loading..." : "Refresh History"}
          </button>
        }
      />

      {history.length === 0 ? (
        <section className="empty-state">
          <div className="empty-icon">◷</div>
          <h2>No optimization history</h2>
          <p>
            Optimization runs will appear here after they are completed.
          </p>
        </section>
      ) : (
        <section className="panel history-panel">
          <div className="history-table-header">
            <span>RUN</span>
            <span>ALGORITHM</span>
            <span>SCENARIO</span>
            <span>FITNESS</span>
            <span>RUNTIME</span>
            <span></span>
          </div>

          {history.map((item) => (
            <button
              className="history-table-row"
              key={item.id}
              onClick={() => loadHistoricalResult(item.id)}
            >
              <span className="run-number">#{item.id}</span>

              <strong>{item.algorithm}</strong>

              <span className="scenario-tag">
                {item.scenario}
              </span>

              <strong>{item.fitness}</strong>

              <span>
                {item.runtime !== null
                  ? `${Number(item.runtime).toFixed(4)} s`
                  : "N/A"}
              </span>

              <span className="view-arrow">→</span>
            </button>
          ))}
        </section>
      )}
    </div>
  );
}

/* =========================================================
   SHARED COMPONENTS
========================================================= */

function PageHeader({
  eyebrow,
  title,
  subtitle,
  action,
}) {
  return (
    <div className="page-header">
      <div>
        <span className="page-eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>

      {action && <div>{action}</div>}
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}) {
  return (
    <div className="field">
      <label>{label}</label>

      <select
        className="dark-select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map(([optionValue, optionLabel]) => (
          <option key={optionValue} value={optionValue}>
            {optionLabel}
          </option>
        ))}
      </select>
    </div>
  );
}

function KpiCard({
  label,
  value,
  unit,
  icon,
  accent,
}) {
  return (
    <div className={`kpi-card ${accent}`}>
      <div className="kpi-top">
        <span>{label}</span>
        <span className="kpi-icon">{icon}</span>
      </div>

      <div className="kpi-value">
        {value}
        {unit && <small>{unit}</small>}
      </div>
    </div>
  );
}

function ComparisonTable({
  data,
  bestFitness,
}) {
  return (
    <div className="data-table">
      <div className="data-row data-header">
        <span>ALGORITHM</span>
        <span>BEST FITNESS</span>
        <span>BEST RUNTIME</span>
        <span>RUNS</span>
        <span>STATUS</span>
      </div>

      {data.map((item, index) => (
        <div className="data-row" key={index}>
          <strong>
            <span className="algorithm-dot"></span>
            {item.algorithm}
          </strong>

          <span>{item.best_fitness}</span>

          <span>
            {Number(item.best_runtime).toFixed(6)} s
          </span>

          <span>{item.runs}</span>

          <span>
            {item.best_fitness === bestFitness ? (
              <span className="best-label">★ BEST</span>
            ) : (
              <span className="muted">—</span>
            )}
          </span>
        </div>
      ))}
    </div>
  );
}

export default App;