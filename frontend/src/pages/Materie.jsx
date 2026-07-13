import React, { useEffect, useState } from "react";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { BookOpen, Plus, Edit2, Trash2 } from "lucide-react";
import { Modal, Field } from "./Docenti";
import { tipologiaLabels } from "@/lib/tipologia";

function emptyForm() { return { descrizione: "", prezzo: "" }; }

export default function Materie() {
  const { user, studio } = useAuth();
  const L = tipologiaLabels(studio?.tipologia);
  const isAdmin = user?.role === "admin";
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyForm());
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setLoading(true);
    try { const { data } = await api.get("/materie"); setItems(data); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const openCreate = () => { setEditing(null); setForm(emptyForm()); setError(""); setShowModal(true); };
  const openEdit = (m) => { setEditing(m); setForm({ descrizione: m.descrizione, prezzo: m.prezzo ?? "" }); setError(""); setShowModal(true); };

  const onSubmit = async (e) => {
    e.preventDefault(); setBusy(true); setError("");
    try {
      const payload = { descrizione: form.descrizione, prezzo: form.prezzo === "" ? null : Number(form.prezzo) };
      if (editing) await api.patch(`/materie/${editing.id}`, payload);
      else await api.post("/materie", payload);
      setShowModal(false); await load();
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore");
    } finally { setBusy(false); }
  };

  const remove = async (m) => {
    if (!window.confirm(`Eliminare "${m.descrizione}"? Sarà rimossa anche da tutti i ${L.docenti.toLowerCase()} associati.`)) return;
    await api.delete(`/materie/${m.id}`);
    await load();
  };

  return (
    <div data-testid="materie-page">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <div className="label-eyebrow mb-1.5">Catalogo</div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight">{L.materie}</h1>
          <p className="text-[color:var(--text-2)] mt-1">{L.materie} del centro. Associale ai {L.docenti.toLowerCase()} dalla scheda.</p>
        </div>
        {isAdmin && (
          <button onClick={openCreate} className="btn-primary" data-testid="materia-create-button">
            <Plus size={16} /> Nuova {L.materia.toLowerCase()}
          </button>
        )}
      </div>

      <div className="surface-card overflow-hidden">
        {loading ? <div className="p-10 text-center text-[color:var(--text-2)]">Caricamento…</div> : items.length === 0 ? (
          <div className="p-12 text-center">
            <BookOpen className="mx-auto mb-3 text-[color:var(--border)]" size={36} />
            <h3 className="font-display text-lg font-bold mb-1">Nessuna {L.materia.toLowerCase()}</h3>
            <p className="text-sm text-[color:var(--text-2)] mb-4">Crea {L.materie.toLowerCase()} del catalogo.</p>
            {isAdmin && <button onClick={openCreate} className="btn-primary"><Plus size={16} /> Nuova {L.materia.toLowerCase()}</button>}
          </div>
        ) : (
          <table className="table-clean w-full">
            <thead><tr><th>Descrizione</th><th>Prezzo (€)</th><th></th></tr></thead>
            <tbody>
              {items.map((m) => (
                <tr key={m.id} data-testid={`materia-row-${m.id}`}>
                  <td className="font-semibold">{m.descrizione}</td>
                  <td className="text-[color:var(--text-2)]">{m.prezzo != null ? `€ ${Number(m.prezzo).toFixed(2)}` : "—"}</td>
                  <td className="text-right">
                    {isAdmin && (
                      <div className="flex justify-end gap-2">
                        <button onClick={() => openEdit(m)} className="btn-secondary text-xs" data-testid={`materia-edit-${m.id}`}><Edit2 size={13} /></button>
                        <button onClick={() => remove(m)} className="btn-danger" data-testid={`materia-delete-${m.id}`}><Trash2 size={13} /></button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <Modal title={editing ? `Modifica ${L.materia.toLowerCase()}` : `Nuova ${L.materia.toLowerCase()}`} onClose={() => setShowModal(false)}>
          <form onSubmit={onSubmit} className="space-y-3.5" data-testid="materia-form">
            <Field label="Descrizione" required value={form.descrizione} onChange={(v) => setForm({ ...form, descrizione: v })} testid="materia-descrizione-input" />
            <div>
              <label className="block text-sm font-medium mb-1.5">Prezzo orario (€)</label>
              <input type="number" step="0.01" min="0" className="input-base" value={form.prezzo} onChange={(e) => setForm({ ...form, prezzo: e.target.value })} placeholder="es. 25.00" data-testid="materia-prezzo-input" />
            </div>
            {error && <div className="text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="materia-form-error">{error}</div>}
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={() => setShowModal(false)} className="btn-secondary flex-1 justify-center">Annulla</button>
              <button type="submit" disabled={busy} className="btn-primary flex-1 justify-center" data-testid="materia-submit-button">{busy ? "Salvataggio…" : "Salva"}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
