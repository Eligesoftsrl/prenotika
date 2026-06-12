# EligeHub – SaaS gestione appuntamenti per centri studi

## Original problem statement
Convertire un'applicazione legacy Flask + MySQL (Wk) in un SaaS moderno per centri studi / professionisti che gestiscono appuntamenti di clienti/alunni in base alla disponibilità oraria di docenti. Frontend React mobile-friendly, backend Python, DB con chiavi primarie solide. Ogni docente sceglie giorni e fasce di disponibilità per costruire un calendario orario personalizzato.

## User choices (Iter 1)
- Scope MVP: core (multi-tenant + Docenti + Clienti + Orari + Appuntamenti + Calendario)
- Multi-tenancy: super_admin (piattaforma) crea i tenant
- Ruoli: Admin (centro studi) + Docente
- Auth: JWT email/password
- Design: deciso dall'agent (palette "Organic & Earthy", font Cabinet Grotesk + Outfit)

## Stack
- Backend: FastAPI + Motor (MongoDB) - JWT (PyJWT) - bcrypt
- Frontend: React 19 + Tailwind + lucide-react + react-router 7
- Tutto in Italiano, mobile-first

## Architettura
- Multi-tenant: ogni risorsa scoped per `studio_id`
- Ruoli: `super_admin`, `admin`, `docente` (RBAC su ogni route)
- ID: UUID `str` come `_id` Mongo (chiavi primarie esplicite)
- Indici: users.email unique, users.studio_id, clienti(studio_id,cognome), orari(studio_id,docente_id,giorno), appuntamenti(studio_id,docente_id,data)

## Endpoint principali
- `POST /api/auth/login`, `GET /api/auth/me`
- `GET/POST/DELETE /api/studios` (super_admin)
- `GET/POST/PATCH/DELETE /api/docenti` (admin scope)
- `GET/POST/PATCH/DELETE /api/clienti` (admin scope)
- `GET/POST/DELETE /api/orari` (docente own / admin all)
- `GET/POST/PATCH/DELETE /api/appuntamenti` con check overlap (409)
- `GET /api/disponibilita?docente_id&data&slot_minuti` → slot liberi
- `GET /api/dashboard/stats` → KPI + prossimi 5 appuntamenti

## Pagine frontend
- `/login` (split-screen con hero verde + form, demo buttons)
- `/dashboard` (KPI + prossimi appuntamenti + suggerimento)
- `/appuntamenti` (calendario settimanale stile Cal.com, click cella → crea)
- `/orari` (editor settimanale a blocchi colorati per docente)
- `/docenti` (lista/CRUD con avatar colorato)
- `/clienti` (lista/CRUD + search)
- `/studios` (super_admin: gestione tenant)

## Implementato (12 Giu 2026)
- Backend completo single-file `server.py` con seed idempotente super_admin + demo studio
- Frontend React multi-page con AuthContext (token in localStorage `eh_token`)
- Layout responsive con sidebar (desktop) + drawer (mobile)
- 100% backend tests passed (22 test) + 100% frontend critical flows
- Account demo seeded automaticamente

## Backlog (priorità)
- **P1**: Pagina pubblica di booking per clienti finali (con `/api/disponibilita`)
- **P1**: Annullamento/spostamento appuntamenti con stato
- **P1**: Notifiche email (SendGrid/Resend) su conferma/annullo appuntamento
- **P2**: Vista mensile calendario + drag&drop appuntamenti
- **P2**: Ferie/eccezioni alla disponibilità ricorrente
- **P2**: Multi-lingua (i18n) + export CSV/iCal
- **P3**: Self-service signup tenant + checkout Stripe per acquisto piani
- **P3**: Branding personalizzabile per tenant (logo, colore primario)
- **P3**: Moduli aggiuntivi differiti: materie, note, news

## Credenziali test
Vedi `/app/memory/test_credentials.md`
