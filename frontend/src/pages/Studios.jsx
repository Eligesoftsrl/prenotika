import React, { useEffect, useState } from "react";
import { api, formatApiError } from "@/lib/api";
import { Building2, Plus, Trash2 } from "lucide-react";
import { Modal, Field } from "./Docenti";
import { TIPOLOGIE } from "@/lib/tipologia";

function emptyForm() {
  return {
    nome: "", sede: "", telefono: "", email: "", piva: "", note: "", tipologia: "centro_studi",
    admin_nome: "", admin_cognome: "", admin_email: "", admin_password: "",
  };
}

export default function Studios() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(emptyForm());
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setLoading(true);
    try { const { data } = await api.get("/studios"); setItems(data); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const onSubmit = async (e) => {
    e.preventDefault(); setBusy(true); setError("");
    try {
      const payload = { ...form };
      if (!payload.email) delete payload.email;
      await api.post("/studios", payload);
      setShowModal(false); setForm(emptyForm()); await load();
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore");
    } finally { setBusy(false); }
  };

  const remove = async (s) => {
    if (!window.confirm(`Eliminare lo studio "${s.nome}" e tutti i suoi dati?`)) return;
    await api.delete(`/studios/${s.id}`);
    await load();
  };

  return (
    <div data-testid="studios-page">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <div className="label-eyebrow mb-1.5">Piattaforma</div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight">Centri Studi</h1>
          <p className="text-[color:var(--text-2)] mt-1">Crea e gestisci i tenant della piattaforma.</p>
        </div>
        <button onClick={() => { setForm(emptyForm()); setShowModal(true); setError(""); }} className="btn-primary" data-testid="studio-create-button">
          <Plus size={16} /> Nuovo centro
        </button>
      </div>

      <div className="surface-card overflow-hidden">
        {loading ? <div className="p-10 text-center text-[color:var(--text-2)]">Caricamento…</div> : items.length === 0 ? (
          <div className="p-12 text-center">
            <Building2 className="mx-auto mb-3 text-[color:var(--border)]" size={36} />
            <h3 className="font-display text-lg font-bold mb-1">Nessun centro studi</h3>
            <p className="text-sm text-[color:var(--text-2)] mb-4">Crea il primo tenant per iniziare.</p>
          </div>
        ) : (
          <table className="table-clean w-full">
            <thead>
              <tr><th>Nome</th><th>Tipologia</th><th>Sede</th><th>Email</th><th>P.IVA</th><th></th></tr>
            </thead>
            <tbody>
              {items.map((s) => {
                const tip = TIPOLOGIE.find((t) => t.value === s.tipologia);
                return (
                <tr key={s.id} data-testid={`studio-row-${s.id}`}>
                  <td className="font-semibold">{s.nome}</td>
                  <td><span className="pill">{tip?.label || s.tipologia}</span></td>
                  <td className="text-[color:var(--text-2)]">{s.sede || "—"}</td>
                  <td className="text-[color:var(--text-2)]">{s.email || "—"}</td>
                  <td className="text-[color:var(--text-2)]">{s.piva || "—"}</td>
                  <td className="text-right">
                    <button onClick={() => remove(s)} className="btn-danger" data-testid={`studio-delete-${s.id}`}><Trash2 size={13} /></button>
                  </td>
                </tr>
              );})}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <Modal title="Nuovo Centro Studi" onClose={() => setShowModal(false)}>
          <form onSubmit={onSubmit} className="space-y-3.5" data-testid="studio-form">
            <div className="label-eyebrow">Dati centro</div>
            <Field label="Nome centro" required value={form.nome} onChange={(v) => setForm({ ...form, nome: v })} testid="studio-nome-input" />
            <div>
              <label className="block text-sm font-medium mb-1.5">Tipologia <span className="text-[color:var(--secondary)]">*</span></label>
              <select className="input-base" value={form.tipologia} onChange={(e) => setForm({ ...form, tipologia: e.target.value })} required data-testid="studio-tipologia-select">
                {TIPOLOGIE.map((t) => (<option key={t.value} value={t.value}>{t.label}</option>))}
              </select>
              <div className="text-xs text-[color:var(--text-2)] mt-1">Determina le etichette (Studente/Docente/Materia ecc.) e la logica di associazione.</div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Field label="Sede" value={form.sede} onChange={(v) => setForm({ ...form, sede: v })} testid="studio-sede-input" />
              <Field label="Telefono" value={form.telefono} onChange={(v) => setForm({ ...form, telefono: v })} testid="studio-telefono-input" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Field label="Email centro" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} testid="studio-email-input" />
              <Field label="P.IVA" value={form.piva} onChange={(v) => setForm({ ...form, piva: v })} testid="studio-piva-input" />
            </div>
            <div className="pt-2 label-eyebrow">Amministratore</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Field label="Nome admin" required value={form.admin_nome} onChange={(v) => setForm({ ...form, admin_nome: v })} testid="studio-admin-nome-input" />
              <Field label="Cognome admin" required value={form.admin_cognome} onChange={(v) => setForm({ ...form, admin_cognome: v })} testid="studio-admin-cognome-input" />
            </div>
            <Field label="Email admin" type="email" required value={form.admin_email} onChange={(v) => setForm({ ...form, admin_email: v })} testid="studio-admin-email-input" />
            <Field label="Password admin" type="password" required value={form.admin_password} onChange={(v) => setForm({ ...form, admin_password: v })} testid="studio-admin-password-input" />

            {error && <div className="text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="studio-form-error">{error}</div>}
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={() => setShowModal(false)} className="btn-secondary flex-1 justify-center">Annulla</button>
              <button type="submit" disabled={busy} className="btn-primary flex-1 justify-center" data-testid="studio-submit-button">{busy ? "Salvataggio…" : "Crea centro"}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
