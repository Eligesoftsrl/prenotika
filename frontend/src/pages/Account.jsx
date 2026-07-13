import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { KeyRound, Eye, EyeOff, Save, User as UserIcon, Shield, CreditCard, CheckCircle2, Zap, Sparkles, RefreshCw } from "lucide-react";

function PasswordInput({ value, onChange, placeholder, testId, required, autoComplete }) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <input
        type={show ? "text" : "password"}
        className="input-base pr-11"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        autoComplete={autoComplete}
        data-testid={testId}
      />
      <button
        type="button"
        onClick={() => setShow((s) => !s)}
        aria-label={show ? "Nascondi" : "Mostra"}
        tabIndex={-1}
        className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-md text-[color:var(--text-2)] hover:text-[color:var(--text)] hover:bg-[color:var(--surface-2)] transition-colors"
        data-testid={`${testId}-toggle`}
      >
        {show ? <EyeOff size={16} /> : <Eye size={16} />}
      </button>
    </div>
  );
}

export default function Account() {
  const { user, studio, refresh } = useAuth();
  const [sp, setSp] = useSearchParams();
  const [form, setForm] = useState({ current_password: "", new_password: "", confirm_password: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [plans, setPlans] = useState([]);
  const [checkoutBusy, setCheckoutBusy] = useState(""); // plan id in progress
  const [payStatus, setPayStatus] = useState(null); // {plan, status, payment_status}

  useEffect(() => {
    api.get("/payments/plans").then(({ data }) => setPlans(data)).catch(() => {});
  }, []);

  // Se torniamo da Stripe con session_id → poll status
  useEffect(() => {
    const sid = sp.get("stripe_session_id");
    if (!sid) return;
    let attempts = 0;
    let cancelled = false;
    const poll = async () => {
      attempts += 1;
      try {
        const { data } = await api.get(`/payments/checkout/status/${sid}`);
        if (cancelled) return;
        setPayStatus(data);
        if (data.payment_status === "paid") {
          if (refresh) await refresh();
          setSp({}, { replace: true });
          return;
        }
        if (data.status === "expired" || attempts >= 8) {
          setSp({}, { replace: true });
          return;
        }
        setTimeout(poll, 2000);
      } catch (err) {
        if (attempts < 3) setTimeout(poll, 2500);
      }
    };
    poll();
    return () => { cancelled = true; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const upgradePlan = async (planId) => {
    setCheckoutBusy(planId); setError("");
    try {
      const { data } = await api.post("/payments/checkout/session", {
        plan: planId,
        origin_url: window.location.origin,
      });
      window.location.href = data.url;
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Impossibile avviare il pagamento.");
      setCheckoutBusy("");
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setSuccess("");
    if (form.new_password.length < 8) {
      setError("La nuova password deve avere almeno 8 caratteri.");
      return;
    }
    if (form.new_password !== form.confirm_password) {
      setError("La conferma password non coincide.");
      return;
    }
    if (form.new_password === form.current_password) {
      setError("La nuova password deve essere diversa dall'attuale.");
      return;
    }
    setBusy(true);
    try {
      await api.post("/auth/change-password", {
        current_password: form.current_password,
        new_password: form.new_password,
      });
      setSuccess("Password aggiornata con successo.");
      setForm({ current_password: "", new_password: "", confirm_password: "" });
      setTimeout(() => setSuccess(""), 4000);
    } catch (err) {
      setError(formatApiError(err?.response?.data?.detail) || "Errore aggiornamento password.");
    } finally { setBusy(false); }
  };

  const roleLabel = { super_admin: "Super Admin", admin: "Amministratore", docente: "Professionista" }[user?.role] || user?.role;

  return (
    <div data-testid="account-page">
      <div className="mb-7">
        <div className="label-eyebrow mb-1.5">Il tuo account</div>
        <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight">Profilo e sicurezza</h1>
        <p className="text-[color:var(--text-2)] mt-1">Gestisci i tuoi dati di accesso e cambia la password quando vuoi.</p>
      </div>

      {/* Billing / Piano corrente */}
      {user?.role === "admin" && (
        <div className="mb-6" data-testid="billing-section">
          {sp.get("stripe_cancelled") === "1" && (
            <div className="mb-4 text-sm text-[color:var(--text-2)] bg-[color:var(--surface-2)] border border-[color:var(--border)] px-3 py-2 rounded-lg" data-testid="stripe-cancelled-banner">
              Pagamento annullato. Nessun addebito è stato effettuato.
            </div>
          )}
          {payStatus?.payment_status === "paid" && (
            <div className="mb-4 text-sm text-[color:var(--success)] bg-[#E5F0E9] border border-[#C8DDD0] px-3 py-2 rounded-lg inline-flex items-center gap-2" data-testid="stripe-paid-banner">
              <CheckCircle2 size={15} /> Pagamento completato! Il piano <strong>{payStatus.plan}</strong> è ora attivo.
            </div>
          )}
          {payStatus && payStatus.payment_status !== "paid" && payStatus.status !== "expired" && sp.get("stripe_session_id") && (
            <div className="mb-4 text-sm text-[color:var(--text-2)] bg-[color:var(--surface-2)] border border-[color:var(--border)] px-3 py-2 rounded-lg inline-flex items-center gap-2" data-testid="stripe-processing-banner">
              <RefreshCw size={13} className="animate-spin" /> Elaborazione pagamento in corso…
            </div>
          )}

          <div className="surface-card p-6">
            <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
              <div className="flex items-center gap-2">
                <CreditCard size={16} className="text-[color:var(--primary)]" />
                <h3 className="font-display font-bold text-lg">Piano & abbonamento</h3>
              </div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[color:var(--primary)]/10 text-[color:var(--primary)] text-xs font-semibold uppercase tracking-[0.14em]" data-testid="current-plan-badge">
                Piano attuale: {studio?.plan || "free"}
              </div>
            </div>
            <p className="text-xs text-[color:var(--text-2)] mb-5">Passa a un piano superiore per sbloccare più professionisti e funzionalità. Pagamento sicuro con Stripe.</p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {plans.map((p) => {
                const isCurrent = (studio?.plan || "free") === p.id;
                return (
                  <div key={p.id} className={`border rounded-2xl p-5 ${isCurrent ? "border-[color:var(--primary)] bg-[color:var(--primary)]/5" : "border-[color:var(--border)]"}`} data-testid={`billing-plan-${p.id}`}>
                    <div className="flex items-baseline justify-between mb-3">
                      <div className="inline-flex items-center gap-2">
                        {p.id === "pro" ? <Zap size={16} className="text-[color:var(--primary)]" /> : <Sparkles size={16} className="text-[color:var(--secondary)]" />}
                        <div className="font-display text-xl font-bold">{p.label}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-display text-2xl font-black">€{p.amount.toFixed(0)}<span className="text-xs font-medium text-[color:var(--text-2)]">/mese</span></div>
                      </div>
                    </div>
                    <ul className="space-y-1.5 mb-4">
                      {p.features.map((f) => (
                        <li key={f} className="flex items-start gap-1.5 text-xs text-[color:var(--text)]">
                          <CheckCircle2 size={13} className="text-[color:var(--success)] mt-0.5 shrink-0" /> {f}
                        </li>
                      ))}
                    </ul>
                    <button
                      disabled={isCurrent || checkoutBusy === p.id}
                      onClick={() => upgradePlan(p.id)}
                      className={isCurrent ? "btn-secondary w-full justify-center opacity-60" : "btn-primary w-full justify-center"}
                      data-testid={`billing-upgrade-${p.id}`}
                    >
                      {isCurrent ? "Piano attivo" : (checkoutBusy === p.id ? "Attendere…" : (<><CreditCard size={14} /> Passa a {p.label}</>))}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="surface-card p-6">
          <div className="flex items-center gap-2 mb-3"><UserIcon size={16} className="text-[color:var(--primary)]" /><h3 className="font-display font-bold text-lg">Dati profilo</h3></div>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between border-b border-[color:var(--border)] pb-2.5">
              <dt className="text-[color:var(--text-2)]">Nome</dt>
              <dd className="font-medium" data-testid="account-nome">{user?.nome} {user?.cognome}</dd>
            </div>
            <div className="flex justify-between border-b border-[color:var(--border)] pb-2.5">
              <dt className="text-[color:var(--text-2)]">Email</dt>
              <dd className="font-medium" data-testid="account-email">{user?.email}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-[color:var(--text-2)]">Ruolo</dt>
              <dd className="inline-flex items-center gap-1.5 font-medium" data-testid="account-role">
                <Shield size={13} className="text-[color:var(--primary)]" /> {roleLabel}
              </dd>
            </div>
          </dl>
        </div>

        <form onSubmit={submit} className="surface-card p-6 space-y-4" data-testid="change-password-form">
          <div className="flex items-center gap-2 mb-1"><KeyRound size={16} className="text-[color:var(--primary)]" /><h3 className="font-display font-bold text-lg">Cambia password</h3></div>
          <p className="text-xs text-[color:var(--text-2)] -mt-2 mb-2">Almeno 8 caratteri. Ti consigliamo una combinazione di lettere, numeri e simboli.</p>

          <div>
            <label className="block text-sm font-medium mb-1.5">Password attuale</label>
            <PasswordInput
              value={form.current_password}
              onChange={(e) => setForm({ ...form, current_password: e.target.value })}
              placeholder="La password che usi adesso"
              testId="current-password-input"
              autoComplete="current-password"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Nuova password</label>
            <PasswordInput
              value={form.new_password}
              onChange={(e) => setForm({ ...form, new_password: e.target.value })}
              placeholder="Nuova password (min. 8 caratteri)"
              testId="new-password-input"
              autoComplete="new-password"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Conferma nuova password</label>
            <PasswordInput
              value={form.confirm_password}
              onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
              placeholder="Ripeti la nuova password"
              testId="confirm-password-input"
              autoComplete="new-password"
              required
            />
          </div>

          {error && <div className="text-sm text-[color:var(--error)] bg-[#FBEFEF] border border-[#E5C4C4] px-3 py-2 rounded-lg" data-testid="account-error">{error}</div>}
          {success && <div className="text-sm text-[color:var(--success)] bg-[#E5F0E9] border border-[#C8DDD0] px-3 py-2 rounded-lg" data-testid="account-success">{success}</div>}

          <button type="submit" disabled={busy} className="btn-primary w-full justify-center" data-testid="account-submit-button">
            <Save size={15} /> {busy ? "Aggiornamento…" : "Aggiorna password"}
          </button>
        </form>
      </div>
    </div>
  );
}
