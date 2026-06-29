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

export function tipologiaLabels(tipologia) {
  return LABELS[tipologia] || LABELS.centro_studi;
}

export const TIPOLOGIE = [
  { value: "centro_studi", label: "Centro studi (scuola / ripetizioni)" },
  { value: "studio_legale", label: "Studio legale (avvocati)" },
  { value: "studio_medico", label: "Studio medico" },
];
