export function money(value) {
  return new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(Number(value));
}
export function humanDate(value, compact = false) {
  return new Intl.DateTimeFormat("en-GB", compact ? { day: "numeric", month: "short", year: "2-digit", timeZone: "UTC" } : { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));
}
export function statusMarkup(status) {
  const modifier = status === "confirmed" ? "success" : status === "pending" ? "warning" : "error";
  const label = status.charAt(0).toUpperCase() + status.slice(1);
  return `<span class="status status--${modifier}">${label}</span>`;
}
export function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
}
export function roomTypeLabel(value) { return value.charAt(0).toUpperCase() + value.slice(1); }
export function pathId(segment) {
  const parts = window.location.pathname.split("/").filter(Boolean);
  const index = parts.indexOf(segment);
  return index >= 0 ? Number(parts[index + 1]) : NaN;
}
