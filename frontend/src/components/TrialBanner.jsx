import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import { Sparkles, Clock, AlertTriangle, X, ArrowRight, Zap } from "lucide-react";

/**
 * Banner elegante mostrato in cima a tutte le pagine autenticate per lo studio in trial.
 * - >7 giorni: banner soft, dismissibile per la sessione
 * - 3-7 giorni: warning ambra, dismissibile
 * - ≤3 giorni: urgente rosso, NON dismissibile
 * - scaduto: notice permanente rosso con downgrade avvenuto
 */
export default function TrialBanner() {
  const { studio } = useAuth();
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!studio?.id) return;
    // Il dismiss è per giorno (torna il banner ogni nuovo giorno)
    const key = `trial-dismissed-${studio.id}-${new Date().toDateString()}`;
    setDismissed(localStorage.getItem(key) === "1");
  }, [studio?.id]);

  if (!studio) return null;

  const trialActive = studio.trial_active;
  const trialEndsAt = studio.trial_ends_at;
  const trialPlan = studio.trial_plan || studio.plan;

  // Nessun trial → no banner
  if (!trialActive || !trialEndsAt) return null;

  const endDate = new Date(trialEndsAt);
  const now = Date.now();
  const msLeft = endDate.getTime() - now;
  // Conta i GIORNI DI CALENDARIO tra oggi e la scadenza (a mezzanotte), così il contatore scende una volta al giorno anche se il trial è stato creato a metà giornata
  const todayMidnight = new Date(); todayMidnight.setHours(0, 0, 0, 0);
  const endMidnight = new Date(trialEndsAt); endMidnight.setHours(0, 0, 0, 0);
  const daysLeft = Math.max(0, Math.round((endMidnight.getTime() - todayMidnight.getTime()) / (1000 * 60 * 60 * 24)));
  const isExpired = msLeft <= 0;

  // Livelli di urgenza
  let level = "info";    // > 7 giorni
  if (daysLeft <= 7 && daysLeft > 3) level = "warn";
  else if (daysLeft <= 3 && daysLeft > 0) level = "urgent";
  else if (isExpired) level = "expired";

  const canDismiss = level === "info" || level === "warn";

  if (canDismiss && dismissed) return null;

  const styles = {
    info: {
      bg: "linear-gradient(90deg, rgba(124,58,237,0.08) 0%, rgba(45,212,191,0.08) 100%)",
      border: "border-[color:var(--primary)]/25",
      accent: "text-[color:var(--primary)]",
      Icon: Sparkles,
    },
    warn: {
      bg: "linear-gradient(90deg, rgba(245,158,11,0.10) 0%, rgba(251,146,60,0.10) 100%)",
      border: "border-[#F59E0B]/40",
      accent: "text-[#B45309]",
      Icon: Clock,
    },
    urgent: {
      bg: "linear-gradient(90deg, rgba(239,68,68,0.10) 0%, rgba(244,63,94,0.10) 100%)",
      border: "border-[#EF4444]/45",
      accent: "text-[#B91C1C]",
      Icon: AlertTriangle,
    },
    expired: {
      bg: "linear-gradient(90deg, rgba(148,163,184,0.10) 0%, rgba(100,116,139,0.10) 100%)",
      border: "border-[#64748B]/40",
      accent: "text-[#334155]",
      Icon: AlertTriangle,
    },
  }[level];

  const messages = {
    info: (
      <>
        Prova gratuita <strong className={styles.accent}>{(trialPlan || "").toUpperCase()}</strong> attiva ·
        <strong className="ml-1.5">{daysLeft} giorni</strong> rimanenti
      </>
    ),
    warn: (
      <>
        La tua prova <strong>{(trialPlan || "").toUpperCase()}</strong> scade tra
        <strong className={`ml-1.5 ${styles.accent}`}>{daysLeft} giorni</strong>.
        Attivala per non perdere le funzionalità.
      </>
    ),
    urgent: (
      <>
        <strong className={styles.accent}>Attenzione:</strong> la prova
        <strong> {(trialPlan || "").toUpperCase()}</strong> scade tra
        <strong className={`ml-1.5 ${styles.accent}`}>{daysLeft} giorn{daysLeft === 1 ? "o" : "i"}</strong>.
        Attivala ora per non essere declassato al piano Free.
      </>
    ),
    expired: (
      <>
        La tua prova gratuita è <strong>scaduta</strong>. L&apos;account è temporaneamente al piano Free.
        Riattiva <strong>{(trialPlan || "").toUpperCase()}</strong> per ripristinare tutte le funzionalità.
      </>
    ),
  };

  const onDismiss = () => {
    if (studio?.id) {
      const key = `trial-dismissed-${studio.id}-${new Date().toDateString()}`;
      localStorage.setItem(key, "1");
    }
    setDismissed(true);
  };

  const Icon = styles.Icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={`relative border ${styles.border} rounded-xl px-4 py-3 mb-5`}
      style={{ background: styles.bg, backdropFilter: "blur(8px)" }}
      data-testid={`trial-banner-${level}`}
    >
        <div className="flex items-center gap-3 flex-wrap">
          <div className={`w-9 h-9 rounded-full bg-white/70 border ${styles.border} flex items-center justify-center shrink-0`}>
            <Icon size={17} className={styles.accent} />
          </div>
          <div className="flex-1 min-w-0 text-sm text-[color:var(--text)] leading-snug">
            {messages[level]}
            {!isExpired && (
              <span className="hidden sm:inline text-xs text-[color:var(--text-2)] ml-2">
                · scade il {endDate.toLocaleDateString("it-IT", { day: "2-digit", month: "long", year: "numeric" })}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 ml-auto">
            <Link
              to="/account"
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all ${
                level === "urgent" || level === "expired"
                  ? "text-white shadow-md"
                  : "text-[color:var(--primary)] bg-white/70 hover:bg-white border border-[color:var(--primary)]/20"
              }`}
              style={
                level === "urgent" || level === "expired"
                  ? { background: "linear-gradient(135deg,#EF4444 0%,#F97316 100%)" }
                  : {}
              }
              data-testid="trial-banner-cta"
            >
              <Zap size={12} /> {isExpired ? "Riattiva ora" : "Attiva piano"} <ArrowRight size={11} />
            </Link>
            {canDismiss && (
              <button
                onClick={onDismiss}
                className="w-7 h-7 flex items-center justify-center rounded-md text-[color:var(--text-2)] hover:bg-white/60 transition-colors"
                aria-label="Nascondi per oggi"
                data-testid="trial-banner-dismiss"
              >
                <X size={14} />
              </button>
            )}
          </div>
        </div>
      </motion.div>
  );
}
