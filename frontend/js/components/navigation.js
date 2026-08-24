import { APP_CONFIG } from "../config.js";

function navLink(item, currentPath) {
  const isCurrent = item.href === currentPath;
  return `
    <a class="primary-nav__link" href="${item.href}"${isCurrent ? ' aria-current="page"' : ""}>
      ${item.label}
    </a>
  `;
}

export function renderPrimaryNavigation({ currentPath = "/", role = "student" } = {}) {
  const host = document.querySelector("[data-primary-navigation]");
  if (!host) return;

  const studentItems = [
    { label: "Dashboard", href: "/dashboard" },
    { label: "Rooms", href: "/rooms" },
    { label: "My Bookings", href: "/bookings" },
    { label: "Account", href: "/account" },
  ];

  const adminItems = [
    { label: "Dashboard", href: "/admin" },
    { label: "Rooms", href: "/admin/rooms" },
    { label: "Account", href: "/account" },
  ];

  const items = role === "admin" ? adminItems : studentItems;

  host.innerHTML = `
    <header class="site-header">
      <div class="container site-header__inner">
        <a class="wordmark" href="/">${APP_CONFIG.name}</a>
        <button class="mobile-menu-button" type="button" data-menu-button aria-expanded="false" aria-controls="primary-menu">
          Menu
        </button>
        <nav class="primary-nav" id="primary-menu" data-primary-menu aria-label="Primary navigation">
          ${items.map((item) => navLink(item, currentPath)).join("")}
        </nav>
      </div>
    </header>
  `;

  const menuButton = host.querySelector("[data-menu-button]");
  const menu = host.querySelector("[data-primary-menu]");

  menuButton?.addEventListener("click", () => {
    const open = menu.dataset.open !== "true";
    menu.dataset.open = String(open);
    menuButton.setAttribute("aria-expanded", String(open));
  });
}

export function renderAdminNavigation({ currentPath = "/admin" } = {}) {
  const host = document.querySelector("[data-admin-navigation]");
  if (!host) return;

  const items = [
    { label: "Overview", href: "/admin" },
    { label: "Rooms", href: "/admin/rooms" },
    { label: "Students", href: "/admin/students" },
    { label: "Bookings", href: "/admin/bookings" },
  ];

  host.innerHTML = `
    <div class="secondary-nav">
      <div class="container">
        <div class="secondary-nav__heading">Administration</div>
        <nav class="secondary-nav__links" aria-label="Administration navigation">
          ${items
            .map(
              (item) => `
                <a class="secondary-nav__link" href="${item.href}"${item.href === currentPath ? ' aria-current="page"' : ""}>
                  ${item.label}
                </a>
              `,
            )
            .join("")}
        </nav>
      </div>
    </div>
  `;
}
