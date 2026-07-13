import React, { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ArrowLeft, Plus, Trash2, BookOpen } from "lucide-react";
import { Modal } from "./Docenti";
import { tipologiaLabels } from "@/lib/tipologia";

export default function DocenteMaterie() {
  const { studio } = useAuth();
  const L = tipologiaLabels(studio?.tipologia);
  const { id: docenteId } = useParams();
  const [docente, setDocente] = useState(null);
  const [mie, setMie] = useState([]);
  const [tutte, setTutte] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [docs, mine, tutteRes] = await Promise.all([
        api.get("/docenti"),
        api.get(`/docenti/${docenteId}/materie`),
        api.get("/materie"),
      ]);
      setDocente(docs.data.find((x) => x.id === docenteId) || null);
      setMie(mine.data);
      setTutte(tutteRes.data);
    } finally { setLoading(false); }
  }, [docenteId]);
  useEffect(() => { load(); }, [load]);

  const associate = async (e) => {
    e.preventDefault();
    if (!selected) return;
    setBusy(true); setError("");
    try {
      await api.post(`/docenti/${docenteId}/materie/${selected}`);
      setShowAdd(false); setSelected(""); await load();
    } catch (err) { setError(formatApiError(err?.response?.data?.detail) || "Errore"); }
    finally { setBusy(false); }
  };

  const disassocia = async (m) => {
    if (!window.confirm(`Rimuovere "${m.descrizione}" dal ${L.docente.toLowerCase()}?`)) return;
    await api.delete(`/docenti/${docenteId}/materie/${m.id}`);
    await load();
  };

  const giaAssociate = new Set(mie.map((x) => x.id));
  const disponibili = tutte.filter((m) => !giaAssociate.has(m.id));

  return (
    <div data-testid="docente-materie-page">
      <Link to="/docenti" className="inline-flex items-center gap-1.5 text-sm text-[color:var(--text-2)] hover:text-[color:var(--text)] mb-4">
        <ArrowLeft size={14} /> Tutti i {L.docenti.toLowerCase()}
      </Link>
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <div className="label-eyebrow mb-1.5">{L.materie_label}</div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight">
            {docente ? `${docente.nome} ${docente.cognome}` : L.docente}
          </h1>
          <p className="text-[color:var(--text-2)] mt-1">{L.materie} associate a questo {L.docente.toLowerCase()}.</p>
        </div>
        <button onClick={() => { setSelected(""); setShowAdd(true); setError(""); }} className="btn-primary" disabled={disponibili.length === 0} data-testid="associa-materia-button">
          <Plus size={16} /> Associa {L.materia.toLowerCase()}
        </button>
      </div>

      <div className="surface-card overflow-hidden">
        {loading ? <div className="p-10 text-center text-[color:var(--text-2)]">Caricamento…</div> : mie.length === 0 ? (
          <div className="p-12 text-center">
            <BookOpen className="mx-auto mb-3 text-[color:var(--border)]" size={36} />
            <h3 className="font-display text-lg font-bold mb-1">Nessuna {L.materia.toLowerCase()} associata</h3>
            <p className="text-sm text-[color:var(--text-2)] mb-4">Associa {L.materie.toLowerCase()} dal catalogo a questo {L.docente.toLowerCase()}.</p>
            {disponibili.length === 0 ? (
              <Link to="/materie" className="btn-primary inline-flex">Crea {L.materie.toLowerCase()} nel catalogo</Link>
            ) : (
              <button onClick={() => setShowAdd(true)} className="btn-primary"><Plus size={16} /> Associa {L.materia.toLowerCase()}</button>
            )}
          </div>
        ) : (
          <table className="table-clean w-full">
            <thead><tr><th>{L.materia}</th><th>Prezzo (€)</th><th></th></tr></thead>
            <tbody>
              {mie.map((m) => (
                <tr key={m.id} data-testid={`docente-materia-row-${m.id}`}>
                  <td className="font-semibold">{m.descrizione}</td>
                  <td className="text-[color:var(--text-2)]">{m.prezzo != null ? `€ ${Number(m.prezzo).toFixed(2)}` : "—"}</td>
                  <td className="text-right">
                    <button onClick={() => disassocia(m)} className="btn-danger" data-testid={`docente-materia-remove-${m.id}`}><Trash2 size={13} /> Rimuovi</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showAdd && (
        <Modal title={`Associa ${L.materia.toLowerCase()} al ${L.docente.toLowerCase()}`} onClose={() => setShowAdd(false)}>
          <form onSubmit={associate} className="space-y-3.5">
            <div>
              <label className="block text-sm font-medium mb-1.5">{L.materia}</label>
              <select className="input-base" value={selected} onChange={(e) => setSelected(e.target.value)} required data-testid="associa-materia-select">
                <option value="">Seleziona una {L.materia.toLowerCase()}…</option>
                {disponibili.map((m) => (<option key={m.id} value={m.id}>{m.descrizione}{m.prezzo != null ? ` — € ${Number(m.prezzo).toFixed(2)}` : ""}</option>))}
              </select>
              <div className="text-xs text-[color:var(--text-2)] mt-1">{disponibili.length} {L.materie.toLowerCase()} disponibili.</div>
            </div>
            {error && <div className="text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg">{error}</div>}
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={() => setShowAdd(false)} className="btn-secondary flex-1 justify-center">Annulla</button>
              <button type="submit" disabled={busy || !selected} className="btn-primary flex-1 justify-center" data-testid="associa-materia-submit">{busy ? "Associo…" : "Associa"}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
