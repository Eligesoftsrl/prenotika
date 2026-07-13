import React, { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { LayoutDashboard, Calendar, Users, GraduationCap, Clock, Building2, LogOut, Menu, X, BookOpen, Settings, FileText, Plane, Inbox, UserCog } from "lucide-react";
import { tipologiaLabels } from "@/lib/tipologia";
import Logo from "@/components/Logo";

const ROLE_LABEL = {
  super_admin: "Super Admin",
  admin: "Amministratore",
};

export default function Layout() {
  const { user, studio, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [leadsCount, setLeadsCount] = useState(0);

  const isSuper = user?.role === "super_admin";
  const isAdmin = user?.role === "admin";

  // Polling contatore lead nuovi (solo per super admin)
  useEffect(() => {
    if (!isSuper) return;
    let cancelled = false;
    const fetchCount = async () => {
      try {
        const { data } = await api.get("/leads/count?status=new");
        if (!cancelled) setLeadsCount(data?.count || 0);
      } catch { /* ignore */ }
    };
    fetchCount();
    const t = setInterval(fetchCount, 45000); // refresh ogni 45s
    return () => { cancelled = true; clearInterval(t); };
  }, [isSuper, location.pathname]);
  const L = tipologiaLabels(studio?.tipologia, studio?.custom_labels);

  const accountItem = { to: "/account", icon: UserCog, label: "Account", testid: "nav-link-account" };

  const items = isSuper
    ? [
        { to: "/studios", icon: Building2, label: "Aziende", testid: "nav-link-studios" },
        { to: "/leads", icon: Inbox, label: "Richieste", testid: "nav-link-leads", badge: leadsCount },
        accountItem,
      ]
    : [
        { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard", testid: "nav-link-dashboard" },
        { to: "/appuntamenti", icon: Calendar, label: "Appuntamenti", testid: "nav-link-appuntamenti" },
        { to: "/orari", icon: Clock, label: "Orari", testid: "nav-link-orari" },
        { to: "/eccezioni", icon: Plane, label: "Ferie", testid: "nav-link-eccezioni" },
        ...(isAdmin
          ? [
              { to: "/docenti", icon: GraduationCap, label: L.docenti, testid: "nav-link-docenti" },
              { to: "/clienti", icon: Users, label: L.clienti, testid: "nav-link-clienti" },
              { to: "/materie", icon: BookOpen, label: L.materie, testid: "nav-link-materie" },
              { to: "/report", icon: FileText, label: "Report", testid: "nav-link-report" },
              { to: "/impostazioni", icon: Settings, label: "Impostazioni", testid: "nav-link-impostazioni" },
            ]
          : []),
        accountItem,
      ];

  const SideContent = (
    <>
      <div className="px-6 py-7">
        <div className="flex items-center gap-3">
          <Logo size={42} />
          <div>
            <div className="font-display text-lg font-bold leading-none tracking-tight">Prenotika</div>
            <div className="text-[10px] text-[color:var(--text-2)] tracking-[0.22em] uppercase mt-1">Smart Booking</div>
          </div>
        </div>
      </div>
      <div className="px-4 mb-3">
        <div className="label-eyebrow px-3 mb-2">Menu</div>
        <nav className="flex flex-col gap-1">
          {items.map((it) => (
            <NavLink
              key={it.to}
              to={it.to}
              data-testid={it.testid}
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
              onClick={() => setOpen(false)}
            >
              <it.icon size={18} strokeWidth={1.6} />
              <span className="flex-1">{it.label}</span>
              {it.badge > 0 && (
                <span
                  className="ml-auto min-w-[20px] h-5 px-1.5 flex items-center justify-center rounded-full text-[10px] font-bold text-white"
                  style={{ background: "linear-gradient(135deg,#EF4444 0%,#F97316 100%)", boxShadow: "0 4px 10px -2px rgba(239,68,68,0.5)" }}
                  data-testid={`${it.testid}-badge`}
                >
                  {it.badge > 99 ? "99+" : it.badge}
                </span>
              )}
            </NavLink>
          ))}
        </nav>
      </div>
      <div className="mt-auto px-4 pb-6">
        <div className="surface-card p-3.5">
          <div className="text-xs text-[color:var(--text-2)] mb-0.5">{ROLE_LABEL[user?.role] || L.docente}</div>
          <div className="text-sm font-semibold truncate" data-testid="user-fullname">
            {user?.nome} {user?.cognome}
          </div>
          {studio?.nome ? (
            <div className="text-[11px] text-[color:var(--text-2)] mt-0.5 truncate" data-testid="user-studio">{studio.nome}</div>
          ) : null}
          <button
            onClick={logout}
            data-testid="logout-button"
            className="mt-3 w-full btn-secondary justify-center text-sm"
          >
            <LogOut size={15} strokeWidth={1.6} /> Esci
          </button>
        </div>
      </div>
    </>
  );

  return (
    <div className="min-h-screen flex bg-[color:var(--bg)]">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-[260px] flex-col border-r border-[color:var(--border)] bg-[color:var(--bg)] sticky top-0 h-screen">
        {SideContent}
      </aside>

      {/* Mobile drawer */}
      {open && (
        <div className="md:hidden fixed inset-0 z-40">
          <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={() => setOpen(false)} />
          <aside className="absolute left-0 top-0 bottom-0 w-[280px] bg-[color:var(--bg)] border-r border-[color:var(--border)] flex flex-col anim-fade-up">
            <div className="flex justify-end px-3 pt-3">
              <button onClick={() => setOpen(false)} className="btn-secondary" data-testid="mobile-close">
                <X size={16} />
              </button>
            </div>
            {SideContent}
          </aside>
        </div>
      )}

      {/* Main */}
      <main className="flex-1 min-w-0">
        <header className="md:hidden flex items-center justify-between px-4 py-3 border-b border-[color:var(--border)] bg-[color:var(--surface)]">
          <button onClick={() => setOpen(true)} className="btn-secondary" data-testid="mobile-menu-button">
            <Menu size={16} />
          </button>
          <div className="font-display font-bold tracking-tight">Prenotika</div>
          <div className="w-9" />
        </header>
        <div className="p-5 md:p-8 max-w-[1400px] mx-auto anim-fade-up">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
