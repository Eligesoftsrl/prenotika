import React, { useEffect, useMemo, useState } from "react";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Plus, ChevronLeft, ChevronRight, Calendar as CalIcon, Trash2 } from "lucide-react";
import { Modal } from "./Docenti";

const GIORNI = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"];
const HOURS = Array.from({ length: 14 }, (_, i) => i + 7); // 7..20

function startOfWeek(d) {
  const date = new Date(d);
  const day = (date.getDay() + 6) % 7; // 0 = Mon
  date.setDate(date.getDate() - day);
  date.setHours(0, 0, 0, 0);
  return date;
}
function addDays(d, n) { const x = new Date(d); x.setDate(x.getDate() + n); return x; }
function fmtISO(d) { return d.toISOString().slice(0, 10); }
function fmtShort(d) { return d.toLocaleDateString("it-IT", { day: "2-digit", month: "short" }); }
function toMin(hhmm) { const [h, m] = hhmm.split(":").map(Number); return h * 60 + m; }
function toHHMM(mins) {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

export default function Appuntamenti() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [weekStart, setWeekStart] = useState(startOfWeek(new Date()));
  const [docenti, setDocenti] = useState([]);
  const [clienti, setClienti] = useState([]);
  const [items, setItems] = useState([]);
  const [orari, setOrari] = useState([]);
  // Quando admin: nessuna preselezione (forza la scelta). Quando docente: sempre se stesso
  const [selectedDocenteId, setSelectedDocenteId] = useState(user?.role === "docente" ? user.id : "");
  const [loading, setLoading] = useState(false);

  const [showCreate, setShowCreate] = useState(false);
  const [createDefaults, setCreateDefaults] = useState(null);

  const days = useMemo(() => Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)), [weekStart]);
  const da = fmtISO(days[0]);
  const a = fmtISO(days[6]);

  useEffect(() => {
    api.get("/docenti").then(({ data }) => {
      setDocenti(data);
      // Se docente -> userId; se admin senza selezione e c'è almeno un docente, suggerisci il primo automaticamente
      if (isAdmin && !selectedDocenteId && data[0]) {
        setSelectedDocenteId(data[0].id);
      }
    });
    api.get("/clienti").then(({ data }) => setClienti(data));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const docenteSel = docenti.find((d) => d.id === selectedDocenteId);
  const slotMinuti = docenteSel?.slot_minuti || 60;

  const load = async () => {
    if (!selectedDocenteId) { setItems([]); setOrari([]); return; }
    setLoading(true);
    try {
      const [appResp, orResp] = await Promise.all([
        api.get("/appuntamenti", { params: { data_da: da, data_a: a, docente_id: selectedDocenteId } }),
        api.get("/orari", { params: { docente_id: selectedDocenteId } }),
      ]);
      setItems(appResp.data);
      setOrari(orResp.data);
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, [da, a, selectedDocenteId]);

  // Range orario: from min(orari.dal) to max(orari.al). Fallback 8-19 se nessuna disponibilità.
  const dayRange = useMemo(() => {
    if (orari.length === 0) return { startMin: 8 * 60, endMin: 19 * 60 };
    let s = Infinity, e = -Infinity;
    orari.forEach((o) => {
      s = Math.min(s, toMin(o.dal));
      e = Math.max(e, toMin(o.al));
    });
    // Allinea al multiplo di slotMinuti
    s = Math.floor(s / slotMinuti) * slotMinuti;
    e = Math.ceil(e / slotMinuti) * slotMinuti;
    return { startMin: s, endMin: e };
  }, [orari, slotMinuti]);

  // Genera gli slot per ogni giorno: array di {dal, al, isAvailable, appointment|null}
  const computeDaySlots = (date) => {
    const giorno = (date.getDay() + 6) % 7; // 0=Mon
    const dayOrari = orari.filter((o) => o.giorno === giorno);
    const slots = [];
    for (let m = dayRange.startMin; m + slotMinuti <= dayRange.endMin; m += slotMinuti) {
      const dal = toHHMM(m);
      const al = toHHMM(m + slotMinuti);
      const isAvailable = dayOrari.some((o) => toMin(o.dal) <= m && m + slotMinuti <= toMin(o.al));
      slots.push({ dal, al, m, isAvailable });
    }
    return slots;
  };

  const itemsByDay = useMemo(() => {
    const map = {};
    days.forEach((d) => { map[fmtISO(d)] = []; });
    items.forEach((it) => { if (map[it.data]) map[it.data].push(it); });
    return map;
  }, [items, days]);

  const findAppointment = (dayKey, slotM) => {
    return itemsByDay[dayKey]?.find((ev) => {
      const evStart = toMin(ev.dal);
      const evEnd = toMin(ev.al);
      return evStart < slotM + slotMinuti && evEnd > slotM && ev.stato !== "annullato";
    });
  };

  const onCellClick = (dayDate, slot) => {
    if (!slot.isAvailable) return;
    setCreateDefaults({ data: fmtISO(dayDate), dal: slot.dal, al: slot.al });
    setShowCreate(true);
  };

  const remove = async (id) => {
    if (!window.confirm("Eliminare questo appuntamento?")) return;
    await api.delete(`/appuntamenti/${id}`);
    await load();
  };

  return (
    <div data-testid="appuntamenti-page">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <div className="label-eyebrow mb-1.5">Agenda</div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight">Appuntamenti</h1>
          <p className="text-[color:var(--text-2)] mt-1">Calendario personalizzato del docente — celle verdi = libere, colorate = prenotate, grigie = fuori disponibilità.</p>
        </div>
        <button onClick={() => { setCreateDefaults(null); setShowCreate(true); }} className="btn-primary" disabled={!selectedDocenteId} data-testid="appuntamento-create-button">
          <Plus size={16} /> Nuovo appuntamento
        </button>
      </div>

      {/* Docente selector (admin only) */}
      {isAdmin && (
        <div className="surface-card p-4 mb-4">
          <label className="label-eyebrow block mb-2">Docente</label>
          <div className="flex items-center gap-3 flex-wrap">
            <select className="input-base max-w-md" value={selectedDocenteId} onChange={(e) => setSelectedDocenteId(e.target.value)} data-testid="cal-docente-select">
              <option value="">— Seleziona un docente —</option>
              {docenti.map((d) => (<option key={d.id} value={d.id}>{d.nome} {d.cognome} ({d.slot_minuti || 60} min)</option>))}
            </select>
            {docenteSel && (
              <div className="text-xs text-[color:var(--text-2)]">
                Slot: <strong>{slotMinuti} min</strong> • Disponibilità: {orari.length ? `${toHHMM(dayRange.startMin)}–${toHHMM(dayRange.endMin)}` : "non configurata"}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty states */}
      {!selectedDocenteId ? (
        <div className="surface-card p-12 text-center">
          <CalIcon className="mx-auto mb-3 text-[color:var(--border)]" size={42} />
          <h3 className="font-display text-lg font-bold mb-1">Seleziona un docente</h3>
          <p className="text-sm text-[color:var(--text-2)]">Ogni docente ha la sua durata standard e i suoi orari. Scegli sopra il docente di cui vuoi vedere il calendario.</p>
        </div>
      ) : orari.length === 0 ? (
        <div className="surface-card p-12 text-center">
          <CalIcon className="mx-auto mb-3 text-[color:var(--border)]" size={42} />
          <h3 className="font-display text-lg font-bold mb-1">Nessuna disponibilità configurata</h3>
          <p className="text-sm text-[color:var(--text-2)] mb-4">Imposta prima gli orari del docente per vedere il suo calendario.</p>
          <a href={`/orari?docente=${selectedDocenteId}`} className="btn-primary inline-flex">Imposta orari</a>
        </div>
      ) : (
        <>
          {/* Toolbar */}
          <div className="surface-card p-3 mb-4 flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <button className="btn-secondary" onClick={() => setWeekStart(addDays(weekStart, -7))} data-testid="cal-prev"><ChevronLeft size={16} /></button>
              <button className="btn-secondary" onClick={() => setWeekStart(startOfWeek(new Date()))} data-testid="cal-today">Oggi</button>
              <button className="btn-secondary" onClick={() => setWeekStart(addDays(weekStart, 7))} data-testid="cal-next"><ChevronRight size={16} /></button>
              <div className="ml-3 font-display font-bold text-base">
                {fmtShort(days[0])} – {fmtShort(days[6])} {days[0].getFullYear()}
              </div>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-sm bg-[#E5F0E9] border border-[#C8DDD0]" /> Libero</div>
              <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-sm" style={{background: docenteSel?.color || "#2C4C3B"}} /> Prenotato</div>
              <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-sm bg-[color:var(--surface-2)] border border-[color:var(--border)]" /> Non disponibile</div>
            </div>
          </div>

          {/* Calendar settimanale per-docente */}
          <div className="surface-card p-2 sm:p-4 overflow-x-auto" data-testid="docente-calendar">
            <div className="min-w-[820px]">
              <div className="grid grid-cols-[70px_repeat(7,minmax(0,1fr))] gap-1.5 mb-2">
                <div></div>
                {days.map((d, i) => {
                  const isToday = fmtISO(d) === fmtISO(new Date());
                  return (
                    <div key={i} className={`text-center py-2 rounded-md ${isToday ? "bg-[color:var(--primary)] text-white" : "bg-[color:var(--surface-2)] text-[color:var(--text)]"}`}>
                      <div className="text-[11px] uppercase tracking-[0.15em] font-bold opacity-80">{GIORNI[i]}</div>
                      <div className="font-display font-bold text-base">{d.getDate()}</div>
                    </div>
                  );
                })}
              </div>

              {/* Rows of slots */}
              {(() => {
                const refSlots = [];
                for (let m = dayRange.startMin; m + slotMinuti <= dayRange.endMin; m += slotMinuti) {
                  refSlots.push({ m, label: toHHMM(m) });
                }
                return refSlots.map(({ m, label }) => (
                  <div key={m} className="grid grid-cols-[70px_repeat(7,minmax(0,1fr))] gap-1.5 mb-1.5">
                    <div className="text-right pr-2 text-[11px] text-[color:var(--text-2)] flex items-center justify-end">{label}</div>
                    {days.map((d, di) => {
                      const slots = computeDaySlots(d);
                      const slot = slots.find((s) => s.m === m);
                      const dayKey = fmtISO(d);
                      const ev = slot ? findAppointment(dayKey, m) : null;
                      if (ev) {
                        // Solo nello slot di START dell'appuntamento mostra il blocco; rowspan visuale by ratio
                        const startsHere = toMin(ev.dal) === m;
                        if (!startsHere) {
                          return <div key={`${m}-${di}`} className="rounded-md" style={{ background: docenteSel?.color, opacity: 0.85, minHeight: 36 }} />;
                        }
                        return (
                          <div
                            key={`${m}-${di}`}
                            className="rounded-md p-1.5 text-[11px] text-white shadow-sm relative group min-h-[36px]"
                            style={{ background: docenteSel?.color || "#2C4C3B" }}
                            data-testid={`appuntamento-${ev.id}`}
                            title={`${ev.cliente_nome} • ${ev.dal}-${ev.al}${ev.note ? ` • ${ev.note}` : ""}`}
                          >
                            <div className="font-bold truncate leading-tight">{ev.cliente_nome}</div>
                            <div className="text-[10px] opacity-90">{ev.dal}–{ev.al}</div>
                            <button onClick={() => remove(ev.id)} className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 text-white/80 hover:text-white" data-testid={`appuntamento-delete-${ev.id}`}><Trash2 size={11} /></button>
                          </div>
                        );
                      }
                      if (slot && slot.isAvailable) {
                        return (
                          <button
                            key={`${m}-${di}`}
                            onClick={() => onCellClick(d, slot)}
                            className="rounded-md min-h-[36px] bg-[#E5F0E9] border border-[#C8DDD0] hover:bg-[#D2E5DA] hover:border-[#A6C8B3] transition-colors text-[11px] font-semibold text-[color:var(--success)]"
                            data-testid={`cal-cell-${dayKey}-${slot.dal}`}
                          >
                            <span className="opacity-60 hover:opacity-100">+</span>
                          </button>
                        );
                      }
                      return (
                        <div
                          key={`${m}-${di}`}
                          className="rounded-md min-h-[36px] bg-[color:var(--surface-2)] border border-dashed border-[color:var(--border)]"
                          data-testid={`cal-cell-${dayKey}-${toHHMM(m)}-na`}
                          title="Fuori disponibilità"
                        />
                      );
                    })}
                  </div>
                ));
              })()}
            </div>
          </div>

          {loading && <div className="text-center text-[color:var(--text-2)] mt-3 text-sm">Caricamento…</div>}
        </>
      )}

      {showCreate && (
        <AppuntamentoModal
          onClose={() => setShowCreate(false)}
          onSaved={() => { setShowCreate(false); load(); }}
          defaults={createDefaults}
          docenti={docenti}
          clienti={clienti}
          isAdmin={isAdmin}
          currentDocenteId={user?.role === "docente" ? user.id : ""}
        />
      )}
    </div>
  );
}

function addMinutes(hhmm, minutes) {
  const [h, m] = hhmm.split(":").map(Number);
  const total = h * 60 + m + minutes;
  const hh = Math.floor(total / 60) % 24;
  const mm = total % 60;
  return `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
}

const GIORNI_LABEL = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"];

function AppuntamentoModal({ onClose, onSaved, defaults, docenti, clienti, isAdmin, currentDocenteId }) {
  const today = new Date().toISOString().slice(0, 10);
  // Se passato currentDocenteId, usa quello (anche per admin pre-seleziona dal calendario)
  const initialDocente = currentDocenteId || (isAdmin ? (docenti[0]?.id || "") : "");
  const initialDocObj = docenti.find((d) => d.id === initialDocente);
  const initialSlot = initialDocObj?.slot_minuti || 60;
  const initialDal = defaults?.dal || "09:00";
  const [form, setForm] = useState({
    docente_id: initialDocente,
    cliente_id: "",
    data: defaults?.data || today,
    dal: initialDal,
    al: defaults?.al || addMinutes(initialDal, initialSlot),
    note: "",
  });
  const [alunni, setAlunni] = useState([]);
  const [loadingAlunni, setLoadingAlunni] = useState(false);
  const [freeSlots, setFreeSlots] = useState([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [mode, setMode] = useState("existing"); // "existing" | "new"
  const [nuovoCliente, setNuovoCliente] = useState({ nome: "", cognome: "", email: "", cellulare: "" });
  const [recurrenceDates, setRecurrenceDates] = useState([]); // selected ISO dates
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  const docenteSel = docenti.find((d) => d.id === form.docente_id);
  const slot = docenteSel?.slot_minuti || 60;

  // Calcolare le prossime 6 settimane: stessa data + 7,14,21,28,35,42 giorni
  const dateObj = new Date(form.data + "T00:00:00");
  const weekday = (dateObj.getDay() + 6) % 7; // 0=Mon
  const recurrenceOptions = Array.from({ length: 6 }, (_, i) => {
    const d = new Date(dateObj);
    d.setDate(d.getDate() + 7 * (i + 1));
    return d.toISOString().slice(0, 10);
  });

  useEffect(() => {
    if (!form.docente_id) { setAlunni([]); return; }
    setLoadingAlunni(true);
    api.get(`/docenti/${form.docente_id}/alunni`).then(({ data }) => {
      setAlunni(data);
      if (!data.find((c) => c.id === form.cliente_id)) {
        setForm((f) => ({ ...f, cliente_id: data[0]?.id || "" }));
      }
    }).finally(() => setLoadingAlunni(false));
    setForm((f) => ({ ...f, al: addMinutes(f.dal, slot) }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.docente_id]);

  // Carica gli slot liberi quando cambia docente o data
  useEffect(() => {
    if (!form.docente_id || !form.data) { setFreeSlots([]); return; }
    setLoadingSlots(true);
    api.get("/disponibilita", { params: { docente_id: form.docente_id, data: form.data, slot_minuti: slot } })
      .then(({ data }) => setFreeSlots(data.slots || []))
      .catch(() => setFreeSlots([]))
      .finally(() => setLoadingSlots(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.docente_id, form.data, slot]);

  const onDalChange = (v) => {
    setForm((f) => ({ ...f, dal: v, al: addMinutes(v, slot) }));
  };

  const toggleRecurrence = (iso) => {
    setRecurrenceDates((prev) => prev.includes(iso) ? prev.filter((x) => x !== iso) : [...prev, iso]);
  };

  const onSubmit = async (e) => {
    e.preventDefault(); setBusy(true); setError(""); setResult(null);
    try {
      const slots = [{ data: form.data, dal: form.dal, al: form.al }];
      recurrenceDates.forEach((d) => slots.push({ data: d, dal: form.dal, al: form.al }));
      const payload = {
        docente_id: form.docente_id,
        slots,
        note: form.note || null,
        associa_alunno: true,
      };
      if (mode === "new") {
        if (!nuovoCliente.nome.trim() || !nuovoCliente.cognome.trim()) {
          setError("Nome e cognome del nuovo studente sono obbligatori");
          setBusy(false);
          return;
        }
        payload.nuovo_cliente = {
          nome: nuovoCliente.nome.trim(),
          cognome: nuovoCliente.cognome.trim(),
          email: nuovoCliente.email || null,
          cellulare: nuovoCliente.cellulare || null,
        };
      } else {
        if (!form.cliente_id) { setError("Seleziona uno studente"); setBusy(false); return; }
        payload.cliente_id = form.cliente_id;
      }
      const { data } = await api.post("/appuntamenti/bulk", payload);
      setResult(data);
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore");
    } finally { setBusy(false); }
  };

  const noAlunni = !loadingAlunni && alunni.length === 0 && !!form.docente_id;
  const giornoLabel = GIORNI_LABEL[weekday];

  if (result) {
    return (
      <Modal title="Risultato prenotazione" onClose={() => { setResult(null); onSaved(); }} size="md">
        <div className="space-y-3" data-testid="bulk-result">
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
          <button onClick={() => { setResult(null); onSaved(); }} className="btn-primary w-full justify-center" data-testid="bulk-result-close">Chiudi</button>
        </div>
      </Modal>
    );
  }

  return (
    <Modal title="Nuovo appuntamento" onClose={onClose} size="lg">
      <form onSubmit={onSubmit} className="space-y-4" data-testid="appuntamento-form">
        {isAdmin && (
          <div>
            <label className="block text-sm font-medium mb-1.5">Docente *</label>
            <select className="input-base" value={form.docente_id} onChange={(e) => setForm({ ...form, docente_id: e.target.value })} required data-testid="app-docente-select">
              {docenti.map((d) => (<option key={d.id} value={d.id}>{d.nome} {d.cognome}</option>))}
            </select>
            {docenteSel && (
              <div className="text-xs text-[color:var(--text-2)] mt-1">Durata standard: <strong>{slot} minuti</strong></div>
            )}
          </div>
        )}

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-sm font-medium mb-1.5">Data</label>
            <input type="date" className="input-base" value={form.data} onChange={(e) => { setForm({ ...form, data: e.target.value }); setRecurrenceDates([]); }} required data-testid="app-data-input" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Dalle ore</label>
            <input type="time" className="input-base" value={form.dal} onChange={(e) => onDalChange(e.target.value)} required data-testid="app-dal-input" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Alle ore</label>
            <input type="time" className="input-base" value={form.al} onChange={(e) => setForm({ ...form, al: e.target.value })} required data-testid="app-al-input" />
          </div>
        </div>

        {/* Slot liberi (chip) */}
        <div>
          <div className="label-eyebrow mb-2 flex items-center justify-between">
            <span>Slot liberi del giorno</span>
            {loadingSlots && <span className="text-[10px] normal-case tracking-normal text-[color:var(--text-2)]">caricamento…</span>}
          </div>
          {!loadingSlots && freeSlots.length === 0 ? (
            <div className="text-xs text-[color:var(--warning)] bg-[#FDF1E3] border border-[#EBD1A3] rounded-md px-3 py-2" data-testid="no-slots-warning">
              Nessuno slot libero per il docente in questa data. Verifica gli orari di disponibilità del docente o scegli un altro giorno.
            </div>
          ) : (
            <div className="flex flex-wrap gap-1.5" data-testid="free-slots">
              {freeSlots.map((s) => {
                const active = form.dal === s.dal && form.al === s.al;
                return (
                  <button
                    type="button"
                    key={`${s.dal}-${s.al}`}
                    onClick={() => setForm((f) => ({ ...f, dal: s.dal, al: s.al }))}
                    className={`px-2.5 py-1 rounded-md text-xs font-semibold border transition-colors ${active ? "bg-[color:var(--primary)] border-[color:var(--primary)] text-white" : "bg-[color:var(--surface)] border-[color:var(--border)] text-[color:var(--text)] hover:bg-[color:var(--surface-2)]"}`}
                    data-testid={`free-slot-${s.dal}`}
                  >
                    {s.dal}–{s.al}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Studente: existing / new tabs */}
        <div>
          <div className="flex gap-1.5 mb-3 p-1 rounded-lg bg-[color:var(--surface-2)]">
            <button type="button" onClick={() => setMode("existing")} className={`flex-1 py-1.5 px-3 text-sm rounded-md font-medium ${mode === "existing" ? "bg-white shadow-sm" : "text-[color:var(--text-2)]"}`} data-testid="mode-existing-button">Studente in archivio</button>
            <button type="button" onClick={() => setMode("new")} className={`flex-1 py-1.5 px-3 text-sm rounded-md font-medium ${mode === "new" ? "bg-white shadow-sm" : "text-[color:var(--text-2)]"}`} data-testid="mode-new-button">Nuovo studente</button>
          </div>

          {mode === "existing" ? (
            <div>
              <select className="input-base" value={form.cliente_id} onChange={(e) => setForm({ ...form, cliente_id: e.target.value })} disabled={noAlunni} data-testid="app-cliente-select">
                <option value="">{loadingAlunni ? "Caricamento…" : "Seleziona uno studente associato…"}</option>
                {alunni.map((c) => (<option key={c.id} value={c.id}>{c.cognome} {c.nome}</option>))}
              </select>
              {noAlunni && (
                <div className="text-xs text-[color:var(--warning)] mt-1.5">Nessun alunno associato. Crea un nuovo studente qui sotto o associane uno dalla scheda del docente.</div>
              )}
            </div>
          ) : (
            <div className="space-y-2.5">
              <div className="grid grid-cols-2 gap-2.5">
                <input className="input-base" placeholder="Nome" value={nuovoCliente.nome} onChange={(e) => setNuovoCliente({ ...nuovoCliente, nome: e.target.value })} data-testid="new-nome-input" />
                <input className="input-base" placeholder="Cognome" value={nuovoCliente.cognome} onChange={(e) => setNuovoCliente({ ...nuovoCliente, cognome: e.target.value })} data-testid="new-cognome-input" />
              </div>
              <input type="email" className="input-base" placeholder="Email (opzionale)" value={nuovoCliente.email} onChange={(e) => setNuovoCliente({ ...nuovoCliente, email: e.target.value })} data-testid="new-email-input" />
              <input className="input-base" placeholder="Telefono (opzionale)" value={nuovoCliente.cellulare} onChange={(e) => setNuovoCliente({ ...nuovoCliente, cellulare: e.target.value })} data-testid="new-tel-input" />
              <div className="text-xs text-[color:var(--text-2)]">Lo studente verrà creato e automaticamente associato al docente.</div>
            </div>
          )}
        </div>

        {/* Ricorrenza */}
        <div className="border-t border-[color:var(--border)] pt-3.5">
          <div className="label-eyebrow mb-2">Vuoi prenotare anche i prossimi {giornoLabel}? (stesso orario)</div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {recurrenceOptions.map((iso) => {
              const checked = recurrenceDates.includes(iso);
              const d = new Date(iso + "T00:00:00");
              const label = d.toLocaleDateString("it-IT", { day: "2-digit", month: "2-digit", year: "numeric" });
              return (
                <label key={iso} className={`flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer border ${checked ? "border-[color:var(--primary)] bg-[color:var(--primary)]/5" : "border-[color:var(--border)]"}`} data-testid={`recurrence-${iso}`}>
                  <input type="checkbox" checked={checked} onChange={() => toggleRecurrence(iso)} className="accent-[color:var(--primary)]" />
                  <span className="text-sm font-medium">{label}</span>
                </label>
              );
            })}
          </div>
          {recurrenceDates.length > 0 && (
            <div className="text-xs text-[color:var(--text-2)] mt-2">+{recurrenceDates.length} prenotazione/i aggiuntive verranno create. Gli slot già occupati saranno saltati automaticamente.</div>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1.5">Note</label>
          <textarea rows={2} className="input-base" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} data-testid="app-note-input" />
        </div>

        {error && <div className="text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="app-form-error">{error}</div>}
        <div className="flex gap-2 pt-1 sticky bottom-0 bg-[color:var(--surface)]">
          <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center" data-testid="app-cancel-button">Annulla</button>
          <button type="submit" disabled={busy} className="btn-primary flex-1 justify-center" data-testid="app-submit-button">
            {busy ? "Salvataggio…" : `Registra${recurrenceDates.length > 0 ? ` (${recurrenceDates.length + 1})` : ""}`}
          </button>
        </div>
      </form>
    </Modal>
  );
}
