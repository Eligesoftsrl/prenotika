# EligeHub – SaaS gestione appuntamenti per centri studi

## Original problem statement
Convertire un'applicazione legacy Flask + MySQL (Wk) in un SaaS moderno per centri studi / professionisti che gestiscono appuntamenti di clienti/alunni in base alla disponibilità oraria di docenti. Frontend React mobile-friendly, backend Python, DB con chiavi primarie solide. Ogni docente sceglie giorni e fasce di disponibilità per costruire un calendario orario personalizzato.

Dove si trova il codice originale: `/app/uploads/Wk_extracted/` (Flask + MySQL, conservato come riferimento, non eseguito).

## User choices
- Scope MVP: core (multi-tenant + Docenti + Clienti + Orari + Appuntamenti + Calendario)
- Multi-tenancy: super_admin (piattaforma) crea i tenant
- Ruoli: Admin (centro studi) + Docente
- Auth: JWT email/password
- Design: deciso dall'agent (palette "Organic & Earthy", Cabinet Grotesk + Outfit)

## Stack
- Backend: FastAPI + Motor (MongoDB) - JWT (PyJWT) - bcrypt
- Frontend: React 19 + Tailwind + lucide-react + react-router 7
- Italiano, mobile-first

## Architettura
- Multi-tenant: ogni risorsa scoped per `studio_id`
- Ruoli: `super_admin`, `admin`, `docente` (RBAC su ogni route)
- ID: UUID `str` come `_id` Mongo
- Indici: users.email unique, users.studio_id, clienti(studio_id,cognome), orari(studio_id,docente_id,giorno), appuntamenti(studio_id,docente_id,data), docente_clienti(studio_id,docente_id,cliente_id) unique

## Endpoint principali
- `POST /api/auth/login`, `GET /api/auth/me`
- `GET/POST/DELETE /api/studios` (super_admin)
- `GET/POST/PATCH/DELETE /api/docenti` (admin) — campo `slot_minuti` (15/30/45/60/90/120)
- `GET /api/docenti/{id}/alunni`, `POST/DELETE /api/docenti/{id}/alunni/{cliente_id}` (relazione N:M alunno↔docente, riproduce tabella `pubblico`)
- `GET/POST/PATCH/DELETE /api/clienti` (admin scope). Docente: vede SOLO i propri alunni associati. Admin: filtro opzionale `?docente_id=X`
- `GET/POST/DELETE /api/orari` (docente own / admin all)
- `GET/POST/PATCH/DELETE /api/appuntamenti` con check overlap (409)
- `GET /api/disponibilita?docente_id&data&slot_minuti` (default = slot del docente)
- `GET /api/dashboard/stats`

## Pagine frontend
- `/login` (split-screen, demo buttons)
- `/dashboard` (KPI + prossimi appuntamenti)
- `/appuntamenti` (calendario settimanale stile Cal.com, click cella → crea, **Al** autocalcolato da `slot_minuti`, **Alunno** filtrato per docente selezionato)
- `/orari` (editor settimanale, supporta `?docente=ID` per quick-link da Docenti)
- `/docenti` (CRUD + colonna **Durata app.** + pulsanti **Calendario** e **Alunni**)
- `/docenti/:id/alunni` (gestione alunni associati al docente)
- `/clienti` (CRUD + search)
- `/studios` (super_admin: gestione tenant)

## Implementato
**Iter 1 (12 Giu 2026):**
- Backend + Frontend MVP completi con seed idempotente (super_admin, studio demo, admin, docente, 2 clienti)
- 22/22 backend tests + UI flows passed

**Iter 2 (12 Giu 2026) — feature mancanti dal progetto originale:**
- Campo `slot_minuti` per docente (durata standard appuntamento)
- Relazione N:M alunni↔docenti (collection `docente_clienti`, riproduce tabella `pubblico`)
- Pagina dedicata `/docenti/:id/alunni` per associare/disassociare alunni
- Form Appuntamento: alunni filtrati per docente, "Al" autocalcolato da slot
- Pulsanti **Calendario** e **Alunni** sulla riga docente
- Cascade delete su docente_clienti
- 33/33 backend tests + 6/6 critical UI flows passed

## Backlog (priorità)
- **P1**: Pagina pubblica di booking per clienti finali (usa `/api/disponibilita` con slot docente)
- **P1**: Annullamento/spostamento appuntamenti + notifiche email (SendGrid/Resend)
- **P2**: Vista mensile calendario + drag&drop appuntamenti
- **P2**: Ferie/eccezioni alla disponibilità ricorrente
- **P2**: Date/time picker italiani (dd/mm/yyyy + 24h) al posto dei nativi
- **P3**: Self-service signup tenant + Stripe checkout
- **P3**: Branding personalizzabile per tenant (logo, colore primario)
- **P3**: Moduli aggiuntivi differiti: materie, note, news

## Credenziali test
Vedi `/app/memory/test_credentials.md`
