import React, { useEffect, useState } from "react";
import { api, formatApiError } from "@/lib/api";
import { Plus, Edit2, Trash2, Users } from "lucide-react";
import { Modal, Field } from "./Docenti";
import { useAuth } from "@/context/AuthContext";
import { tipologiaLabels } from "@/lib/tipologia";

function emptyForm() {
  return { nome: "", cognome: "", email: "", cellulare: "", residenza: "", cap: "", indirizzo: "", data_nascita: "", note: "" };
}

export default function Clienti() {
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
  const [search, setSearch] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/clienti");
      setItems(data);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { load(); }, []);

  const filtered = items.filter((c) => {
    const q = search.toLowerCase().trim();
    if (!q) return true;
    return [c.nome, c.cognome, c.email, c.cellulare].filter(Boolean).some((s) => s.toLowerCase().includes(q));
  });

  const openCreate = () => { setEditing(null); setForm(emptyForm()); setError(""); setShowModal(true); };
  const openEdit = (c) => {
    setEditing(c);
    setForm({
      nome: c.nome, cognome: c.cognome, email: c.email || "", cellulare: c.cellulare || "",
      residenza: c.residenza || "", cap: c.cap || "", indirizzo: c.indirizzo || "",
      data_nascita: c.data_nascita || "", note: c.note || "",
    });
    setError(""); setShowModal(true);
  };

  const onSubmit = async (e) => {
    e.preventDefault(); setBusy(true); setError("");
    try {
      const payload = { ...form };
      if (!payload.email) delete payload.email;
      if (editing) await api.patch(`/clienti/${editing.id}`, payload);
      else await api.post("/clienti", payload);
      setShowModal(false); await load();
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore");
    } finally { setBusy(false); }
  };

  const remove = async (c) => {
    if (!window.confirm(`Eliminare il cliente ${c.nome} ${c.cognome}?`)) return;
    await api.delete(`/clienti/${c.id}`);
    await load();
  };

  return (
    <div data-testid="clienti-page">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <div className="label-eyebrow mb-1.5">Anagrafica</div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight">{L.clienti}</h1>
          <p className="text-[color:var(--text-2)] mt-1">Tutti i tuoi {L.clienti.toLowerCase()}.</p>
        </div>
        {isAdmin && (
          <button onClick={openCreate} className="btn-primary" data-testid="cliente-create-button">
            <Plus size={16} /> Nuovo {L.cliente.toLowerCase()}
          </button>
        )}
      </div>

      <div className="mb-4">
        <input
          className="input-base max-w-md"
          placeholder="Cerca per nome, cognome, email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          data-testid="cliente-search-input"
        />
      </div>

      <div className="surface-card overflow-hidden">
        {loading ? (
          <div className="p-10 text-center text-[color:var(--text-2)]">Caricamento…</div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center">
            <Users className="mx-auto mb-3 text-[color:var(--border)]" size={36} />
            <h3 className="font-display text-lg font-bold mb-1">Nessun cliente</h3>
            <p className="text-sm text-[color:var(--text-2)] mb-4">{search ? "Nessun risultato per la ricerca." : "Inizia aggiungendo il primo cliente."}</p>
            {isAdmin && !search && (
              <button onClick={openCreate} className="btn-primary" data-testid="cliente-empty-create"><Plus size={16} /> Nuovo cliente</button>
            )}
          </div>
        ) : (
          <>
            <div className="hidden md:block">
              <table className="table-clean w-full">
                <thead>
                  <tr><th>Cliente</th><th>Email</th><th>Cellulare</th><th>Residenza</th><th></th></tr>
                </thead>
                <tbody>
                  {filtered.map((c) => (
                    <tr key={c.id} data-testid={`cliente-row-${c.id}`}>
                      <td className="font-semibold">{c.cognome} {c.nome}</td>
                      <td className="text-[color:var(--text-2)]">{c.email || "—"}</td>
                      <td className="text-[color:var(--text-2)]">{c.cellulare || "—"}</td>
                      <td className="text-[color:var(--text-2)]">{c.residenza || "—"}</td>
                      <td className="text-right">
                        {isAdmin && (
                          <div className="flex justify-end gap-2">
                            <button onClick={() => openEdit(c)} className="btn-secondary text-xs" data-testid={`cliente-edit-${c.id}`}><Edit2 size={13} /></button>
                            <button onClick={() => remove(c)} className="btn-danger" data-testid={`cliente-delete-${c.id}`}><Trash2 size={13} /></button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="md:hidden divide-y divide-[color:var(--border)]">
              {filtered.map((c) => (
                <div key={c.id} className="p-4" data-testid={`cliente-card-${c.id}`}>
                  <div className="font-semibold">{c.cognome} {c.nome}</div>
                  <div className="text-xs text-[color:var(--text-2)] mt-1 space-y-0.5">
                    {c.email && <div>{c.email}</div>}
                    {c.cellulare && <div>{c.cellulare}</div>}
                    {c.residenza && <div>{c.residenza}</div>}
                  </div>
                  {isAdmin && (
                    <div className="mt-3 flex gap-2">
                      <button onClick={() => openEdit(c)} className="btn-secondary text-xs flex-1 justify-center"><Edit2 size={13} /> Modifica</button>
                      <button onClick={() => remove(c)} className="btn-danger flex-1 justify-center"><Trash2 size={13} /> Elimina</button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {showModal && (
        <Modal title={editing ? "Modifica cliente" : "Nuovo cliente"} onClose={() => setShowModal(false)}>
          <form onSubmit={onSubmit} className="space-y-3.5" data-testid="cliente-form">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Field label="Nome" required value={form.nome} onChange={(v) => setForm({ ...form, nome: v })} testid="cliente-nome-input" />
              <Field label="Cognome" required value={form.cognome} onChange={(v) => setForm({ ...form, cognome: v })} testid="cliente-cognome-input" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Field label="Email" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} testid="cliente-email-input" />
              <Field label="Cellulare" value={form.cellulare} onChange={(v) => setForm({ ...form, cellulare: v })} testid="cliente-cellulare-input" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Field label="Residenza" value={form.residenza} onChange={(v) => setForm({ ...form, residenza: v })} testid="cliente-residenza-input" />
              <Field label="CAP" value={form.cap} onChange={(v) => setForm({ ...form, cap: v })} testid="cliente-cap-input" />
              <Field label="Data nascita" type="date" value={form.data_nascita} onChange={(v) => setForm({ ...form, data_nascita: v })} testid="cliente-datanascita-input" />
            </div>
            <Field label="Indirizzo" value={form.indirizzo} onChange={(v) => setForm({ ...form, indirizzo: v })} testid="cliente-indirizzo-input" />
            <div>
              <label className="block text-sm font-medium mb-1.5">Note</label>
              <textarea rows={3} className="input-base" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} data-testid="cliente-note-input" />
            </div>
            {error && <div className="text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="cliente-form-error">{error}</div>}
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={() => setShowModal(false)} className="btn-secondary flex-1 justify-center" data-testid="cliente-cancel-button">Annulla</button>
              <button type="submit" disabled={busy} className="btn-primary flex-1 justify-center" data-testid="cliente-submit-button">{busy ? "Salvataggio…" : "Salva"}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
