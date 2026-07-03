import React, { useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { api, formatApiError } from "@/lib/api";
import { ArrowLeft, Eye, EyeOff, KeyRound, CheckCircle2 } from "lucide-react";
import Logo from "@/components/Logo";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") || "";
  const [newPwd, setNewPwd] = useState("");
  const [confirmPwd, setConfirmPwd] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (!token) { setError("Link non valido. Richiedine uno nuovo."); return; }
    if (newPwd.length < 8) { setError("La password deve avere almeno 8 caratteri."); return; }
    if (newPwd !== confirmPwd) { setError("Le due password non coincidono."); return; }
    setBusy(true);
    try {
      await api.post("/auth/reset-password", { token, new_password: newPwd });
      setDone(true);
      setTimeout(() => navigate("/login"), 2500);
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore. Riprova.");
    } finally { setBusy(false); }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2 relative overflow-hidden">
      <div className="hidden lg:flex relative items-end p-12 overflow-hidden" style={{ background: "linear-gradient(160deg, #0F172A 0%, #1E1B4B 45%, #0F172A 100%)" }}>
        <div className="anim-blob" style={{ background: "#7C3AED", width: 380, height: 380, top: "-60px", left: "-80px" }} />
        <div className="anim-blob" style={{ background: "#2DD4BF", width: 320, height: 320, bottom: "-80px", right: "-60px", animationDelay: "3s" }} />
        <div className="absolute inset-0 opacity-[0.06]" style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, #fff 1px, transparent 0)', backgroundSize: '28px 28px' }} />
        <div className="relative z-10 text-white max-w-md">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-md border border-white/15 text-xs tracking-[0.18em] uppercase font-semibold mb-7">
            <KeyRound size={12} /> Nuova password
          </div>
          <h1 className="font-display text-5xl xl:text-6xl font-extrabold tracking-tight leading-[1.02] mb-5">
            Scegli una <br />
            <span style={{ background: "linear-gradient(120deg, #A78BFA 0%, #60A5FA 50%, #2DD4BF 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>nuova password.</span>
          </h1>
          <p className="text-white/70 text-base leading-relaxed">
            Usane una che ricorderai facilmente ma difficile da indovinare. Ti consigliamo almeno 12 caratteri con lettere, numeri e simboli.
          </p>
        </div>
      </div>

      <div className="flex items-center justify-center p-6 sm:p-10 relative">
        <div className="w-full max-w-md relative z-10">
          <div className="flex items-center gap-3 mb-9">
            <Logo size={44} />
            <div>
              <div className="font-display text-xl font-bold leading-none tracking-tight">Prenotika</div>
              <div className="text-[10px] text-[color:var(--text-2)] tracking-[0.22em] uppercase mt-1">Smart Booking</div>
            </div>
          </div>

          {done ? (
            <div data-testid="reset-done">
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-5" style={{ background: "linear-gradient(135deg,#7C3AED,#2DD4BF)" }}>
                <CheckCircle2 size={26} className="text-white" />
              </div>
              <h2 className="font-display text-3xl font-bold mb-2 tracking-tight">Password aggiornata</h2>
              <p className="text-[color:var(--text-2)] mb-6">Ora puoi accedere con la nuova password. Ti stiamo reindirizzando al login…</p>
              <Link to="/login" className="btn-primary w-full justify-center" data-testid="reset-goto-login">Vai al login</Link>
            </div>
          ) : (
            <form onSubmit={submit} data-testid="reset-form">
              <h2 className="font-display text-3xl font-bold mb-1.5 tracking-tight">Reimposta password</h2>
              <p className="text-[color:var(--text-2)] mb-7">Inserisci la nuova password che vuoi utilizzare.</p>

              <label className="block text-sm font-medium mb-1.5">Nuova password</label>
              <div className="relative mb-4">
                <input
                  type={showNew ? "text" : "password"}
                  className="input-base pr-11"
                  value={newPwd}
                  onChange={(e) => setNewPwd(e.target.value)}
                  placeholder="Almeno 8 caratteri"
                  required
                  autoComplete="new-password"
                  autoFocus
                  data-testid="reset-new-password-input"
                />
                <button type="button" onClick={() => setShowNew((s) => !s)} tabIndex={-1} className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-md text-[color:var(--text-2)] hover:text-[color:var(--text)] hover:bg-[color:var(--surface-2)] transition-colors" data-testid="reset-new-toggle">
                  {showNew ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>

              <label className="block text-sm font-medium mb-1.5">Conferma nuova password</label>
              <div className="relative mb-2">
                <input
                  type={showConfirm ? "text" : "password"}
                  className="input-base pr-11"
                  value={confirmPwd}
                  onChange={(e) => setConfirmPwd(e.target.value)}
                  placeholder="Ripeti la nuova password"
                  required
                  autoComplete="new-password"
                  data-testid="reset-confirm-password-input"
                />
                <button type="button" onClick={() => setShowConfirm((s) => !s)} tabIndex={-1} className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-md text-[color:var(--text-2)] hover:text-[color:var(--text)] hover:bg-[color:var(--surface-2)] transition-colors" data-testid="reset-confirm-toggle">
                  {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>

              {error && <div className="mt-3 text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="reset-error">{error}</div>}

              <button type="submit" disabled={busy || !token} className="btn-primary w-full justify-center mt-6" data-testid="reset-submit-button">
                {busy ? "Aggiornamento…" : "Salva nuova password"}
              </button>

              <Link to="/login" className="mt-5 flex items-center justify-center gap-1.5 text-sm text-[color:var(--text-2)] hover:text-[color:var(--primary)] transition-colors" data-testid="reset-back-link">
                <ArrowLeft size={13} /> Torna al login
              </Link>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
