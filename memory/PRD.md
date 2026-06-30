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

## Backlog (priorità)
- **P1**: pagina pubblica self-booking clienti finali (link condivisibile `/book/[studio]/[docente]`)
- **P1**: notifiche email su prenotazione/annullo
- **P2**: vista mensile + drag&drop, gestione ferie/eccezioni, date picker localizzato dd/mm/yyyy
- **P2**: cross-modulo: assegnazione materia + alunno in fase di prenotazione
- **P3**: signup tenant self-service + Stripe
- **P3**: branding personalizzabile per tenant

## Credenziali
Vedi `/app/memory/test_credentials.md`
