import React, { useEffect, useMemo, useState, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ArrowLeft, Calendar as CalendarIcon, Clock, User, Users, BookOpen, Repeat, Sparkles, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import { tipologiaLabels } from "@/lib/tipologia";
import { fmtISO, todayISO } from "@/lib/dates";

const GIORNI_LABEL = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"];

function fmtDayLabel(iso) {
  const d = new Date(iso + "T00:00:00");
  return {
    dow: GIORNI_LABEL[(d.getDay() + 6) % 7],
    day: d.getDate(),
    month: d.toLocaleDateString("it-IT", { month: "short" }).replace(".", ""),
  };
}

function toMinutes(hhmm) {
  if (!hhmm) return 0;
  const [h, m] = hhmm.split(":").map((x) => parseInt(x, 10));
  return h * 60 + m;
}

export default function NuovoAppuntamento() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, studio } = useAuth();
  const L = tipologiaLabels(studio?.tipologia, studio?.custom_labels);
  const isAdmin = user?.role === "admin";

  const defaults = location.state || {};
  const [docenti, setDocenti] = useState([]);
  const [alunni, setAlunni] = useState([]);
  const [docenteMaterie, setDocenteMaterie] = useState([]);
  const [mode, setMode] = useState("existing");
  const [nuovoCliente, setNuovoCliente] = useState({ nome: "", cognome: "", email: "", cellulare: "" });
  const [availableSlots, setAvailableSlots] = useState([]); // slot liberi per la data selezionata
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [recurrenceSlots, setRecurrenceSlots] = useState([]); // slot liberi per settimane future
  const [recurrenceDates, setRecurrenceDates] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  const today = todayISO();
  const initialDocenteId = defaults.docente_id || (user?.role === "docente" ? user.id : "");
  const [form, setForm] = useState({
    docente_id: initialDocenteId,
    cliente_id: "",
    data: defaults.data || today,
    dal: defaults.dal || "",
    al: defaults.al || "",
    note: "",
    materia_id: "",
  });

  const docenteSel = docenti.find((d) => d.id === form.docente_id);

  // Carica docenti (una volta)
  useEffect(() => {
    api.get("/docenti").then(({ data }) => {
      setDocenti(data);
      if (!form.docente_id && data[0]) setForm((f) => ({ ...f, docente_id: data[0].id }));
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Quando cambia docente: carica alunni + materie
  useEffect(() => {
    if (!form.docente_id) { setAlunni([]); setDocenteMaterie([]); return; }
    const fetchClients = L.needs_association
      ? api.get(`/docenti/${form.docente_id}/alunni`).then(({ data }) => data)
      : api.get("/clienti").then(({ data }) => data);
    Promise.all([
      fetchClients,
      api.get(`/docenti/${form.docente_id}/materie`).then(({ data }) => data).catch(() => []),
    ]).then(([cli, mat]) => {
      setAlunni(cli);
      setDocenteMaterie(mat);
      setForm((f) => (cli.find((c) => c.id === f.cliente_id) ? f : { ...f, cliente_id: cli[0]?.id || "" }));
    });
  }, [form.docente_id]); // eslint-disable-line react-hooks/exhaustive-deps

  // Carica slot disponibili quando cambia docente o data
  const loadSlots = useCallback(async () => {
    if (!form.docente_id || !form.data) { setAvailableSlots([]); return; }
    setLoadingSlots(true);
    try {
      const { data } = await api.get("/disponibilita", { params: { docente_id: form.docente_id, data: form.data } });
      setAvailableSlots(data.slots || []);
    } catch {
      setAvailableSlots([]);
    } finally { setLoadingSlots(false); }
  }, [form.docente_id, form.data]);

  useEffect(() => { loadSlots(); }, [loadSlots]);

  // Anteprima settimana: 7 giorni con conteggio slot liberi
  const weekPreviewDays = useMemo(() => {
    if (!form.data) return [];
    const d0 = new Date(form.data + "T00:00:00");
    const dow = (d0.getDay() + 6) % 7; // Lun=0
    const monday = new Date(d0);
    monday.setDate(monday.getDate() - dow);
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(monday);
      d.setDate(d.getDate() + i);
      return fmtISO(d);
    });
  }, [form.data]);

  const [weekAvail, setWeekAvail] = useState({}); // { iso: count }
  useEffect(() => {
    if (!form.docente_id || weekPreviewDays.length === 0) { setWeekAvail({}); return; }
    let cancelled = false;
    Promise.all(
      weekPreviewDays.map((iso) =>
        api.get("/disponibilita", { params: { docente_id: form.docente_id, data: iso } })
          .then(({ data }) => [iso, (data.slots || []).length])
          .catch(() => [iso, 0])
      )
    ).then((entries) => { if (!cancelled) setWeekAvail(Object.fromEntries(entries)); });
    return () => { cancelled = true; };
  }, [form.docente_id, weekPreviewDays]);

  // Helper: verifica che il range [dal, al] sia coperto da slot consecutivi liberi in una data
  // Usa confronto numerico (minuti) invece di stringhe per essere robusto a piccole differenze di formato
  const isRangeCoveredBy = (slots, dal, al) => {
    if (!dal || !al) return false;
    const target = toMinutes(al);
    let cur = toMinutes(dal);
    if (cur >= target) return false;
    let guard = 0;
    while (cur < target) {
      const s = slots.find((x) => toMinutes(x.dal) === cur);
      if (!s) return false;
      cur = toMinutes(s.al);
      if (++guard > 60) return false;
    }
    return cur === target;
  };

  // Se il range selezionato non è più valido dopo il refresh degli slot, deseleziona
  useEffect(() => {
    if (!form.dal || !form.al) return;
    if (!isRangeCoveredBy(availableSlots, form.dal, form.al)) {
      setForm((f) => ({ ...f, dal: "", al: "" }));
    }
  }, [availableSlots]); // eslint-disable-line react-hooks/exhaustive-deps

  // Ricorrenza: 6 settimane successive
  const recurrenceOptions = useMemo(() => {
    if (!form.data) return [];
    const d0 = new Date(form.data + "T00:00:00");
    return Array.from({ length: 6 }, (_, i) => {
      const d = new Date(d0);
      d.setDate(d.getDate() + 7 * (i + 1));
      return fmtISO(d);
    });
  }, [form.data]);

  // Verifica disponibilità del range corrente per ogni settimana futura
  useEffect(() => {
    if (!form.docente_id || !form.dal || !form.al || recurrenceOptions.length === 0) {
      setRecurrenceSlots([]);
      return;
    }
    let cancelled = false;
    Promise.all(
      recurrenceOptions.map((iso) =>
        api.get("/disponibilita", { params: { docente_id: form.docente_id, data: iso } })
          .then(({ data }) => ({ iso, free: isRangeCoveredBy(data.slots || [], form.dal, form.al) }))
          .catch(() => ({ iso, free: false }))
      )
    ).then((res) => { if (!cancelled) setRecurrenceSlots(res); });
    return () => { cancelled = true; };
  }, [form.docente_id, form.dal, form.al, recurrenceOptions]);

  // Se lo slot cambia, ripulisci le date di ricorrenza (per evitare selezioni ora occupate)
  useEffect(() => {
    setRecurrenceDates((prev) => prev.filter((iso) => recurrenceSlots.find((r) => r.iso === iso && r.free)));
  }, [recurrenceSlots]);

  const toggleRecurrence = (iso) => {
    const info = recurrenceSlots.find((r) => r.iso === iso);
    if (!info?.free) return;
    setRecurrenceDates((prev) => prev.includes(iso) ? prev.filter((x) => x !== iso) : [...prev, iso]);
  };

  // Selezione tramite due dropdown Dalle/Alle
  const startsOptions = availableSlots.map((s) => s.dal);
  const endsOptions = useMemo(() => {
    if (!form.dal) return [];
    // A partire da form.dal, cammina in avanti tra slot consecutivi liberi
    const results = [];
    let cur = form.dal;
    let guard = 0;
    while (guard++ < 60) {
      const s = availableSlots.find((x) => x.dal === cur);
      if (!s) break;
      results.push(s.al);
      cur = s.al;
    }
    return results;
  }, [form.dal, availableSlots]);

  const setStart = (dal) => {
    if (!dal) { setForm((f) => ({ ...f, dal: "", al: "" })); return; }
    // Default: end = fine del primo slot dopo dal
    const first = availableSlots.find((x) => x.dal === dal);
    setForm((f) => ({ ...f, dal, al: first ? first.al : "" }));
  };
  const setEnd = (al) => setForm((f) => ({ ...f, al }));

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!form.dal || !form.al) { setError("Seleziona un orario dagli slot disponibili."); return; }
    setBusy(true); setError(""); setResult(null);
    try {
      const slots = [{ data: form.data, dal: form.dal, al: form.al }];
      recurrenceDates.forEach((d) => slots.push({ data: d, dal: form.dal, al: form.al }));
      const payload = {
        docente_id: form.docente_id,
        slots,
        note: form.note || null,
        materia_id: form.materia_id || null,
        associa_alunno: true,
      };
      if (mode === "new") {
        if (!nuovoCliente.nome.trim() || !nuovoCliente.cognome.trim()) {
          setError(`Nome e cognome del nuovo ${(L.cliente || "cliente").toLowerCase()} sono obbligatori`);
          setBusy(false); return;
        }
        payload.nuovo_cliente = {
          nome: nuovoCliente.nome.trim(), cognome: nuovoCliente.cognome.trim(),
          email: nuovoCliente.email || null, cellulare: nuovoCliente.cellulare || null,
        };
      } else {
        if (!form.cliente_id) { setError(`Seleziona ${(L.cliente || "uno").toLowerCase()}`); setBusy(false); return; }
        payload.cliente_id = form.cliente_id;
      }
      const { data } = await api.post("/appuntamenti/bulk", payload);
      setResult(data);
      if (data.count_skipped === 0) {
        setTimeout(() => navigate("/appuntamenti", { state: { docente_id: form.docente_id } }), 900);
      }
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore");
    } finally { setBusy(false); }
  };

  const noAlunni = alunni.length === 0 && !!form.docente_id;
  const canSubmit = form.dal && form.al && (mode === "new" || form.cliente_id);
  const totale = 1 + recurrenceDates.length;

  const clienteSel = alunni.find((c) => c.id === form.cliente_id);
  const materiaSel = docenteMaterie.find((m) => m.id === form.materia_id);

  return (
    <div data-testid="nuovo-appuntamento-page" className="max-w-5xl mx-auto">
      <button onClick={() => navigate(-1)} className="inline-flex items-center gap-1.5 text-sm text-[color:var(--text-2)] hover:text-[color:var(--text)] mb-4" data-testid="back-button">
        <ArrowLeft size={14} /> Torna al calendario
      </button>

      {/* HERO header */}
      <div className="mb-7 relative overflow-hidden rounded-2xl p-6 sm:p-8 text-white" style={{ background: "linear-gradient(135deg,#0F172A 0%,#1E1B4B 50%,#312E81 100%)" }}>
        <div className="absolute -top-16 -right-16 w-60 h-60 rounded-full opacity-30 blur-3xl" style={{ background: "#7C3AED" }} />
        <div className="absolute -bottom-20 -left-16 w-72 h-72 rounded-full opacity-20 blur-3xl" style={{ background: "#2DD4BF" }} />
        <div className="relative">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/10 backdrop-blur border border-white/15 text-[10px] tracking-[0.22em] uppercase font-semibold mb-3 text-white">
            <Sparkles size={11} /> Nuovo appuntamento
          </div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight leading-tight text-white">Fissa un incontro in pochi tocchi</h1>
          <p className="text-white/70 mt-1.5 text-sm max-w-xl">Ti mostriamo solo gli orari davvero liberi. Clicca uno slot per selezionarlo, poi clicca uno slot adiacente per estendere la durata.</p>
        </div>
      </div>

      {result ? (
        <div className="surface-card p-6 space-y-3" data-testid="bulk-result">
          <div className="p-3 rounded-lg bg-[#E5F0E9] border border-[#C8DDD0] text-[color:var(--success)]">
            <div className="font-semibold">{result.count_created} appuntamento/i creato/i con successo</div>
          </div>
          {result.count_skipped > 0 && (
            <div className="p-3 rounded-lg bg-[#FDF1E3] border border-[#EBD1A3] text-[#B0721F]">
              <div className="font-semibold mb-1">{result.count_skipped} slot saltati:</div>
              <ul className="text-xs list-disc ml-5 space-y-0.5">
                {result.skipped.map((s, i) => (<li key={i}>{s.data} {s.dal}-{s.al}: {s.motivo}</li>))}
              </ul>
            </div>
          )}
          <button onClick={() => navigate("/appuntamenti", { state: { docente_id: form.docente_id } })} className="btn-primary w-full justify-center" data-testid="result-back-button">Torna al calendario</button>
        </div>
      ) : (
      <form onSubmit={onSubmit} className="space-y-5" data-testid="appuntamento-form">

        {/* STEP 1 · CHI */}
        <section className="surface-card p-5 sm:p-6">
          <div className="flex items-center gap-2 mb-4">
            <StepBadge n={1} />
            <div>
              <div className="font-display font-bold text-lg tracking-tight">Chi</div>
              <div className="text-xs text-[color:var(--text-2)]">Seleziona {L.docente.toLowerCase()} e {L.cliente.toLowerCase()}</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Docente card */}
            {isAdmin ? (
              <div>
                <label className="label-eyebrow block mb-1.5"><User size={11} className="inline mr-1" /> {L.docente}</label>
                <select className="input-base" value={form.docente_id} onChange={(e) => setForm({ ...form, docente_id: e.target.value })} required data-testid="app-docente-select">
                  {docenti.map((d) => (<option key={d.id} value={d.id}>{d.nome} {d.cognome}</option>))}
                </select>
                {docenteSel && (
                  <div className="mt-2 inline-flex items-center gap-2 text-xs text-[color:var(--text-2)] bg-[color:var(--surface-2)] px-2.5 py-1.5 rounded-lg">
                    <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: docenteSel.color || "#7C3AED" }} />
                    Slot standard: <strong className="text-[color:var(--text)]">{docenteSel.slot_minuti || 60} min</strong>
                  </div>
                )}
              </div>
            ) : (
              <div>
                <label className="label-eyebrow block mb-1.5"><User size={11} className="inline mr-1" /> {L.docente}</label>
                <div className="rounded-xl border border-[color:var(--border)] px-3.5 py-3 bg-[color:var(--surface-2)] flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full flex items-center justify-center text-white font-semibold text-sm" style={{ background: user?.color || "#7C3AED" }}>{(user?.nome?.[0] || "?").toUpperCase()}</div>
                  <div>
                    <div className="font-semibold text-sm">{user?.nome} {user?.cognome}</div>
                    <div className="text-xs text-[color:var(--text-2)]">Slot standard: <strong>{docenteSel?.slot_minuti || user?.slot_minuti || 60} min</strong></div>
                  </div>
                </div>
              </div>
            )}

            {/* Cliente switch */}
            <div>
              <label className="label-eyebrow block mb-1.5"><Users size={11} className="inline mr-1" /> {L.cliente}</label>
              <div className="flex gap-1.5 mb-3 p-1 rounded-lg bg-[color:var(--surface-2)]">
                <button type="button" onClick={() => setMode("existing")} className={`flex-1 py-1.5 px-3 text-sm rounded-md font-medium transition-all ${mode === "existing" ? "bg-white shadow-sm" : "text-[color:var(--text-2)] hover:text-[color:var(--text)]"}`} data-testid="mode-existing-button">In archivio</button>
                <button type="button" onClick={() => setMode("new")} className={`flex-1 py-1.5 px-3 text-sm rounded-md font-medium transition-all ${mode === "new" ? "bg-white shadow-sm" : "text-[color:var(--text-2)] hover:text-[color:var(--text)]"}`} data-testid="mode-new-button">Nuovo</button>
              </div>
              {mode === "existing" ? (
                <>
                  <select className="input-base" value={form.cliente_id} onChange={(e) => setForm({ ...form, cliente_id: e.target.value })} disabled={noAlunni} data-testid="app-cliente-select">
                    <option value="">Seleziona {L.cliente.toLowerCase()}…</option>
                    {alunni.map((c) => (<option key={c.id} value={c.id}>{c.cognome} {c.nome}</option>))}
                  </select>
                  {noAlunni && <div className="text-xs text-[color:var(--warning)] mt-1.5">Nessun {L.cliente.toLowerCase()}. Passa a &quot;Nuovo&quot;.</div>}
                </>
              ) : (
                <div className="space-y-2.5">
                  <div className="grid grid-cols-2 gap-2.5">
                    <input className="input-base" placeholder="Nome" value={nuovoCliente.nome} onChange={(e) => setNuovoCliente({ ...nuovoCliente, nome: e.target.value })} data-testid="new-nome-input" />
                    <input className="input-base" placeholder="Cognome" value={nuovoCliente.cognome} onChange={(e) => setNuovoCliente({ ...nuovoCliente, cognome: e.target.value })} data-testid="new-cognome-input" />
                  </div>
                  <input type="email" className="input-base" placeholder="Email (opzionale)" value={nuovoCliente.email} onChange={(e) => setNuovoCliente({ ...nuovoCliente, email: e.target.value })} data-testid="new-email-input" />
                  <input className="input-base" placeholder="Telefono (opzionale)" value={nuovoCliente.cellulare} onChange={(e) => setNuovoCliente({ ...nuovoCliente, cellulare: e.target.value })} data-testid="new-tel-input" />
                </div>
              )}
            </div>
          </div>

          {/* Materia */}
          {docenteMaterie.length > 0 && (
            <div className="mt-5">
              <label className="label-eyebrow block mb-1.5"><BookOpen size={11} className="inline mr-1" /> {L.materia} <span className="normal-case text-[color:var(--text-2)]">(opzionale)</span></label>
              <select className="input-base" value={form.materia_id} onChange={(e) => setForm({ ...form, materia_id: e.target.value })} data-testid="app-materia-select">
                <option value="">— nessuna —</option>
                {docenteMaterie.map((m) => (<option key={m.id} value={m.id}>{m.descrizione}</option>))}
              </select>
            </div>
          )}
        </section>

        {/* STEP 2 · QUANDO */}
        <section className="surface-card p-5 sm:p-6">
          <div className="flex items-center gap-2 mb-4">
            <StepBadge n={2} />
            <div>
              <div className="font-display font-bold text-lg tracking-tight">Quando</div>
              <div className="text-xs text-[color:var(--text-2)]">Scegli data e slot orario (solo quelli davvero liberi)</div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-[220px_1fr] gap-5">
            <div>
              <label className="label-eyebrow block mb-1.5"><CalendarIcon size={11} className="inline mr-1" /> Data</label>
              <input type="date" className="input-base" min={today} value={form.data} onChange={(e) => setForm({ ...form, data: e.target.value, dal: "", al: "" })} required data-testid="app-data-input" />

              {/* Anteprima settimana */}
              {weekPreviewDays.length > 0 && (
                <div className="mt-3">
                  <div className="text-[10px] tracking-[0.2em] uppercase text-[color:var(--text-2)] font-semibold mb-1.5">Questa settimana</div>
                  <div className="grid grid-cols-7 gap-1" data-testid="week-preview">
                    {weekPreviewDays.map((iso) => {
                      const count = weekAvail[iso];
                      const active = iso === form.data;
                      const past = iso < today;
                      const busy = count === 0;
                      const label = fmtDayLabel(iso);
                      return (
                        <button
                          type="button"
                          key={iso}
                          onClick={() => !past && setForm((f) => ({ ...f, data: iso, dal: "", al: "" }))}
                          disabled={past}
                          data-testid={`week-day-${iso}`}
                          className={`relative p-1.5 rounded-lg text-center transition-all border ${
                            past ? "opacity-40 cursor-not-allowed border-transparent bg-transparent" :
                            active ? "text-white border-transparent shadow-md" :
                            busy ? "border-[color:var(--border)] bg-[color:var(--surface-2)] hover:border-[color:var(--warning)]" :
                            "border-[color:var(--border)] bg-white hover:border-[color:var(--primary)] hover:-translate-y-0.5"
                          }`}
                          style={active && !past ? { background: "linear-gradient(135deg,#7C3AED,#2DD4BF)" } : {}}
                          title={busy ? "Nessuno slot libero" : count ? `${count} slot liberi` : "Verifica…"}
                        >
                          <div className="text-[9px] uppercase font-bold tracking-wider opacity-70">{label.dow}</div>
                          <div className="text-sm font-black tabular-nums leading-none mt-0.5">{label.day}</div>
                          <div className={`text-[9px] mt-0.5 font-semibold ${active ? "text-white/85" : busy ? "text-[color:var(--warning)]" : "text-[color:var(--success)]"}`}>
                            {count === undefined ? "…" : count === 0 ? "0" : `${count}`}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                  <div className="text-[10px] text-[color:var(--text-2)] mt-1.5">Numero = slot liberi in quel giorno</div>
                </div>
              )}

              <div className="mt-3 rounded-xl p-3 bg-gradient-to-br from-[#7C3AED]/5 to-[#2DD4BF]/5 border border-[color:var(--border)]">
                <div className="text-[10px] tracking-[0.2em] uppercase text-[color:var(--text-2)] font-semibold">Riepilogo</div>
                <div className="mt-1.5 text-sm space-y-0.5">
                  <div>📅 {new Date(form.data + "T00:00:00").toLocaleDateString("it-IT", { weekday: "long", day: "numeric", month: "long" })}</div>
                  <div>👤 {docenteSel ? `${docenteSel.nome} ${docenteSel.cognome}` : "—"}</div>
                  <div>🧑 {clienteSel ? `${clienteSel.cognome} ${clienteSel.nome}` : (mode === "new" ? (nuovoCliente.nome ? `${nuovoCliente.nome} ${nuovoCliente.cognome} (nuovo)` : "Nuovo cliente") : "—")}</div>
                  {materiaSel && <div>📚 {materiaSel.descrizione}</div>}
                  {form.dal && <div className="text-[color:var(--primary)] font-semibold">🕐 {form.dal} → {form.al}</div>}
                </div>
              </div>
            </div>

            <div>
              <label className="label-eyebrow block mb-1.5"><Clock size={11} className="inline mr-1" /> Slot disponibili</label>
              {loadingSlots ? (
                <div className="rounded-xl border border-dashed border-[color:var(--border)] p-6 text-center text-sm text-[color:var(--text-2)]">Caricamento slot…</div>
              ) : availableSlots.length === 0 ? (
                <div className="rounded-xl border border-[color:var(--border)] p-6 text-center bg-[color:var(--surface-2)]" data-testid="no-slots">
                  <AlertTriangle size={28} className="mx-auto text-[color:var(--warning)] mb-2" />
                  <div className="font-semibold text-sm">Nessuno slot libero</div>
                  <div className="text-xs text-[color:var(--text-2)] mt-1">Il {L.docente.toLowerCase()} non ha orari configurati per questo giorno oppure sono già tutti occupati.</div>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <div className="text-[10px] tracking-[0.2em] uppercase text-[color:var(--text-2)] font-bold mb-1">Dalle</div>
                      <select
                        className="input-base tabular-nums font-semibold"
                        value={form.dal}
                        onChange={(e) => setStart(e.target.value)}
                        data-testid="slot-dalle-select"
                      >
                        <option value="">Seleziona…</option>
                        {startsOptions.map((t) => (<option key={t} value={t}>{t}</option>))}
                      </select>
                    </div>
                    <div>
                      <div className="text-[10px] tracking-[0.2em] uppercase text-[color:var(--text-2)] font-bold mb-1">Alle</div>
                      <select
                        className="input-base tabular-nums font-semibold"
                        value={form.al}
                        onChange={(e) => setEnd(e.target.value)}
                        disabled={!form.dal}
                        data-testid="slot-alle-select"
                      >
                        <option value="">{form.dal ? "Seleziona…" : "Prima scegli Dalle"}</option>
                        {endsOptions.map((t) => (<option key={t} value={t}>{t}</option>))}
                      </select>
                    </div>
                  </div>

                  {/* Anteprima "pill" del range selezionato */}
                  {form.dal && form.al && (
                    <div className="mt-4">
                      <div className="text-[10px] tracking-[0.2em] uppercase text-[color:var(--text-2)] font-semibold mb-1.5">Il tuo appuntamento</div>
                      <div className="inline-flex items-stretch rounded-xl overflow-hidden shadow-lg shadow-[#7C3AED]/25" data-testid="slot-preview" style={{ background: "linear-gradient(135deg,#7C3AED,#2DD4BF)" }}>
                        <div className="px-4 py-2.5 text-white">
                          <div className="text-[10px] tracking-widest opacity-80">DALLE</div>
                          <div className="tabular-nums font-bold">{form.dal}</div>
                        </div>
                        <div className="flex items-center px-2 text-white/80">→</div>
                        <div className="px-4 py-2.5 text-white text-right">
                          <div className="text-[10px] tracking-widest opacity-80">ALLE</div>
                          <div className="tabular-nums font-bold">{form.al}</div>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
              {form.dal && form.al && (
                <div className="mt-3 text-xs text-[color:var(--text-2)] inline-flex items-center gap-1.5"><CheckCircle2 size={13} className="text-[color:var(--success)]" /> Durata: <strong className="text-[color:var(--text)]">{Math.round((toMinutes(form.al) - toMinutes(form.dal)))} minuti</strong></div>
              )}
            </div>
          </div>
        </section>

        {/* STEP 3 · RICORRENZA */}
        {form.dal && recurrenceOptions.length > 0 && (
          <section className="surface-card p-5 sm:p-6">
            <div className="flex items-center gap-2 mb-4">
              <StepBadge n={3} />
              <div>
                <div className="font-display font-bold text-lg tracking-tight flex items-center gap-2">Ricorrenza <span className="text-[10px] tracking-[0.2em] uppercase text-[color:var(--text-2)]">Opzionale</span></div>
                <div className="text-xs text-[color:var(--text-2)]">Ripeti l&apos;appuntamento nelle prossime 6 settimane allo stesso orario. Ti mostriamo solo le date libere.</div>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5" data-testid="recurrence-grid">
              {recurrenceOptions.map((iso) => {
                const info = recurrenceSlots.find((r) => r.iso === iso);
                const free = info?.free !== false; // se manca info, permesso in ottica ottimistica
                const checked = recurrenceDates.includes(iso);
                const label = fmtDayLabel(iso);
                return (
                  <button
                    type="button"
                    key={iso}
                    onClick={() => toggleRecurrence(iso)}
                    disabled={!free}
                    data-testid={`recurrence-${iso}`}
                    className={`relative rounded-xl border-2 p-2.5 transition-all text-left ${
                      !free ? "border-[color:var(--border)] bg-[color:var(--surface-2)] opacity-60 cursor-not-allowed"
                      : checked ? "border-transparent text-white shadow-lg shadow-[#7C3AED]/20"
                      : "bg-white border-[color:var(--border)] hover:border-[color:var(--primary)] hover:-translate-y-0.5"
                    }`}
                    style={checked && free ? { background: "linear-gradient(135deg,#7C3AED,#2DD4BF)" } : {}}
                  >
                    <div className="text-[10px] tracking-[0.2em] uppercase opacity-70 font-semibold">{label.dow}</div>
                    <div className="text-2xl font-black leading-none mt-0.5 tabular-nums">{label.day}</div>
                    <div className="text-[10px] uppercase mt-0.5">{label.month}</div>
                    <div className="absolute top-2 right-2">
                      {!free ? <XCircle size={13} className="text-[color:var(--error)]" />
                        : checked ? <CheckCircle2 size={14} className="text-white" />
                        : <span className="w-1.5 h-1.5 rounded-full bg-[color:var(--success)] inline-block" />}
                    </div>
                    {!free && <div className="text-[9px] mt-1 text-[color:var(--error)] font-semibold uppercase tracking-wide">Occupato</div>}
                  </button>
                );
              })}
            </div>
            {recurrenceDates.length > 0 && (
              <div className="mt-3 text-xs text-[color:var(--text-2)] inline-flex items-center gap-1.5"><Repeat size={12} /> Prenoterai <strong className="text-[color:var(--text)]">{totale} appuntamenti</strong> in totale.</div>
            )}
          </section>
        )}

        {/* STEP 4 · NOTE + SUBMIT */}
        <section className="surface-card p-5 sm:p-6">
          <div className="flex items-center gap-2 mb-4">
            <StepBadge n={form.dal && recurrenceOptions.length > 0 ? 4 : 3} />
            <div>
              <div className="font-display font-bold text-lg tracking-tight">Note e conferma</div>
              <div className="text-xs text-[color:var(--text-2)]">Aggiungi eventuali note e conferma la prenotazione</div>
            </div>
          </div>

          <label className="label-eyebrow block mb-1.5">Note (opzionale)</label>
          <textarea rows={3} className="input-base resize-none" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} placeholder="Es. Argomento della lezione, richieste particolari…" data-testid="app-note-input" />

          {error && <div className="mt-4 text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="app-form-error">{error}</div>}

          <div className="flex flex-col sm:flex-row gap-2 pt-5 mt-5 border-t border-[color:var(--border)]">
            <button type="button" onClick={() => navigate(-1)} className="btn-secondary sm:px-8 justify-center" data-testid="app-cancel-button">Annulla</button>
            <button type="submit" disabled={busy || !canSubmit} className="btn-primary sm:flex-1 justify-center" data-testid="app-submit-button">
              {busy ? "Salvataggio…" : (
                <>Registra {totale > 1 ? `${totale} appuntamenti` : "appuntamento"}</>
              )}
            </button>
          </div>
        </section>
      </form>
      )}
    </div>
  );
}

function StepBadge({ n }) {
  return (
    <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-display font-bold text-sm flex-shrink-0" style={{ background: "linear-gradient(135deg,#7C3AED,#2DD4BF)" }}>
      {n}
    </div>
  );
}
