import { getCurrentUser } from "../api/client.js";
import { APP_CONFIG } from "../config.js";

function destinationFor(user) {
  return user.role === "admin" ? APP_CONFIG.routes.adminHome : APP_CONFIG.routes.home;
}

export async function redirectAuthenticatedUser() {
  try {
    const user = await getCurrentUser();
    window.location.replace(destinationFor(user));
    return user;
  } catch {
    return null;
  }
}

export async function requireAuthentication({ role = null } = {}) {
  try {
    const user = await getCurrentUser();
    if (role && user.role !== role) {
      window.location.replace(destinationFor(user));
      return null;
    }
    return user;
  } catch {
    window.location.replace(APP_CONFIG.routes.login);
    return null;
  }
}
