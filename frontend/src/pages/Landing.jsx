import React, { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, useMotionValue, useSpring, useTransform, useScroll, AnimatePresence, useInView } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import { api, formatApiError } from "@/lib/api";
import Logo from "@/components/Logo";
import { ArrowRight, CalendarCheck2, Users2, FileText, BellRing, Sparkles, Mail, ShieldCheck, CheckCircle2, Check, Zap, Plane, Clock, ChevronDown, Star } from "lucide-react";

const TIPOLOGIE = [
  { v: "centro_studi", label: "Centro studi / formazione" },
  { v: "studio_legale", label: "Studio legale" },
  { v: "studio_medico", label: "Studio medico" },
  { v: "altro", label: "Altro" },
];

/* ================= Reusable bits ================= */

const SectionHeader = ({ eyebrow, title, sub, light = false }) => (
  <div className="mb-12 max-w-2xl">
    <div className={`label-eyebrow mb-2 ${light ? "text-white/60" : ""}`}>{eyebrow}</div>
    <motion.h2
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.4 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className={`font-display text-3xl sm:text-5xl font-bold tracking-tight mb-3 ${light ? "text-white" : ""}`}
    >
      {title}
    </motion.h2>
    {sub && <p className={light ? "text-white/65 max-w-xl" : "text-[color:var(--text-2)] max-w-xl"}>{sub}</p>}
  </div>
);

const Counter = ({ value, suffix = "", duration = 2 }) => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, amount: 0.5 });
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!inView) return;
    let start = 0;
    const end = value;
    const t0 = performance.now();
    let raf;
    const tick = (now) => {
      const p = Math.min(1, (now - t0) / (duration * 1000));
      const eased = 1 - Math.pow(1 - p, 3);
      setN(Math.floor(start + (end - start) * eased));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, value, duration]);
  return <span ref={ref}>{n.toLocaleString("it-IT")}{suffix}</span>;
};

const MagneticButton = ({ children, className = "", onClick, ...props }) => {
  const ref = useRef(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const sx = useSpring(x, { stiffness: 200, damping: 18, mass: 0.4 });
  const sy = useSpring(y, { stiffness: 200, damping: 18, mass: 0.4 });

  const onMove = (e) => {
    const r = ref.current.getBoundingClientRect();
    const cx = e.clientX - r.left - r.width / 2;
    const cy = e.clientY - r.top - r.height / 2;
    x.set(cx * 0.35);
    y.set(cy * 0.35);
  };
  const onLeave = () => { x.set(0); y.set(0); };
  return (
    <motion.button
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      style={{ x: sx, y: sy }}
      onClick={onClick}
      className={className}
      {...props}
    >
      {children}
    </motion.button>
  );
};

const TiltCard = ({ children, className = "", testid }) => {
  const ref = useRef(null);
  const mx = useMotionValue(0); const my = useMotionValue(0);
  const rx = useSpring(useTransform(my, [-50, 50], [8, -8]), { stiffness: 200, damping: 18 });
  const ry = useSpring(useTransform(mx, [-50, 50], [-8, 8]), { stiffness: 200, damping: 18 });

  const onMove = (e) => {
    const r = ref.current.getBoundingClientRect();
    mx.set(e.clientX - r.left - r.width / 2);
    my.set(e.clientY - r.top - r.height / 2);
  };
  const onLeave = () => { mx.set(0); my.set(0); };
  return (
    <motion.div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      style={{ rotateX: rx, rotateY: ry, transformStyle: "preserve-3d" }}
      className={className}
      data-testid={testid}
    >
      {children}
    </motion.div>
  );
};

/* ================ Page ================= */

export default function Landing() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ nome: "", email: "", telefono: "", tipologia: "centro_studi", studio: "", messaggio: "", piano_interesse: "" });
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  /* Spotlight effect hero */
  const heroRef = useRef(null);
  const sx = useMotionValue(50); const sy = useMotionValue(30);
  const ssx = useSpring(sx, { stiffness: 100, damping: 25 });
  const ssy = useSpring(sy, { stiffness: 100, damping: 25 });
  const spotlightBg = useTransform(
    [ssx, ssy],
    ([x, y]) => `radial-gradient(circle 480px at ${x}% ${y}%, rgba(124,58,237,0.18), transparent 60%)`
  );
  const onHeroMove = (e) => {
    if (!heroRef.current) return;
    const r = heroRef.current.getBoundingClientRect();
    sx.set(((e.clientX - r.left) / r.width) * 100);
    sy.set(((e.clientY - r.top) / r.height) * 100);
  };

  /* Scroll parallax on hero */
  const { scrollY } = useScroll();
  const heroY = useTransform(scrollY, [0, 600], [0, 80]);

  /* Ticker mock data */
  const tickerItems = [
    { name: "Centro Studi Arco Iris", what: "ha confermato 4 lezioni della settimana", when: "30 sec fa" },
    { name: "Sara M.", what: "ha prenotato una visita di controllo", when: "1 min fa" },
    { name: "Studio Legale Conti", what: "ha generato il report mensile", when: "4 min fa" },
    { name: "Dr.ssa Marini", what: "ha aggiunto un nuovo paziente", when: "6 min fa" },
    { name: "Scuola di Lingue Roma", what: "ha bookato 12 lezioni ricorrenti", when: "9 min fa" },
  ];
  const [tickerIdx, setTickerIdx] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setTickerIdx((i) => (i + 1) % tickerItems.length), 2800);
    return () => clearInterval(t);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectPlan = (planName) => {
    setForm((f) => ({ ...f, piano_interesse: planName, messaggio: f.messaggio || `Sono interessato al piano ${planName}. Vorrei attivare la prova gratuita di 14 giorni.` }));
    const el = document.getElementById("contatti");
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      await api.post("/leads", form);
      setSent(true);
      setForm({ nome: "", email: "", telefono: "", tipologia: "centro_studi", studio: "", messaggio: "", piano_interesse: "" });
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore nell'invio. Riprova.");
    } finally { setBusy(false); }
  };

  return (
    <div className="min-h-screen bg-[color:var(--bg)] text-[color:var(--text)] overflow-x-hidden" data-testid="landing-page">
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
            <a href="#prezzi" className="hidden sm:inline text-sm text-[color:var(--text-2)] hover:text-[color:var(--text)] font-medium">Prezzi</a>
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

      {/* ==================== HERO with Aurora, Spotlight, Floating cards ==================== */}
      <section
        ref={heroRef}
        onMouseMove={onHeroMove}
        className="relative overflow-hidden pt-12 pb-32 sm:pt-20 sm:pb-44"
        style={{ background: "linear-gradient(180deg,#0B1020 0%,#0F172A 100%)" }}
      >
        {/* Aurora gradient mesh */}
        <div className="aurora-mesh" />
        {/* Animated dot grid */}
        <div className="absolute inset-0 opacity-[0.08]" style={{ backgroundImage: "radial-gradient(circle at 1px 1px,#fff 1px, transparent 0)", backgroundSize: "32px 32px" }} />
        {/* Spotlight following cursor */}
        <motion.div className="pointer-events-none absolute inset-0" style={{ background: spotlightBg }} />
        {/* Big floating blobs */}
        <div className="anim-blob" style={{ background: "#7C3AED", width: 520, height: 520, top: "-150px", left: "-100px", opacity: 0.45 }} />
        <div className="anim-blob" style={{ background: "#2DD4BF", width: 420, height: 420, bottom: "-120px", right: "-80px", opacity: 0.35, animationDelay: "3s" }} />

        <div className="relative max-w-6xl mx-auto px-5 sm:px-8 grid lg:grid-cols-[1.15fr_1fr] gap-12 items-center">
          {/* Left: Headline */}
          <motion.div style={{ y: heroY }}>
            <motion.div
              initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/8 border border-white/15 backdrop-blur text-xs tracking-[0.18em] uppercase font-semibold mb-6 text-white"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-[#2DD4BF] animate-pulse" /> Versione 2026 · Nuova UI
            </motion.div>

            <h1 className="font-display text-5xl sm:text-7xl lg:text-[5.5rem] font-extrabold tracking-tight leading-[0.98] mb-7 text-white">
              {"La gestione".split(" ").map((w, i) => (
                <motion.span
                  key={i}
                  className="inline-block mr-[0.25em]"
                  initial={{ opacity: 0, y: 40, rotateX: -25 }} animate={{ opacity: 1, y: 0, rotateX: 0 }}
                  transition={{ delay: 0.1 + i * 0.07, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
                >{w}</motion.span>
              ))}<br />
              <motion.span
                className="inline-block"
                initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.35, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
                style={{ background: "linear-gradient(120deg,#A78BFA 0%,#60A5FA 45%,#2DD4BF 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text" }}
              >intelligente</motion.span>{" "}
              <motion.span
                className="inline-block text-white"
                initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
              >degli</motion.span><br />
              <motion.span
                className="inline-block text-white"
                initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.65, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
              >appuntamenti.</motion.span>
            </h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.85, duration: 0.7 }}
              className="text-lg text-white/70 max-w-xl mb-9 leading-relaxed"
            >
              Tutte le agende del tuo studio, in un&apos;unica piattaforma viva.<br />
              Organizza il tempo. Coordina il team. Ottimizza il lavoro.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.95, duration: 0.7 }}
              className="flex flex-wrap gap-3"
            >
              <MagneticButton onClick={() => selectPlan("Pro")} className="btn-primary" data-testid="landing-cta-contatti">
                <Mail size={15} /> Richiedi una demo
              </MagneticButton>
              {user ? (
                <button onClick={() => navigate("/dashboard")} className="btn-secondary" style={{ background: "rgba(255,255,255,0.08)", color: "#fff", borderColor: "rgba(255,255,255,0.15)" }}><ArrowRight size={14} /> Apri dashboard</button>
              ) : (
                <Link to="/login" className="btn-secondary" style={{ background: "rgba(255,255,255,0.08)", color: "#fff", borderColor: "rgba(255,255,255,0.15)" }}><ArrowRight size={14} /> Accedi</Link>
              )}
            </motion.div>

            {/* Live ticker */}
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.15, duration: 0.8 }}
              className="mt-10 surface-glass !bg-white/[0.06] !border-white/15 px-4 py-2.5 rounded-full inline-flex items-center gap-3 text-white text-sm max-w-full overflow-hidden"
              style={{ backdropFilter: "blur(20px)" }}
            >
              <span className="w-2 h-2 rounded-full bg-[#2DD4BF] shrink-0">
                <span className="absolute w-2 h-2 rounded-full bg-[#2DD4BF] animate-ping" style={{ opacity: 0.6 }} />
              </span>
              <AnimatePresence mode="wait">
                <motion.span
                  key={tickerIdx}
                  initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}
                  transition={{ duration: 0.35 }}
                  className="truncate"
                >
                  <span className="font-semibold">{tickerItems[tickerIdx].name}</span>
                  <span className="text-white/70"> {tickerItems[tickerIdx].what}</span>
                  <span className="text-white/40"> · {tickerItems[tickerIdx].when}</span>
                </motion.span>
              </AnimatePresence>
            </motion.div>
          </motion.div>

          {/* Right: Floating mock cards */}
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6, duration: 1 }}
            className="relative hidden lg:block h-[520px]"
          >
            <motion.div
              className="absolute top-0 right-0 surface-glass !bg-white/95 p-4 w-[260px] rounded-2xl shadow-2xl"
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
              style={{ boxShadow: "0 30px 60px -20px rgba(124,58,237,0.45)" }}
            >
              <div className="flex items-center gap-2 mb-3">
                <div className="w-9 h-9 rounded-full" style={{ background: "var(--grad-brand)" }} />
                <div>
                  <div className="text-xs text-[color:var(--text-2)]">Oggi · 14:30</div>
                  <div className="font-semibold text-sm">Visita controllo</div>
                </div>
                <span className="ml-auto pill pill-success">Conferm.</span>
              </div>
              <div className="text-xs text-[color:var(--text-2)]">Dr. Marco Bianchi · Studio Medico Demo</div>
              <div className="mt-3 flex items-center gap-2 text-[10px]">
                <Mail size={11} className="text-[color:var(--primary)]" />
                <span className="text-[color:var(--text-2)]">Email inviata · ICS allegato</span>
              </div>
            </motion.div>

            <motion.div
              className="absolute top-[170px] left-0 surface-glass !bg-white/95 p-4 w-[230px] rounded-2xl"
              animate={{ y: [0, 14, 0] }}
              transition={{ duration: 6, repeat: Infinity, ease: "easeInOut", delay: 0.4 }}
              style={{ boxShadow: "0 24px 50px -22px rgba(45,212,191,0.45)" }}
            >
              <div className="label-eyebrow !text-[color:var(--secondary-hover)] mb-2 flex items-center gap-1"><BellRing size={10} /> Promemoria</div>
              <div className="font-semibold text-sm leading-tight">Lezione di matematica domani 10:00</div>
              <div className="text-xs text-[color:var(--text-2)] mt-1">con Prof. Verdi</div>
            </motion.div>

            <motion.div
              className="absolute bottom-[40px] right-[20px] surface-glass !bg-white/95 p-4 w-[240px] rounded-2xl"
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 7, repeat: Infinity, ease: "easeInOut", delay: 0.8 }}
              style={{ boxShadow: "0 24px 50px -22px rgba(96,165,250,0.5)" }}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="font-display font-bold">Settimana</div>
                <div className="text-[10px] text-[color:var(--text-2)]">12 — 18 Feb</div>
              </div>
              <div className="grid grid-cols-7 gap-1">
                {[2, 3, 5, 1, 4, 0, 2].map((n, i) => (
                  <div key={i} className="text-center">
                    <div className="text-[9px] text-[color:var(--text-3)] mb-1">{["L", "M", "M", "G", "V", "S", "D"][i]}</div>
                    <div className="w-full rounded" style={{ height: 28 + n * 6, background: `linear-gradient(180deg, rgba(124,58,237,${0.3 + n * 0.08}), rgba(45,212,191,${0.3 + n * 0.08}))` }} />
                  </div>
                ))}
              </div>
              <div className="mt-3 text-[10px] text-[color:var(--text-2)]"><strong className="text-[color:var(--text)]">17 appuntamenti</strong> · 4 docenti</div>
            </motion.div>

            <motion.div
              className="absolute bottom-[200px] left-[30px] px-3 py-1.5 rounded-full text-xs font-semibold"
              style={{ background: "var(--grad-brand)", color: "#fff", boxShadow: "0 12px 30px -8px rgba(124,58,237,0.6)" }}
              animate={{ rotate: [-3, 3, -3], y: [0, -6, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            >
              <Sparkles size={11} className="inline -mt-0.5 mr-1" /> Reminder automatici
            </motion.div>
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 text-white/40 text-[10px] uppercase tracking-[0.22em] flex flex-col items-center gap-2"
        >
          <span>Scroll</span>
          <motion.div animate={{ y: [0, 6, 0] }} transition={{ duration: 1.6, repeat: Infinity }}>
            <ChevronDown size={16} />
          </motion.div>
        </motion.div>
      </section>

      {/* ==================== STATS COUNTERS ==================== */}
      <section className="relative bg-white border-y border-[color:var(--border)] py-14">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 grid grid-cols-2 md:grid-cols-4 gap-6">
          {[
            { n: 12000, suf: "+", label: "Appuntamenti gestiti" },
            { n: 320, suf: "", label: "Studi attivi" },
            { n: 24, suf: "/7", label: "Disponibilità" },
            { n: 99.9, suf: "%", label: "Uptime garantito", float: true },
          ].map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.4 }} transition={{ delay: i * 0.07, duration: 0.5 }}
              className="text-center md:text-left"
            >
              <div className="font-display text-4xl sm:text-5xl font-extrabold tracking-tight">
                {s.float ? "99.9%" : <><Counter value={s.n} suffix={s.suf} /></>}
              </div>
              <div className="text-xs uppercase tracking-[0.18em] text-[color:var(--text-2)] mt-2">{s.label}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ==================== MARQUEE ==================== */}
      <section className="bg-[color:var(--bg)] py-10 overflow-hidden border-b border-[color:var(--border)]">
        <div className="label-eyebrow text-center mb-5">Funziona con il tuo flusso</div>
        <div className="marquee-track flex gap-12 whitespace-nowrap">
          {Array.from({ length: 2 }).flatMap((_, k) => [
            "Google Calendar", "Apple Calendar", "Outlook", "Brevo Email", "Stripe", "WhatsApp Reminder", "PDF Brandizzati", "Multi-tenant", "API REST", "GDPR Ready"
          ].map((label, i) => (
            <span key={`${k}-${i}`} className="text-2xl sm:text-3xl font-display font-bold tracking-tight text-[color:var(--text-3)]/70 hover:text-[color:var(--primary)] transition-colors">
              {label} <span className="text-[color:var(--primary)] mx-3">·</span>
            </span>
          )))}
        </div>
      </section>

      {/* ==================== BENTO FEATURES ==================== */}
      <section id="features" className="max-w-6xl mx-auto px-5 sm:px-8 py-24">
        <SectionHeader eyebrow="Funzioni" title="Tutto in un unico flusso." sub="Sei strumenti, una sola interfaccia. Pensata per chi gestisce tempo e persone ogni giorno." />

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 auto-rows-[180px]">
          {/* Big tile - calendario */}
          <motion.div
            initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.3 }} transition={{ duration: 0.6 }}
            className="col-span-2 row-span-2 rounded-2xl p-7 relative overflow-hidden text-white"
            style={{ background: "linear-gradient(135deg,#0F172A 0%,#312E81 60%,#7C3AED 130%)" }}
          >
            <div className="absolute inset-0 opacity-30" style={{ backgroundImage: "radial-gradient(circle at 80% 10%, #2DD4BF 0%, transparent 50%)" }} />
            <div className="relative">
              <CalendarCheck2 size={28} strokeWidth={1.6} className="mb-4" />
              <div className="font-display text-2xl font-bold mb-2">Calendario per professionista</div>
              <p className="text-sm text-white/70 max-w-md mb-5">Mese, settimana e giorno. Ogni docente, avvocato o medico ha il suo spazio con orari, ferie e materie personalizzate.</p>
              {/* Mock week view */}
              <div className="grid grid-cols-7 gap-1.5 max-w-md">
                {[3, 5, 2, 6, 4, 1, 0].map((n, i) => (
                  <div key={i} className="rounded-md" style={{ height: 70, background: `linear-gradient(180deg, rgba(167,139,250,${0.2 + n*0.1}), rgba(45,212,191,${0.15 + n*0.08}))`, border: "1px solid rgba(255,255,255,0.08)" }} />
                ))}
              </div>
            </div>
          </motion.div>

          {[
            { icon: BellRing, title: "Email + ICS automatiche", desc: "Conferma, reminder 24h e disdetta inviate via Brevo." },
            { icon: FileText, title: "PDF brandizzati", desc: "Report planning con logo e carta intestata dello studio." },
            { icon: Users2, title: "Clienti & team", desc: "Anagrafica con relazioni N:M e ruoli (admin/operatore)." },
            { icon: Plane, title: "Ferie & eccezioni", desc: "Blocchi orari per giorno o fascia. Mai prenotazioni indesiderate." },
            { icon: ShieldCheck, title: "Multi-tenant sicuro", desc: "Ogni studio isolato. JWT, GDPR, backup giornalieri." },
            { icon: Sparkles, title: "Sempre in evoluzione", desc: "Aggiornamenti continui e migliorie senza interruzioni." },
          ].map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              className="surface-card p-5 relative overflow-hidden group hover:border-[color:var(--primary)]/30 transition-colors"
            >
              <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full opacity-0 group-hover:opacity-100 transition-opacity" style={{ background: "var(--grad-soft)", filter: "blur(30px)" }} />
              <div className="relative">
                <div className="w-10 h-10 rounded-md mb-3 flex items-center justify-center" style={{ background: "var(--grad-soft)" }}>
                  <f.icon size={18} className="text-[color:var(--primary)]" strokeWidth={1.7} />
                </div>
                <div className="font-display font-bold text-base mb-1 leading-tight">{f.title}</div>
                <p className="text-xs text-[color:var(--text-2)] leading-relaxed">{f.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ==================== PER CHI ==================== */}
      <section id="chi" className="bg-white border-y border-[color:var(--border)] py-24">
        <div className="max-w-6xl mx-auto px-5 sm:px-8">
          <SectionHeader eyebrow="Per chi è" title="Una piattaforma. Tre mondi." sub="Stesse fondamenta, linguaggio diverso. Prenotika si adatta automaticamente al tuo settore." />
          <div className="grid md:grid-cols-3 gap-5">
            {[
              { tag: "Centri studi", title: "Docenti · Studenti · Materie", desc: "Lezioni private, ripetizioni e corsi.", grad: "linear-gradient(135deg,#7C3AED 0%,#A855F7 100%)" },
              { tag: "Studi legali", title: "Avvocati · Clienti · Pratiche", desc: "Consulenze, udienze, ricorrenze.", grad: "linear-gradient(135deg,#0EA5E9 0%,#60A5FA 100%)" },
              { tag: "Studi medici", title: "Medici · Pazienti · Prestazioni", desc: "Visite, esami e controlli.", grad: "linear-gradient(135deg,#14B8A6 0%,#2DD4BF 100%)" },
            ].map((c, i) => (
              <motion.div
                key={c.tag}
                initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.3 }}
                transition={{ duration: 0.6, delay: i * 0.08 }}
                whileHover={{ y: -6 }}
                className="rounded-2xl p-7 text-white relative overflow-hidden cursor-pointer"
                style={{ background: c.grad }}
              >
                <div className="absolute inset-0 opacity-30" style={{ backgroundImage: "radial-gradient(circle at 100% 0%, rgba(255,255,255,0.4) 0%, transparent 50%)" }} />
                <div className="relative">
                  <div className="text-[10px] tracking-[0.22em] uppercase opacity-85 mb-4">{c.tag}</div>
                  <div className="font-display text-2xl font-bold mb-2 leading-tight">{c.title}</div>
                  <p className="text-sm opacity-90 leading-relaxed">{c.desc}</p>
                  <ArrowRight size={18} className="mt-6 opacity-80 group-hover:translate-x-1 transition-transform" />
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ==================== PRICING with 3D tilt ==================== */}
      <section id="prezzi" className="py-24 relative overflow-hidden" style={{ background: "linear-gradient(180deg,#F8FAFC 0%,#fff 100%)" }}>
        <div className="anim-blob" style={{ background: "#7C3AED", width: 380, height: 380, top: "20%", left: "-150px", opacity: 0.18 }} />
        <div className="anim-blob" style={{ background: "#2DD4BF", width: 320, height: 320, bottom: "5%", right: "-100px", opacity: 0.18, animationDelay: "2s" }} />

        <div className="max-w-6xl mx-auto px-5 sm:px-8 relative">
          <div className="text-center mb-14">
            <div className="label-eyebrow mb-2">Prezzi</div>
            <motion.h2
              initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.4 }}
              className="font-display text-3xl sm:text-5xl font-bold tracking-tight mb-3"
            >Scegli il piano giusto.</motion.h2>
            <p className="text-[color:var(--text-2)] max-w-xl mx-auto">Inizia gratis 14 giorni, senza carta di credito. Cambia o annulla quando vuoi.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-5 max-w-5xl mx-auto" style={{ perspective: 1200 }}>
            {[
              {
                name: "Free", tagline: "Per iniziare", price: "0", period: "/ sempre", cta: "Inizia gratis", accent: false, badge: null,
                features: [
                  "1 professionista",
                  "Calendario mese / settimana / giorno",
                  "Anagrafica clienti e materie",
                  "Email + ICS automatiche",
                  "PDF brandizzati",
                  "Ferie & eccezioni",
                  "Email di supporto",
                ],
                excluded: [],
              },
              {
                name: "Pro", tagline: "Per studi attivi", price: "14", period: "€ / mese", cta: "Inizia gratis 14 giorni", accent: true, badge: "Più scelto",
                features: [
                  "Fino a 5 professionisti",
                  "Tutto del piano Free",
                  "Reminder 24h pre-appuntamento",
                  "Report planning aggregato di studio",
                  "Supporto prioritario via email",
                ],
                excluded: [],
              },
              {
                name: "Business", tagline: "Per centri e cliniche", price: "24", period: "€ / mese", cta: "Parla col team", accent: false, badge: null,
                features: [
                  "Professionisti illimitati",
                  "Tutto del piano Pro",
                  "Branding personalizzato (colori, dominio)",
                  "Onboarding e migrazione dati",
                  "Accesso API",
                  "SLA garantito 99,9%",
                ],
                excluded: [],
              },
            ].map((p, idx) => (
              <motion.div
                key={p.name}
                initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.2 }}
                transition={{ duration: 0.6, delay: idx * 0.08 }}
              >
                <TiltCard testid={`plan-card-${p.name.toLowerCase()}`} className={`relative rounded-2xl p-7 ${p.accent ? "text-white" : "bg-white text-[color:var(--text)]"} flex flex-col h-full`}
                >
                  <div
                    className="absolute inset-0 rounded-2xl"
                    style={p.accent
                      ? { background: "linear-gradient(160deg,#0F172A 0%,#1E1B4B 55%,#312E81 100%)", border: "1px solid rgba(124,58,237,0.4)", boxShadow: "0 24px 60px -20px rgba(124,58,237,0.55)" }
                      : { background: "#fff", border: "1px solid var(--border)" }
                    }
                  />
                  <div className="relative" style={{ transform: "translateZ(40px)" }}>
                    {p.badge && (
                      <div className="absolute -top-6 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-[0.18em] whitespace-nowrap" style={{ background: "var(--grad-brand)", color: "#fff", boxShadow: "0 8px 20px -4px rgba(124,58,237,0.6)" }}>
                        <Zap size={10} className="inline mr-1 -mt-0.5" /> {p.badge}
                      </div>
                    )}
                    <div className={`text-xs uppercase tracking-[0.22em] font-semibold mb-1 ${p.accent ? "text-white/65" : "text-[color:var(--text-2)]"}`}>{p.tagline}</div>
                    <div className="font-display text-2xl font-bold mb-3">{p.name}</div>
                    <div className="flex items-end gap-1 mb-1">
                      <span className="font-display text-5xl font-extrabold tracking-tight" style={p.accent ? { background: "linear-gradient(120deg,#A78BFA,#60A5FA,#2DD4BF)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text" } : {}}>{p.price === "0" ? "€0" : `€${p.price}`}</span>
                      <span className={`text-sm pb-1.5 ${p.accent ? "text-white/65" : "text-[color:var(--text-2)]"}`}>{p.period}</span>
                    </div>
                    <p className={`text-xs ${p.accent ? "text-white/55" : "text-[color:var(--text-3)]"} mb-5`}>IVA esclusa · pagamento annuale -20%</p>
                    <ul className="space-y-2.5 mb-6">
                      {p.features.map((f) => (
                        <li key={f} className={`flex items-start gap-2 text-sm ${p.accent ? "text-white/90" : "text-[color:var(--text)]"}`}>
                          <Check size={16} className={`mt-0.5 shrink-0 ${p.accent ? "text-[#2DD4BF]" : "text-[color:var(--secondary)]"}`} strokeWidth={2.5} />
                          <span>{f}</span>
                        </li>
                      ))}
                      {p.excluded.map((f) => (
                        <li key={f} className={`flex items-start gap-2 text-sm ${p.accent ? "text-white/40 line-through" : "text-[color:var(--text-3)] line-through"}`}>
                          <span className="inline-block w-4 h-4 mt-0.5 shrink-0" />
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                    <button
                      type="button"
                      onClick={() => selectPlan(p.name)}
                      data-testid={`plan-cta-${p.name.toLowerCase()}`}
                      className={p.accent ? "btn-primary w-full justify-center" : "btn-secondary w-full justify-center"}
                    >
                      {p.cta} <ArrowRight size={14} />
                    </button>
                  </div>
                </TiltCard>
              </motion.div>
            ))}
          </div>

          <div className="text-center mt-12 text-xs text-[color:var(--text-2)]">
            <strong className="text-[color:var(--text-1)]">Tutte le funzioni sono incluse in ogni piano.</strong> I prezzi scalano sul numero di professionisti e il livello di supporto.
            <br />Hosting in Europa · GDPR compliant · Backup automatici giornalieri · Aggiornamenti gratuiti
          </div>
        </div>
      </section>

      {/* ==================== TESTIMONIAL ==================== */}
      <section className="py-20 bg-white border-y border-[color:var(--border)]">
        <div className="max-w-3xl mx-auto px-5 sm:px-8 text-center">
          <div className="flex justify-center mb-6">
            {[...Array(5)].map((_, i) => (
              <Star key={i} size={20} fill="#F59E0B" className="text-[#F59E0B]" />
            ))}
          </div>
          <motion.blockquote
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.5 }}
            transition={{ duration: 0.7 }}
            className="font-display text-2xl sm:text-3xl font-bold leading-snug tracking-tight"
          >
            &ldquo;Prima gestivamo studenti, docenti e lezioni con planning cartacei e tanta &laquo;memoria umana&raquo;. Con Prenotika tutto è in un&apos;unica agenda viva: niente più appunti persi, niente più sovrapposizioni. Le famiglie ricevono email di conferma automatiche e i ragazzi non si dimenticano più della lezione.&rdquo;
          </motion.blockquote>
          <div className="mt-6 flex items-center justify-center gap-3">
            <div className="w-11 h-11 rounded-full flex items-center justify-center text-white font-display font-bold" style={{ background: "var(--grad-brand)" }}>F</div>
            <div className="text-left">
              <div className="font-semibold text-sm">Francesca</div>
              <div className="text-xs text-[color:var(--text-2)]">Direttrice · Centro Studi Arco Iris</div>
            </div>
          </div>
        </div>
      </section>

      {/* ==================== CONTATTI ==================== */}
      <section id="contatti" className="max-w-6xl mx-auto px-5 sm:px-8 py-24">
        <div className="grid lg:grid-cols-2 gap-12 items-start">
          <div>
            <div className="label-eyebrow mb-2">Contattaci</div>
            <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight mb-4">Vuoi vedere Prenotika in azione?</h2>
            <p className="text-[color:var(--text-2)] mb-7 leading-relaxed">Raccontaci del tuo studio: ti contatteremo entro 24h per una demo personalizzata e un accesso di prova.</p>
            <div className="space-y-3">
              <div className="flex items-start gap-3"><CheckCircle2 size={18} className="text-[color:var(--secondary)] mt-0.5 shrink-0" /><div><div className="font-semibold text-sm">Demo personalizzata</div><div className="text-xs text-[color:var(--text-2)]">30 minuti, sulla tua realtà.</div></div></div>
              <div className="flex items-start gap-3"><CheckCircle2 size={18} className="text-[color:var(--secondary)] mt-0.5 shrink-0" /><div><div className="font-semibold text-sm">Setup guidato</div><div className="text-xs text-[color:var(--text-2)]">Migrazione gratuita dei tuoi dati.</div></div></div>
              <div className="flex items-start gap-3"><CheckCircle2 size={18} className="text-[color:var(--secondary)] mt-0.5 shrink-0" /><div><div className="font-semibold text-sm">Supporto rapido</div><div className="text-xs text-[color:var(--text-2)]">Email diretta al nostro team.</div></div></div>
            </div>
          </div>

          <motion.form
            initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6 }}
            onSubmit={submit}
            className="surface-card p-6 sm:p-7"
            style={{ boxShadow: "0 30px 60px -30px rgba(124,58,237,0.25)" }}
            data-testid="lead-form"
          >
            {sent ? (
              <div className="text-center py-8" data-testid="lead-form-success">
                <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 300, damping: 15 }} className="w-14 h-14 mx-auto mb-4 rounded-full bg-[color:var(--secondary)]/15 flex items-center justify-center">
                  <CheckCircle2 size={28} className="text-[color:var(--success)]" />
                </motion.div>
                <h3 className="font-display text-xl font-bold mb-2">Richiesta inviata!</h3>
                <p className="text-sm text-[color:var(--text-2)] mb-5">Ti contatteremo entro 24h al recapito che ci hai indicato.</p>
                <button type="button" onClick={() => setSent(false)} className="btn-secondary" data-testid="lead-form-reset">Invia un&apos;altra richiesta</button>
              </div>
            ) : (
              <>
                <h3 className="font-display text-xl font-bold mb-1">Richiedi informazioni</h3>
                <p className="text-xs text-[color:var(--text-2)] mb-5">I campi con * sono obbligatori.</p>
                {form.piano_interesse && (
                  <div className="flex items-center justify-between gap-3 px-3 py-2 rounded-lg mb-4" style={{ background: "var(--grad-soft)", border: "1px solid rgba(124,58,237,0.25)" }} data-testid="lead-piano-badge">
                    <div className="text-xs"><span className="text-[color:var(--text-2)]">Piano selezionato: </span><strong className="text-[color:var(--primary)]">{form.piano_interesse}</strong></div>
                    <button type="button" onClick={() => setForm((f) => ({ ...f, piano_interesse: "" }))} className="text-xs text-[color:var(--text-2)] hover:text-[color:var(--text)]">Rimuovi</button>
                  </div>
                )}
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
                  <div><label className="label-eyebrow block mb-1.5">Azienda</label><input className="input-base" value={form.studio} onChange={(e) => setForm({ ...form, studio: e.target.value })} data-testid="lead-studio" /></div>
                  <div><label className="label-eyebrow block mb-1.5">Messaggio</label><textarea rows={3} className="input-base resize-none" value={form.messaggio} onChange={(e) => setForm({ ...form, messaggio: e.target.value })} placeholder="Raccontaci brevemente come gestisci oggi gli appuntamenti..." data-testid="lead-messaggio" /></div>
                </div>
                {error && <div className="text-sm text-[color:var(--error)] mt-3" data-testid="lead-form-error">{error}</div>}
                <MagneticButton type="submit" disabled={busy} className="btn-primary w-full justify-center mt-5" data-testid="lead-submit-button">
                  {busy ? "Invio in corso…" : (<><Mail size={15} /> Invia richiesta</>)}
                </MagneticButton>
                <p className="text-[10px] text-[color:var(--text-2)] text-center mt-3">Risposta entro 24h · Nessun impegno · Tuoi dati al sicuro</p>
              </>
            )}
          </motion.form>
        </div>
      </section>

      {/* ==================== FINAL CTA ==================== */}
      <section className="relative overflow-hidden py-20" style={{ background: "linear-gradient(160deg,#0F172A 0%,#1E1B4B 55%,#312E81 100%)" }}>
        <div className="absolute inset-0 opacity-20" style={{ backgroundImage: "radial-gradient(circle at 30% 50%, #7C3AED 0%, transparent 50%), radial-gradient(circle at 70% 50%, #2DD4BF 0%, transparent 50%)" }} />
        <div className="relative max-w-3xl mx-auto px-5 sm:px-8 text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.5 }}
            className="font-display text-4xl sm:text-6xl font-extrabold tracking-tight text-white mb-5"
          >
            Pronto a cambiare <br />
            <span style={{ background: "linear-gradient(120deg,#A78BFA,#60A5FA,#2DD4BF)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text" }}>il tuo modo di prenotare?</span>
          </motion.h2>
          <p className="text-white/70 max-w-xl mx-auto mb-9">Configura il tuo studio in meno di 10 minuti. Iniziamo insieme.</p>
          <div className="flex flex-wrap justify-center gap-3">
            <MagneticButton onClick={() => selectPlan("Pro")} className="btn-primary"><Mail size={15} /> Inizia gratis 14 giorni</MagneticButton>
            {!user && (
              <Link to="/login" className="btn-secondary" style={{ background: "rgba(255,255,255,0.08)", color: "#fff", borderColor: "rgba(255,255,255,0.15)" }}><ArrowRight size={14} /> Accedi</Link>
            )}
          </div>
        </div>
      </section>

      {/* ==================== FOOTER ==================== */}
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
