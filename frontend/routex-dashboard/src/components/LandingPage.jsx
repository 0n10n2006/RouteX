import React, { useState } from "react";
import { motion } from "framer-motion";
import { auth } from "../firebase";
import { signInWithEmailAndPassword, createUserWithEmailAndPassword } from "firebase/auth";

export default function LandingPage({ onLoginClick }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSignUp, setIsSignUp] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

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
    <div className="min-h-screen bg-surface flex flex-col">
      <div className="pointer-events-none fixed inset-0 z-0 bg-[radial-gradient(circle_at_50%_0%,rgba(97,212,255,0.08)_0%,rgba(0,19,48,0)_70%)]"></div><header className="fixed top-0 left-0 right-0 z-50 bg-surface-container-lowest/80 backdrop-blur-xl border-b border-outline-variant"><div className="h-16 w-full px-margin-lg flex items-center justify-between gap-space-lg"><div className="flex items-center gap-space-md"><img alt="RouteX Wordmark Logo" className="h-8 w-auto object-contain" src="/routex-logo.png"/><span className="font-headline-sm text-headline-sm text-on-surface uppercase tracking-wider hidden sm:inline-block">RouteX</span></div><div className="flex items-center gap-space-md"><a className="inline-flex items-center justify-center h-9 px-space-lg rounded border border-primary text-primary hover:bg-primary hover:text-on-primary font-label-md text-label-md uppercase tracking-wider transition-all" data-path="login" href="#">Login</a><div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0"><span className="material-symbols-outlined text-on-primary text-[18px]">person</span></div></div></div></header><main className="relative z-10 w-full pt-16 bg-surface flex-grow"><div className="flex flex-col w-full text-on-surface bg-surface relative overflow-hidden h-full">
{/* Dynamic Ambient Glow Gradients */}
<div className="absolute top-0 right-0 w-[640px] h-[640px] bg-[radial-gradient(circle,rgba(24,185,232,0.08)_0%,rgba(0,19,48,0)_70%)] pointer-events-none -z-0"></div>
<div className="absolute top-[480px] left-[-200px] w-[500px] h-[500px] bg-[radial-gradient(circle,rgba(167,139,250,0.05)_0%,rgba(0,19,48,0)_70%)] pointer-events-none -z-0"></div>
{/* Hero Section & Live Portal Access */}
<section className="w-full px-margin-lg pt-space-2xl pb-space-2xl relative z-10 max-w-7xl mx-auto">
<div className="grid grid-cols-1 lg:grid-cols-12 gap-space-xl items-start">
{/* Left Column: Value Proposition & Live Telemetry Badge */}
<div className="lg:col-span-7 flex flex-col justify-center space-y-space-lg pt-space-sm">

{/* Headline & Accentuated Glow */}
<div className="relative space-y-space-xs">
<div className="absolute -top-10 -left-6 w-72 h-20 bg-primary/10 blur-2xl pointer-events-none rounded-full"></div>
<h1 className="font-headline-xl text-headline-xl text-on-surface font-bold tracking-tight text-[36px] sm:text-[44px] leading-tight">
            Smarter Routes.<br/>
<span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-[#42d9ff] drop-shadow-[0_0_24px_rgba(24,185,232,0.35)]">
              Smoother Cities.
            </span>
</h1>
<p className="font-body-lg text-body-lg text-on-surface-variant max-w-xl pt-space-xs leading-relaxed">
            Real-time, traffic-aware fleet route optimization powered by Hybrid QPSO. Coordinate high-density metropolitan fleets with millisecond trajectory updates and adaptive sensor networks.
          </p>
</div>
{/* Action CTAs */}
<div className="flex flex-wrap items-center gap-space-md pt-space-sm">
<a className="inline-flex items-center justify-center h-10 px-space-xl rounded bg-gradient-to-r from-[#18b9e8] to-[#42d9ff] text-on-primary font-headline-sm text-headline-sm uppercase tracking-wider font-semibold transition-all duration-200 shadow-[0_0_20px_rgba(24,185,232,0.4)] hover:shadow-[0_0_28px_rgba(66,217,255,0.65)] hover:scale-[1.01]" onClick={onLoginClick}>
<span className="material-symbols-outlined text-[18px] mr-space-xs">bolt</span>
            Get Started
          </a>
<a className="inline-flex items-center justify-center h-10 px-space-lg rounded border border-outline-variant bg-surface-container/50 text-on-surface font-label-md text-label-md uppercase tracking-wider hover:border-primary hover:text-primary hover:bg-surface-container-high transition-all" onClick={onLoginClick}>
<span className="material-symbols-outlined text-[18px] mr-space-xs">terminal</span>
            View Demo
          </a>
<div className="flex items-center gap-space-xs text-on-surface-variant font-code-sm text-code-sm ml-auto sm:ml-0">
<span className="material-symbols-outlined text-primary text-[16px]">verified</span>
            ISO-27001 & Autonomous Compliant
          </div>
</div>
</div>

{/* Right Column: Login Interface Integration */}
<div className="lg:col-span-5 w-full">
<div className="w-full rounded-[14px] bg-[#0d172a] border border-outline-variant/80 p-space-xl shadow-[0_8px_32px_rgba(0,0,0,0.7),0_0_0_1px_rgba(24,185,232,0.15)] relative backdrop-blur-md">
{/* Top Accent Light Bar */}
<div className="absolute top-0 left-6 right-6 h-[2px] bg-gradient-to-r from-transparent via-primary to-transparent opacity-80"></div>
<div className="flex items-center gap-space-md mb-space-md">
<div className="h-11 w-11 rounded-lg bg-surface-container-lowest flex items-center justify-center p-1.5 border border-outline-variant/50 shadow-inner">
<img alt="RouteX Wordmark Logo" className="h-full w-full object-contain" src="/routex-logo.png"/>
</div>
<div>
<h2 className="font-headline-sm text-headline-sm text-on-surface font-semibold tracking-tight">Welcome Back</h2>
<p className="font-body-sm text-body-sm text-on-surface-variant">Access your fleet telemetry and optimization portal</p>
</div>
</div>
<form className="space-y-space-md" onSubmit={handleLogin}>
{error && <div className="text-red-500 text-sm">{error}</div>}
<div className="space-y-space-xs">
<label className="block font-label-sm text-label-sm uppercase text-on-surface-variant tracking-wider" htmlFor="fleet-email">
Fleet Dispatch Identifier / Email
</label>
<div className="relative flex items-center">
<span className="material-symbols-outlined absolute left-space-md text-on-surface-variant text-[18px] pointer-events-none">badge</span>
<input className="w-full h-10 pl-10 pr-space-md rounded bg-[#091326] border border-outline-variant text-on-surface placeholder:text-outline font-body-md text-body-md focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary focus:shadow-[inset_0_0_4px_rgba(24,185,232,0.25)] transition-all" id="fleet-email" placeholder="operator@metro-grid.net" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
</div>
</div>
<div className="space-y-space-xs">
<div className="flex items-center justify-between">
<label className="block font-label-sm text-label-sm uppercase text-on-surface-variant tracking-wider" htmlFor="fleet-password">
Security Token / Key
</label>
</div>
<div className="relative flex items-center">
<span className="material-symbols-outlined absolute left-space-md text-on-surface-variant text-[18px] pointer-events-none">lock</span>
<input className="w-full h-10 pl-10 pr-10 rounded bg-[#091326] border border-outline-variant text-on-surface placeholder:text-outline font-body-md text-body-md focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary focus:shadow-[inset_0_0_4px_rgba(24,185,232,0.25)] transition-all" id="fleet-password" placeholder="••••••••••••" type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} required />
<button className="absolute right-space-md text-on-surface-variant hover:text-primary transition-colors focus:outline-none" onClick={() => setShowPassword(!showPassword)} type="button">
<span className="material-symbols-outlined text-[18px]">{showPassword ? "visibility_off" : "visibility"}</span>
</button>
</div>
</div>
<div className="flex items-center justify-between pt-space-xs">
<label className="flex items-center gap-space-xs cursor-pointer select-none">
<input className="w-4 h-4 rounded bg-[#091326] border-outline-variant text-primary focus:ring-0 focus:ring-offset-0 transition-all cursor-pointer accent-[#18b9e8]" type="checkbox" />
<span className="font-body-sm text-body-sm text-on-surface-variant">Remember fleet session</span>
</label>
<span className="font-code-sm text-code-sm text-secondary flex items-center gap-1">
<span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
Auth: TLS 1.3
</span>
</div>
<button disabled={loading} className="w-full h-10 mt-space-sm rounded bg-gradient-to-r from-[#18b9e8] to-[#42d9ff] text-on-primary font-headline-sm text-headline-sm uppercase tracking-wider font-semibold shadow-[0_4px_20px_rgba(24,185,232,0.4)] hover:shadow-[0_4px_26px_rgba(24,185,232,0.65)] hover:brightness-105 active:scale-[0.99] transition-all flex items-center justify-center gap-space-xs disabled:opacity-50" type="submit">
<span>{isSignUp ? "Initialize Deck" : "Log In to Mission Deck"}</span>
<span className="material-symbols-outlined text-[18px]">login</span>
</button>
<div className="text-center pt-space-xs font-body-sm text-body-sm text-on-surface-variant">
<span>{isSignUp ? "Already have a license?" : "Don't have an operations license?"} </span>
<button type="button" className="text-primary hover:underline font-medium" onClick={() => setIsSignUp(!isSignUp)}>
{isSignUp ? "Authenticate Here" : "Deploy Instance"}
</button>
</div>
</form>
</div>
</div>
</div>
</section>

{/* Feature Cards Row (4 Cards) */}
<section className="w-full px-margin-lg py-space-xl max-w-7xl mx-auto relative z-10">
<div className="flex flex-col space-y-space-xs mb-space-lg">
<div className="flex items-center gap-space-xs">
<span className="w-2 h-2 rounded bg-primary"></span>
<span className="font-label-sm text-label-sm uppercase text-primary tracking-widest font-semibold">Core Architecture</span>
</div>
<h2 className="font-headline-lg text-headline-lg text-on-surface font-semibold tracking-tight">
        Engineered for Zero-Latency Fleet Orchestration
      </h2>
<p className="font-body-md text-body-md text-on-surface-variant max-w-2xl">
        Algorithmic depth coupled with hyper-local physical validation guarantees executable, disruption-proof delivery schedules.
      </p>
</div>
{/* 4 High Density Cards Grid */}
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-space-lg">
{/* Card 1: Live Traffic Adaptation */}
<div className="group rounded-[12px] bg-[#111d36] border border-outline-variant/60 p-space-lg transition-all duration-300 hover:border-primary hover:shadow-[0_0_20px_rgba(24,185,232,0.25)] flex flex-col justify-between">
<div>
<div className="w-11 h-11 rounded-lg bg-surface-container-lowest border border-outline-variant/40 flex items-center justify-center text-primary mb-space-md group-hover:border-primary transition-colors">
<span className="material-symbols-outlined text-[24px]">radar</span>
</div>
<h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold mb-space-xs tracking-tight">
            Live Traffic Adaptation
          </h3>
<p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
            Dynamic sensor ingestion continuously streams real-time arterial flow, highway telemetry, and municipal traffic cams for instant detour recalculation.
          </p>
</div>

</div>
{/* Card 2: Hybrid QPSO + Local Search */}
<div className="group rounded-[12px] bg-[#111d36] border border-outline-variant/60 p-space-lg transition-all duration-300 hover:border-primary hover:shadow-[0_0_20px_rgba(24,185,232,0.25)] flex flex-col justify-between">
<div>
<div className="w-11 h-11 rounded-lg bg-surface-container-lowest border border-outline-variant/40 flex items-center justify-center text-primary mb-space-md group-hover:border-primary transition-colors">
<span className="material-symbols-outlined text-[24px]">hub</span>
</div>
<h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold mb-space-xs tracking-tight">
            Hybrid QPSO + Local Search
          </h3>
<p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
            Quantum-behaved Particle Swarm Optimization coupled with refined 2-opt and k-opt combinatorial neighborhood search prevents premature convergence.
          </p>
</div>

</div>
{/* Card 3: Feasibility-First Optimization */}
<div className="group rounded-[12px] bg-[#111d36] border border-outline-variant/60 p-space-lg transition-all duration-300 hover:border-primary hover:shadow-[0_0_20px_rgba(24,185,232,0.25)] flex flex-col justify-between">
<div>
<div className="w-11 h-11 rounded-lg bg-surface-container-lowest border border-outline-variant/40 flex items-center justify-center text-primary mb-space-md group-hover:border-primary transition-colors">
<span className="material-symbols-outlined text-[24px]">verified_user</span>
</div>
<h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold mb-space-xs tracking-tight">
            Feasibility-First Optimization
          </h3>
<p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
            Strict algorithmic time-window adherence, payload tare capacities, mandatory driver duty rest cycles, and multi-depot physical constraints.
          </p>
</div>

</div>
{/* Card 4: Incident-Aware Re-Routing */}
<div className="group rounded-[12px] bg-[#111d36] border border-outline-variant/60 p-space-lg transition-all duration-300 hover:border-primary hover:shadow-[0_0_20px_rgba(24,185,232,0.25)] flex flex-col justify-between">
<div>
<div className="w-11 h-11 rounded-lg bg-surface-container-lowest border border-outline-variant/40 flex items-center justify-center text-primary mb-space-md group-hover:border-primary transition-colors">
<span className="material-symbols-outlined text-[24px]">alt_route</span>
</div>
<h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold mb-space-xs tracking-tight">
            Incident-Aware Re-Routing
          </h3>
<p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
            Instant automated detection of unexpected road closures, structural construction, and micro-climate weather hazards with autonomous diversion vectors.
          </p>
</div>

</div>
</div>
</section>
{/* Interactive Terminal & Performance Validation Block */}
<section className="w-full px-margin-lg py-space-xl max-w-7xl mx-auto relative z-10 mb-space-2xl">
<div className="p-space-lg rounded-[14px] bg-[#0c1f3d] border border-outline-variant/70 flex flex-col lg:flex-row items-center justify-between gap-space-lg">
<div className="flex items-center gap-space-md">
<div className="w-12 h-12 rounded-lg bg-primary/20 flex items-center justify-center text-primary shrink-0 border border-primary/40">
<span className="material-symbols-outlined text-[28px]">terminal</span>
</div>
<div>
<div className="font-headline-sm text-headline-sm text-on-surface font-semibold">
            Ready to integrate with your TMS or Fleet Telematics API?
          </div>
<div className="font-body-sm text-body-sm text-on-surface-variant">
            Compatible with Geotab, Samsara, Omnitracs, and custom MQTT/gRPC telemetry collectors.
          </div>
</div>
</div>
<div className="flex items-center gap-space-md w-full lg:w-auto justify-end">
<div className="font-code-sm text-code-sm text-primary px-space-md py-2 rounded bg-surface-container-lowest border border-outline-variant/50 hidden sm:block">
          curl -X POST https://api.routex.network/v1/qpso/solve
        </div>
<a className="inline-flex items-center justify-center h-10 px-space-lg rounded bg-primary text-on-primary font-label-md text-label-md uppercase font-bold tracking-wider hover:bg-[#42d9ff] transition-all whitespace-nowrap" onClick={onLoginClick}>
          Read API Docs
        </a>
</div>
</div>
</section>
</div></main><footer className="relative z-10 w-full bg-surface-container-lowest border-t border-outline-variant py-space-xl"><div className="w-full px-margin-lg flex flex-col md:flex-row items-center justify-between gap-space-lg"><div className="flex items-center gap-space-sm"><div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div><span className="font-code-sm text-code-sm text-on-surface uppercase tracking-wider">SYSTEM STATUS: NORMAL • 99.98% OPTIMIZATION UPTIME</span></div><div className="flex items-center gap-space-lg font-label-sm text-label-sm text-on-surface-variant"><a className="hover:text-primary transition-colors uppercase" data-path="documentation" href="#">API Spec</a><a className="hover:text-primary transition-colors uppercase" data-path="platform" href="#">Network Mesh</a><a className="hover:text-primary transition-colors uppercase" data-path="fleet-telemetry" href="#">Telemetry Nodes</a></div><div className="font-code-sm text-code-sm text-outline">© 2025 RouteX Systems Inc. Precision Autonomous Logistics.</div></div></footer>
    </div>
  );
}
