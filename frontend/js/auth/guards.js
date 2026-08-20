import { getCurrentUser } from "../api/client.js";
import { APP_CONFIG } from "../config.js";
import { clearAccessToken, hasAccessToken } from "./session.js";

function destinationFor(user) {
  return user.role === "admin" ? APP_CONFIG.routes.adminSession : APP_CONFIG.routes.session;
}

export async function redirectAuthenticatedUser() {
  if (!hasAccessToken()) return null;

  try {
    const user = await getCurrentUser();
    window.location.replace(destinationFor(user));
    return user;
  } catch {
    clearAccessToken();
    return null;
  }
}

export async function requireAuthentication({ role = null } = {}) {
  if (!hasAccessToken()) {
    window.location.replace(APP_CONFIG.routes.login);
    return null;
  }

  try {
    const user = await getCurrentUser();
    if (role && user.role !== role) {
      window.location.replace(destinationFor(user));
      return null;
    }
    return user;
  } catch {
    clearAccessToken();
    window.location.replace(APP_CONFIG.routes.login);
    return null;
  }
}
