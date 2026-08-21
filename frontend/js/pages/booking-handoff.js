import { requireAuthentication } from "../auth/guards.js";
import { renderPrimaryNavigation } from "../components/navigation.js";
const page = document.querySelector("[data-handoff-page]");
const user = await requireAuthentication({ role: "student" });
if (user && page) {
  renderPrimaryNavigation({ currentPath: "/rooms", role: "student" });
  const params = new URLSearchParams(window.location.search);
  const roomId = params.get("room_id"); const start = params.get("start"); const end = params.get("end");
  const back = document.querySelector("[data-return-room]");
  if (roomId) { const q = new URLSearchParams(); if (start) q.set("start", start); if (end) q.set("end", end); back.href = `/rooms/${roomId}${q.size ? `?${q}` : ""}`; }
  page.hidden = false;
}
