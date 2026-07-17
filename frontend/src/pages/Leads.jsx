import React, { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Inbox, Mail, Phone, Building2, Sparkles, Trash2, Search, CheckCircle2, Clock, X, Pencil, Save, Ban, Rocket } from "lucide-react";

const STATUS = {
  new: { label: "Nuovo", color: "bg-indigo-100 text-indigo-700", icon: Inbox },
  onboarding_started: { label: "Onboarding avviato", color: "bg-violet-100 text-violet-700", icon: Rocket },
  contacted: { label: "Contattato", color: "bg-amber-100 text-amber-700", icon: Clock },
  converted: { label: "Convertito", color: "bg-emerald-100 text-emerald-700", icon: CheckCircle2 },
  closed: { label: "Chiuso", color: "bg-slate-100 text-slate-600", icon: X },
  cancellata: { label: "Cancellata", color: "bg-rose-100 text-rose-700", icon: Ban },
};

const TIPO_LABELS = {
  centro_studi: "Centro studi",
  studio_legale: "Studio legale",
  studio_medico: "Studio medico",
  altro: "Altro",
};

function fmtDateTime(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleString("it-IT", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch { return iso; }
}

function TenantPill({ tenant }) {
  const isPaid = !!tenant.paid_since;
  const trialEnds = tenant.trial_ends_at ? new Date(tenant.trial_ends_at) : null;
  const daysLeft = trialEnds ? Math.max(0, Math.round((new Date(trialEnds.getFullYear(), trialEnds.getMonth(), trialEnds.getDate()).getTime() - new Date(new Date().getFullYear(), new Date().getMonth(), new Date().getDate()).getTime()) / 86400000)) : null;
  if (isPaid) return <span className="pill bg-emerald-100 text-emerald-700 font-bold">💳 {(tenant.plan||"").toUpperCase()} · pagato</span>;
  if (tenant.trial_active && daysLeft != null) {
    const cls = daysLeft <= 3 ? "bg-red-100 text-red-700" : daysLeft <= 7 ? "bg-amber-100 text-amber-700" : "bg-violet-100 text-violet-700";
    return <span className={`pill font-bold ${cls}`}>✨ Trial {(tenant.trial_plan||tenant.plan||"").toUpperCase()} · {daysLeft}gg</span>;
  }
  return <span className="pill bg-slate-100 text-slate-600 font-semibold">{(tenant.plan||"free").toUpperCase()}</span>;
}

export default function Leads() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/leads");
      setItems(data || []);
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const filtered = useMemo(() => {
    const s = search.trim().toLowerCase();
    return items.filter((l) => {
      if (filter !== "all" && (l.status || "new") !== filter) return false;
      if (!s) return true;
      return [l.nome, l.email, l.telefono, l.studio, l.messaggio].some((f) => (f || "").toLowerCase().includes(s));
    });
  }, [items, filter, search]);

  const counts = useMemo(() => {
    const c = { all: items.length, new: 0, contacted: 0, converted: 0, closed: 0, cancellata: 0 };
    items.forEach((l) => { c[l.status || "new"] = (c[l.status || "new"] || 0) + 1; });
    return c;
  }, [items]);

  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [saving, setSaving] = useState(false);

  const startEdit = () => {
    setEditForm({
      nome: selected.nome || "",
      email: selected.email || "",
      telefono: selected.telefono || "",
      studio: selected.studio || "",
      tipologia: selected.tipologia || "centro_studi",
      piano_interesse: selected.piano_interesse || "",
      messaggio: selected.messaggio || "",
      notes: selected.notes || "",
    });
    setEditing(true);
  };
  const saveEdit = async () => {
    setSaving(true);
    try {
      const payload = { ...editForm };
      Object.keys(payload).forEach((k) => { if (payload[k] === "") payload[k] = null; });
      const { data } = await api.patch(`/leads/${selected.id}`, payload);
      setSelected(data);
      setEditing(false);
      await load();
    } finally { setSaving(false); }
  };

  const updateStatus = async (lead, status) => {
    await api.patch(`/leads/${lead.id}`, { status });
    await load();
    if (selected && selected.id === lead.id) setSelected({ ...selected, status });
  };

  const removeLead = async (lead) => {
    if (!window.confirm(`Eliminare il lead di ${lead.nome}?`)) return;
    await api.delete(`/leads/${lead.id}`);
    await load();
    if (selected && selected.id === lead.id) setSelected(null);
  };

  return (
    <div data-testid="leads-page" className="max-w-6xl">
      <div className="mb-6">
        <div className="label-eyebrow mb-1.5">Marketing</div>
        <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight">Richieste dal sito</h1>
        <p className="text-[color:var(--text-2)] mt-1">Tutti i contatti arrivati dalla landing page. Contatta rapidamente e traccia gli stati.</p>
      </div>

      {/* Filters */}
      <div className="surface-card p-3 mb-5 flex items-center gap-3 flex-wrap">
        <div className="flex p-0.5 rounded-md bg-[color:var(--surface-2)]">
          {["all", "new", "onboarding_started", "contacted", "converted", "closed"].map((k) => (
            <button
              key={k}
              onClick={() => setFilter(k)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-sm ${filter === k ? "bg-white shadow-sm" : "text-[color:var(--text-2)] hover:text-[color:var(--text)]"}`}
              data-testid={`leads-filter-${k}`}
            >
              {k === "all" ? "Tutti" : STATUS[k].label} <span className="ml-1 text-[10px] text-[color:var(--text-3)]">({counts[k] || 0})</span>
            </button>
          ))}
        </div>
        <div className="relative flex-1 min-w-[220px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[color:var(--text-3)]" />
          <input
            type="search"
            placeholder="Cerca per nome, email, azienda..."
            className="input-base pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            data-testid="leads-search"
          />
        </div>
      </div>

      <div className="grid lg:grid-cols-[1fr_400px] gap-5">
        {/* List */}
        <div className="surface-card overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-[color:var(--text-2)]">Caricamento…</div>
          ) : filtered.length === 0 ? (
            <div className="p-10 text-center text-[color:var(--text-2)]">
              <Inbox size={40} strokeWidth={1.3} className="mx-auto mb-3 text-[color:var(--text-3)]" />
              <div className="font-semibold">Nessuna richiesta {filter !== "all" ? `con stato "${STATUS[filter]?.label || filter}"` : "ancora"}.</div>
              <div className="text-xs mt-1">I contatti dal form della landing appariranno qui in tempo reale.</div>
            </div>
          ) : (
            <table className="table-clean w-full">
              <thead>
                <tr><th>Contatto</th><th>Azienda</th><th>Piano</th><th>Stato</th><th>Data</th></tr>
              </thead>
              <tbody>
                {filtered.map((l) => {
                  const s = STATUS[l.status] || STATUS.new;
                  const StatusIcon = s.icon;
                  return (
                    <tr key={l.id} onClick={() => setSelected(l)} className="cursor-pointer" data-testid={`lead-row-${l.id}`}>
                      <td>
                        <div className="font-semibold">{l.nome}</div>
                        <div className="text-xs text-[color:var(--text-2)]">{l.email}</div>
                      </td>
                      <td>
                        <div>{l.tenant?.studio_nome || l.studio || "—"}</div>
                        <div className="text-xs text-[color:var(--text-2)]">{TIPO_LABELS[l.tipologia] || l.tipologia || "—"}</div>
                      </td>
                      <td>
                        {l.tenant ? (
                          <TenantPill tenant={l.tenant} />
                        ) : (
                          l.piano_interesse ? <span className="pill" style={{ background: "var(--grad-soft)", color: "var(--primary)", fontWeight: 700 }}><Sparkles size={10} className="mr-1" /> {l.piano_interesse}</span> : <span className="text-[color:var(--text-3)] text-xs">—</span>
                        )}
                      </td>
                      <td>
                        <span className={`pill ${s.color}`}><StatusIcon size={10} className="mr-1" /> {s.label}</span>
                      </td>
                      <td className="text-xs text-[color:var(--text-2)]">{fmtDateTime(l.created_at)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Detail panel */}
        <div className="surface-card p-5 h-fit sticky top-4">
          {selected ? (
            <div data-testid="lead-detail">
              <div className="flex items-start justify-between gap-3 mb-4">
                <div className="flex-1 min-w-0">
                  <div className="label-eyebrow mb-1">Dettaglio richiesta</div>
                  {editing ? (
                    <input className="input-base font-display text-lg font-bold" value={editForm.nome} onChange={(e) => setEditForm({ ...editForm, nome: e.target.value })} data-testid="lead-edit-nome" />
                  ) : (
                    <div className="font-display text-xl font-bold truncate">{selected.nome}</div>
                  )}
                </div>
                <div className="flex gap-1.5 flex-shrink-0">
                  {!editing && <button onClick={startEdit} className="text-[color:var(--text-2)] hover:text-[color:var(--primary)]" title="Modifica" data-testid="lead-edit-btn"><Pencil size={15} /></button>}
                  <button onClick={() => { setSelected(null); setEditing(false); }} className="text-[color:var(--text-3)] hover:text-[color:var(--text)]"><X size={16} /></button>
                </div>
              </div>

              {editing ? (
                <div className="space-y-2.5 mb-4" data-testid="lead-edit-form">
                  <div>
                    <label className="label-eyebrow block mb-1">Email</label>
                    <input type="email" className="input-base" value={editForm.email} onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} data-testid="lead-edit-email" />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="label-eyebrow block mb-1">Telefono</label>
                      <input className="input-base" value={editForm.telefono} onChange={(e) => setEditForm({ ...editForm, telefono: e.target.value })} data-testid="lead-edit-telefono" />
                    </div>
                    <div>
                      <label className="label-eyebrow block mb-1">Tipologia</label>
                      <select className="input-base" value={editForm.tipologia} onChange={(e) => setEditForm({ ...editForm, tipologia: e.target.value })} data-testid="lead-edit-tipologia">
                        <option value="centro_studi">Centro studi</option>
                        <option value="studio_legale">Studio legale</option>
                        <option value="studio_medico">Studio medico</option>
                        <option value="altro">Altro</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="label-eyebrow block mb-1">Azienda</label>
                    <input className="input-base" value={editForm.studio} onChange={(e) => setEditForm({ ...editForm, studio: e.target.value })} data-testid="lead-edit-studio" />
                  </div>
                  <div>
                    <label className="label-eyebrow block mb-1">Piano interesse</label>
                    <select className="input-base" value={editForm.piano_interesse} onChange={(e) => setEditForm({ ...editForm, piano_interesse: e.target.value })} data-testid="lead-edit-piano">
                      <option value="">— nessuno —</option>
                      <option value="Free">Free</option>
                      <option value="Pro">Pro</option>
                      <option value="Business">Business</option>
                    </select>
                  </div>
                  <div>
                    <label className="label-eyebrow block mb-1">Messaggio</label>
                    <textarea rows={3} className="input-base resize-none" value={editForm.messaggio} onChange={(e) => setEditForm({ ...editForm, messaggio: e.target.value })} data-testid="lead-edit-messaggio" />
                  </div>
                  <div>
                    <label className="label-eyebrow block mb-1">Note interne (super admin)</label>
                    <textarea rows={2} className="input-base resize-none" value={editForm.notes} onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })} placeholder="Solo per uso interno" data-testid="lead-edit-notes" />
                  </div>
                  <div className="flex gap-2 pt-2">
                    <button onClick={() => setEditing(false)} className="btn-secondary flex-1 justify-center" data-testid="lead-edit-cancel">Annulla</button>
                    <button onClick={saveEdit} disabled={saving} className="btn-primary flex-1 justify-center" data-testid="lead-edit-save"><Save size={13} /> {saving ? "Salvo…" : "Salva"}</button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="space-y-2 mb-4 text-sm">
                    <a href={`mailto:${selected.email}`} className="flex items-center gap-2 text-[color:var(--primary)] hover:underline"><Mail size={14} />{selected.email}</a>
                    {selected.telefono && <a href={`tel:${selected.telefono}`} className="flex items-center gap-2 text-[color:var(--text)] hover:underline"><Phone size={14} />{selected.telefono}</a>}
                    {selected.studio && <div className="flex items-center gap-2 text-[color:var(--text-2)]"><Building2 size={14} />{selected.studio} · {TIPO_LABELS[selected.tipologia] || "—"}</div>}
                    {selected.piano_interesse && (
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold" style={{ background: "var(--grad-soft)", color: "var(--primary)" }}>
                        <Sparkles size={11} /> Piano interesse: {selected.piano_interesse}
                      </div>
                    )}
                  </div>

                  {selected.messaggio && (
                    <>
                      <div className="label-eyebrow mb-1.5">Messaggio</div>
                      <div className="p-3 rounded-md bg-[color:var(--surface-2)] text-sm text-[color:var(--text)] whitespace-pre-wrap mb-4">{selected.messaggio}</div>
                    </>
                  )}
                  {selected.notes && (
                    <>
                      <div className="label-eyebrow mb-1.5">Note interne</div>
                      <div className="p-3 rounded-md bg-amber-50 border border-amber-200 text-sm text-[color:var(--text)] whitespace-pre-wrap mb-4">{selected.notes}</div>
                    </>
                  )}
                </>
              )}

              <div className="label-eyebrow mb-1.5">Cambia stato</div>
              <div className="grid grid-cols-2 gap-1.5 mb-5">
                {Object.entries(STATUS).map(([k, v]) => {
                  const active = (selected.status || "new") === k;
                  return (
                    <button
                      key={k}
                      onClick={() => updateStatus(selected, k)}
                      className={`text-xs px-2.5 py-1.5 rounded-md font-semibold border transition ${active ? `${v.color} border-transparent shadow-sm` : "border-[color:var(--border)] text-[color:var(--text-2)] hover:bg-[color:var(--surface-2)]"}`}
                      data-testid={`lead-status-${k}`}
                    >
                      {v.label}
                    </button>
                  );
                })}
              </div>

              {/* Tenant / trial status block */}
              {selected.tenant && (
                <div className="mb-3 p-3 rounded-lg border border-[color:var(--border)] bg-[color:var(--surface-2)]" data-testid="lead-tenant-block">
                  <div className="label-eyebrow mb-2">Stato tenant</div>
                  <div className="mb-2"><TenantPill tenant={selected.tenant} /></div>
                  <div className="text-xs text-[color:var(--text)] space-y-0.5">
                    <div><strong>Studio:</strong> {selected.tenant.studio_nome}</div>
                    <div><strong>Piano attivo:</strong> {(selected.tenant.plan || "free").toUpperCase()}</div>
                    {selected.tenant.trial_active && selected.tenant.trial_ends_at && (
                      <div><strong>Trial scade il:</strong> {fmtDateTime(selected.tenant.trial_ends_at)}</div>
                    )}
                    {selected.tenant.paid_since && (
                      <div className="text-emerald-700"><strong>Pagante dal:</strong> {fmtDateTime(selected.tenant.paid_since)}</div>
                    )}
                    <div><strong>Setup completato:</strong> {selected.tenant.onboarding_completed ? "sì" : "no"}</div>
                  </div>
                </div>
              )}

              <div className="text-[10px] text-[color:var(--text-3)] mb-3">Ricevuto {fmtDateTime(selected.created_at)}</div>

              <div className="flex gap-2">
                <a href={`mailto:${selected.email}?subject=Prenotika — Grazie per la tua richiesta`} className="btn-primary flex-1 justify-center" data-testid="lead-reply-btn"><Mail size={14} /> Rispondi</a>
                <button onClick={() => removeLead(selected)} className="btn-danger" data-testid="lead-delete-btn"><Trash2 size={12} /></button>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-[color:var(--text-2)] text-sm">
              <Inbox size={36} strokeWidth={1.3} className="mx-auto mb-3 text-[color:var(--text-3)]" />
              <div>Seleziona una richiesta<br />per vedere i dettagli.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
