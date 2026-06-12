import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Users, GraduationCap, CalendarClock, CalendarDays, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

const GIORNI = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"];

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("it-IT", { day: "2-digit", month: "short", weekday: "short" });
}

export default function Dashboard() {
  const { user, studio } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get("/dashboard/stats");
        setStats(data);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const cards = [
    { label: "Clienti totali", value: stats?.totale_clienti ?? "—", icon: Users, hide: user?.role === "docente" },
    { label: "Docenti", value: stats?.totale_docenti ?? "—", icon: GraduationCap, hide: user?.role === "docente" },
    { label: "Appuntamenti oggi", value: stats?.appuntamenti_oggi ?? "—", icon: CalendarClock },
    { label: "Appuntamenti 7 giorni", value: stats?.appuntamenti_settimana ?? "—", icon: CalendarDays },
  ].filter((c) => !c.hide);

  return (
    <div data-testid="dashboard-page">
      <div className="flex items-start justify-between flex-wrap gap-3 mb-7">
        <div>
          <div className="label-eyebrow mb-1.5">{studio?.nome || "Piattaforma"}</div>
          <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight" data-testid="dashboard-title">
            Ciao, {user?.nome} <span className="text-[color:var(--secondary)]">.</span>
          </h1>
          <p className="text-[color:var(--text-2)] mt-1.5">Ecco una panoramica della tua agenda.</p>
        </div>
        <Link to="/appuntamenti" className="btn-primary" data-testid="dashboard-go-calendar">
          <CalendarDays size={16} /> Vai al calendario
        </Link>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {cards.map((c) => (
          <div key={c.label} className="kpi-card" data-testid={`kpi-${c.label.toLowerCase().replace(/\s+/g, '-')}`}>
            <div className="flex items-start justify-between">
              <div className="label-eyebrow">{c.label}</div>
              <c.icon size={18} strokeWidth={1.5} className="text-[color:var(--text-2)]" />
            </div>
            <div className="mt-3 font-display text-3xl font-black tracking-tight">{loading ? "…" : c.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 surface-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display text-lg font-bold">Prossimi appuntamenti</h3>
            <Link to="/appuntamenti" className="text-sm text-[color:var(--primary)] hover:underline" data-testid="see-all-appointments">Vedi tutti</Link>
          </div>
          {loading ? (
            <div className="text-[color:var(--text-2)] text-sm">Caricamento…</div>
          ) : stats?.prossimi_appuntamenti?.length ? (
            <ul className="divide-y divide-[color:var(--border)]" data-testid="upcoming-list">
              {stats.prossimi_appuntamenti.map((a) => (
                <li key={a.id} className="py-3 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="font-semibold truncate">{a.cliente_nome}</div>
                    <div className="text-xs text-[color:var(--text-2)] mt-0.5">
                      con <span className="font-medium">{a.docente_nome}</span> • {a.note || "Nessuna nota"}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-sm font-semibold">{formatDate(a.data)}</div>
                    <div className="text-xs text-[color:var(--text-2)]">{a.dal} – {a.al}</div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-center py-10 text-[color:var(--text-2)]">
              <Sparkles className="mx-auto mb-2 text-[color:var(--border)]" size={28} />
              <div className="text-sm">Nessun appuntamento in programma.</div>
              <Link to="/appuntamenti" className="btn-primary mt-4 inline-flex" data-testid="empty-create-appointment">Crea il primo</Link>
            </div>
          )}
        </div>

        <div className="surface-card p-5">
          <h3 className="font-display text-lg font-bold mb-1">Suggerimento</h3>
          <p className="text-sm text-[color:var(--text-2)] mb-4">Imposta prima la disponibilità dei docenti, poi crea gli appuntamenti dal calendario.</p>
          <Link to="/orari" className="btn-secondary w-full justify-center" data-testid="suggestion-orari">Gestisci orari</Link>
        </div>
      </div>
    </div>
  );
}
