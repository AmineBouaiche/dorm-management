import { getCurrentUser } from "../api/client.js";
import { APP_CONFIG } from "../config.js";

const menuButton = document.querySelector("[data-landing-menu-button]");
const menu = document.querySelector("[data-landing-menu]");
const actions = document.querySelector("[data-landing-actions]");

menuButton?.addEventListener("click", () => {
  const open = menu?.dataset.open !== "true";
  if (menu) menu.dataset.open = String(open);
  menuButton.setAttribute("aria-expanded", String(open));
});

try {
  const user = await getCurrentUser();
  if (actions) {
    const destination = user.role === "admin" ? APP_CONFIG.routes.adminHome : APP_CONFIG.routes.home;
    actions.replaceChildren();

    const dashboardLink = document.createElement("a");
    dashboardLink.className = "primary-nav__link";
    dashboardLink.href = destination;
    dashboardLink.textContent = user.role === "admin" ? "Administration" : "Dashboard";

    const accountLink = document.createElement("a");
    accountLink.className = "button button--secondary landing-nav__button";
    accountLink.href = APP_CONFIG.routes.account;
    accountLink.textContent = "Account";

    actions.append(dashboardLink, accountLink);
  }
} catch {
  // Public visitors keep the default sign-in and registration actions.
}
