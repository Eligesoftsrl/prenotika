import React, { useEffect, useRef, useState } from "react";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Settings as SettingsIcon, Save, MessageSquare, Image as ImageIcon, Upload, Trash2 } from "lucide-react";
import { TIPOLOGIE } from "@/lib/tipologia";

const MAX_LOGO_BYTES = 600 * 1024; // 600KB after base64

export default function Impostazioni() {
  const { studio, refresh } = useAuth();
  const [form, setForm] = useState({ nome: "", sede: "", telefono: "", email: "", piva: "", comunicazioni: "", logo_base64: "" });
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const fileRef = useRef(null);

  useEffect(() => {
    api.get("/studio").then(({ data }) => {
      setForm({
        nome: data.nome || "",
        sede: data.sede || "",
        telefono: data.telefono || "",
        email: data.email || "",
        piva: data.piva || "",
        comunicazioni: data.comunicazioni || "",
        logo_base64: data.logo_base64 || "",
      });
      setLoaded(true);
    });
  }, []);

  const onLogoChange = (e) => {
    setError("");
    const file = e.target.files?.[0];
    if (!file) return;
    if (!/^image\/(png|jpeg|jpg|webp|svg\+xml)$/.test(file.type)) {
      setError("Formato non supportato. Usa PNG, JPG, WEBP o SVG.");
      e.target.value = "";
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = String(reader.result || "");
      // size check based on base64 payload length
      const payload = dataUrl.split(",")[1] || "";
      const approxBytes = Math.floor(payload.length * 0.75);
      if (approxBytes > MAX_LOGO_BYTES) {
        setError(`Immagine troppo grande (${Math.round(approxBytes/1024)}KB). Massimo 600KB.`);
        if (fileRef.current) fileRef.current.value = "";
        return;
      }
      setForm((f) => ({ ...f, logo_base64: dataUrl }));
    };
    reader.onerror = () => setError("Impossibile leggere il file.");
    reader.readAsDataURL(file);
  };

  const onLogoRemove = () => {
    setForm((f) => ({ ...f, logo_base64: "" }));
    if (fileRef.current) fileRef.current.value = "";
  };

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
          <div className="flex items-center gap-2 mb-1"><ImageIcon size={16} className="text-[color:var(--primary)]" /><h3 className="font-display font-bold text-lg">Logo del centro</h3></div>
          <p className="text-xs text-[color:var(--text-2)] mb-3">Stampato in cima a tutti i report PDF. PNG, JPG, WEBP o SVG (max 600KB).</p>
          <div className="flex items-center gap-4 flex-wrap">
            <div className="w-32 h-32 rounded-md border border-[color:var(--border)] bg-[color:var(--surface-2)] flex items-center justify-center overflow-hidden" data-testid="logo-preview">
              {form.logo_base64 ? (
                <img src={form.logo_base64} alt="Logo del centro" className="max-w-full max-h-full object-contain" />
              ) : (
                <div className="text-xs text-[color:var(--text-2)] text-center px-2">Nessun logo<br/>caricato</div>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <input
                ref={fileRef}
                type="file"
                accept="image/png,image/jpeg,image/webp,image/svg+xml"
                onChange={onLogoChange}
                className="hidden"
                data-testid="settings-logo-file"
              />
              <button type="button" onClick={() => fileRef.current?.click()} className="btn-secondary" data-testid="settings-logo-upload">
                <Upload size={14} /> {form.logo_base64 ? "Sostituisci" : "Carica logo"}
              </button>
              {form.logo_base64 && (
                <button type="button" onClick={onLogoRemove} className="btn-secondary text-[color:var(--error)]" data-testid="settings-logo-remove">
                  <Trash2 size={14} /> Rimuovi
                </button>
              )}
              <div className="text-xs text-[color:var(--text-2)] mt-1">Consigliato: PNG con sfondo trasparente, 600×600px circa.</div>
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
