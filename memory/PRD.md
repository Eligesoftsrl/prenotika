# EligeHub – SaaS gestione appuntamenti per centri studi

## Original problem statement
Convertire un'applicazione legacy Flask + MySQL (Wk) in un SaaS moderno per centri studi / professionisti che gestiscono appuntamenti di clienti/alunni in base alla disponibilità oraria di docenti. Frontend React mobile-friendly, backend Python, DB con chiavi primarie solide. Ogni docente sceglie giorni e fasce di disponibilità per costruire un calendario orario personalizzato.

Codice originale conservato in `/app/uploads/Wk_extracted/` (Flask + MySQL, riferimento - non eseguito).

## Stack
- Backend: FastAPI + Motor (MongoDB) + JWT (PyJWT) + bcrypt
- Frontend: React 19 + Tailwind + lucide-react + react-router 7
- Italiano, mobile-first

## Architettura
- Multi-tenant per `studio_id` con RBAC: `super_admin`, `admin`, `docente`
- UUID `str` come `_id`. Indici unique su: users.email, materie(studio_id,descrizione), docente_clienti(studio_id,docente_id,cliente_id), docente_materie(studio_id,docente_id,materia_id)

## Endpoint principali
- Auth: `POST /api/auth/login`, `GET /api/auth/me`
- Tenant: `GET/POST/DELETE /api/studios` (super_admin)
- Docenti: `GET/POST/PATCH/DELETE /api/docenti` + campo `slot_minuti` (15/30/45/60/90/120)
- Clienti: `GET/POST/PATCH/DELETE /api/clienti` (filtro `?docente_id`, scope automatico per docenti)
- Orari (disponibilità ricorrente): `GET/POST/DELETE /api/orari`
- Appuntamenti: `GET/POST/PATCH/DELETE /api/appuntamenti` (check overlap → 409)
- **Bulk + ricorrenza + nuovo cliente inline**: `POST /api/appuntamenti/bulk` con `slots[]`, `cliente_id` o `nuovo_cliente`. Ritorna `{created, skipped, count_*}`
- Disponibilità slot liberi: `GET /api/disponibilita?docente_id&data&slot_minuti`
- **Materie**: `GET/POST/PATCH/DELETE /api/materie` + N:M `/api/docenti/{id}/materie/{materia_id}` (replica tabella `combomat`)
- **Alunni↔Docenti** N:M: `/api/docenti/{id}/alunni/{cliente_id}` (replica tabella `pubblico`)
- Dashboard: `GET /api/dashboard/stats`

## Pagine frontend
- `/login`, `/dashboard`
- `/appuntamenti` — calendario settimanale, modal potenziato con tab "Studente in archivio / Nuovo studente" + ricorrenza prossime 6 settimane
- `/orari?docente=ID` — editor settimanale
- `/docenti` — CRUD + colonna Durata + pulsanti **Calendario / Alunni / Materie**
- `/docenti/:id/alunni` — gestione alunni associati
- `/docenti/:id/materie` — gestione materie associate
- `/clienti` — CRUD + search
- `/materie` — catalogo materie del centro studi
- `/studios` (super_admin)

## Implementato (12 Giu 2026)
**Iter 1**: backend + frontend MVP completi, seed idempotente. 22/22 backend test.
**Iter 2**: durata appuntamento per docente (`slot_minuti`), relazione N:M alunni↔docenti, pagina dedicata alunni docente, autocalcolo "Al" da slot, filtri. 33/33 test.
**Iter 3**: catalogo Materie + N:M docenti↔materie, modal appuntamento con tab "esistente / nuovo studente" inline, ricorrenza +7..+42 giorni, endpoint `/api/appuntamenti/bulk`, fix centratura modal con scroll. 46/46 backend test + 12/12 frontend dopo fix.
**Iter 4**: 3 tipologie studio (`centro_studi` / `studio_legale` / `studio_medico`), terminologia dinamica via `tipologia.js`, modali con React Portals, PDF report con merging contigui, pagina dedicata `/appuntamenti/nuovo`.
**Iter 5 (Feb 2026)**: Rebrand **Prenotika** + Logo SVG, pagina `/impostazioni` con campo `comunicazioni` (admin) appeso al footer dei PDF generati. Fix nav: link "Impostazioni" aggiunto alla sidebar admin in `Layout.jsx`. Nuova pagina **/report** (admin) per generare PDF planning aggregato giorno/settimana/mese di tutti i professionisti o singolo, con date picker e selettore docente. Upload **logo studio** in Impostazioni (PNG/JPG/WEBP/SVG max 600KB) salvato come base64 e stampato in cima a tutti i PDF (validazione PIL, fallback silente se corrotto).
**Iter 6 (Feb 2026)**: Bug fix P.IVA in Impostazioni (RCA: `EmailStr` rifiutava `''` con 422 → fix: frontend normalizza `''→null` per campi opzionali, mantiene `''` per `logo_base64`/`comunicazioni` come cancella esplicito). Carta intestata PDF: nuovo header con logo (sx) + nome studio, sede, telefono • email, P.IVA (dx) + linea separatrice verde brand. Test iter11 100% (6/6 backend + 3/3 frontend).
**Iter 7 (Feb 2026)**: Rebrand completo seguendo Prenotika Brand Guidelines v1.0. Palette: Electric Indigo `#7C3AED`, Neo Cyan `#2DD4BF`, Soft Sky `#60A5FA`, Midnight `#0F172A`, Light Neutral `#F8FAFC`. Font: **Sora** (display) + **Inter** (body) + **Manrope** (fallback). Logo PNG ufficiale (`/prenotika-icon.png`). Login dark hero con 3 blob animati + headline brand "La gestione **intelligente** degli appuntamenti". Sidebar/Layout/PDF aggiornati con la nuova palette. Test iter12 100% (6/6 backend + 3/3 frontend, nessuna regressione). Rimossi i claim "SaaS" dal copy pubblico.
**Iter 8 (Feb 2026)**: Integrazione **Brevo Transactional Email + ICS**. Nuovo modulo `email_service.py` con: build_ics() conforme RFC 5545 (METHOD:REQUEST, UID, DTSTAMP, DTSTART/DTEND in UTC, ATTENDEE/ORGANIZER), html_body brandizzato Prenotika (gradient header viola/cyan/teal), invio async via httpx a Brevo `/v3/smtp/email`. Hook in `POST /api/appuntamenti` (singolo) e `POST /api/appuntamenti/bulk` (multi-evento in un unico VCALENDAR). Fail-safe: errori loggati ma appuntamento creato comunque. Env: `BREVO_API_KEY`, `BREVO_SENDER_EMAIL=team@zioners.com`, `BREVO_SENDER_NAME=Prenotika`. Test: HTTP 201 da Brevo confermato sia per singolo che bulk.
**Iter 9 (Feb 2026)**: Quattro feature insieme. (a) **Landing page pubblica** `/` con hero brand (3 blob animati, gradient text), sezione Funzioni (6 card), "Per chi" (centri studi/legali/medici), Contatti con form lead POST `/api/leads` (non-auth) + notifica Brevo a team@zioners.com. (b) **Email disdetta**: hook DELETE `/api/appuntamenti/:id` invia ICS METHOD:CANCEL + HTML stile dark. (c) **Scheduler reminder 24h**: nuovo `reminder_scheduler.py` con APScheduler AsyncIO, cron(minute=5) cerca appuntamenti tra +23h/+25h non ancora avvisati, invia email con `reminded_at` marker (TZ Europe/Rome). (d) **Ferie/Eccezioni**: nuova entità `eccezioni` con CRUD `/api/eccezioni`, tipo chiuso/personalizzato, validate in POST appuntamenti (singolo + bulk → skip o 409). Frontend: pagina `/eccezioni` (admin+docente) con form, lista, link sidebar "Ferie". Test iter13 100% (11/11 backend + UI flows + regressioni).
**Iter 10 (Feb 2026)**: Permission tightening + Pricing vetrina. (a) **DELETE /api/appuntamenti/:id** ristretto a `admin` only (era admin+docente). Frontend Appuntamenti: pulsante Trash nascosto a docente sia in vista settimana che giorno. (b) **Sezione Prezzi** nella landing tra Per chi e Contatti: 3 piani (Free €0, Pro €29 con badge "Più scelto" e card dark gradient, Business €79), CTA "Inizia gratis 14 giorni" su Pro che scrolla al form e pre-compila `piano_interesse` + messaggio. Form lead esteso con `piano_interesse` + badge visivo, propagato in email notifica Brevo. Test self via curl: DELETE doc=403, admin=204, POST lead+piano=201.
**Iter 11 (Feb 2026)**: **Landing "wow 2026"**. Riscritta usando `framer-motion`. Effetti: (a) hero dark con **aurora gradient mesh** animato + dot grid + **spotlight cursor-tracking** (radial gradient che segue il mouse) + **3 floating cards** mock (visita, promemoria, settimana) con animazioni y up/down + **live ticker** prenotazioni recenti con AnimatePresence + scroll indicator + parallax scroll-Y. Headline con **stagger reveal** word-by-word. (b) **Stats counters** animati on viewport (12k appuntamenti, 320 studi, 24/7, 99.9% uptime). (c) **Marquee** scroll continuo con integrations. (d) **Bento grid** features con card grande "Calendario per professionista" + 6 card secondarie con glow hover. (e) **Pricing 3D tilt** mouse-tracking + magnetic buttons. (f) **Testimonial** card stelle. (g) **CTA finale** dark gradient con magnetic CTA. Aggiunti in CSS: `.aurora-mesh`, `.marquee-track`, animazioni keyframes.
**Iter 12 (Feb 2026)**: Pricing onesto + testimonial reale. RCA: l'utente ha chiesto se le limitazioni piano Free fossero applicate — risposta: **NO** (nessun enforcement tecnico). Quindi rimosse le esclusioni sbarrate (Email auto, PDF brandizzati, ferie) dal piano Free; ridifferenziati i piani solo per dimensione/supporto (Free: 1 prof, Pro: 5 prof + reminder, Business: illimitato + branding + SLA + API). Aggiunta nota trasparenza "Tutte le funzioni sono incluse in ogni piano". Testimonial cambiato a **Francesca · Centro Studi Arco Iris** (utente reale della vecchia versione). Ticker hero aggiornato con riferimento ad Arco Iris.
**Iter 13 (Feb 2026)**: **Piani con enforcement reale**. Prezzi aggiornati: Pro **€14**, Business **€24** (era €29/€79). Testimonial Francesca ampliata (sostituzione planning cartacei + memoria umana). Backend: aggiunto campo `plan` (Free/Pro/Business) a `StudioBase`. `PLAN_LIMITS_PROFESSIONISTI = {free:1, pro:5, business:None}`. Hook in `POST /api/docenti`: HTTP 403 se count >= limit. Nuovo endpoint `GET /api/studio/quota`. Nuovo endpoint `PATCH /api/studios/:id` (super_admin) per cambiare il piano. **Security**: in `PATCH /api/studio` (admin) il campo `plan` viene filtrato server-side → impossibile self-upgrade. Frontend: pagina Studios con colonna Piano + dropdown inline + selettore nel form di creazione. Pagina Docenti con `quota-indicator` + banner `quota-warning` + bottone "Nuovo" disabled se al limite. Studio demo seed → plan=business per test smooth. Test iter14 100% (12/12 backend + UI + 17/17 regressioni).
**Iter 14 (Feb 2026)**: **Area Leads + Upgrade modal + Badge sidebar**. (a) Backend nuovi endpoint super_admin: `GET /api/leads`, `GET /api/leads/count?status=new`, `PATCH /api/leads/:id` (status new/contacted/converted/closed + notes), `DELETE /api/leads/:id`. (b) Nuova pagina frontend `/leads` (super_admin) con lista + filtri per stato + search + pannello dettaglio con quick actions (cambia stato, mailto rispondi, elimina). Link "Richieste" (icon Inbox) in sidebar super_admin **con badge contatore** (gradient rosso→arancio) che polling ogni 45s il numero di lead con status="new" e ad ogni cambio route. (c) **Upgrade modal elegante** in `/docenti`: quando l'admin è già al limite quota, cliccare "Nuovo docente" apre direttamente un Modal brandizzato invece del form → card dark gradient con piano suggerito (Pro €14 o Business €24), CTA mailto team@zioners.com "Contatta il team di Prenotika". Anche l'intercept 403 (path fallback) apre lo stesso modal. Bottone create disabled durante il caricamento della quota (fix race condition). Test iter15 100% (6/6 backend + 29/29 regressioni + UI happy path).

## Backlog (priorità)
- **P1**: pagina pubblica self-booking clienti finali (link condivisibile `/book/[studio]/[docente]`)
- **P1**: notifiche email su prenotazione/annullo
- **P2**: vista mensile + drag&drop, gestione ferie/eccezioni, date picker localizzato dd/mm/yyyy
- **P2**: cross-modulo: assegnazione materia + alunno in fase di prenotazione
- **P3**: signup tenant self-service + Stripe
- **P3**: branding personalizzabile per tenant

## Credenziali
Vedi `/app/memory/test_credentials.md`
