// Etichette dinamiche dipendenti dalla tipologia dello studio.
const LABELS = {
  centro_studi: {
    cliente: "Studente",
    clienti: "Studenti",
    docente: "Docente",
    docenti: "Docenti",
    materia: "Materia",
    materie: "Materie",
    materie_label: "Materie insegnate",
    associa_alunno: "Associa studente",
    needs_association: false,
  },
  studio_legale: {
    cliente: "Cliente",
    clienti: "Clienti",
    docente: "Avvocato",
    docenti: "Avvocati",
    materia: "Specializzazione",
    materie: "Specializzazioni",
    materie_label: "Specializzazioni",
    associa_alunno: "Associa cliente",
    needs_association: true,
  },
  studio_medico: {
    cliente: "Paziente",
    clienti: "Pazienti",
    docente: "Medico",
    docenti: "Medici",
    materia: "Specializzazione",
    materie: "Specializzazioni",
    materie_label: "Specializzazioni",
    associa_alunno: "Associa paziente",
    needs_association: true,
  },
};

// Chiavi delle etichette personalizzabili dall'admin (needs_association resta gestito da tipologia)
export const CUSTOM_LABEL_KEYS = [
  "cliente", "clienti", "docente", "docenti",
  "materia", "materie", "materie_label", "associa_alunno",
];

/**
 * Ritorna le etichette per la tipologia data, fondendo eventuali override custom impostati dall'admin.
 * @param {string} tipologia - centro_studi | studio_legale | studio_medico
 * @param {object|null|undefined} custom - eventuali override forniti dallo studio ({cliente:"…",…})
 */
export function tipologiaLabels(tipologia, custom) {
  const base = LABELS[tipologia] || LABELS.centro_studi;
  if (!custom || typeof custom !== "object") return base;
  const overrides = {};
  for (const k of CUSTOM_LABEL_KEYS) {
    const v = custom[k];
    if (typeof v === "string" && v.trim().length > 0) overrides[k] = v.trim();
  }
  return { ...base, ...overrides };
}

export const TIPOLOGIE = [
  { value: "centro_studi", label: "Centro studi (scuola / ripetizioni)" },
  { value: "studio_legale", label: "Studio legale (avvocati)" },
  { value: "studio_medico", label: "Studio medico" },
];
