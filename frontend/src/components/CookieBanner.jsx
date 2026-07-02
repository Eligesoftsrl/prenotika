import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Cookie, X } from "lucide-react";

const STORAGE_KEY = "prenotika_cookie_consent_v1";

export default function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Mostra il banner solo se l'utente non ha ancora scelto
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      // piccolo delay per non essere invasivo al primo paint
      const t = setTimeout(() => setVisible(true), 600);
      return () => clearTimeout(t);
    }
  }, []);

  const persist = (choice) => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ choice, date: new Date().toISOString() })
    );
    setVisible(false);
  };

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ y: 120, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 120, opacity: 0 }}
          transition={{ type: "spring", stiffness: 220, damping: 26 }}
          className="fixed z-[100] left-3 right-3 sm:left-6 sm:right-auto sm:bottom-6 bottom-3 sm:max-w-md"
          data-testid="cookie-banner"
        >
          <div className="rounded-2xl shadow-2xl border border-white/10 overflow-hidden" style={{ background: "linear-gradient(160deg,#0F172A 0%,#1E1B4B 55%,#312E81 100%)" }}>
            <div className="p-5 sm:p-6 text-white">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: "linear-gradient(135deg,#7C3AED,#2DD4BF)" }}>
                  <Cookie size={18} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-display font-bold text-base mb-1">Usiamo i cookie</div>
                  <p className="text-xs text-white/70 leading-relaxed">
                    Utilizziamo cookie tecnici necessari al funzionamento del sito. Con il tuo consenso possiamo
                    anche usarne per finalità di misurazione anonima. Puoi accettare o rifiutare quelli non essenziali.
                    Maggiori dettagli nell&apos;<a href="/privacy" className="underline hover:text-white" data-testid="cookie-privacy-link">informativa privacy</a>.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => persist("dismissed")}
                  aria-label="Chiudi"
                  className="text-white/50 hover:text-white transition-colors"
                  data-testid="cookie-close-button"
                >
                  <X size={16} />
                </button>
              </div>

              <div className="flex flex-col sm:flex-row gap-2 mt-4">
                <button
                  type="button"
                  onClick={() => persist("rejected")}
                  className="flex-1 rounded-xl border border-white/15 hover:border-white/30 hover:bg-white/5 transition-colors text-sm font-medium py-2.5 px-4"
                  data-testid="cookie-reject-button"
                >
                  Solo essenziali
                </button>
                <button
                  type="button"
                  onClick={() => persist("accepted")}
                  className="flex-1 rounded-xl text-sm font-semibold py-2.5 px-4 text-white shadow-lg hover:brightness-110 transition-all"
                  style={{ background: "linear-gradient(135deg,#7C3AED 0%,#2DD4BF 100%)" }}
                  data-testid="cookie-accept-button"
                >
                  Accetta tutto
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
