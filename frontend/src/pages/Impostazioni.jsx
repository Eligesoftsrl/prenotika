import React, { useEffect, useState } from "react";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Settings as SettingsIcon, Save, MessageSquare } from "lucide-react";
import { TIPOLOGIE } from "@/lib/tipologia";

export default function Impostazioni() {
  const { studio, refresh } = useAuth();
  const [form, setForm] = useState({ nome: "", sede: "", telefono: "", email: "", piva: "", comunicazioni: "" });
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    api.get("/studio").then(({ data }) => {
      setForm({
        nome: data.nome || "",
        sede: data.sede || "",
        telefono: data.telefono || "",
        email: data.email || "",
        piva: data.piva || "",
        comunicazioni: data.comunicazioni || "",
      });
      setLoaded(true);
    });
  }, []);

  const onSubmit = async (e) => {
    e.preventDefault(); setBusy(true); setError(""); setSuccess("");
    try {
      await api.patch("/studio", form);
      setSuccess("Impostazioni salvate.");
      if (refresh) refresh();
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore");
    } finally { setBusy(false); }
  };

  const tipLabel = TIPOLOGIE.find((t) => t.value === studio?.tipologia)?.label || studio?.tipologia;

  return (
    <div data-testid="impostazioni-page">
      <div className="mb-7">
        <div className="label-eyebrow mb-1.5">Amministrazione</div>
        <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight">Impostazioni del centro</h1>
        <p className="text-[color:var(--text-2)] mt-1">Dati anagrafici e comunicazioni mostrate in calce ai report PDF.</p>
      </div>

      {!loaded ? (
        <div className="surface-card p-10 text-center text-[color:var(--text-2)]">Caricamento…</div>
      ) : (
      <form onSubmit={onSubmit} className="grid grid-cols-1 lg:grid-cols-2 gap-5" data-testid="impostazioni-form">
        <div className="surface-card p-6 space-y-4">
          <div className="flex items-center gap-2 mb-1"><SettingsIcon size={16} className="text-[color:var(--primary)]" /><h3 className="font-display font-bold text-lg">Dati anagrafici</h3></div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Nome centro *</label>
            <input className="input-base" required value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} data-testid="settings-nome-input" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Tipologia</label>
            <input className="input-base bg-[color:var(--surface-2)]" value={tipLabel} disabled />
            <div className="text-xs text-[color:var(--text-2)] mt-1">La tipologia è impostata dal Super Admin alla creazione del tenant.</div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1.5">Telefono</label>
              <input className="input-base" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} data-testid="settings-telefono-input" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">Email</label>
              <input type="email" className="input-base" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} data-testid="settings-email-input" />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1.5">P.IVA</label>
              <input className="input-base" value={form.piva} onChange={(e) => setForm({ ...form, piva: e.target.value })} data-testid="settings-piva-input" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">Sede</label>
              <input className="input-base" value={form.sede} onChange={(e) => setForm({ ...form, sede: e.target.value })} data-testid="settings-sede-input" />
            </div>
          </div>
        </div>

        <div className="surface-card p-6">
          <div className="flex items-center gap-2 mb-1"><MessageSquare size={16} className="text-[color:var(--primary)]" /><h3 className="font-display font-bold text-lg">Comunicazioni</h3></div>
          <p className="text-xs text-[color:var(--text-2)] mb-3">Testo libero. Verrà stampato in calce a tutti i report PDF (giorno, settimana, mese).</p>
          <textarea
            rows={14}
            className="input-base font-mono text-sm"
            value={form.comunicazioni}
            onChange={(e) => setForm({ ...form, comunicazioni: e.target.value })}
            placeholder="Esempi:&#10;- Le segreteria è aperta dal lunedì al venerdì, 9-18&#10;- Per disdire un appuntamento contattare entro 24h&#10;- Modalità di pagamento: bonifico o POS"
            data-testid="settings-comunicazioni-input"
          />
        </div>

        <div className="lg:col-span-2 surface-card p-4 flex items-center justify-between flex-wrap gap-3">
          {error && <div className="text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="settings-error">{error}</div>}
          {success && <div className="text-sm text-[color:var(--success)] bg-[#E5F0E9] border border-[#C8DDD0] px-3 py-2 rounded-lg" data-testid="settings-success">{success}</div>}
          <div className="ml-auto">
            <button type="submit" disabled={busy} className="btn-primary" data-testid="settings-submit-button"><Save size={15} /> {busy ? "Salvataggio…" : "Salva modifiche"}</button>
          </div>
        </div>
      </form>
      )}
    </div>
  );
}
