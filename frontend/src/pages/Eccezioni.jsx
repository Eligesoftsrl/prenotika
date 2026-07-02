import React, { useEffect, useState, useCallback } from "react";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { tipologiaLabels } from "@/lib/tipologia";
import { Plane, Plus, Trash2, Calendar as CalendarIcon, Clock, AlertCircle } from "lucide-react";

function fmtIT(s) {
  if (!s) return "";
  const d = new Date(s + "T00:00:00");
  return d.toLocaleDateString("it-IT", { day: "2-digit", month: "long", year: "numeric" });
}

export default function Eccezioni() {
  const { user, studio } = useAuth();
  const L = tipologiaLabels(studio?.tipologia);
  const isAdmin = user?.role === "admin";

  const [docenti, setDocenti] = useState([]);
  const [docenteId, setDocenteId] = useState("");
  const [eccezioni, setEccezioni] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ data_inizio: "", data_fine: "", motivo: "", tipo: "chiuso", ora_inizio: "", ora_fine: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAdmin) { setDocenteId(user?.id || ""); return; }
    api.get("/docenti").then(({ data }) => {
      setDocenti(data || []);
      if (data && data.length && !docenteId) setDocenteId(data[0].id);
    });
  }, [user, isAdmin]);

  const load = useCallback(async () => {
    if (!docenteId) return;
    const params = isAdmin ? `?docente_id=${docenteId}` : "";
    const { data } = await api.get(`/eccezioni${params}`);
    setEccezioni(data || []);
  }, [docenteId, isAdmin]);

  useEffect(() => { load(); }, [load]);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      const payload = {
        data_inizio: form.data_inizio,
        data_fine: form.data_fine || form.data_inizio,
        motivo: form.motivo || null,
        tipo: form.tipo,
      };
      if (form.tipo === "personalizzato") {
        payload.ora_inizio = form.ora_inizio;
        payload.ora_fine = form.ora_fine;
      }
      if (isAdmin) payload.docente_id = docenteId;
      await api.post("/eccezioni", payload);
      setShowForm(false);
      setForm({ data_inizio: "", data_fine: "", motivo: "", tipo: "chiuso", ora_inizio: "", ora_fine: "" });
      await load();
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore");
    } finally { setBusy(false); }
  };

  const remove = async (id) => {
    if (!window.confirm("Eliminare questa eccezione?")) return;
    await api.delete(`/eccezioni/${id}`);
    await load();
  };

  const docenteSel = docenti.find((d) => d.id === docenteId);

  return (
    <div data-testid="eccezioni-page" className="max-w-4xl">
      <div className="mb-7 flex items-start justify-between flex-wrap gap-3">
        <div>
          <div className="label-eyebrow mb-1.5">Pianificazione</div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight">Ferie & Eccezioni</h1>
          <p className="text-[color:var(--text-2)] mt-1">Giorni di chiusura, ferie o blocchi orari del professionista. Nessun appuntamento potrà essere creato in queste fasce.</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary" data-testid="eccezione-add-btn"><Plus size={15} /> Nuova eccezione</button>
      </div>

      {isAdmin && (
        <div className="surface-card p-4 mb-5">
          <div className="label-eyebrow mb-2">{L.docenti}</div>
          <select className="input-base max-w-md" value={docenteId} onChange={(e) => setDocenteId(e.target.value)} data-testid="eccezioni-docente-select">
            {docenti.map((d) => <option key={d.id} value={d.id}>{d.nome} {d.cognome}</option>)}
          </select>
        </div>
      )}

      {showForm && (
        <form onSubmit={submit} className="surface-card p-5 mb-5 anim-fade-up" data-testid="eccezione-form">
          <div className="flex items-center gap-2 mb-4"><Plane size={16} className="text-[color:var(--primary)]" /><h3 className="font-display font-bold">Nuova eccezione {docenteSel ? `· ${docenteSel.nome} ${docenteSel.cognome}` : ""}</h3></div>
          <div className="grid sm:grid-cols-2 gap-3 mb-3">
            <div><label className="label-eyebrow block mb-1.5">Dal *</label><input required type="date" className="input-base" value={form.data_inizio} onChange={(e) => setForm({ ...form, data_inizio: e.target.value })} data-testid="eccezione-data-inizio" /></div>
            <div><label className="label-eyebrow block mb-1.5">Al (opzionale)</label><input type="date" className="input-base" value={form.data_fine} onChange={(e) => setForm({ ...form, data_fine: e.target.value })} data-testid="eccezione-data-fine" /></div>
          </div>
          <div className="grid sm:grid-cols-2 gap-3 mb-3">
            <div>
              <label className="label-eyebrow block mb-1.5">Tipo</label>
              <select className="input-base" value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })} data-testid="eccezione-tipo">
                <option value="chiuso">Chiuso tutto il giorno</option>
                <option value="personalizzato">Solo una fascia oraria</option>
              </select>
            </div>
            <div><label className="label-eyebrow block mb-1.5">Motivo</label><input className="input-base" placeholder="Ferie, malattia, congresso..." value={form.motivo} onChange={(e) => setForm({ ...form, motivo: e.target.value })} data-testid="eccezione-motivo" /></div>
          </div>
          {form.tipo === "personalizzato" && (
            <div className="grid sm:grid-cols-2 gap-3 mb-3">
              <div><label className="label-eyebrow block mb-1.5">Dalle</label><input type="time" className="input-base" value={form.ora_inizio} onChange={(e) => setForm({ ...form, ora_inizio: e.target.value })} data-testid="eccezione-ora-inizio" /></div>
              <div><label className="label-eyebrow block mb-1.5">Alle</label><input type="time" className="input-base" value={form.ora_fine} onChange={(e) => setForm({ ...form, ora_fine: e.target.value })} data-testid="eccezione-ora-fine" /></div>
            </div>
          )}
          {error && <div className="text-sm text-[color:var(--error)] mb-3" data-testid="eccezione-form-error">{error}</div>}
          <div className="flex gap-2 justify-end">
            <button type="button" onClick={() => { setShowForm(false); setError(""); }} className="btn-secondary">Annulla</button>
            <button type="submit" disabled={busy} className="btn-primary" data-testid="eccezione-submit">{busy ? "Salvataggio…" : "Salva eccezione"}</button>
          </div>
        </form>
      )}

      <div className="surface-card overflow-hidden">
        {eccezioni.length === 0 ? (
          <div className="p-10 text-center text-[color:var(--text-2)]">
            <CalendarIcon size={36} strokeWidth={1.4} className="mx-auto mb-3 text-[color:var(--text-3)]" />
            <p>Nessuna eccezione registrata.</p>
            <p className="text-xs mt-1">Aggiungi ferie, festività o blocchi orari per impedire prenotazioni indesiderate.</p>
          </div>
        ) : (
          <table className="table-clean w-full">
            <thead>
              <tr><th>Periodo</th><th>Tipo</th><th>Motivo</th><th></th></tr>
            </thead>
            <tbody>
              {eccezioni.map((e) => (
                <tr key={e.id} data-testid={`eccezione-row-${e.id}`}>
                  <td>
                    <div className="font-semibold flex items-center gap-1.5"><CalendarIcon size={13} className="text-[color:var(--primary)]" />{fmtIT(e.data_inizio)}{e.data_fine && e.data_fine !== e.data_inizio ? ` → ${fmtIT(e.data_fine)}` : ""}</div>
                    {e.tipo === "personalizzato" && e.ora_inizio && (
                      <div className="text-xs text-[color:var(--text-2)] mt-0.5 flex items-center gap-1"><Clock size={11} /> {e.ora_inizio} – {e.ora_fine}</div>
                    )}
                  </td>
                  <td>
                    {e.tipo === "chiuso" ? (
                      <span className="pill pill-error"><AlertCircle size={11} className="mr-1" /> Chiuso</span>
                    ) : (
                      <span className="pill pill-warning">Fascia</span>
                    )}
                  </td>
                  <td className="text-[color:var(--text-2)]">{e.motivo || "—"}</td>
                  <td className="text-right">
                    <button onClick={() => remove(e.id)} className="btn-danger" data-testid={`eccezione-delete-${e.id}`}><Trash2 size={12} /> Elimina</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
