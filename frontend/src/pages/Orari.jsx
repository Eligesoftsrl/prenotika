import React, { useEffect, useMemo, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Plus, Trash2, Clock, Copy } from "lucide-react";
import { Modal } from "./Docenti";
import { tipologiaLabels } from "@/lib/tipologia";

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
  const { user, studio } = useAuth();
  const L = tipologiaLabels(studio?.tipologia, studio?.custom_labels);
  const isAdmin = user?.role === "admin";
  const [searchParams] = useSearchParams();
  const queryDocente = searchParams.get("docente");

  const [docenti, setDocenti] = useState([]);
  const [docenteId, setDocenteId] = useState(user?.role === "docente" ? user.id : (queryDocente || ""));
  const [orari, setOrari] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [giorniSel, setGiorniSel] = useState([0]);
  const [fasce, setFasce] = useState([{ dal: "09:00", al: "13:00" }]);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (isAdmin) {
      api.get("/docenti").then(({ data }) => {
        setDocenti(data);
        if (data[0]) setDocenteId((prev) => prev || data[0].id);
      });
    }
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
    e.preventDefault(); setBusy(true); setError(""); setInfo("");
    try {
      const payload = {
        giorni: giorniSel.map(Number),
        fasce: fasce.filter((f) => f.dal && f.al),
      };
      if (isAdmin) payload.docente_id = docenteId;
      const { data } = await api.post("/orari/bulk", payload);
      setShowAdd(false);
      if (data.skipped && data.skipped.length) {
        setInfo(`${data.created} fasce create · ${data.skipped.length} saltate per sovrapposizione`);
      }
      await load();
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore");
    } finally { setBusy(false); }
  };

  const toggleGiorno = (idx) => {
    setGiorniSel((prev) => prev.includes(idx) ? prev.filter((x) => x !== idx) : [...prev, idx].sort((a, b) => a - b));
  };
  const copiaLavorativi = () => setGiorniSel([0, 1, 2, 3, 4]);
  const copiaTutti = () => setGiorniSel([0, 1, 2, 3, 4, 5, 6]);
  const addFascia = () => setFasce((f) => [...f, { dal: "15:00", al: "19:00" }]);
  const removeFascia = (i) => setFasce((f) => f.length > 1 ? f.filter((_, idx) => idx !== i) : f);
  const updateFascia = (i, key, val) => setFasce((f) => f.map((x, idx) => idx === i ? { ...x, [key]: val } : x));

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
        <button onClick={() => { setGiorniSel([0]); setFasce([{ dal: "09:00", al: "13:00" }]); setShowAdd(true); setError(""); setInfo(""); }} className="btn-primary" disabled={isAdmin && !docenteId} data-testid="orario-add-button">
          <Plus size={16} /> Aggiungi fasce
        </button>
      </div>

      {info && (
        <div className="mb-4 p-3 rounded-lg bg-[#F1F5FF] border border-[#DCE3F4] text-sm text-[color:var(--primary)]" data-testid="orari-info">
          {info}
        </div>
      )}

      {isAdmin && (
        <div className="surface-card p-4 mb-5">
          <label className="label-eyebrow block mb-2">{L.docente}</label>
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
        <Modal title="Aggiungi fasce orarie" onClose={() => setShowAdd(false)}>
          <form onSubmit={onAdd} className="space-y-4" data-testid="orario-form">

            {/* Giorni multi-select */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="label-eyebrow">Applica ai giorni</label>
                <div className="flex gap-1.5 text-xs">
                  <button type="button" onClick={copiaLavorativi} className="text-[color:var(--primary)] hover:underline inline-flex items-center gap-1" data-testid="orario-preset-lavorativi">
                    <Copy size={11} /> Lun-Ven
                  </button>
                  <span className="text-[color:var(--text-3)]">·</span>
                  <button type="button" onClick={copiaTutti} className="text-[color:var(--primary)] hover:underline" data-testid="orario-preset-tutti">
                    Tutti
                  </button>
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5" data-testid="orario-giorni-chips">
                {GIORNI.map((g) => {
                  const sel = giorniSel.includes(g.idx);
                  return (
                    <button
                      key={g.idx}
                      type="button"
                      onClick={() => toggleGiorno(g.idx)}
                      className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                        sel
                          ? "bg-[color:var(--primary)] text-white border-[color:var(--primary)] shadow-sm"
                          : "bg-white text-[color:var(--text)] border-[color:var(--border)] hover:border-[color:var(--primary)]"
                      }`}
                      data-testid={`orario-giorno-${g.idx}`}
                    >
                      {g.label}
                    </button>
                  );
                })}
              </div>
              <div className="text-xs text-[color:var(--text-2)] mt-1.5">
                {giorniSel.length === 0 ? "Nessun giorno selezionato" : giorniSel.length === 1 ? "1 giorno selezionato" : `${giorniSel.length} giorni selezionati`}
              </div>
            </div>

            {/* Fasce orarie multi-riga */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="label-eyebrow">Fasce orarie</label>
                <button type="button" onClick={addFascia} className="text-xs text-[color:var(--primary)] hover:underline inline-flex items-center gap-1" data-testid="orario-add-fascia">
                  <Plus size={12} /> Aggiungi fascia
                </button>
              </div>
              <div className="space-y-2">
                {fasce.map((f, i) => (
                  <div key={i} className="grid grid-cols-[1fr_1fr_auto] gap-2 items-end" data-testid={`orario-fascia-${i}`}>
                    <div>
                      <div className="text-[10px] text-[color:var(--text-2)] mb-1 uppercase tracking-wide">Dalle</div>
                      <input type="time" className="input-base" value={f.dal} onChange={(e) => updateFascia(i, "dal", e.target.value)} required data-testid={`orario-fascia-${i}-dal`} />
                    </div>
                    <div>
                      <div className="text-[10px] text-[color:var(--text-2)] mb-1 uppercase tracking-wide">Alle</div>
                      <input type="time" className="input-base" value={f.al} onChange={(e) => updateFascia(i, "al", e.target.value)} required data-testid={`orario-fascia-${i}-al`} />
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFascia(i)}
                      disabled={fasce.length === 1}
                      className="p-2 text-[color:var(--text-2)] hover:text-[color:var(--error)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                      title="Rimuovi fascia"
                      data-testid={`orario-fascia-${i}-remove`}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
              <div className="text-xs text-[color:var(--text-2)] mt-2 leading-relaxed">
                Verranno create <strong>{giorniSel.length * fasce.length}</strong> fasce ({giorniSel.length} giorni × {fasce.length} fasce). Le fasce che si sovrappongono a orari esistenti saranno saltate.
              </div>
            </div>

            {error && <div className="text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="orario-form-error">{error}</div>}
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={() => setShowAdd(false)} className="btn-secondary flex-1 justify-center">Annulla</button>
              <button type="submit" disabled={busy || giorniSel.length === 0 || fasce.length === 0} className="btn-primary flex-1 justify-center" data-testid="orario-submit-button">
                {busy ? "Salvataggio…" : `Salva ${giorniSel.length * fasce.length} fasce`}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
