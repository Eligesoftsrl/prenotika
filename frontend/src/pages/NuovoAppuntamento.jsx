import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ArrowLeft } from "lucide-react";
import { tipologiaLabels } from "@/lib/tipologia";

function addMinutes(hhmm, minutes) {
  const [h, m] = hhmm.split(":").map(Number);
  const total = h * 60 + m + minutes;
  const hh = Math.floor(total / 60) % 24;
  const mm = total % 60;
  return `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
}

export default function NuovoAppuntamento() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, studio } = useAuth();
  const L = tipologiaLabels(studio?.tipologia);
  const isAdmin = user?.role === "admin";

  const defaults = location.state || {};
  const [docenti, setDocenti] = useState([]);
  const [alunni, setAlunni] = useState([]);
  const [docenteMaterie, setDocenteMaterie] = useState([]);
  const [mode, setMode] = useState("existing");
  const [nuovoCliente, setNuovoCliente] = useState({ nome: "", cognome: "", email: "", cellulare: "" });
  const [recurrenceDates, setRecurrenceDates] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  const today = new Date().toISOString().slice(0, 10);
  const initialDocenteId = defaults.docente_id || (user?.role === "docente" ? user.id : "");
  const [form, setForm] = useState({
    docente_id: initialDocenteId,
    cliente_id: "",
    data: defaults.data || today,
    dal: defaults.dal || "09:00",
    al: defaults.al || "10:00",
    note: "",
    materia_id: "",
  });

  const docenteSel = docenti.find((d) => d.id === form.docente_id);
  const slot = docenteSel?.slot_minuti || 60;

  // Carica docenti
  useEffect(() => {
    api.get("/docenti").then(({ data }) => {
      setDocenti(data);
      if (!form.docente_id && data[0]) {
        setForm((f) => ({ ...f, docente_id: data[0].id }));
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Quando cambia docente: carica clienti + materie + ricalcola "al"
  useEffect(() => {
    if (!form.docente_id) { setAlunni([]); setDocenteMaterie([]); return; }
    const fetchClients = L.needs_association
      ? api.get(`/docenti/${form.docente_id}/alunni`).then(({ data }) => data)
      : api.get("/clienti").then(({ data }) => data);
    Promise.all([
      fetchClients,
      api.get(`/docenti/${form.docente_id}/materie`).then(({ data }) => data).catch(() => []),
    ]).then(([cli, mat]) => {
      setAlunni(cli);
      setDocenteMaterie(mat);
      if (!cli.find((c) => c.id === form.cliente_id)) {
        setForm((f) => ({ ...f, cliente_id: cli[0]?.id || "" }));
      }
    });
    setForm((f) => ({ ...f, al: addMinutes(f.dal, slot) }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.docente_id]);

  const onDalChange = (v) => setForm((f) => ({ ...f, dal: v, al: addMinutes(v, slot) }));

  // 6 settimane di ricorrenza
  const recurrenceOptions = useMemo(() => {
    const d0 = new Date(form.data + "T00:00:00");
    return Array.from({ length: 6 }, (_, i) => {
      const d = new Date(d0);
      d.setDate(d.getDate() + 7 * (i + 1));
      return d.toISOString().slice(0, 10);
    });
  }, [form.data]);

  const giornoLabel = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"][(new Date(form.data + "T00:00:00").getDay() + 6) % 7];

  const toggleRecurrence = (iso) => {
    setRecurrenceDates((prev) => prev.includes(iso) ? prev.filter((x) => x !== iso) : [...prev, iso]);
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setBusy(true); setError(""); setResult(null);
    try {
      const slots = [{ data: form.data, dal: form.dal, al: form.al }];
      recurrenceDates.forEach((d) => slots.push({ data: d, dal: form.dal, al: form.al }));
      const payload = {
        docente_id: form.docente_id,
        slots,
        note: form.note || null,
        materia_id: form.materia_id || null,
        associa_alunno: true,
      };
      if (mode === "new") {
        if (!nuovoCliente.nome.trim() || !nuovoCliente.cognome.trim()) {
          setError(`Nome e cognome del nuovo ${(L.cliente || "cliente").toLowerCase()} sono obbligatori`);
          setBusy(false); return;
        }
        payload.nuovo_cliente = {
          nome: nuovoCliente.nome.trim(), cognome: nuovoCliente.cognome.trim(),
          email: nuovoCliente.email || null, cellulare: nuovoCliente.cellulare || null,
        };
      } else {
        if (!form.cliente_id) { setError(`Seleziona ${(L.cliente || "uno").toLowerCase()}`); setBusy(false); return; }
        payload.cliente_id = form.cliente_id;
      }
      const { data } = await api.post("/appuntamenti/bulk", payload);
      setResult(data);
      if (data.count_skipped === 0) {
        // ritorna al calendario
        setTimeout(() => navigate("/appuntamenti", { state: { docente_id: form.docente_id } }), 800);
      }
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore");
    } finally { setBusy(false); }
  };

  const noAlunni = alunni.length === 0 && !!form.docente_id;

  return (
    <div data-testid="nuovo-appuntamento-page" className="max-w-3xl mx-auto">
      <button onClick={() => navigate(-1)} className="inline-flex items-center gap-1.5 text-sm text-[color:var(--text-2)] hover:text-[color:var(--text)] mb-4" data-testid="back-button">
        <ArrowLeft size={14} /> Torna al calendario
      </button>
      <div className="mb-7">
        <div className="label-eyebrow mb-1.5">Agenda</div>
        <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight">Nuovo appuntamento</h1>
        <p className="text-[color:var(--text-2)] mt-1">Compila il modulo. Puoi anche prenotare le settimane successive con un solo invio.</p>
      </div>

      {result ? (
        <div className="surface-card p-6 space-y-3" data-testid="bulk-result">
          <div className="p-3 rounded-lg bg-[#E5F0E9] border border-[#C8DDD0] text-[color:var(--success)]">
            <div className="font-semibold">{result.count_created} appuntamento/i creato/i con successo</div>
          </div>
          {result.count_skipped > 0 && (
            <div className="p-3 rounded-lg bg-[#FDF1E3] border border-[#EBD1A3] text-[#B0721F]">
              <div className="font-semibold mb-1">{result.count_skipped} slot saltati:</div>
              <ul className="text-xs list-disc ml-5 space-y-0.5">
                {result.skipped.map((s, i) => (<li key={i}>{s.data} {s.dal}-{s.al}: {s.motivo}</li>))}
              </ul>
            </div>
          )}
          <button onClick={() => navigate("/appuntamenti", { state: { docente_id: form.docente_id } })} className="btn-primary w-full justify-center" data-testid="result-back-button">
            Torna al calendario
          </button>
        </div>
      ) : (
      <form onSubmit={onSubmit} className="surface-card p-6 space-y-5" data-testid="appuntamento-form">
        {isAdmin && (
          <div>
            <label className="block text-sm font-medium mb-1.5">{L.docente} *</label>
            <select className="input-base" value={form.docente_id} onChange={(e) => setForm({ ...form, docente_id: e.target.value })} required data-testid="app-docente-select">
              {docenti.map((d) => (<option key={d.id} value={d.id}>{d.nome} {d.cognome}</option>))}
            </select>
            {docenteSel && <div className="text-xs text-[color:var(--text-2)] mt-1">Durata standard: <strong>{slot} minuti</strong></div>}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="block text-sm font-medium mb-1.5">Data *</label>
            <input type="date" className="input-base" value={form.data} onChange={(e) => { setForm({ ...form, data: e.target.value }); setRecurrenceDates([]); }} required data-testid="app-data-input" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Dalle ore *</label>
            <input type="time" className="input-base" value={form.dal} onChange={(e) => onDalChange(e.target.value)} required data-testid="app-dal-input" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Alle ore *</label>
            <input type="time" className="input-base" value={form.al} onChange={(e) => setForm({ ...form, al: e.target.value })} required data-testid="app-al-input" />
          </div>
        </div>

        {/* Tabs studente */}
        <div>
          <div className="flex gap-1.5 mb-3 p-1 rounded-lg bg-[color:var(--surface-2)]">
            <button type="button" onClick={() => setMode("existing")} className={`flex-1 py-1.5 px-3 text-sm rounded-md font-medium ${mode === "existing" ? "bg-white shadow-sm" : "text-[color:var(--text-2)]"}`} data-testid="mode-existing-button">{L.cliente} in archivio</button>
            <button type="button" onClick={() => setMode("new")} className={`flex-1 py-1.5 px-3 text-sm rounded-md font-medium ${mode === "new" ? "bg-white shadow-sm" : "text-[color:var(--text-2)]"}`} data-testid="mode-new-button">Nuovo {L.cliente.toLowerCase()}</button>
          </div>
          {mode === "existing" ? (
            <div>
              <select className="input-base" value={form.cliente_id} onChange={(e) => setForm({ ...form, cliente_id: e.target.value })} disabled={noAlunni} data-testid="app-cliente-select">
                <option value="">Seleziona {L.cliente.toLowerCase()}…</option>
                {alunni.map((c) => (<option key={c.id} value={c.id}>{c.cognome} {c.nome}</option>))}
              </select>
              {noAlunni && <div className="text-xs text-[color:var(--warning)] mt-1.5">Nessun {L.cliente.toLowerCase()} disponibile. Crea un nuovo {L.cliente.toLowerCase()} qui sotto.</div>}
            </div>
          ) : (
            <div className="space-y-2.5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                <input className="input-base" placeholder="Nome" value={nuovoCliente.nome} onChange={(e) => setNuovoCliente({ ...nuovoCliente, nome: e.target.value })} data-testid="new-nome-input" />
                <input className="input-base" placeholder="Cognome" value={nuovoCliente.cognome} onChange={(e) => setNuovoCliente({ ...nuovoCliente, cognome: e.target.value })} data-testid="new-cognome-input" />
              </div>
              <input type="email" className="input-base" placeholder="Email (opzionale)" value={nuovoCliente.email} onChange={(e) => setNuovoCliente({ ...nuovoCliente, email: e.target.value })} data-testid="new-email-input" />
              <input className="input-base" placeholder="Telefono (opzionale)" value={nuovoCliente.cellulare} onChange={(e) => setNuovoCliente({ ...nuovoCliente, cellulare: e.target.value })} data-testid="new-tel-input" />
              <div className="text-xs text-[color:var(--text-2)]">{L.needs_association ? `Il ${L.cliente.toLowerCase()} verrà creato e associato al ${L.docente.toLowerCase()}.` : `Il ${L.cliente.toLowerCase()} verrà creato nel pool comune.`}</div>
            </div>
          )}
        </div>

        {/* Materia / Specializzazione */}
        <div>
          <label className="block text-sm font-medium mb-1.5">{L.materia} (opzionale)</label>
          <select className="input-base" value={form.materia_id} onChange={(e) => setForm({ ...form, materia_id: e.target.value })} data-testid="app-materia-select">
            <option value="">— nessuna —</option>
            {docenteMaterie.map((m) => (<option key={m.id} value={m.id}>{m.descrizione}</option>))}
          </select>
        </div>

        {/* Ricorrenza */}
        <div className="border-t border-[color:var(--border)] pt-4">
          <div className="label-eyebrow mb-2">Vuoi prenotare anche i prossimi {giornoLabel}? (stesso orario)</div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {recurrenceOptions.map((iso) => {
              const checked = recurrenceDates.includes(iso);
              const d = new Date(iso + "T00:00:00");
              const label = d.toLocaleDateString("it-IT", { day: "2-digit", month: "2-digit", year: "numeric" });
              return (
                <label key={iso} className={`flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer border ${checked ? "border-[color:var(--primary)] bg-[color:var(--primary)]/5" : "border-[color:var(--border)]"}`} data-testid={`recurrence-${iso}`}>
                  <input type="checkbox" checked={checked} onChange={() => toggleRecurrence(iso)} className="accent-[color:var(--primary)]" />
                  <span className="text-sm font-medium">{label}</span>
                </label>
              );
            })}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1.5">Note</label>
          <textarea rows={3} className="input-base" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} data-testid="app-note-input" />
        </div>

        {error && <div className="text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="app-form-error">{error}</div>}

        <div className="flex gap-2 pt-2 border-t border-[color:var(--border)]">
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary flex-1 justify-center" data-testid="app-cancel-button">Annulla</button>
          <button type="submit" disabled={busy} className="btn-primary flex-1 justify-center" data-testid="app-submit-button">
            {busy ? "Salvataggio…" : `Registra${recurrenceDates.length > 0 ? ` (${recurrenceDates.length + 1})` : ""}`}
          </button>
        </div>
      </form>
      )}
    </div>
  );
}
