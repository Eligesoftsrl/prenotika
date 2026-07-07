import React, { useEffect, useState } from "react";
import { api, formatApiError } from "@/lib/api";
import { Building2, Plus, Trash2, Pencil } from "lucide-react";
import { Modal, Field } from "./Docenti";
import { TIPOLOGIE } from "@/lib/tipologia";

function emptyForm() {
  return {
    nome: "", sede: "", telefono: "", email: "", piva: "", note: "", tipologia: "centro_studi", plan: "free",
    admin_nome: "", admin_cognome: "", admin_email: "", admin_password: "",
  };
}

const PIANI = [
  { value: "free", label: "Free · 1 professionista", color: "bg-slate-100 text-slate-700" },
  { value: "pro", label: "Pro · 5 professionisti", color: "bg-indigo-100 text-indigo-700" },
  { value: "business", label: "Business · illimitato", color: "bg-emerald-100 text-emerald-700" },
];

export default function Studios() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(emptyForm());
  const [editingId, setEditingId] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setLoading(true);
    try { const { data } = await api.get("/studios"); setItems(data); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setEditingId(null); setForm(emptyForm()); setError(""); setShowModal(true);
  };

  const openEdit = (s) => {
    setEditingId(s.id);
    setForm({
      nome: s.nome || "", sede: s.sede || "", telefono: s.telefono || "",
      email: s.email || "", piva: s.piva || "", note: s.note || "",
      tipologia: s.tipologia || "centro_studi", plan: s.plan || "free",
      admin_nome: "", admin_cognome: "", admin_email: "", admin_password: "",
    });
    setError(""); setShowModal(true);
  };

  const onSubmit = async (e) => {
    e.preventDefault(); setBusy(true); setError("");
    try {
      if (editingId) {
        const payload = {
          nome: form.nome, sede: form.sede || null, telefono: form.telefono || null,
          email: form.email || null, piva: form.piva || null, note: form.note || null,
          tipologia: form.tipologia, plan: form.plan,
        };
        await api.patch(`/studios/${editingId}`, payload);
      } else {
        const payload = { ...form };
        if (!payload.email) delete payload.email;
        await api.post("/studios", payload);
      }
      setShowModal(false); setForm(emptyForm()); setEditingId(null); await load();
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore");
    } finally { setBusy(false); }
  };

  const remove = async (s) => {
    if (!window.confirm(`Eliminare l'azienda "${s.nome}" e tutti i suoi dati?`)) return;
    await api.delete(`/studios/${s.id}`);
    await load();
  };

  return (
    <div data-testid="studios-page">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <div className="label-eyebrow mb-1.5">Piattaforma</div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight">Aziende</h1>
          <p className="text-[color:var(--text-2)] mt-1">Crea e gestisci le aziende (tenant) della piattaforma.</p>
        </div>
        <button onClick={() => { setForm(emptyForm()); setShowModal(true); setError(""); }} className="btn-primary" data-testid="studio-create-button">
          <Plus size={16} /> Nuova azienda
        </button>
      </div>

      <div className="surface-card overflow-hidden">
        {loading ? <div className="p-10 text-center text-[color:var(--text-2)]">Caricamento…</div> : items.length === 0 ? (
          <div className="p-12 text-center">
            <Building2 className="mx-auto mb-3 text-[color:var(--border)]" size={36} />
            <h3 className="font-display text-lg font-bold mb-1">Nessuna azienda</h3>
            <p className="text-sm text-[color:var(--text-2)] mb-4">Crea la prima azienda per iniziare.</p>
          </div>
        ) : (
          <table className="table-clean w-full">
            <thead>
              <tr><th>Nome</th><th>Tipologia</th><th>Piano</th><th>Sede</th><th>Email</th><th></th></tr>
            </thead>
            <tbody>
              {items.map((s) => {
                const tip = TIPOLOGIE.find((t) => t.value === s.tipologia);
                const piano = PIANI.find((p) => p.value === (s.plan || "free"));
                return (
                <tr key={s.id} data-testid={`studio-row-${s.id}`}>
                  <td className="font-semibold">{s.nome}</td>
                  <td><span className="pill">{tip?.label || s.tipologia}</span></td>
                  <td>
                    <select
                      value={s.plan || "free"}
                      onChange={async (e) => {
                        try {
                          await api.patch(`/studios/${s.id}`, { plan: e.target.value });
                          await load();
                        } catch { /* ignore */ }
                      }}
                      className={`text-xs font-bold rounded-full px-3 py-1 border-0 cursor-pointer ${piano?.color || "bg-slate-100"}`}
                      data-testid={`studio-plan-select-${s.id}`}
                    >
                      <option value="free">Free</option>
                      <option value="pro">Pro</option>
                      <option value="business">Business</option>
                    </select>
                  </td>
                  <td className="text-[color:var(--text-2)]">{s.sede || "—"}</td>
                  <td className="text-[color:var(--text-2)]">{s.email || "—"}</td>
                  <td className="text-right">
                    <div className="inline-flex gap-1.5">
                      <button onClick={() => openEdit(s)} className="btn-secondary" data-testid={`studio-edit-${s.id}`} title="Modifica"><Pencil size={13} /></button>
                      <button onClick={() => remove(s)} className="btn-danger" data-testid={`studio-delete-${s.id}`} title="Elimina"><Trash2 size={13} /></button>
                    </div>
                  </td>
                </tr>
              );})}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <Modal title={editingId ? "Modifica Azienda" : "Nuova Azienda"} onClose={() => { setShowModal(false); setEditingId(null); }}>
          <form onSubmit={onSubmit} className="space-y-3.5" data-testid="studio-form">
            <div className="label-eyebrow">Dati azienda</div>
            <Field label="Nome azienda" required value={form.nome} onChange={(v) => setForm({ ...form, nome: v })} testid="studio-nome-input" />
            <div>
              <label className="block text-sm font-medium mb-1.5">Tipologia <span className="text-[color:var(--secondary)]">*</span></label>
              <select className="input-base" value={form.tipologia} onChange={(e) => setForm({ ...form, tipologia: e.target.value })} required data-testid="studio-tipologia-select">
                {TIPOLOGIE.map((t) => (<option key={t.value} value={t.value}>{t.label}</option>))}
              </select>
              <div className="text-xs text-[color:var(--text-2)] mt-1">Determina le etichette (Studente/Docente/Materia ecc.) e la logica di associazione.</div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">Piano <span className="text-[color:var(--secondary)]">*</span></label>
              <select className="input-base" value={form.plan} onChange={(e) => setForm({ ...form, plan: e.target.value })} required data-testid="studio-plan-select">
                {PIANI.map((p) => (<option key={p.value} value={p.value}>{p.label}</option>))}
              </select>
              <div className="text-xs text-[color:var(--text-2)] mt-1">Determina il limite massimo di professionisti che il tenant può creare.</div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Field label="Sede" value={form.sede} onChange={(v) => setForm({ ...form, sede: v })} testid="studio-sede-input" />
              <Field label="Telefono" value={form.telefono} onChange={(v) => setForm({ ...form, telefono: v })} testid="studio-telefono-input" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Field label="Email azienda" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} testid="studio-email-input" />
              <Field label="P.IVA" value={form.piva} onChange={(v) => setForm({ ...form, piva: v })} testid="studio-piva-input" />
            </div>

            {!editingId && (
              <>
                <div className="pt-2 label-eyebrow">Amministratore</div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <Field label="Nome admin" required value={form.admin_nome} onChange={(v) => setForm({ ...form, admin_nome: v })} testid="studio-admin-nome-input" />
                  <Field label="Cognome admin" required value={form.admin_cognome} onChange={(v) => setForm({ ...form, admin_cognome: v })} testid="studio-admin-cognome-input" />
                </div>
                <Field label="Email admin" type="email" required value={form.admin_email} onChange={(v) => setForm({ ...form, admin_email: v })} testid="studio-admin-email-input" />
                <Field label="Password admin" type="password" required value={form.admin_password} onChange={(v) => setForm({ ...form, admin_password: v })} testid="studio-admin-password-input" />
                <div className="text-xs text-[color:var(--text-2)] bg-[color:var(--surface-2)] px-3 py-2 rounded-lg">
                  📧 Alla creazione l&apos;admin riceverà una email di benvenuto con le credenziali e un link per impostare la propria password.
                </div>
              </>
            )}

            {error && <div className="text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="studio-form-error">{error}</div>}
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={() => { setShowModal(false); setEditingId(null); }} className="btn-secondary flex-1 justify-center">Annulla</button>
              <button type="submit" disabled={busy} className="btn-primary flex-1 justify-center" data-testid="studio-submit-button">{busy ? "Salvataggio…" : (editingId ? "Salva modifiche" : "Crea azienda")}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
