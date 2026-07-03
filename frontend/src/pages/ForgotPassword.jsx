import React, { useState } from "react";
import { Link } from "react-router-dom";
import { api, formatApiError } from "@/lib/api";
import { ArrowLeft, Mail, Send, CheckCircle2 } from "lucide-react";
import Logo from "@/components/Logo";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setBusy(true);
    try {
      await api.post("/auth/forgot-password", { email });
      setSent(true);
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
            <Mail size={12} /> Recupero password
          </div>
          <h1 className="font-display text-5xl xl:text-6xl font-extrabold tracking-tight leading-[1.02] mb-5">
            Ti riportiamo <br />
            <span style={{ background: "linear-gradient(120deg, #A78BFA 0%, #60A5FA 50%, #2DD4BF 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>subito dentro.</span>
          </h1>
          <p className="text-white/70 text-base leading-relaxed">
            Inserisci l&apos;email del tuo account: ti mandiamo un link sicuro per scegliere una nuova password.
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

          {sent ? (
            <div data-testid="forgot-sent">
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-5" style={{ background: "linear-gradient(135deg,#7C3AED,#2DD4BF)" }}>
                <CheckCircle2 size={26} className="text-white" />
              </div>
              <h2 className="font-display text-3xl font-bold mb-2 tracking-tight">Controlla la tua email</h2>
              <p className="text-[color:var(--text-2)] mb-6 leading-relaxed">
                Se esiste un account associato a <strong className="text-[color:var(--text)]">{email}</strong>, riceverai a breve un&apos;email con il link per reimpostare la password. Il link è valido per 60 minuti.
              </p>
              <p className="text-xs text-[color:var(--text-2)] bg-[color:var(--surface-2)] px-4 py-3 rounded-lg mb-6">
                💡 Non trovi l&apos;email? Controlla la cartella <em>Spam</em> o <em>Promozioni</em>. Il mittente è <strong>booking@prenotika.com</strong>.
              </p>
              <Link to="/login" className="btn-secondary w-full justify-center" data-testid="forgot-back-to-login">
                <ArrowLeft size={14} /> Torna al login
              </Link>
            </div>
          ) : (
            <form onSubmit={submit} data-testid="forgot-form">
              <h2 className="font-display text-3xl font-bold mb-1.5 tracking-tight">Password dimenticata?</h2>
              <p className="text-[color:var(--text-2)] mb-7">Ti mandiamo un link per reimpostarla via email.</p>

              <label className="block text-sm font-medium mb-1.5">Email account</label>
              <input
                type="email"
                className="input-base mb-2"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="nome@studio.it"
                required
                autoComplete="email"
                autoFocus
                data-testid="forgot-email-input"
              />

              {error && <div className="mt-3 text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="forgot-error">{error}</div>}

              <button type="submit" disabled={busy} className="btn-primary w-full justify-center mt-6" data-testid="forgot-submit-button">
                {busy ? "Invio…" : (<><Send size={15} /> Invia link di reset</>)}
              </button>

              <Link to="/login" className="mt-5 flex items-center justify-center gap-1.5 text-sm text-[color:var(--text-2)] hover:text-[color:var(--primary)] transition-colors" data-testid="forgot-back-link">
                <ArrowLeft size={13} /> Torna al login
              </Link>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
