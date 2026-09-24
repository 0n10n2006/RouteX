import { useRef, useState } from "react";
import {
  Zap,
  PlayCircle,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Radar,
  GitMerge,
  ShieldCheck,
  AlertTriangle,
  LogIn,
  MapPin,
  Share2,
  Atom,
  SlidersHorizontal,
  CheckCircle2,
  Route,
  RefreshCw,
} from "lucide-react";
import { auth } from "../firebase";
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
} from "firebase/auth";

const STATS = [
  { value: "18%", label: "faster than greedy baseline" },
  { value: "5 / 5", label: "seeds beaten vs. GA, larger-area scenario" },
  { value: "5", label: "algorithms benchmarked head-to-head" },
  { value: "<0.1s", label: "to optimize an 8-stop fleet run" },
];

const PIPELINE = [
  { icon: MapPin, label: "Real-World Data", caption: "OSM roads, vehicles, live traffic" },
  { icon: Share2, label: "Graph Model", caption: "Road network as nodes & edges" },
  { icon: Atom, label: "Hybrid QPSO", caption: "Global search, multiple routes" },
  { icon: SlidersHorizontal, label: "2-opt / Or-opt", caption: "Local refinement" },
  { icon: CheckCircle2, label: "Feasibility Check", caption: "Repair & validate constraints" },
  { icon: Route, label: "Optimized Routes", caption: "Feasible, traffic-aware" },
];

const FEATURES = [
  {
    icon: Radar,
    title: "Continuous Route Adaptation",
    description:
      "Re-optimizes routes automatically when traffic conditions change, instead of treating routing as a one-time calculation.",
  },
  {
    icon: GitMerge,
    title: "Hybrid QPSO + Local Search",
    description:
      "Combines global QPSO search with 2-opt, Or-opt, and iterated local search refinement to escape local optima that simpler algorithms get stuck in.",
  },
  {
    icon: ShieldCheck,
    title: "Feasibility-First Optimization",
    description:
      "Every candidate route is repaired and validated against vehicle capacity and depot constraints before it's scored, so infeasible solutions never dominate the search.",
  },
  {
    icon: AlertTriangle,
    title: "Live Traffic + Incident-Aware Re-Optimization",
    description:
      "Pulls real-time TomTom traffic data and detects road incidents or closures, automatically triggering a re-optimization so routes stay valid.",
  },
];

export default function LandingPage({ onLoginClick }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSignUp, setIsSignUp] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const emailInputRef = useRef(null);

  const scrollToLogin = () => {
    emailInputRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
    emailInputRef.current?.focus();
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isSignUp) {
        await createUserWithEmailAndPassword(auth, email, password);
      } else {
        await signInWithEmailAndPassword(auth, email, password);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="landing">
      {/* HEADER */}
      <header className="landing-header">
        <div className="landing-header-inner">
          <div className="landing-brand">
            <img src="/routex-logo.png" alt="RouteX" className="landing-brand-logo" />
          </div>

          <button className="secondary-button" onClick={scrollToLogin}>
            Log In
          </button>
        </div>
      </header>

      <main className="landing-main">
        {/* HERO */}
        <section className="landing-hero">
          <div className="landing-hero-grid">
            <div className="landing-hero-copy">
              <h1>
                Smarter Routes.
                <br />
                <span className="landing-hero-accent">Smoother Cities.</span>
              </h1>

              <p>
                Real-time, traffic-aware fleet route optimization powered by
                Hybrid QPSO — benchmarked against Greedy, GA, PSO, and QPSO on
                real OpenStreetMap road data.
              </p>

              <div className="landing-hero-actions">
                <button className="primary-button" onClick={scrollToLogin}>
                  <Zap size={16} />
                  Get Started
                  <span className="button-arrow">→</span>
                </button>

                <button className="secondary-button" onClick={onLoginClick}>
                  <PlayCircle size={16} />
                  View Demo (no account needed)
                </button>
              </div>
            </div>

            <div className="landing-login-card panel">
              <div className="panel-heading">
                <div>
                  <span className="micro-label">ACCOUNT ACCESS</span>
                  <h2>{isSignUp ? "Create an Account" : "Welcome Back"}</h2>
                  <p>
                    {isSignUp
                      ? "Set up access to the RouteX optimization dashboard."
                      : "Sign in to access the RouteX optimization dashboard."}
                  </p>
                </div>
              </div>

              <form className="landing-login-form" onSubmit={handleLogin}>
                {error && <div className="landing-form-error">{error}</div>}

                <div className="field">
                  <label htmlFor="login-email">EMAIL</label>
                  <div className="landing-input-wrap">
                    <Mail size={16} className="landing-input-icon" />
                    <input
                      ref={emailInputRef}
                      id="login-email"
                      className="landing-input"
                      type="email"
                      placeholder="you@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="field">
                  <label htmlFor="login-password">PASSWORD</label>
                  <div className="landing-input-wrap">
                    <Lock size={16} className="landing-input-icon" />
                    <input
                      id="login-password"
                      className="landing-input"
                      type={showPassword ? "text" : "password"}
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                    <button
                      type="button"
                      className="landing-input-toggle"
                      onClick={() => setShowPassword((v) => !v)}
                      aria-label={
                        showPassword ? "Hide password" : "Show password"
                      }
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                <button
                  className="primary-button full-width"
                  type="submit"
                  disabled={loading}
                >
                  <LogIn size={16} />
                  {loading
                    ? "Please wait..."
                    : isSignUp
                    ? "Create Account"
                    : "Log In"}
                </button>

                <button
                  type="button"
                  className="text-button landing-form-toggle"
                  onClick={() => setIsSignUp((v) => !v)}
                >
                  {isSignUp
                    ? "Already have an account? Log in"
                    : "Don't have an account? Sign up"}
                </button>
              </form>
            </div>
          </div>
        </section>

        {/* STATS */}
        <section className="landing-stats">
          {STATS.map((stat) => (
            <div className="landing-stat" key={stat.label}>
              <span className="landing-stat-value">{stat.value}</span>
              <span className="landing-stat-label">{stat.label}</span>
            </div>
          ))}
        </section>

        {/* PIPELINE */}
        <section className="landing-pipeline-section">
          <div className="landing-section-heading">
            <span className="micro-label">HOW IT WORKS</span>
            <h2>From road network to deployable routes</h2>
            <p>
              One pipeline, run continuously — every stage re-runs the
              moment traffic conditions change.
            </p>
          </div>

          <div className="landing-pipeline">
            {PIPELINE.map(({ icon: Icon, label, caption }, i) => (
              <div className="landing-pipeline-step" key={label}>
                <div className="landing-pipeline-icon">
                  <Icon size={20} />
                </div>
                <span className="landing-pipeline-label">{label}</span>
                <span className="landing-pipeline-caption">{caption}</span>
                {i < PIPELINE.length - 1 && (
                  <span className="landing-pipeline-arrow">→</span>
                )}
              </div>
            ))}
          </div>

          <div className="landing-pipeline-loop">
            <RefreshCw size={14} />
            Traffic change detected — re-optimize automatically
          </div>
        </section>

        {/* FEATURES */}
        <section className="landing-features">
          <div className="landing-section-heading">
            <span className="micro-label">CORE ARCHITECTURE</span>
            <h2>What makes RouteX different</h2>
            <p>
              Route planning that keeps adapting after it starts, backed by
              an optimizer that's benchmarked, feasibility-checked, and
              reproducible.
            </p>
          </div>

          <div className="landing-feature-grid">
            {FEATURES.map(({ icon: Icon, title, description }) => (
              <div className="landing-feature-card" key={title}>
                <div className="landing-feature-icon">
                  <Icon size={22} />
                </div>
                <h3>{title}</h3>
                <p>{description}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <span>© 2026 RouteX — Built for Smart India Hackathon</span>
        <span className="landing-footer-status">
          <span className="status-dot"></span>
          Benchmarked against Greedy, GA, PSO &amp; QPSO
        </span>
      </footer>
    </div>
  );
}
