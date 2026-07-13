import React, { useEffect, useRef, useState } from "react";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Settings as SettingsIcon, Save, MessageSquare, Image as ImageIcon, Upload, Trash2, Tag, RotateCcw } from "lucide-react";
import { TIPOLOGIE, tipologiaLabels, CUSTOM_LABEL_KEYS } from "@/lib/tipologia";

const MAX_LOGO_BYTES = 600 * 1024; // 600KB after base64

const LABEL_META = [
  { key: "docente",         desc: "Singolare del professionista",   ph: "es. Terapeuta, Coach…" },
  { key: "docenti",         desc: "Plurale del professionista",     ph: "es. Terapeuti, Coach…" },
  { key: "cliente",         desc: "Singolare del cliente finale",   ph: "es. Assistito, Atleta…" },
  { key: "clienti",         desc: "Plurale del cliente finale",     ph: "es. Assistiti, Atleti…" },
  { key: "materia",         desc: "Servizio / area di competenza (sing.)", ph: "es. Terapia, Corso…" },
  { key: "materie",         desc: "Servizio / area di competenza (plur.)", ph: "es. Terapie, Corsi…" },
  { key: "materie_label",   desc: "Titolo sezione servizi",         ph: "es. Servizi erogati" },
  { key: "associa_alunno",  desc: "Testo pulsante 'associa cliente'", ph: "es. Associa assistito" },
];

export default function Impostazioni() {
  const { studio, refresh } = useAuth();
  const [form, setForm] = useState({ nome: "", sede: "", telefono: "", email: "", piva: "", comunicazioni: "", logo_base64: "", custom_labels: {} });
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
        custom_labels: data.custom_labels || {},
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
      // Normalizza stringhe vuote -> null per campi opzionali (specie email/piva),
      // ECCETTO logo_base64 e comunicazioni: lì "" vuol dire "cancella" e deve passare al backend
      const CLEARABLE = new Set(["logo_base64", "comunicazioni"]);
      const payload = {};
      for (const k of Object.keys(form)) {
        const v = form[k];
        if (k === "nome") payload[k] = v;                  // required
        else if (k === "custom_labels") {
          // Compatta: mantieni solo le chiavi con valore non-vuoto (usa default della tipologia altrimenti)
          const cleaned = {};
          for (const lk of CUSTOM_LABEL_KEYS) {
            const val = (v?.[lk] || "").trim();
            if (val) cleaned[lk] = val;
          }
          payload[k] = cleaned;
        }
        else if (CLEARABLE.has(k)) payload[k] = v;         // "" = cancella esplicito
        else payload[k] = (v === "" ? null : v);           // optional: "" -> null
      }
      await api.patch("/studio", payload);
      setSuccess("Impostazioni salvate.");
      if (refresh) refresh();
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore");
    } finally { setBusy(false); }
  };

  // Etichette di default per la tipologia corrente (mostrate come placeholder)
  const defaultLabels = tipologiaLabels(studio?.tipologia, null);
  const setLabel = (key, val) => setForm((f) => ({ ...f, custom_labels: { ...(f.custom_labels || {}), [key]: val } }));
  const resetLabels = () => setForm((f) => ({ ...f, custom_labels: {} }));

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

        {/* ==================== Etichette personalizzate ==================== */}
        <div className="lg:col-span-2 surface-card p-6" data-testid="settings-labels-section">
          <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <Tag size={16} className="text-[color:var(--primary)]" />
              <h3 className="font-display font-bold text-lg">Etichette personalizzate</h3>
            </div>
            <button type="button" onClick={resetLabels} className="btn-secondary text-xs" data-testid="labels-reset-btn">
              <RotateCcw size={12} /> Ripristina default della tipologia
            </button>
          </div>
          <p className="text-xs text-[color:var(--text-2)] mb-5">
            Sovrascrivi le etichette di default per adattare la piattaforma al tuo settore. Es. per uno studio di psicoterapia: <strong>Terapeuta / Assistito</strong>, per un centro fitness: <strong>Coach / Atleta</strong>. Lascia vuoto per mantenere il default della tipologia (<strong>{TIPOLOGIE.find((t) => t.value === studio?.tipologia)?.label || "—"}</strong>).
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {LABEL_META.map((lm) => (
              <div key={lm.key} data-testid={`label-field-${lm.key}`}>
                <label className="block text-sm font-medium mb-1">
                  {lm.desc}
                  <span className="ml-2 text-[10px] uppercase tracking-[0.14em] text-[color:var(--text-2)] font-normal">default: {defaultLabels[lm.key]}</span>
                </label>
                <input
                  className="input-base"
                  placeholder={defaultLabels[lm.key]}
                  value={form.custom_labels?.[lm.key] || ""}
                  onChange={(e) => setLabel(lm.key, e.target.value)}
                  data-testid={`label-input-${lm.key}`}
                />
              </div>
            ))}
          </div>
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
