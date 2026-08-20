import { requireAuthentication } from "../auth/guards.js";
import { signOut } from "../auth/session.js";
import { renderPrimaryNavigation } from "../components/navigation.js";

const page = document.querySelector("[data-session-page]");
const user = await requireAuthentication({ role: "student" });

if (user && page) {
  renderPrimaryNavigation({ currentPath: "/", role: "student" });
  const name = user.student ? `${user.student.first_name} ${user.student.last_name}` : user.email;
  page.querySelector("[data-user-name]").textContent = name;
  page.querySelector("[data-user-email]").textContent = user.email;
  page.querySelector("[data-user-role]").textContent = "Student";
  page.hidden = false;
}

document.querySelector("[data-sign-out]")?.addEventListener("click", signOut);
