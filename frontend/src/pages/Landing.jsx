import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { api, formatApiError } from "@/lib/api";
import Logo from "@/components/Logo";
import { ArrowRight, CalendarCheck2, Users2, FileText, BellRing, Sparkles, Mail, ShieldCheck, CheckCircle2 } from "lucide-react";

const TIPOLOGIE = [
  { v: "centro_studi", label: "Centro studi / formazione" },
  { v: "studio_legale", label: "Studio legale" },
  { v: "studio_medico", label: "Studio medico" },
  { v: "altro", label: "Altro" },
];

export default function Landing() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ nome: "", email: "", telefono: "", tipologia: "centro_studi", studio: "", messaggio: "" });
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      await api.post("/leads", form);
      setSent(true);
      setForm({ nome: "", email: "", telefono: "", tipologia: "centro_studi", studio: "", messaggio: "" });
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore nell'invio. Riprova.");
    } finally { setBusy(false); }
  };

  return (
    <div className="min-h-screen bg-[color:var(--bg)] text-[color:var(--text)]" data-testid="landing-page">
      {/* NAV */}
      <header className="sticky top-0 z-30 backdrop-blur-md bg-white/70 border-b border-[color:var(--border)]">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-3.5 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5" data-testid="landing-logo-home">
            <Logo size={36} />
            <div>
              <div className="font-display text-lg font-bold leading-none tracking-tight">Prenotika</div>
              <div className="text-[9px] text-[color:var(--text-2)] tracking-[0.22em] uppercase mt-1">Smart Booking</div>
            </div>
          </Link>
          <nav className="flex items-center gap-3 sm:gap-5">
            <a href="#features" className="hidden sm:inline text-sm text-[color:var(--text-2)] hover:text-[color:var(--text)] font-medium">Funzioni</a>
            <a href="#chi" className="hidden sm:inline text-sm text-[color:var(--text-2)] hover:text-[color:var(--text)] font-medium">Per chi</a>
            <a href="#contatti" className="hidden sm:inline text-sm text-[color:var(--text-2)] hover:text-[color:var(--text)] font-medium">Contatti</a>
            {user ? (
              <button onClick={() => navigate("/dashboard")} className="btn-primary" data-testid="landing-go-app-btn"><ArrowRight size={14} /> Apri dashboard</button>
            ) : (
              <Link to="/login" className="btn-primary" data-testid="landing-login-btn"><ArrowRight size={14} /> Accedi</Link>
            )}
          </nav>
        </div>
      </header>

      {/* HERO */}
      <section className="relative overflow-hidden">
        <div className="anim-blob" style={{ background: "#7C3AED", width: 480, height: 480, top: "-160px", left: "-120px" }} />
        <div className="anim-blob" style={{ background: "#2DD4BF", width: 420, height: 420, bottom: "-180px", right: "-120px", animationDelay: "3s" }} />
        <div className="anim-blob" style={{ background: "#60A5FA", width: 340, height: 340, top: "30%", left: "55%", animationDelay: "6s", opacity: 0.4 }} />

        <div className="relative max-w-6xl mx-auto px-5 sm:px-8 py-16 sm:py-24">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white border border-[color:var(--border)] text-xs tracking-[0.18em] uppercase font-semibold mb-6 anim-fade-up">
              <Sparkles size={12} className="text-[color:var(--primary)]" /> Nuovo · per studi e professionisti
            </div>
            <h1 className="font-display text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.02] mb-6 anim-fade-up" style={{ animationDelay: "0.05s" }}>
              La gestione <span className="gradient-text">intelligente</span><br />degli appuntamenti.
            </h1>
            <p className="text-lg text-[color:var(--text-2)] max-w-2xl mb-9 leading-relaxed anim-fade-up" style={{ animationDelay: "0.1s" }}>
              Tutte le agende del tuo studio, in un&apos;unica piattaforma. Organizza il tempo. Coordina il team. Ottimizza il lavoro.
            </p>
            <div className="flex flex-wrap gap-3 anim-fade-up" style={{ animationDelay: "0.15s" }}>
              <a href="#contatti" className="btn-primary" data-testid="landing-cta-contatti"><Mail size={15} /> Richiedi una demo</a>
              {user ? (
                <button onClick={() => navigate("/dashboard")} className="btn-secondary"><ArrowRight size={14} /> Apri dashboard</button>
              ) : (
                <Link to="/login" className="btn-secondary"><ArrowRight size={14} /> Hai già un account? Accedi</Link>
              )}
            </div>

            <div className="mt-14 grid grid-cols-2 sm:grid-cols-4 gap-6 max-w-3xl anim-fade-up" style={{ animationDelay: "0.2s" }}>
              {[
                { k: "Multi-tenant", v: "Studi isolati" },
                { k: "Orari custom", v: "Per professionista" },
                { k: "Email + ICS", v: "Calendario automatico" },
                { k: "Mobile-first", v: "Sempre con te" },
              ].map((s) => (
                <div key={s.k} className="border-l-2 border-[color:var(--primary)]/30 pl-3">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-[color:var(--text-2)] mb-1.5">{s.k}</div>
                  <div className="text-sm font-semibold">{s.v}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className="max-w-6xl mx-auto px-5 sm:px-8 py-20">
        <div className="label-eyebrow mb-2">Funzioni</div>
        <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight mb-3">Tutto ciò che serve per gestire i tuoi appuntamenti.</h2>
        <p className="text-[color:var(--text-2)] max-w-2xl mb-12">Una piattaforma pensata per chi gestisce tempo e persone ogni giorno: segretarie, professionisti, centri studi.</p>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {[
            { icon: CalendarCheck2, title: "Calendario per professionista", desc: "Ogni docente/avvocato/medico ha il proprio calendario con vista mese, settimana e giorno." },
            { icon: Users2, title: "Gestione clienti & team", desc: "Anagrafica, materie e relazioni N:M. Ogni operatore vede solo i propri appuntamenti." },
            { icon: BellRing, title: "Notifiche email automatiche", desc: "Conferma, promemoria 24h prima e disdetta inviate con allegato calendario .ics." },
            { icon: FileText, title: "Report PDF brandizzati", desc: "Esporta planning giorno/settimana/mese con carta intestata personalizzata." },
            { icon: ShieldCheck, title: "Multi-tenant sicuro", desc: "Ogni studio è isolato. JWT, ruoli (super admin / admin / docente)." },
            { icon: Sparkles, title: "Ferie & eccezioni", desc: "Imposta i giorni di chiusura e le ferie del singolo professionista in pochi click." },
          ].map((f) => (
            <div key={f.title} className="kpi-card">
              <div className="w-11 h-11 rounded-md mb-3 flex items-center justify-center" style={{ background: "var(--grad-soft)" }}>
                <f.icon size={20} className="text-[color:var(--primary)]" strokeWidth={1.7} />
              </div>
              <div className="font-display font-bold text-base mb-1">{f.title}</div>
              <p className="text-sm text-[color:var(--text-2)] leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* PER CHI */}
      <section id="chi" className="bg-white border-y border-[color:var(--border)] py-20">
        <div className="max-w-6xl mx-auto px-5 sm:px-8">
          <div className="label-eyebrow mb-2">Per chi è</div>
          <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight mb-12">Una piattaforma. Tre mondi.</h2>
          <div className="grid md:grid-cols-3 gap-5">
            {[
              { tag: "Centri studi", title: "Docenti, alunni, materie", desc: "Gestisci lezioni private, ripetizioni e corsi di gruppo." },
              { tag: "Studi legali", title: "Avvocati, clienti, specializzazioni", desc: "Consulenze, udienze e pratiche tutto in un'unica agenda." },
              { tag: "Studi medici", title: "Medici, pazienti, prestazioni", desc: "Visite, esami e controlli ordinati per ogni professionista." },
            ].map((c, i) => (
              <div key={c.tag} className="rounded-2xl p-6 text-white relative overflow-hidden" style={{ background: ["linear-gradient(135deg,#7C3AED 0%,#A855F7 100%)", "linear-gradient(135deg,#0EA5E9 0%,#60A5FA 100%)", "linear-gradient(135deg,#14B8A6 0%,#2DD4BF 100%)"][i] }}>
                <div className="text-[10px] tracking-[0.22em] uppercase opacity-80 mb-4">{c.tag}</div>
                <div className="font-display text-2xl font-bold mb-2 leading-tight">{c.title}</div>
                <p className="text-sm opacity-90 leading-relaxed">{c.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CONTATTI */}
      <section id="contatti" className="max-w-6xl mx-auto px-5 sm:px-8 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-start">
          <div>
            <div className="label-eyebrow mb-2">Contattaci</div>
            <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight mb-4">Vuoi vedere Prenotika in azione?</h2>
            <p className="text-[color:var(--text-2)] mb-7 leading-relaxed">
              Raccontaci del tuo studio: ti contatteremo entro 24h per una demo personalizzata e un accesso di prova.
            </p>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <CheckCircle2 size={18} className="text-[color:var(--secondary)] mt-0.5 shrink-0" />
                <div><div className="font-semibold text-sm">Demo personalizzata</div><div className="text-xs text-[color:var(--text-2)]">30 minuti, sulla tua realtà.</div></div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 size={18} className="text-[color:var(--secondary)] mt-0.5 shrink-0" />
                <div><div className="font-semibold text-sm">Setup guidato</div><div className="text-xs text-[color:var(--text-2)]">Migrazione gratuita dei tuoi dati.</div></div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 size={18} className="text-[color:var(--secondary)] mt-0.5 shrink-0" />
                <div><div className="font-semibold text-sm">Supporto rapido</div><div className="text-xs text-[color:var(--text-2)]">Email diretta al nostro team.</div></div>
              </div>
            </div>
          </div>

          <form onSubmit={submit} className="surface-card p-6 sm:p-7 anim-fade-up" data-testid="lead-form">
            {sent ? (
              <div className="text-center py-8" data-testid="lead-form-success">
                <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-[color:var(--secondary)]/15 flex items-center justify-center"><CheckCircle2 size={28} className="text-[color:var(--success)]" /></div>
                <h3 className="font-display text-xl font-bold mb-2">Richiesta inviata!</h3>
                <p className="text-sm text-[color:var(--text-2)] mb-5">Ti contatteremo entro 24h al recapito che ci hai indicato.</p>
                <button type="button" onClick={() => setSent(false)} className="btn-secondary" data-testid="lead-form-reset">Invia un&apos;altra richiesta</button>
              </div>
            ) : (
              <>
                <h3 className="font-display text-xl font-bold mb-1">Richiedi informazioni</h3>
                <p className="text-xs text-[color:var(--text-2)] mb-5">I campi con * sono obbligatori.</p>
                <div className="space-y-3.5">
                  <div className="grid sm:grid-cols-2 gap-3">
                    <div><label className="label-eyebrow block mb-1.5">Nome e cognome *</label><input required className="input-base" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} data-testid="lead-nome" /></div>
                    <div><label className="label-eyebrow block mb-1.5">Email *</label><input required type="email" className="input-base" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} data-testid="lead-email" /></div>
                  </div>
                  <div className="grid sm:grid-cols-2 gap-3">
                    <div><label className="label-eyebrow block mb-1.5">Telefono</label><input className="input-base" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} data-testid="lead-telefono" /></div>
                    <div>
                      <label className="label-eyebrow block mb-1.5">Tipo di studio</label>
                      <select className="input-base" value={form.tipologia} onChange={(e) => setForm({ ...form, tipologia: e.target.value })} data-testid="lead-tipologia">
                        {TIPOLOGIE.map((t) => <option key={t.v} value={t.v}>{t.label}</option>)}
                      </select>
                    </div>
                  </div>
                  <div><label className="label-eyebrow block mb-1.5">Nome del centro</label><input className="input-base" value={form.studio} onChange={(e) => setForm({ ...form, studio: e.target.value })} data-testid="lead-studio" /></div>
                  <div><label className="label-eyebrow block mb-1.5">Messaggio</label><textarea rows={3} className="input-base resize-none" value={form.messaggio} onChange={(e) => setForm({ ...form, messaggio: e.target.value })} placeholder="Raccontaci brevemente come gestisci oggi gli appuntamenti..." data-testid="lead-messaggio" /></div>
                </div>
                {error && <div className="text-sm text-[color:var(--error)] mt-3" data-testid="lead-form-error">{error}</div>}
                <button type="submit" disabled={busy} className="btn-primary w-full justify-center mt-5" data-testid="lead-submit-button">
                  {busy ? "Invio in corso…" : (<><Mail size={15} /> Invia richiesta</>)}
                </button>
                <p className="text-[10px] text-[color:var(--text-2)] text-center mt-3">Risposta entro 24h · Nessun impegno · Tuoi dati al sicuro</p>
              </>
            )}
          </form>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-[color:var(--border)] bg-white">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <Logo size={28} />
            <div className="text-sm font-display font-bold">Prenotika</div>
            <span className="text-[10px] tracking-[0.22em] uppercase text-[color:var(--text-2)] ml-2">Smart Booking</span>
          </div>
          <div className="text-xs text-[color:var(--text-2)]">© {new Date().getFullYear()} Prenotika · La gestione intelligente degli appuntamenti.</div>
        </div>
      </footer>
    </div>
  );
}
