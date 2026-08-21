import { requireAuthentication } from "../auth/guards.js";
import { renderPrimaryNavigation } from "../components/navigation.js";
const page = document.querySelector("[data-bookings-handoff]");
const user = await requireAuthentication({ role: "student" });
if (user && page) { renderPrimaryNavigation({ currentPath: "/bookings", role: "student" }); page.hidden = false; }
