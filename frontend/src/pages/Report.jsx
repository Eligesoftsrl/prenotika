import React, { useEffect, useMemo, useState } from "react";
import { api, API_BASE } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { tipologiaLabels } from "@/lib/tipologia";
import { FileText, Download, Calendar, Users, ChevronLeft, ChevronRight } from "lucide-react";

const MESI = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno","Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"];

function fmtISO(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function startOfWeek(d) {
  const x = new Date(d);
  const dow = (x.getDay() + 6) % 7; // Mon=0
  x.setDate(x.getDate() - dow);
  x.setHours(0, 0, 0, 0);
  return x;
}

function addDays(d, n) {
  const x = new Date(d);
  x.setDate(x.getDate() + n);
  return x;
}

function fmtIT(d) {
  return d.toLocaleDateString("it-IT", { day: "2-digit", month: "long", year: "numeric" });
}

export default function Report() {
  const { studio } = useAuth();
  const L = tipologiaLabels(studio?.tipologia);

  const [period, setPeriod] = useState("week"); // day | week | month
  const [refDate, setRefDate] = useState(new Date());
  const [docenteId, setDocenteId] = useState(""); // "" = tutti
  const [docenti, setDocenti] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get("/docenti");
        setDocenti(data || []);
      } catch {
        // ignore
      }
    })();
  }, []);

  const rangeLabel = useMemo(() => {
    if (period === "day") return fmtIT(refDate);
    if (period === "week") {
      const s = startOfWeek(refDate);
      const e = addDays(s, 6);
      return `${s.toLocaleDateString("it-IT", { day: "2-digit", month: "short" })} – ${e.toLocaleDateString("it-IT", { day: "2-digit", month: "short", year: "numeric" })}`;
    }
    return `${MESI[refDate.getMonth()]} ${refDate.getFullYear()}`;
  }, [period, refDate]);

  const shift = (dir) => {
    const x = new Date(refDate);
    if (period === "day") x.setDate(x.getDate() + dir);
    else if (period === "week") x.setDate(x.getDate() + 7 * dir);
    else x.setMonth(x.getMonth() + dir);
    setRefDate(x);
  };

  const docenteSel = docenti.find((d) => d.id === docenteId);

  const download = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ period, data: fmtISO(refDate) });
      if (docenteId) params.set("docente_id", docenteId);
      const token = localStorage.getItem("eh_token");
      const resp = await fetch(`${API_BASE}/reports/appuntamenti.pdf?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) {
        const j = await resp.json().catch(() => ({}));
        alert(j.detail || "Errore nella generazione del PDF");
        return;
      }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      const scope = docenteId ? (docenteSel ? `${docenteSel.cognome}` : "docente") : "tutti";
      link.href = url;
      link.download = `planning-${period}-${fmtISO(refDate)}-${scope}.pdf`.toLowerCase();
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch {
      alert("Impossibile scaricare il report.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="report-page" className="max-w-3xl">
      <div className="mb-7">
        <div className="label-eyebrow mb-1.5">Planning</div>
        <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight">Report appuntamenti</h1>
        <p className="text-[color:var(--text-2)] mt-1">Genera un PDF aggregato per giorno, settimana o mese di tutti i {L.docenti.toLowerCase()} oppure di uno solo.</p>
      </div>

      <div className="surface-card p-5 mb-5">
        <div className="label-eyebrow mb-2">Periodo</div>
        <div className="flex p-0.5 rounded-md bg-[color:var(--surface-2)] w-fit mb-4">
          {[
            { v: "day", label: "Giorno" },
            { v: "week", label: "Settimana" },
            { v: "month", label: "Mese" },
          ].map((opt) => (
            <button
              key={opt.v}
              onClick={() => setPeriod(opt.v)}
              data-testid={`report-period-${opt.v}`}
              className={`px-3 py-1.5 text-xs font-semibold rounded-sm ${period === opt.v ? "bg-white shadow-sm" : "text-[color:var(--text-2)]"}`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <div className="label-eyebrow mb-2 flex items-center gap-1.5"><Calendar size={12} /> Data di riferimento</div>
            <div className="flex items-center gap-2">
              <button onClick={() => shift(-1)} className="btn-secondary" data-testid="report-prev"><ChevronLeft size={14} /></button>
              <input
                type="date"
                className="input-base flex-1"
                value={fmtISO(refDate)}
                onChange={(e) => e.target.value && setRefDate(new Date(e.target.value + "T00:00:00"))}
                data-testid="report-date"
              />
              <button onClick={() => shift(1)} className="btn-secondary" data-testid="report-next"><ChevronRight size={14} /></button>
            </div>
            <div className="text-xs text-[color:var(--text-2)] mt-2">Intervallo: <strong className="text-[color:var(--text-1)]">{rangeLabel}</strong></div>
          </div>

          <div>
            <div className="label-eyebrow mb-2 flex items-center gap-1.5"><Users size={12} /> {L.docenti}</div>
            <select
              className="input-base"
              value={docenteId}
              onChange={(e) => setDocenteId(e.target.value)}
              data-testid="report-docente-select"
            >
              <option value="">Tutti i {L.docenti.toLowerCase()}</option>
              {docenti.map((d) => (
                <option key={d.id} value={d.id}>{d.nome} {d.cognome}</option>
              ))}
            </select>
            <div className="text-xs text-[color:var(--text-2)] mt-2">
              {docenteId ? "Report del singolo professionista" : `Planning completo di tutto lo studio (${docenti.length})`}
            </div>
          </div>
        </div>
      </div>

      <div className="surface-card p-5 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-md bg-[color:var(--primary)]/10 flex items-center justify-center text-[color:var(--primary)]">
            <FileText size={20} strokeWidth={1.6} />
          </div>
          <div>
            <div className="font-display font-bold">PDF planning</div>
            <div className="text-xs text-[color:var(--text-2)]">
              {period === "day" ? "Giorno" : period === "week" ? "Settimana" : "Mese"} • {rangeLabel} • {docenteId ? (docenteSel ? `${docenteSel.nome} ${docenteSel.cognome}` : "—") : `Tutti i ${L.docenti.toLowerCase()}`}
            </div>
          </div>
        </div>
        <button
          onClick={download}
          disabled={loading}
          className="btn-primary"
          data-testid="report-download"
        >
          <Download size={15} /> {loading ? "Generazione…" : "Scarica PDF"}
        </button>
      </div>
    </div>
  );
}
