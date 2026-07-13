import React, { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ArrowLeft, Plus, Trash2, Users as UsersIcon } from "lucide-react";
import { Modal } from "./Docenti";
import { tipologiaLabels } from "@/lib/tipologia";

export default function DocenteAlunni() {
  const { studio } = useAuth();
  const L = tipologiaLabels(studio?.tipologia, studio?.custom_labels);
  const { id: docenteId } = useParams();
  const [docente, setDocente] = useState(null);
  const [alunni, setAlunni] = useState([]);
  const [tuttiClienti, setTuttiClienti] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [docs, mine, tutti] = await Promise.all([
        api.get("/docenti"),
        api.get(`/docenti/${docenteId}/alunni`),
        api.get("/clienti"),
      ]);
      const d = docs.data.find((x) => x.id === docenteId);
      setDocente(d || null);
      setAlunni(mine.data);
      setTuttiClienti(tutti.data);
    } finally { setLoading(false); }
  }, [docenteId]);
  useEffect(() => { load(); }, [load]);

  const associate = async (e) => {
    e.preventDefault();
    if (!selected) return;
    setBusy(true); setError("");
    try {
      await api.post(`/docenti/${docenteId}/alunni/${selected}`);
      setShowAdd(false); setSelected(""); await load();
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore");
    } finally { setBusy(false); }
  };

  const disassocia = async (c) => {
    if (!window.confirm(`Rimuovere ${c.nome} ${c.cognome} dai ${L.clienti.toLowerCase()} del ${L.docente.toLowerCase()}?`)) return;
    await api.delete(`/docenti/${docenteId}/alunni/${c.id}`);
    await load();
  };

  const giaAssociati = new Set(alunni.map((a) => a.id));
  const disponibili = tuttiClienti.filter((c) => !giaAssociati.has(c.id));

  return (
    <div data-testid="docente-alunni-page">
      <Link to="/docenti" className="inline-flex items-center gap-1.5 text-sm text-[color:var(--text-2)] hover:text-[color:var(--text)] mb-4">
        <ArrowLeft size={14} /> Tutti i {L.docenti.toLowerCase()}
      </Link>
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <div className="label-eyebrow mb-1.5">{L.clienti} associati</div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight">
            {docente ? `${docente.nome} ${docente.cognome}` : L.docente}
          </h1>
          <p className="text-[color:var(--text-2)] mt-1">Gestisci i {L.clienti.toLowerCase()} assegnati a questo {L.docente.toLowerCase()}.</p>
        </div>
        <button onClick={() => { setSelected(""); setShowAdd(true); setError(""); }} className="btn-primary" data-testid="associa-alunno-button" disabled={disponibili.length === 0}>
          <Plus size={16} /> {L.associa_alunno}
        </button>
      </div>

      <div className="surface-card overflow-hidden">
        {loading ? (
          <div className="p-10 text-center text-[color:var(--text-2)]">Caricamento…</div>
        ) : alunni.length === 0 ? (
          <div className="p-12 text-center">
            <UsersIcon className="mx-auto mb-3 text-[color:var(--border)]" size={36} />
            <h3 className="font-display text-lg font-bold mb-1">Nessun {L.cliente.toLowerCase()} associato</h3>
            <p className="text-sm text-[color:var(--text-2)] mb-4">Associa un {L.cliente.toLowerCase()} a questo {L.docente.toLowerCase()}.</p>
            <button onClick={() => setShowAdd(true)} className="btn-primary" disabled={disponibili.length === 0}><Plus size={16} /> {L.associa_alunno}</button>
            {disponibili.length === 0 && <div className="text-xs text-[color:var(--text-2)] mt-3">Nessun {L.cliente.toLowerCase()} disponibile. Crea prima un {L.cliente.toLowerCase()} dalla sezione {L.clienti}.</div>}
          </div>
        ) : (
          <table className="table-clean w-full">
            <thead>
              <tr><th>{L.cliente}</th><th>Email</th><th>Cellulare</th><th></th></tr>
            </thead>
            <tbody>
              {alunni.map((c) => (
                <tr key={c.id} data-testid={`alunno-row-${c.id}`}>
                  <td className="font-semibold">{c.cognome} {c.nome}</td>
                  <td className="text-[color:var(--text-2)]">{c.email || "—"}</td>
                  <td className="text-[color:var(--text-2)]">{c.cellulare || "—"}</td>
                  <td className="text-right">
                    <button onClick={() => disassocia(c)} className="btn-danger" data-testid={`alunno-remove-${c.id}`}><Trash2 size={13} /> Rimuovi</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showAdd && (
        <Modal title={`${L.associa_alunno} al ${L.docente.toLowerCase()}`} onClose={() => setShowAdd(false)}>
          <form onSubmit={associate} className="space-y-3.5">
            <div>
              <label className="block text-sm font-medium mb-1.5">{L.cliente}</label>
              <select className="input-base" value={selected} onChange={(e) => setSelected(e.target.value)} required data-testid="associa-cliente-select">
                <option value="">Seleziona un {L.cliente.toLowerCase()}…</option>
                {disponibili.map((c) => (<option key={c.id} value={c.id}>{c.cognome} {c.nome}</option>))}
              </select>
              <div className="text-xs text-[color:var(--text-2)] mt-1">{disponibili.length} {L.clienti.toLowerCase()} disponibili.</div>
            </div>
            {error && <div className="text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg">{error}</div>}
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={() => setShowAdd(false)} className="btn-secondary flex-1 justify-center">Annulla</button>
              <button type="submit" disabled={busy || !selected} className="btn-primary flex-1 justify-center" data-testid="associa-submit-button">{busy ? "Associo…" : "Associa"}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
