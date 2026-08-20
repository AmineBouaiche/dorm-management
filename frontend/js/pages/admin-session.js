import { requireAuthentication } from "../auth/guards.js";
import { signOut } from "../auth/session.js";
import { renderAdminNavigation, renderPrimaryNavigation } from "../components/navigation.js";

const page = document.querySelector("[data-session-page]");
const user = await requireAuthentication({ role: "admin" });

if (user && page) {
  renderPrimaryNavigation({ currentPath: "/admin", role: "admin" });
  renderAdminNavigation({ currentPath: "/admin" });
  page.querySelector("[data-user-name]").textContent = user.email;
  page.querySelector("[data-user-email]").textContent = user.email;
  page.querySelector("[data-user-role]").textContent = "Administrator";
  page.hidden = false;
}

document.querySelector("[data-sign-out]")?.addEventListener("click", signOut);
