import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { api, formatApiError } from "@/lib/api";
import { TIPOLOGIE } from "@/lib/tipologia";
import Logo from "@/components/Logo";
import {
  ArrowRight, ArrowLeft, CheckCircle2, Upload, Trash2, Image as ImageIcon,
  Sparkles, Rocket, KeyRound, SkipForward,
} from "lucide-react";

const MAX_LOGO_BYTES = 600 * 1024;

const STEPS = [
  { key: "welcome", label: "Benvenuto" },
  { key: "studio", label: "Il tuo studio" },
  { key: "brand", label: "Brand & logo" },
  { key: "password", label: "Password (opzionale)" },
  { key: "done", label: "Fatto!" },
];

export default function OnboardingSetup() {
  const [sp] = useSearchParams();
  const token = sp.get("token") || "";
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [invalid, setInvalid] = useState("");
  const [ctx, setCtx] = useState({ user: null, studio: null }); // dati caricati dal token
  const [stepIdx, setStepIdx] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    studio_nome: "",
    tipologia: "centro_studi",
    sede: "",
    telefono: "",
    piva: "",
    comunicazioni: "",
    logo_base64: "",
    new_password: "",
    confirm_password: "",
  });
  const fileRef = useRef(null);

  useEffect(() => {
    if (!token) {
      setInvalid("Token mancante nell'URL.");
      setLoading(false);
      return;
    }
    (async () => {
      try {
        const { data } = await api.get(`/onboarding/verify-token`, { params: { token } });
        // Salva il JWT temporaneo così tutte le chiamate autenticate durante il wizard funzionano
        if (data.access_token) {
          localStorage.setItem("eh_token", data.access_token);
        }
        setCtx({ user: data.user, studio: data.studio });
        setForm((f) => ({
          ...f,
          studio_nome: data.studio?.nome || "",
          tipologia: data.studio?.tipologia || "centro_studi",
          sede: data.studio?.sede || "",
          telefono: data.studio?.telefono || "",
          piva: data.studio?.piva || "",
          comunicazioni: data.studio?.comunicazioni || "",
          logo_base64: data.studio?.logo_base64 || "",
        }));
      } catch (err) {
        setInvalid(formatApiError(err?.response?.data?.detail) || "Link non valido o scaduto.");
      } finally {
        setLoading(false);
      }
    })();
  }, [token]);

  const onLogoChange = (e) => {
    setError("");
    const file = e.target.files?.[0];
    if (!file) return;
    if (!/^image\/(png|jpeg|jpg|webp|svg\+xml)$/.test(file.type)) {
      setError("Formato non supportato. Usa PNG, JPG, WEBP o SVG.");
      e.target.value = ""; return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = String(reader.result || "");
      const payload = dataUrl.split(",")[1] || "";
      const approxBytes = Math.floor(payload.length * 0.75);
      if (approxBytes > MAX_LOGO_BYTES) {
        setError(`Immagine troppo grande (${Math.round(approxBytes/1024)}KB). Massimo 600KB.`);
        if (fileRef.current) fileRef.current.value = "";
        return;
      }
      setForm((f) => ({ ...f, logo_base64: dataUrl }));
    };
    reader.readAsDataURL(file);
  };

  const next = () => setStepIdx((i) => Math.min(STEPS.length - 1, i + 1));
  const prev = () => setStepIdx((i) => Math.max(0, i - 1));

  const complete = async ({ skipPassword = false } = {}) => {
    setError(""); setBusy(true);
    try {
      const payload = {
        token,
        studio_nome: form.studio_nome.trim() || undefined,
        tipologia: form.tipologia,
        sede: form.sede,
        telefono: form.telefono,
        piva: form.piva,
        comunicazioni: form.comunicazioni,
        logo_base64: form.logo_base64,
      };
      if (!skipPassword && form.new_password) {
        if (form.new_password.length < 8) throw new Error("La password deve avere almeno 8 caratteri.");
        if (form.new_password !== form.confirm_password) throw new Error("Le password non coincidono.");
        payload.new_password = form.new_password;
      }
      const { data } = await api.post("/onboarding/complete", payload);
      if (data.access_token) {
        localStorage.setItem("eh_token", data.access_token);
      }
      setStepIdx(STEPS.length - 1);
      // Ricarica la pagina per far ripartire il context auth con i nuovi dati studio.
      setTimeout(() => { window.location.href = "/dashboard"; }, 1400);
    } catch (err) {
      setError(err?.message || formatApiError(err?.response?.data?.detail) || "Errore. Riprova.");
    } finally { setBusy(false); }
  };

  const skipAll = async () => {
    // salva solo default e vai in dashboard
    await complete({ skipPassword: true });
  };

  const progress = useMemo(() => ((stepIdx + 1) / STEPS.length) * 100, [stepIdx]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[color:var(--bg)]">
        <div className="text-[color:var(--text-2)] text-sm">Caricamento in corso…</div>
      </div>
    );
  }
  if (invalid) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[color:var(--bg)] p-6">
        <div className="surface-card p-8 max-w-md text-center" data-testid="onboarding-invalid">
          <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-[color:var(--error)]/10 flex items-center justify-center">
            <KeyRound size={26} className="text-[color:var(--error)]" />
          </div>
          <h1 className="font-display text-2xl font-bold mb-2">Link non valido</h1>
          <p className="text-sm text-[color:var(--text-2)] mb-5">{invalid}</p>
          <button className="btn-primary w-full justify-center" onClick={() => navigate("/login/otp")} data-testid="onboarding-goto-otp">
            <ArrowRight size={15} /> Accedi con codice OTP
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[color:var(--bg)] relative overflow-hidden" data-testid="onboarding-setup-page">
      {/* Decor bg */}
      <div className="absolute inset-0 pointer-events-none opacity-40" style={{ backgroundImage: "radial-gradient(circle at 15% 15%, rgba(124,58,237,0.15) 0%, transparent 40%), radial-gradient(circle at 85% 85%, rgba(45,212,191,0.15) 0%, transparent 40%)" }} />

      <div className="relative max-w-3xl mx-auto px-5 sm:px-8 py-10 sm:py-14">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <Logo size={36} />
            <div>
              <div className="font-display text-lg font-bold leading-none tracking-tight">Prenotika</div>
              <div className="text-[10px] text-[color:var(--text-2)] tracking-[0.22em] uppercase mt-1">Onboarding</div>
            </div>
          </div>
          {stepIdx < STEPS.length - 1 && (
            <button onClick={skipAll} disabled={busy} className="text-xs text-[color:var(--text-2)] hover:text-[color:var(--primary)] transition-colors flex items-center gap-1.5" data-testid="onboarding-skip-all">
              <SkipForward size={13} /> Salta e vai al dashboard
            </button>
          )}
        </div>

        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-medium text-[color:var(--text-2)]">Step {stepIdx + 1} di {STEPS.length}</div>
            <div className="text-xs font-medium text-[color:var(--primary)]">{STEPS[stepIdx].label}</div>
          </div>
          <div className="w-full h-1.5 bg-[color:var(--surface-2)] rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ background: "linear-gradient(90deg, #7C3AED 0%, #2DD4BF 100%)" }}
              initial={false}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.4, ease: "easeOut" }}
            />
          </div>
        </div>

        <div className="surface-card p-6 sm:p-8" data-testid="onboarding-card">
          <AnimatePresence mode="wait">
            {stepIdx === 0 && (
              <motion.div key="welcome" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.35 }}>
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[color:var(--primary)]/10 text-[color:var(--primary)] text-xs tracking-[0.18em] uppercase font-semibold mb-5">
                  <Sparkles size={12} /> Il tuo spazio è attivo
                </div>
                <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight mb-3">
                  Ciao {ctx.user?.nome || "!"} 👋
                </h1>
                <p className="text-[color:var(--text-2)] text-base leading-relaxed mb-6">
                  Abbiamo attivato <strong className="text-[color:var(--text)]">{ctx.studio?.nome}</strong>. In meno di 2 minuti configuriamo insieme le impostazioni essenziali. Potrai modificare tutto in seguito.
                </p>
                <ul className="space-y-2.5 mb-8">
                  {["Nome e tipologia dello studio", "Logo per report PDF", "Password personale (opzionale)"].map((t) => (
                    <li key={t} className="flex items-start gap-2 text-sm text-[color:var(--text)]">
                      <CheckCircle2 size={17} className="text-[color:var(--success)] mt-0.5 shrink-0" />
                      <span>{t}</span>
                    </li>
                  ))}
                </ul>
                <div className="flex flex-wrap gap-3">
                  <button onClick={next} className="btn-primary" data-testid="onboarding-welcome-next">
                    Iniziamo <ArrowRight size={15} />
                  </button>
                  <button onClick={skipAll} disabled={busy} className="btn-secondary" data-testid="onboarding-welcome-skip">
                    <SkipForward size={14} /> Salta l&apos;onboarding
                  </button>
                </div>
              </motion.div>
            )}

            {stepIdx === 1 && (
              <motion.div key="studio" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.35 }}>
                <h2 className="font-display text-2xl sm:text-3xl font-bold tracking-tight mb-2">Parlaci del tuo studio</h2>
                <p className="text-sm text-[color:var(--text-2)] mb-6">La tipologia adatta automaticamente la terminologia in tutta l&apos;app (studenti/clienti/pazienti).</p>
                <div className="grid sm:grid-cols-2 gap-4">
                  <div className="sm:col-span-2">
                    <label className="label-eyebrow block mb-1.5">Nome dello studio *</label>
                    <input className="input-base" value={form.studio_nome} onChange={(e) => setForm({ ...form, studio_nome: e.target.value })} data-testid="onb-studio-nome" required />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="label-eyebrow block mb-1.5">Tipologia *</label>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5" data-testid="onb-tipologia-choices">
                      {TIPOLOGIE.map((t) => (
                        <button
                          key={t.value}
                          type="button"
                          onClick={() => setForm({ ...form, tipologia: t.value })}
                          className={`p-3.5 rounded-xl border text-left transition-all ${form.tipologia === t.value ? "border-[color:var(--primary)] bg-[color:var(--primary)]/5 shadow-sm" : "border-[color:var(--border)] hover:border-[color:var(--text-2)]"}`}
                          data-testid={`onb-tipologia-${t.value}`}
                        >
                          <div className="font-semibold text-sm text-[color:var(--text)]">{t.label}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="label-eyebrow block mb-1.5">Sede</label>
                    <input className="input-base" value={form.sede} onChange={(e) => setForm({ ...form, sede: e.target.value })} data-testid="onb-sede" placeholder="es. Milano" />
                  </div>
                  <div>
                    <label className="label-eyebrow block mb-1.5">Telefono</label>
                    <input className="input-base" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} data-testid="onb-telefono" />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="label-eyebrow block mb-1.5">P.IVA</label>
                    <input className="input-base" value={form.piva} onChange={(e) => setForm({ ...form, piva: e.target.value })} data-testid="onb-piva" />
                  </div>
                </div>
                <div className="flex justify-between mt-8">
                  <button onClick={prev} className="btn-secondary" data-testid="onb-back-1"><ArrowLeft size={15} /> Indietro</button>
                  <button onClick={next} disabled={!form.studio_nome.trim()} className="btn-primary" data-testid="onb-next-1">Continua <ArrowRight size={15} /></button>
                </div>
              </motion.div>
            )}

            {stepIdx === 2 && (
              <motion.div key="brand" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.35 }}>
                <h2 className="font-display text-2xl sm:text-3xl font-bold tracking-tight mb-2">Logo & comunicazioni</h2>
                <p className="text-sm text-[color:var(--text-2)] mb-6">Il logo appare in cima ai report PDF. Puoi caricarlo anche dopo dalle Impostazioni.</p>
                <div className="flex items-start gap-5 flex-wrap mb-6">
                  <div className="w-32 h-32 rounded-xl border border-[color:var(--border)] bg-[color:var(--surface-2)] flex items-center justify-center overflow-hidden shrink-0" data-testid="onb-logo-preview">
                    {form.logo_base64 ? (
                      <img src={form.logo_base64} alt="Logo del centro" className="max-w-full max-h-full object-contain" />
                    ) : (
                      <ImageIcon size={30} className="text-[color:var(--text-3)]" />
                    )}
                  </div>
                  <div className="flex flex-col gap-2 flex-1 min-w-[200px]">
                    <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp,image/svg+xml" onChange={onLogoChange} className="hidden" data-testid="onb-logo-file" />
                    <button type="button" onClick={() => fileRef.current?.click()} className="btn-secondary" data-testid="onb-logo-upload">
                      <Upload size={14} /> {form.logo_base64 ? "Sostituisci logo" : "Carica logo"}
                    </button>
                    {form.logo_base64 && (
                      <button type="button" onClick={() => setForm({ ...form, logo_base64: "" })} className="btn-secondary text-[color:var(--error)]" data-testid="onb-logo-remove">
                        <Trash2 size={14} /> Rimuovi
                      </button>
                    )}
                    <div className="text-xs text-[color:var(--text-2)]">PNG/JPG/WEBP/SVG · Max 600KB · Consigliato 600×600</div>
                  </div>
                </div>
                <div>
                  <label className="label-eyebrow block mb-1.5">Comunicazioni in calce ai PDF</label>
                  <textarea rows={5} className="input-base font-mono text-sm" placeholder={"Es.\n- Segreteria aperta dal lunedì al venerdì, 9-18\n- Disdette entro 24h"} value={form.comunicazioni} onChange={(e) => setForm({ ...form, comunicazioni: e.target.value })} data-testid="onb-comunicazioni" />
                </div>
                {error && <div className="mt-3 text-sm text-[color:var(--error)]" data-testid="onb-brand-error">{error}</div>}
                <div className="flex justify-between mt-8">
                  <button onClick={prev} className="btn-secondary" data-testid="onb-back-2"><ArrowLeft size={15} /> Indietro</button>
                  <button onClick={next} className="btn-primary" data-testid="onb-next-2">Continua <ArrowRight size={15} /></button>
                </div>
              </motion.div>
            )}

            {stepIdx === 3 && (
              <motion.div key="password" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.35 }}>
                <h2 className="font-display text-2xl sm:text-3xl font-bold tracking-tight mb-2">Imposta una password (opzionale)</h2>
                <p className="text-sm text-[color:var(--text-2)] mb-6">Puoi accedere sempre con codice OTP inviato via email. In alternativa imposta una password personale per accessi più veloci.</p>
                <div className="space-y-4 max-w-md">
                  <div>
                    <label className="label-eyebrow block mb-1.5">Nuova password</label>
                    <input type="password" className="input-base" value={form.new_password} onChange={(e) => setForm({ ...form, new_password: e.target.value })} data-testid="onb-new-password" autoComplete="new-password" placeholder="min. 8 caratteri" />
                  </div>
                  <div>
                    <label className="label-eyebrow block mb-1.5">Conferma password</label>
                    <input type="password" className="input-base" value={form.confirm_password} onChange={(e) => setForm({ ...form, confirm_password: e.target.value })} data-testid="onb-confirm-password" autoComplete="new-password" />
                  </div>
                </div>
                {error && <div className="mt-3 text-sm text-[color:var(--error)]" data-testid="onb-password-error">{error}</div>}
                <div className="flex justify-between items-center mt-8 flex-wrap gap-3">
                  <button onClick={prev} className="btn-secondary" data-testid="onb-back-3"><ArrowLeft size={15} /> Indietro</button>
                  <div className="flex flex-wrap gap-2">
                    <button onClick={() => complete({ skipPassword: true })} disabled={busy} className="btn-secondary" data-testid="onb-skip-password">
                      <SkipForward size={14} /> Salta e finisci
                    </button>
                    <button onClick={() => complete({ skipPassword: false })} disabled={busy} className="btn-primary" data-testid="onb-finish">
                      <Rocket size={15} /> {busy ? "Salvataggio…" : "Finisci setup"}
                    </button>
                  </div>
                </div>
              </motion.div>
            )}

            {stepIdx === 4 && (
              <motion.div key="done" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.35 }} className="text-center py-8">
                <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 300, damping: 15 }} className="w-16 h-16 mx-auto mb-5 rounded-full bg-[color:var(--success)]/15 flex items-center justify-center">
                  <CheckCircle2 size={32} className="text-[color:var(--success)]" />
                </motion.div>
                <h2 className="font-display text-2xl sm:text-3xl font-bold tracking-tight mb-2">Setup completato!</h2>
                <p className="text-sm text-[color:var(--text-2)] mb-4">Ti stiamo portando al dashboard…</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
