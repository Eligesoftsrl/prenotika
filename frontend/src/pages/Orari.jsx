import React, { useEffect, useMemo, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Plus, Trash2, Clock } from "lucide-react";
import { Modal } from "./Docenti";

const GIORNI = [
  { idx: 0, label: "Lun" },
  { idx: 1, label: "Mar" },
  { idx: 2, label: "Mer" },
  { idx: 3, label: "Gio" },
  { idx: 4, label: "Ven" },
  { idx: 5, label: "Sab" },
  { idx: 6, label: "Dom" },
];

const HOURS = Array.from({ length: 14 }, (_, i) => i + 7); // 7..20

function toMin(hhmm) { const [h, m] = hhmm.split(":").map(Number); return h * 60 + m; }

export default function Orari() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [searchParams] = useSearchParams();
  const queryDocente = searchParams.get("docente");

  const [docenti, setDocenti] = useState([]);
  const [docenteId, setDocenteId] = useState(user?.role === "docente" ? user.id : (queryDocente || ""));
  const [orari, setOrari] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ giorno: 0, dal: "09:00", al: "13:00" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (isAdmin) {
      api.get("/docenti").then(({ data }) => {
        setDocenti(data);
        if (!docenteId && data[0]) setDocenteId(data[0].id);
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin]);

  const load = useCallback(async () => {
    if (!docenteId) { setOrari([]); setLoading(false); return; }
    setLoading(true);
    try {
      const { data } = await api.get("/orari", { params: { docente_id: docenteId } });
      setOrari(data);
    } finally { setLoading(false); }
  }, [docenteId]);
  useEffect(() => { load(); }, [load]);

  const onAdd = async (e) => {
    e.preventDefault(); setBusy(true); setError("");
    try {
      await api.post("/orari", { giorno: Number(form.giorno), dal: form.dal, al: form.al, docente_id: isAdmin ? docenteId : undefined });
      setShowAdd(false); await load();
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore");
    } finally { setBusy(false); }
  };

  const remove = async (id) => {
    if (!window.confirm("Eliminare questa fascia oraria?")) return;
    await api.delete(`/orari/${id}`);
    await load();
  };

  const orariByDay = useMemo(() => {
    const map = {};
    for (let i = 0; i < 7; i++) map[i] = [];
    orari.forEach((o) => map[o.giorno].push(o));
    Object.values(map).forEach((arr) => arr.sort((a, b) => toMin(a.dal) - toMin(b.dal)));
    return map;
  }, [orari]);

  return (
    <div data-testid="orari-page">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <div className="label-eyebrow mb-1.5">Disponibilità</div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight">Orari settimanali</h1>
          <p className="text-[color:var(--text-2)] mt-1">{isAdmin ? "Imposta la disponibilità ricorrente di ogni docente." : "Imposta la tua disponibilità settimanale ricorrente."}</p>
        </div>
        <button onClick={() => { setForm({ giorno: 0, dal: "09:00", al: "13:00" }); setShowAdd(true); setError(""); }} className="btn-primary" disabled={isAdmin && !docenteId} data-testid="orario-add-button">
          <Plus size={16} /> Aggiungi fascia
        </button>
      </div>

      {isAdmin && (
        <div className="surface-card p-4 mb-5">
          <label className="label-eyebrow block mb-2">Docente</label>
          <select className="input-base max-w-md" value={docenteId} onChange={(e) => setDocenteId(e.target.value)} data-testid="orari-docente-select">
            {docenti.map((d) => (<option key={d.id} value={d.id}>{d.nome} {d.cognome}</option>))}
          </select>
        </div>
      )}

      <div className="surface-card p-3 sm:p-5 overflow-x-auto">
        <div className="min-w-[720px]">
          {/* Header */}
          <div className="grid grid-cols-[60px_repeat(7,minmax(0,1fr))] gap-2 mb-2">
            <div></div>
            {GIORNI.map((g) => (
              <div key={g.idx} className="text-center text-xs uppercase tracking-[0.15em] font-bold text-[color:var(--text-2)] py-1.5 bg-[color:var(--surface-2)] rounded-md">{g.label}</div>
            ))}
          </div>
          <div className="relative">
            <div className="grid grid-cols-[60px_repeat(7,minmax(0,1fr))] gap-2">
              {HOURS.map((h) => (
                <React.Fragment key={h}>
                  <div className="text-right pr-2 text-[11px] text-[color:var(--text-2)] -mt-2">{`${String(h).padStart(2,'0')}:00`}</div>
                  {GIORNI.map((g) => (
                    <div key={`${h}-${g.idx}`} className="h-12 border-t border-[color:var(--border)]"></div>
                  ))}
                </React.Fragment>
              ))}
            </div>
            {/* Overlay blocks */}
            <div className="absolute inset-0 grid grid-cols-[60px_repeat(7,minmax(0,1fr))] gap-2 pointer-events-none">
              <div></div>
              {GIORNI.map((g) => {
                const dayStartMin = HOURS[0] * 60;
                const totalMin = (HOURS[HOURS.length - 1] + 1 - HOURS[0]) * 60;
                return (
                  <div key={g.idx} className="relative">
                    {orariByDay[g.idx]?.map((o) => {
                      const top = ((toMin(o.dal) - dayStartMin) / totalMin) * 100;
                      const height = ((toMin(o.al) - toMin(o.dal)) / totalMin) * 100;
                      return (
                        <div
                          key={o.id}
                          className="absolute left-0 right-0 rounded-md text-white text-[11px] px-2 py-1 pointer-events-auto flex flex-col justify-between shadow-sm"
                          style={{ top: `${top}%`, height: `${height}%`, background: "var(--primary)", minHeight: 28 }}
                          data-testid={`orario-block-${o.id}`}
                        >
                          <div className="font-semibold leading-tight">{o.dal}–{o.al}</div>
                          <button
                            onClick={() => remove(o.id)}
                            className="self-end text-white/85 hover:text-white"
                            title="Elimina"
                            data-testid={`orario-delete-${o.id}`}
                          >
                            <Trash2 size={12} />
                          </button>
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

      {orari.length === 0 && !loading && (
        <div className="text-center text-sm text-[color:var(--text-2)] mt-4">
          <Clock className="inline mr-2 text-[color:var(--border)]" size={16} /> Nessuna fascia impostata. Aggiungi una fascia per iniziare.
        </div>
      )}

      {showAdd && (
        <Modal title="Nuova fascia oraria" onClose={() => setShowAdd(false)}>
          <form onSubmit={onAdd} className="space-y-3.5" data-testid="orario-form">
            <div>
              <label className="block text-sm font-medium mb-1.5">Giorno</label>
              <select className="input-base" value={form.giorno} onChange={(e) => setForm({ ...form, giorno: e.target.value })} data-testid="orario-giorno-select">
                {GIORNI.map((g) => (<option key={g.idx} value={g.idx}>{g.label}</option>))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1.5">Dalle</label>
                <input type="time" className="input-base" value={form.dal} onChange={(e) => setForm({ ...form, dal: e.target.value })} required data-testid="orario-dal-input" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5">Alle</label>
                <input type="time" className="input-base" value={form.al} onChange={(e) => setForm({ ...form, al: e.target.value })} required data-testid="orario-al-input" />
              </div>
            </div>
            {error && <div className="text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="orario-form-error">{error}</div>}
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={() => setShowAdd(false)} className="btn-secondary flex-1 justify-center">Annulla</button>
              <button type="submit" disabled={busy} className="btn-primary flex-1 justify-center" data-testid="orario-submit-button">{busy ? "Salvataggio…" : "Aggiungi"}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
