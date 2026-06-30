import React, { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { formatApiError } from "@/lib/api";
import { ArrowRight } from "lucide-react";
import Logo from "@/components/Logo";

const DEMOS = [
  { label: "Admin Demo", email: "admin@demo.it", password: "Admin123!" },
  { label: "Docente Demo", email: "docente@demo.it", password: "Docente123!" },
  { label: "Super Admin", email: "superadmin@eligehub.it", password: "SuperAdmin123!" },
];

export default function Login() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  if (user) {
    return <Navigate to={user.role === "super_admin" ? "/studios" : "/dashboard"} replace />;
  }

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const data = await login(email, password);
      navigate(data.user.role === "super_admin" ? "/studios" : "/dashboard");
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Login fallito");
    } finally {
      setBusy(false);
    }
  };

  const fillDemo = (d) => {
    setEmail(d.email);
    setPassword(d.password);
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2 relative overflow-hidden">
      {/* Left visual - glassmorphism + gradient depth */}
      <div className="hidden lg:flex relative items-end p-12 overflow-hidden" style={{ background: "linear-gradient(160deg, #0F172A 0%, #1E1B4B 45%, #0F172A 100%)" }}>
        {/* Animated blobs */}
        <div className="anim-blob" style={{ background: "#7C3AED", width: 380, height: 380, top: "-60px", left: "-80px" }} />
        <div className="anim-blob" style={{ background: "#2DD4BF", width: 320, height: 320, bottom: "-80px", right: "-60px", animationDelay: "3s" }} />
        <div className="anim-blob" style={{ background: "#60A5FA", width: 240, height: 240, top: "40%", left: "30%", animationDelay: "6s", opacity: 0.35 }} />

        <div className="absolute inset-0 opacity-[0.06]" style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, #fff 1px, transparent 0)', backgroundSize: '28px 28px' }} />

        <div className="relative z-10 text-white max-w-md">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-md border border-white/15 text-xs tracking-[0.18em] uppercase font-semibold mb-7">
            <span className="w-1.5 h-1.5 rounded-full bg-[#2DD4BF] animate-pulse" /> SaaS · Agenda Multi-operatore
          </div>
          <h1 className="font-display text-5xl xl:text-6xl font-extrabold tracking-tight leading-[1.02] mb-5">
            La gestione <br />
            <span style={{ background: "linear-gradient(120deg, #A78BFA 0%, #60A5FA 50%, #2DD4BF 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text" }}>intelligente</span> <br />
            degli appuntamenti.
          </h1>
          <p className="text-white/70 text-base leading-relaxed">
            Tutte le agende del tuo studio, in un&apos;unica piattaforma. Organizza il tempo. Coordina il team. Ottimizza il lavoro.
          </p>
          <div className="mt-10 grid grid-cols-3 gap-4 text-white/85">
            {[
              { k: "Multi-tenant", v: "Studi isolati" },
              { k: "Orari custom", v: "Per professionista" },
              { k: "Mobile-first", v: "Sempre con te" },
            ].map((s) => (
              <div key={s.k} className="border-l border-white/15 pl-3">
                <div className="text-[10px] uppercase tracking-[0.18em] text-white/55 mb-1.5">{s.k}</div>
                <div className="text-sm font-medium">{s.v}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Form */}
      <div className="flex items-center justify-center p-6 sm:p-10 relative">
        <form onSubmit={submit} className="w-full max-w-md relative z-10" data-testid="login-form">
          <div className="flex items-center gap-3 mb-9">
            <Logo size={44} />
            <div>
              <div className="font-display text-xl font-bold leading-none tracking-tight">Prenotika</div>
              <div className="text-[10px] text-[color:var(--text-2)] tracking-[0.22em] uppercase mt-1">Smart Booking SaaS</div>
            </div>
          </div>

          <h2 className="font-display text-3xl font-bold mb-1.5 tracking-tight">Bentornato.</h2>
          <p className="text-[color:var(--text-2)] mb-7">Accedi al pannello del tuo studio.</p>

          <label className="block text-sm font-medium mb-1.5">Email</label>
          <input
            type="email"
            className="input-base mb-4"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="nome@studio.it"
            data-testid="login-email-input"
            required
            autoComplete="email"
          />
          <label className="block text-sm font-medium mb-1.5">Password</label>
          <input
            type="password"
            className="input-base mb-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            data-testid="login-password-input"
            required
            autoComplete="current-password"
          />

          {error ? (
            <div className="mt-3 text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="login-error">
              {error}
            </div>
          ) : null}

          <button type="submit" disabled={busy} className="btn-primary w-full justify-center mt-6" data-testid="login-submit-button">
            {busy ? "Accesso…" : (<>Accedi <ArrowRight size={16} /></>)}
          </button>

          <div className="mt-8 pt-6 border-t border-[color:var(--border)]">
            <div className="label-eyebrow mb-2">Account demo</div>
            <div className="flex flex-wrap gap-2">
              {DEMOS.map((d) => (
                <button
                  type="button"
                  key={d.email}
                  onClick={() => fillDemo(d)}
                  className="btn-secondary text-xs"
                  data-testid={`demo-${d.label.toLowerCase().replace(/\s+/g, '-')}-button`}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
