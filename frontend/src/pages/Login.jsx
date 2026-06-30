import React, { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { formatApiError } from "@/lib/api";
import { CalendarDays, ArrowRight } from "lucide-react";
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
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left visual */}
      <div className="hidden lg:flex relative items-end p-12 overflow-hidden" style={{ background: "linear-gradient(160deg, #2C4C3B 0%, #3C634D 100%)" }}>
        <div className="absolute inset-0 opacity-[0.07]" style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, #fff 1px, transparent 0)', backgroundSize: '24px 24px' }} />
        <div className="relative z-10 text-white max-w-md">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-sm text-xs tracking-widest uppercase font-semibold mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-[#D96C4A]" /> Gestione Appuntamenti
          </div>
          <h1 className="font-display text-5xl font-black tracking-tight leading-[1.05] mb-5">
            Tempo. Persone. <br />
            <span className="text-[#E6C8AC]">Tutto al posto giusto.</span>
          </h1>
          <p className="text-white/75 text-base leading-relaxed">
            La piattaforma SaaS per centri studi e professionisti: gestisci docenti, clienti e disponibilità in un unico calendario, pensato per il mobile.
          </p>
          <div className="mt-10 grid grid-cols-3 gap-4 text-white/80">
            {[
              { k: "Multi-tenant", v: "Studi isolati" },
              { k: "Orari flessibili", v: "Per giorno e fascia" },
              { k: "Mobile-first", v: "Ovunque tu sia" },
            ].map((s) => (
              <div key={s.k}>
                <div className="text-xs uppercase tracking-[0.18em] text-white/60 mb-1">{s.k}</div>
                <div className="text-sm font-medium">{s.v}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Form */}
      <div className="flex items-center justify-center p-6 sm:p-10">
        <form onSubmit={submit} className="w-full max-w-md" data-testid="login-form">
          <div className="flex items-center gap-2 mb-8">
            <Logo size={40} />
            <div>
              <div className="font-display text-xl font-bold leading-none">Prenotika</div>
              <div className="text-[11px] text-[color:var(--text-2)] tracking-wider uppercase mt-0.5">SaaS Agenda</div>
            </div>
          </div>

          <h2 className="font-display text-3xl font-bold mb-1.5">Bentornato</h2>
          <p className="text-[color:var(--text-2)] mb-7">Accedi al tuo centro studi.</p>

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
