import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, formatApiError } from "@/lib/api";
import { Plus, Edit2, Trash2, X, GraduationCap, CalendarClock, Users as UsersIcon, BookOpen } from "lucide-react";

const COLORS = ["#2C4C3B", "#D96C4A", "#4C6B8B", "#D4A373", "#8B5A2B", "#4A5D23"];
const DURATE = [15, 30, 45, 60, 90, 120];

function emptyForm() {
  return { nome: "", cognome: "", email: "", password: "", telefono: "", color: COLORS[0], slot_minuti: 60, materia_ids: [] };
}

export default function Docenti() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [materie, setMaterie] = useState([]);
  const [docMaterie, setDocMaterie] = useState({});
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyForm());
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [docs, mat] = await Promise.all([api.get("/docenti"), api.get("/materie")]);
      setItems(docs.data);
      setMaterie(mat.data);
      // Fetch materie per ciascun docente in parallelo
      const map = {};
      await Promise.all(docs.data.map(async (d) => {
        try {
          const { data } = await api.get(`/docenti/${d.id}/materie`);
          map[d.id] = data;
        } catch { map[d.id] = []; }
      }));
      setDocMaterie(map);
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

  const openEdit = async (d) => {
    setEditing(d);
    // fetch materie associate del docente
    let mids = [];
    try {
      const { data } = await api.get(`/docenti/${d.id}/materie`);
      mids = data.map((m) => m.id);
    } catch {}
    setForm({
      nome: d.nome, cognome: d.cognome, email: d.email,
      password: "", telefono: d.telefono || "",
      color: d.color || COLORS[0], slot_minuti: d.slot_minuti || 60,
      materia_ids: mids,
    });
    setError("");
    setShowModal(true);
  };

  const toggleMateria = (mid) => {
    setForm((f) => ({
      ...f,
      materia_ids: f.materia_ids.includes(mid) ? f.materia_ids.filter((x) => x !== mid) : [...f.materia_ids, mid],
    }));
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      const payload = { ...form, slot_minuti: Number(form.slot_minuti) };
      if (editing) {
        if (!payload.password) delete payload.password;
        delete payload.email; // email immutable
        await api.patch(`/docenti/${editing.id}`, payload);
      } else {
        await api.post("/docenti", payload);
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
                  <tr><th>Docente</th><th>Email</th><th>Materie</th><th>Durata app.</th><th>Stato</th><th></th></tr>
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
                      <td>
                        <div className="flex flex-wrap gap-1 max-w-[220px]">
                          {(docMaterie[d.id] || []).length === 0 ? <span className="text-[color:var(--text-2)]">—</span> :
                            (docMaterie[d.id] || []).map((m) => (<span key={m.id} className="pill">{m.descrizione}</span>))
                          }
                        </div>
                      </td>
                      <td className="text-[color:var(--text-2)]">{d.slot_minuti || 60} min</td>
                      <td><span className={`pill ${d.active ? 'pill-success' : 'pill-error'}`}>{d.active ? 'Attivo' : 'Inattivo'}</span></td>
                      <td className="text-right">
                        <div className="flex justify-end gap-1.5 flex-wrap">
                          <button onClick={() => navigate(`/orari?docente=${d.id}`)} className="btn-secondary text-xs" title="Calendario disponibilità" data-testid={`docente-calendar-${d.id}`}><CalendarClock size={13} /> <span className="hidden lg:inline">Calendario</span></button>
                          <button onClick={() => navigate(`/docenti/${d.id}/alunni`)} className="btn-secondary text-xs" title="Alunni associati" data-testid={`docente-alunni-${d.id}`}><UsersIcon size={13} /> <span className="hidden lg:inline">Alunni</span></button>
                          <button onClick={() => navigate(`/docenti/${d.id}/materie`)} className="btn-secondary text-xs" title="Materie insegnate" data-testid={`docente-materie-${d.id}`}><BookOpen size={13} /> <span className="hidden lg:inline">Materie</span></button>
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
                  <div className="mt-2.5 text-sm text-[color:var(--text-2)] flex items-center gap-2 flex-wrap">
                    {d.telefono && <span>{d.telefono}</span>}
                    <span className="pill">{d.slot_minuti || 60} min</span>
                    {(docMaterie[d.id] || []).map((m) => (<span key={m.id} className="pill">{m.descrizione}</span>))}
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    <button onClick={() => navigate(`/orari?docente=${d.id}`)} className="btn-secondary text-xs justify-center"><CalendarClock size={13} /> Calendario</button>
                    <button onClick={() => navigate(`/docenti/${d.id}/alunni`)} className="btn-secondary text-xs justify-center"><UsersIcon size={13} /> Alunni</button>
                    <button onClick={() => navigate(`/docenti/${d.id}/materie`)} className="btn-secondary text-xs justify-center"><BookOpen size={13} /> Materie</button>
                    <button onClick={() => openEdit(d)} className="btn-secondary text-xs justify-center"><Edit2 size={13} /> Modifica</button>
                    <button onClick={() => remove(d)} className="btn-danger justify-center col-span-2"><Trash2 size={13} /> Elimina</button>
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
              <div>
                <label className="block text-sm font-medium mb-1.5">Durata standard appuntamento</label>
                <select className="input-base" value={form.slot_minuti} onChange={(e) => setForm({ ...form, slot_minuti: e.target.value })} data-testid="docente-durata-select">
                  {DURATE.map((m) => (<option key={m} value={m}>{m} minuti</option>))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">Materie insegnate</label>
              {materie.length === 0 ? (
                <div className="text-xs text-[color:var(--text-2)] bg-[color:var(--surface-2)] border border-[color:var(--border)] rounded-md px-3 py-2">
                  Nessuna materia nel catalogo. Vai in <strong>Materie</strong> per crearle, poi torna qui per associarle.
                </div>
              ) : (
                <div className="flex flex-wrap gap-2" data-testid="docente-materie-tags">
                  {materie.map((m) => {
                    const active = form.materia_ids.includes(m.id);
                    return (
                      <button
                        type="button"
                        key={m.id}
                        onClick={() => toggleMateria(m.id)}
                        className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${active ? "bg-[color:var(--primary)] border-[color:var(--primary)] text-white" : "bg-[color:var(--surface)] border-[color:var(--border)] text-[color:var(--text)] hover:bg-[color:var(--surface-2)]"}`}
                        data-testid={`docente-materia-tag-${m.id}`}
                      >
                        {active ? "✓ " : "+ "}{m.descrizione}
                      </button>
                    );
                  })}
                </div>
              )}
              <div className="text-xs text-[color:var(--text-2)] mt-1.5">Clicca su una materia per associarla / disassociarla.</div>
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

export function Modal({ title, onClose, children, size = "md" }) {
  const maxW = size === "lg" ? "max-w-2xl" : size === "xl" ? "max-w-3xl" : "max-w-lg";
  // Block body scroll while modal is open
  React.useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = prev; };
  }, []);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6" data-testid="modal">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className={`relative w-full ${maxW} surface-card shadow-xl anim-fade-up flex flex-col max-h-[calc(100vh-1.5rem)]`}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-[color:var(--border)] shrink-0">
          <h3 className="font-display text-xl font-bold pr-4">{title}</h3>
          <button onClick={onClose} className="btn-secondary shrink-0" data-testid="modal-close" aria-label="Chiudi"><X size={16} /></button>
        </div>
        <div className="px-6 py-5 overflow-y-auto flex-1">
          {children}
        </div>
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
