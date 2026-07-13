import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams, Navigate } from "react-router-dom";
import { motion } from "framer-motion";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import Logo from "@/components/Logo";
import { ArrowRight, Mail, KeyRound, RefreshCw, ArrowLeft } from "lucide-react";

const RESEND_COOLDOWN = 45; // seconds

export default function LoginOtp() {
  const { user, refresh } = useAuth();
  const navigate = useNavigate();
  const [sp] = useSearchParams();

  const [phase, setPhase] = useState("email"); // "email" | "code"
  const [email, setEmail] = useState(sp.get("email") || "");
  const [code, setCode] = useState(["", "", "", "", "", ""]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [cooldown, setCooldown] = useState(0);
  const codeRefs = useRef([]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  // Se arrivi con ?email=xxx precompilata, richiedi automaticamente OTP
  useEffect(() => {
    if (sp.get("email") && phase === "email") {
      // trigger auto-request
      void requestOtp(sp.get("email"));
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (user) {
    return <Navigate to={user.role === "super_admin" ? "/studios" : "/dashboard"} replace />;
  }

  const requestOtp = async (targetEmail) => {
    setError(""); setInfo(""); setBusy(true);
    try {
      await api.post("/auth/otp/request", { email: targetEmail || email });
      setPhase("code");
      setInfo(`Codice inviato a ${targetEmail || email}. Controlla la tua email (anche in spam).`);
      setCooldown(RESEND_COOLDOWN);
      setTimeout(() => codeRefs.current[0]?.focus(), 100);
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore nell'invio del codice.");
    } finally { setBusy(false); }
  };

  const onSubmitEmail = (e) => {
    e.preventDefault();
    if (!email.trim()) { setError("Inserisci la tua email."); return; }
    void requestOtp(email);
  };

  const onCodeInput = (idx, val) => {
    const digit = val.replace(/\D/g, "").slice(-1);
    const newCode = [...code];
    newCode[idx] = digit;
    setCode(newCode);
    if (digit && idx < 5) codeRefs.current[idx + 1]?.focus();
  };

  const onCodeKeyDown = (idx, e) => {
    if (e.key === "Backspace" && !code[idx] && idx > 0) {
      codeRefs.current[idx - 1]?.focus();
    }
    if (e.key === "Enter") {
      submitCode();
    }
  };

  const onCodePaste = (e) => {
    const text = (e.clipboardData.getData("text") || "").replace(/\D/g, "").slice(0, 6);
    if (!text) return;
    e.preventDefault();
    const arr = ["", "", "", "", "", ""];
    for (let i = 0; i < text.length; i++) arr[i] = text[i];
    setCode(arr);
    const nextIdx = Math.min(text.length, 5);
    codeRefs.current[nextIdx]?.focus();
  };

  const submitCode = async () => {
    const codeStr = code.join("");
    if (codeStr.length !== 6) { setError("Inserisci tutte e 6 le cifre."); return; }
    setError(""); setBusy(true);
    try {
      const { data } = await api.post("/auth/otp/verify", { email, code: codeStr });
      localStorage.setItem("eh_token", data.access_token);
      if (refresh) await refresh();
      navigate(data.user.role === "super_admin" ? "/studios" : "/dashboard");
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Codice non valido.");
      setCode(["", "", "", "", "", ""]);
      setTimeout(() => codeRefs.current[0]?.focus(), 50);
    } finally { setBusy(false); }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2 relative overflow-hidden" data-testid="login-otp-page">
      {/* Left visual */}
      <div className="hidden lg:flex relative items-end p-12 overflow-hidden" style={{ background: "linear-gradient(160deg, #0F172A 0%, #1E1B4B 45%, #0F172A 100%)" }}>
        <div className="anim-blob" style={{ background: "#2DD4BF", width: 380, height: 380, top: "-60px", left: "-80px" }} />
        <div className="anim-blob" style={{ background: "#7C3AED", width: 320, height: 320, bottom: "-80px", right: "-60px", animationDelay: "3s" }} />
        <div className="absolute inset-0 opacity-[0.06]" style={{ backgroundImage: "radial-gradient(circle at 1px 1px, #fff 1px, transparent 0)", backgroundSize: "28px 28px" }} />
        <div className="relative z-10 text-white max-w-md">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-md border border-white/15 text-xs tracking-[0.18em] uppercase font-semibold mb-7">
            <span className="w-1.5 h-1.5 rounded-full bg-[#2DD4BF] animate-pulse" /> Accesso senza password
          </div>
          <h1 className="font-display text-5xl xl:text-6xl font-extrabold tracking-tight leading-[1.02] mb-5">
            Bastano <br />
            <span style={{ background: "linear-gradient(120deg, #A78BFA 0%, #60A5FA 50%, #2DD4BF 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text" }}>6 cifre</span> <br />
            per entrare.
          </h1>
          <p className="text-white/70 text-base leading-relaxed">
            Ti mandiamo un codice via email. Niente password da ricordare, nessun rischio, accesso immediato.
          </p>
        </div>
      </div>

      {/* Form */}
      <div className="flex items-center justify-center p-6 sm:p-10 relative">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="w-full max-w-md">
          <div className="flex items-center gap-3 mb-9">
            <Logo size={44} />
            <div>
              <div className="font-display text-xl font-bold leading-none tracking-tight">Prenotika</div>
              <div className="text-[10px] text-[color:var(--text-2)] tracking-[0.22em] uppercase mt-1">Smart Booking</div>
            </div>
          </div>

          {phase === "email" ? (
            <form onSubmit={onSubmitEmail} data-testid="otp-email-form">
              <h2 className="font-display text-3xl font-bold mb-1.5 tracking-tight">Accedi con codice</h2>
              <p className="text-[color:var(--text-2)] mb-7">Ti invieremo un codice a 6 cifre via email.</p>
              <label className="block text-sm font-medium mb-1.5">Email</label>
              <input type="email" required className="input-base mb-2" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="nome@studio.it" data-testid="otp-email-input" autoComplete="email" />
              {error && <div className="mt-3 text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="otp-error">{error}</div>}
              <button type="submit" disabled={busy} className="btn-primary w-full justify-center mt-6" data-testid="otp-request-button">
                {busy ? "Invio…" : (<><Mail size={15} /> Invia codice</>)}
              </button>
              <div className="mt-5 text-center">
                <a href="/login" className="text-sm text-[color:var(--text-2)] hover:text-[color:var(--primary)] transition-colors inline-flex items-center gap-1.5" data-testid="otp-back-login">
                  <ArrowLeft size={13} /> Torna al login con password
                </a>
              </div>
            </form>
          ) : (
            <div data-testid="otp-code-form">
              <button type="button" onClick={() => { setPhase("email"); setCode(["","","","","",""]); setError(""); }} className="text-sm text-[color:var(--text-2)] hover:text-[color:var(--primary)] inline-flex items-center gap-1.5 mb-5" data-testid="otp-change-email">
                <ArrowLeft size={13} /> Cambia email
              </button>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[color:var(--primary)]/10 text-[color:var(--primary)] text-xs tracking-[0.18em] uppercase font-semibold mb-4">
                <KeyRound size={12} /> Codice inviato
              </div>
              <h2 className="font-display text-3xl font-bold mb-1.5 tracking-tight">Inserisci il codice</h2>
              <p className="text-[color:var(--text-2)] mb-6">Abbiamo inviato un codice a 6 cifre a <strong className="text-[color:var(--text)]">{email}</strong>. Il codice è valido per 10 minuti.</p>

              <div className="flex justify-between gap-2 mb-3">
                {code.map((c, i) => (
                  <input
                    key={i}
                    ref={(el) => { codeRefs.current[i] = el; }}
                    type="text"
                    inputMode="numeric"
                    autoComplete={i === 0 ? "one-time-code" : "off"}
                    maxLength={1}
                    value={c}
                    onChange={(e) => onCodeInput(i, e.target.value)}
                    onKeyDown={(e) => onCodeKeyDown(i, e)}
                    onPaste={i === 0 ? onCodePaste : undefined}
                    className="w-full aspect-square text-center text-2xl font-mono font-bold border border-[color:var(--border)] rounded-xl bg-white focus:border-[color:var(--primary)] focus:ring-2 focus:ring-[color:var(--primary)]/20 outline-none transition-all"
                    data-testid={`otp-digit-${i}`}
                  />
                ))}
              </div>
              {info && !error && <div className="text-xs text-[color:var(--text-2)]" data-testid="otp-info">{info}</div>}
              {error && <div className="mt-3 text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="otp-error">{error}</div>}

              <button onClick={submitCode} disabled={busy || code.join("").length !== 6} className="btn-primary w-full justify-center mt-5" data-testid="otp-verify-button">
                {busy ? "Verifica…" : (<>Verifica e accedi <ArrowRight size={15} /></>)}
              </button>

              <div className="mt-4 flex items-center justify-between text-xs text-[color:var(--text-2)]">
                <button
                  type="button"
                  disabled={cooldown > 0 || busy}
                  onClick={() => requestOtp(email)}
                  className="inline-flex items-center gap-1.5 hover:text-[color:var(--primary)] disabled:opacity-40 transition-colors"
                  data-testid="otp-resend-button"
                >
                  <RefreshCw size={12} /> {cooldown > 0 ? `Reinvia tra ${cooldown}s` : "Reinvia codice"}
                </button>
                <a href="/login" className="hover:text-[color:var(--primary)] transition-colors">Usa password</a>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
