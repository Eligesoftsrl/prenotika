import React from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import Logo from "@/components/Logo";

export default function Privacy() {
  return (
    <div className="min-h-screen bg-white text-[color:var(--text)]">
      <header className="border-b border-[color:var(--border)] bg-white/80 backdrop-blur sticky top-0 z-30">
        <div className="max-w-4xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5" data-testid="privacy-home-link">
            <Logo size={30} />
            <div className="font-display font-bold">Prenotika</div>
          </Link>
          <Link to="/" className="text-xs text-[color:var(--text-2)] hover:text-[color:var(--primary)] inline-flex items-center gap-1.5" data-testid="privacy-back-link">
            <ArrowLeft size={14} /> Torna alla home
          </Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-5 sm:px-8 py-12" data-testid="privacy-page">
        <div className="mb-8">
          <div className="text-[10px] tracking-[0.22em] uppercase text-[color:var(--text-2)] mb-2">Documento legale</div>
          <h1 className="font-display text-4xl sm:text-5xl font-extrabold tracking-tight mb-3">Informativa Privacy</h1>
          <p className="text-sm text-[color:var(--text-2)]">Ultimo aggiornamento: {new Date().toLocaleDateString("it-IT", { year: "numeric", month: "long", day: "numeric" })}</p>
        </div>

        <div className="prose prose-slate max-w-none space-y-6 text-sm leading-relaxed">
          <section>
            <h2 className="font-display text-xl font-bold mb-2">1. Titolare del trattamento</h2>
            <p>
              Il titolare del trattamento dei dati personali è <strong>Eligesoft Srl</strong>,
              con sede legale in Italia, Partita IVA <strong>04532690650</strong>.
              Per qualsiasi richiesta relativa al trattamento dei dati personali è possibile
              scrivere a <a href="mailto:privacy@eligesoft.com" className="text-[color:var(--primary)] underline">privacy@eligesoft.com</a>.
            </p>
          </section>

          <section>
            <h2 className="font-display text-xl font-bold mb-2">2. Dati raccolti</h2>
            <p>Attraverso il modulo di contatto presente sul sito prenotika.com raccogliamo:</p>
            <ul className="list-disc pl-6 space-y-1 mt-2">
              <li>Nome e cognome</li>
              <li>Indirizzo email</li>
              <li>Numero di telefono (facoltativo)</li>
              <li>Nome dello studio / azienda (facoltativo)</li>
              <li>Tipologia di attività</li>
              <li>Contenuto libero del messaggio</li>
            </ul>
          </section>

          <section>
            <h2 className="font-display text-xl font-bold mb-2">3. Finalità e base giuridica</h2>
            <p>
              I dati sono trattati esclusivamente per rispondere alla tua richiesta di
              informazioni sul servizio Prenotika e per contattarti riguardo alla proposta
              commerciale. La base giuridica è il tuo consenso esplicito (art. 6.1.a GDPR)
              raccolto tramite spunta obbligatoria nel form.
            </p>
          </section>

          <section>
            <h2 className="font-display text-xl font-bold mb-2">4. Conservazione</h2>
            <p>
              I dati sono conservati per il tempo necessario a evadere la richiesta e comunque
              non oltre 24 mesi dall&apos;ultimo contatto, salvo diverso obbligo di legge.
            </p>
          </section>

          <section>
            <h2 className="font-display text-xl font-bold mb-2">5. Soggetti a cui vengono comunicati i dati</h2>
            <p>
              I dati non vengono ceduti a terzi. Vengono trattati unicamente dal personale
              autorizzato di Eligesoft Srl e dai fornitori tecnologici che ci supportano
              nell&apos;erogazione del servizio (hosting su Railway e Vercel, invio email
              transazionali tramite Brevo). Tutti i fornitori sono nominati Responsabili del
              trattamento ai sensi dell&apos;art. 28 GDPR.
            </p>
          </section>

          <section>
            <h2 className="font-display text-xl font-bold mb-2">6. Diritti dell&apos;interessato</h2>
            <p>Puoi in ogni momento esercitare i tuoi diritti previsti dagli artt. 15-22 GDPR:</p>
            <ul className="list-disc pl-6 space-y-1 mt-2">
              <li>Accesso ai tuoi dati</li>
              <li>Rettifica o cancellazione</li>
              <li>Limitazione o opposizione al trattamento</li>
              <li>Portabilità dei dati</li>
              <li>Revoca del consenso in qualsiasi momento</li>
              <li>Reclamo al Garante per la Protezione dei Dati Personali</li>
            </ul>
            <p className="mt-2">
              Per esercitare i tuoi diritti scrivi a{" "}
              <a href="mailto:privacy@eligesoft.com" className="text-[color:var(--primary)] underline">privacy@eligesoft.com</a>.
            </p>
          </section>

          <section>
            <h2 className="font-display text-xl font-bold mb-2">7. Modifiche</h2>
            <p>
              Ci riserviamo il diritto di aggiornare la presente informativa in qualsiasi
              momento. Le modifiche saranno pubblicate su questa pagina.
            </p>
          </section>
        </div>
      </main>

      <footer className="border-t border-[color:var(--border)] bg-white">
        <div className="max-w-4xl mx-auto px-5 sm:px-8 py-6 text-xs text-[color:var(--text-2)] text-center">
          Prenotika è un prodotto sviluppato da <strong className="text-[color:var(--text)]">Eligesoft Srl</strong> · Partita IVA: <strong className="text-[color:var(--text)]">04532690650</strong>
        </div>
      </footer>
    </div>
  );
}
