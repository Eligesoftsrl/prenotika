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

export default function Appuntamenti() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [weekStart, setWeekStart] = useState(startOfWeek(new Date()));
  const [docenti, setDocenti] = useState([]);
  const [clienti, setClienti] = useState([]);
  const [items, setItems] = useState([]);
  const [filterDocente, setFilterDocente] = useState("");
  const [loading, setLoading] = useState(true);

  const [showCreate, setShowCreate] = useState(false);
  const [createDefaults, setCreateDefaults] = useState(null);

  const days = useMemo(() => Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)), [weekStart]);
  const da = fmtISO(days[0]);
  const a = fmtISO(days[6]);

  useEffect(() => {
    api.get("/docenti").then(({ data }) => setDocenti(data));
    api.get("/clienti").then(({ data }) => setClienti(data));
  }, []);

  const load = async () => {
    setLoading(true);
    try {
      const params = { data_da: da, data_a: a };
      if (filterDocente) params.docente_id = filterDocente;
      const { data } = await api.get("/appuntamenti", { params });
      setItems(data);
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, [da, a, filterDocente]);

  const docenteColor = (id) => docenti.find((d) => d.id === id)?.color || "#2C4C3B";

  const itemsByDay = useMemo(() => {
    const map = {};
    days.forEach((d) => { map[fmtISO(d)] = []; });
    items.forEach((it) => { if (map[it.data]) map[it.data].push(it); });
    return map;
  }, [items, days]);

  const onCellClick = (dayDate, hour) => {
    if (!isAdmin && user?.role !== "docente") return;
    const dal = `${String(hour).padStart(2, "0")}:00`;
    const al = `${String(hour + 1).padStart(2, "0")}:00`;
    setCreateDefaults({ data: fmtISO(dayDate), dal, al });
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
          <p className="text-[color:var(--text-2)] mt-1">Clicca una cella libera per creare un appuntamento.</p>
        </div>
        <button onClick={() => { setCreateDefaults(null); setShowCreate(true); }} className="btn-primary" data-testid="appuntamento-create-button">
          <Plus size={16} /> Nuovo appuntamento
        </button>
      </div>

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
        {isAdmin && (
          <div className="flex items-center gap-2">
            <span className="label-eyebrow">Filtra docente</span>
            <select className="input-base" value={filterDocente} onChange={(e) => setFilterDocente(e.target.value)} data-testid="cal-filter-docente">
              <option value="">Tutti</option>
              {docenti.map((d) => (<option key={d.id} value={d.id}>{d.nome} {d.cognome}</option>))}
            </select>
          </div>
        )}
      </div>

      {/* Calendar */}
      <div className="surface-card p-2 sm:p-4 overflow-x-auto">
        <div className="min-w-[820px]">
          {/* day header */}
          <div className="grid grid-cols-[60px_repeat(7,minmax(0,1fr))] gap-2 mb-2">
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

          <div className="relative">
            {/* Hour grid */}
            <div className="grid grid-cols-[60px_repeat(7,minmax(0,1fr))] gap-2">
              {HOURS.map((h) => (
                <React.Fragment key={h}>
                  <div className="text-right pr-2 text-[11px] text-[color:var(--text-2)] -mt-2">{`${String(h).padStart(2,'0')}:00`}</div>
                  {days.map((d, i) => (
                    <button
                      key={`${h}-${i}`}
                      onClick={() => onCellClick(d, h)}
                      className="h-14 border-t border-[color:var(--border)] hover:bg-[color:var(--surface-2)] transition-colors"
                      data-testid={`cal-cell-${fmtISO(d)}-${h}`}
                    />
                  ))}
                </React.Fragment>
              ))}
            </div>

            {/* Events overlay */}
            <div className="absolute inset-0 grid grid-cols-[60px_repeat(7,minmax(0,1fr))] gap-2 pointer-events-none">
              <div></div>
              {days.map((d, i) => {
                const dayKey = fmtISO(d);
                const dayStartMin = HOURS[0] * 60;
                const totalMin = (HOURS[HOURS.length - 1] + 1 - HOURS[0]) * 60;
                return (
                  <div key={i} className="relative">
                    {itemsByDay[dayKey]?.map((ev) => {
                      const top = ((toMin(ev.dal) - dayStartMin) / totalMin) * 100;
                      const height = ((toMin(ev.al) - toMin(ev.dal)) / totalMin) * 100;
                      const color = docenteColor(ev.docente_id);
                      return (
                        <div
                          key={ev.id}
                          className="absolute left-0.5 right-0.5 rounded-md p-1.5 pointer-events-auto text-[11px] text-white shadow-sm overflow-hidden hover:z-10 hover:scale-[1.02] transition-transform"
                          style={{ top: `${top}%`, height: `${height}%`, background: color, minHeight: 30, opacity: ev.stato === "annullato" ? 0.4 : 1 }}
                          data-testid={`appuntamento-${ev.id}`}
                          title={`${ev.cliente_nome} • ${ev.dal}-${ev.al}`}
                        >
                          <div className="flex items-start justify-between gap-1">
                            <div className="min-w-0">
                              <div className="font-bold truncate leading-tight">{ev.cliente_nome}</div>
                              <div className="text-[10px] opacity-90 truncate">{ev.dal} – {ev.al}</div>
                              <div className="text-[10px] opacity-90 truncate">{ev.docente_nome}</div>
                            </div>
                            <button onClick={() => remove(ev.id)} className="text-white/80 hover:text-white shrink-0" data-testid={`appuntamento-delete-${ev.id}`}><Trash2 size={11} /></button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

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

function AppuntamentoModal({ onClose, onSaved, defaults, docenti, clienti, isAdmin, currentDocenteId }) {
  const today = new Date().toISOString().slice(0, 10);
  const [form, setForm] = useState({
    docente_id: isAdmin ? (docenti[0]?.id || "") : currentDocenteId,
    cliente_id: clienti[0]?.id || "",
    data: defaults?.data || today,
    dal: defaults?.dal || "09:00",
    al: defaults?.al || "10:00",
    note: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault(); setBusy(true); setError("");
    try {
      await api.post("/appuntamenti", form);
      onSaved();
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore");
    } finally { setBusy(false); }
  };

  return (
    <Modal title="Nuovo appuntamento" onClose={onClose}>
      <form onSubmit={onSubmit} className="space-y-3.5" data-testid="appuntamento-form">
        {isAdmin && (
          <div>
            <label className="block text-sm font-medium mb-1.5">Docente *</label>
            <select className="input-base" value={form.docente_id} onChange={(e) => setForm({ ...form, docente_id: e.target.value })} required data-testid="app-docente-select">
              {docenti.map((d) => (<option key={d.id} value={d.id}>{d.nome} {d.cognome}</option>))}
            </select>
          </div>
        )}
        <div>
          <label className="block text-sm font-medium mb-1.5">Cliente *</label>
          <select className="input-base" value={form.cliente_id} onChange={(e) => setForm({ ...form, cliente_id: e.target.value })} required data-testid="app-cliente-select">
            <option value="">Seleziona…</option>
            {clienti.map((c) => (<option key={c.id} value={c.id}>{c.cognome} {c.nome}</option>))}
          </select>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-sm font-medium mb-1.5">Data</label>
            <input type="date" className="input-base" value={form.data} onChange={(e) => setForm({ ...form, data: e.target.value })} required data-testid="app-data-input" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Dalle</label>
            <input type="time" className="input-base" value={form.dal} onChange={(e) => setForm({ ...form, dal: e.target.value })} required data-testid="app-dal-input" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Alle</label>
            <input type="time" className="input-base" value={form.al} onChange={(e) => setForm({ ...form, al: e.target.value })} required data-testid="app-al-input" />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1.5">Note</label>
          <textarea rows={3} className="input-base" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} data-testid="app-note-input" />
        </div>
        {error && <div className="text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="app-form-error">{error}</div>}
        <div className="flex gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center" data-testid="app-cancel-button">Annulla</button>
          <button type="submit" disabled={busy} className="btn-primary flex-1 justify-center" data-testid="app-submit-button">{busy ? "Salvataggio…" : "Crea appuntamento"}</button>
        </div>
      </form>
    </Modal>
  );
}
