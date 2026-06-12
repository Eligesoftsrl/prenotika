import React, { useEffect, useState } from "react";
import { api, formatApiError } from "@/lib/api";
import { Plus, Edit2, Trash2, X, GraduationCap } from "lucide-react";

const COLORS = ["#2C4C3B", "#D96C4A", "#4C6B8B", "#D4A373", "#8B5A2B", "#4A5D23"];

function emptyForm() {
  return { nome: "", cognome: "", email: "", password: "", telefono: "", specializzazione: "", color: COLORS[0] };
}

export default function Docenti() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyForm());
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/docenti");
      setItems(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm());
    setError("");
    setShowModal(true);
  };

  const openEdit = (d) => {
    setEditing(d);
    setForm({
      nome: d.nome, cognome: d.cognome, email: d.email,
      password: "", telefono: d.telefono || "", specializzazione: d.specializzazione || "",
      color: d.color || COLORS[0],
    });
    setError("");
    setShowModal(true);
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      if (editing) {
        const payload = { ...form };
        if (!payload.password) delete payload.password;
        delete payload.email; // email immutable
        await api.patch(`/docenti/${editing.id}`, payload);
      } else {
        await api.post("/docenti", form);
      }
      setShowModal(false);
      await load();
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (d) => {
    if (!window.confirm(`Eliminare il docente ${d.nome} ${d.cognome}? Verranno cancellati anche orari e appuntamenti collegati.`)) return;
    await api.delete(`/docenti/${d.id}`);
    await load();
  };

  return (
    <div data-testid="docenti-page">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <div className="label-eyebrow mb-1.5">Team</div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight">Docenti</h1>
          <p className="text-[color:var(--text-2)] mt-1">Gestisci il team del tuo centro studi.</p>
        </div>
        <button onClick={openCreate} className="btn-primary" data-testid="docente-create-button">
          <Plus size={16} /> Nuovo docente
        </button>
      </div>

      <div className="surface-card overflow-hidden">
        {loading ? (
          <div className="p-10 text-center text-[color:var(--text-2)]">Caricamento…</div>
        ) : items.length === 0 ? (
          <div className="p-12 text-center">
            <GraduationCap className="mx-auto mb-3 text-[color:var(--border)]" size={36} />
            <h3 className="font-display text-lg font-bold mb-1">Nessun docente</h3>
            <p className="text-sm text-[color:var(--text-2)] mb-4">Crea il primo docente per iniziare a gestire l&apos;agenda.</p>
            <button onClick={openCreate} className="btn-primary" data-testid="docente-empty-create">
              <Plus size={16} /> Nuovo docente
            </button>
          </div>
        ) : (
          <>
            {/* Desktop table */}
            <div className="hidden md:block">
              <table className="table-clean w-full">
                <thead>
                  <tr><th>Docente</th><th>Email</th><th>Specializzazione</th><th>Telefono</th><th>Stato</th><th></th></tr>
                </thead>
                <tbody>
                  {items.map((d) => (
                    <tr key={d.id} data-testid={`docente-row-${d.id}`}>
                      <td>
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold" style={{ background: d.color || "#2C4C3B" }}>
                            {d.nome?.[0]}{d.cognome?.[0]}
                          </div>
                          <div className="font-semibold">{d.nome} {d.cognome}</div>
                        </div>
                      </td>
                      <td className="text-[color:var(--text-2)]">{d.email}</td>
                      <td>{d.specializzazione || "—"}</td>
                      <td className="text-[color:var(--text-2)]">{d.telefono || "—"}</td>
                      <td><span className={`pill ${d.active ? 'pill-success' : 'pill-error'}`}>{d.active ? 'Attivo' : 'Inattivo'}</span></td>
                      <td className="text-right">
                        <div className="flex justify-end gap-2">
                          <button onClick={() => openEdit(d)} className="btn-secondary text-xs" data-testid={`docente-edit-${d.id}`}><Edit2 size={13} /></button>
                          <button onClick={() => remove(d)} className="btn-danger" data-testid={`docente-delete-${d.id}`}><Trash2 size={13} /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {/* Mobile cards */}
            <div className="md:hidden divide-y divide-[color:var(--border)]">
              {items.map((d) => (
                <div key={d.id} className="p-4" data-testid={`docente-card-${d.id}`}>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold" style={{ background: d.color || "#2C4C3B" }}>
                      {d.nome?.[0]}{d.cognome?.[0]}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="font-semibold truncate">{d.nome} {d.cognome}</div>
                      <div className="text-xs text-[color:var(--text-2)] truncate">{d.email}</div>
                    </div>
                  </div>
                  <div className="mt-2.5 text-sm text-[color:var(--text-2)] flex items-center gap-3 flex-wrap">
                    {d.specializzazione && <span>{d.specializzazione}</span>}
                    {d.telefono && <span>{d.telefono}</span>}
                  </div>
                  <div className="mt-3 flex gap-2">
                    <button onClick={() => openEdit(d)} className="btn-secondary text-xs flex-1 justify-center"><Edit2 size={13} /> Modifica</button>
                    <button onClick={() => remove(d)} className="btn-danger flex-1 justify-center"><Trash2 size={13} /> Elimina</button>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {showModal && (
        <Modal title={editing ? "Modifica docente" : "Nuovo docente"} onClose={() => setShowModal(false)}>
          <form onSubmit={onSubmit} className="space-y-3.5" data-testid="docente-form">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Field label="Nome" required value={form.nome} onChange={(v) => setForm({ ...form, nome: v })} testid="docente-nome-input" />
              <Field label="Cognome" required value={form.cognome} onChange={(v) => setForm({ ...form, cognome: v })} testid="docente-cognome-input" />
            </div>
            <Field label="Email" type="email" disabled={!!editing} required value={form.email} onChange={(v) => setForm({ ...form, email: v })} testid="docente-email-input" />
            <Field label={editing ? "Nuova password (opzionale)" : "Password"} type="password" required={!editing} value={form.password} onChange={(v) => setForm({ ...form, password: v })} testid="docente-password-input" />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Field label="Telefono" value={form.telefono} onChange={(v) => setForm({ ...form, telefono: v })} testid="docente-telefono-input" />
              <Field label="Specializzazione" value={form.specializzazione} onChange={(v) => setForm({ ...form, specializzazione: v })} testid="docente-spec-input" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">Colore (per il calendario)</label>
              <div className="flex gap-2">
                {COLORS.map((c) => (
                  <button type="button" key={c} onClick={() => setForm({ ...form, color: c })} className={`w-8 h-8 rounded-full border-2 ${form.color === c ? "border-[color:var(--text)]" : "border-transparent"}`} style={{ background: c }} data-testid={`docente-color-${c}`} />
                ))}
              </div>
            </div>
            {error && <div className="text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="docente-form-error">{error}</div>}
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={() => setShowModal(false)} className="btn-secondary flex-1 justify-center" data-testid="docente-cancel-button">Annulla</button>
              <button type="submit" disabled={busy} className="btn-primary flex-1 justify-center" data-testid="docente-submit-button">{busy ? "Salvataggio…" : "Salva"}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

export function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-lg surface-card p-6 anim-fade-up max-h-[90vh] overflow-y-auto" data-testid="modal">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-xl font-bold">{title}</h3>
          <button onClick={onClose} className="btn-secondary" data-testid="modal-close"><X size={16} /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function Field({ label, value, onChange, type = "text", required, testid, disabled }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1.5">{label}{required && <span className="text-[color:var(--secondary)]"> *</span>}</label>
      <input type={type} className="input-base" value={value} onChange={(e) => onChange(e.target.value)} required={required} disabled={disabled} data-testid={testid} />
    </div>
  );
}
