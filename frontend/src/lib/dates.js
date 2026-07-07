// Formatta un oggetto Date come "YYYY-MM-DD" usando i componenti LOCALI (NON UTC).
// Serve a evitare l'off-by-one classico causato da toISOString() (che shifta a UTC).
export function fmtISO(d) {
  if (!d) return "";
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function todayISO() {
  return fmtISO(new Date());
}
