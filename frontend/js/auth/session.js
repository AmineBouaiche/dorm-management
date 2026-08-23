import { APP_CONFIG } from "../config.js";

const CSRF_COOKIE = "residence_csrf";

export function getCsrfToken() {
  const prefix = `${CSRF_COOKIE}=`;
  const cookie = document.cookie.split(";").map((part) => part.trim()).find((part) => part.startsWith(prefix));
  return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : "";
}

export async function signOut() {
  const csrf = getCsrfToken();
  try {
    await fetch(`${APP_CONFIG.apiBaseUrl}/auth/logout`, {
      method: "POST",
      headers: csrf ? { "X-CSRF-Token": csrf } : {},
      credentials: "same-origin",
    });
  } finally {
    window.location.assign(`${APP_CONFIG.routes.login}?signed_out=1`);
  }
}
