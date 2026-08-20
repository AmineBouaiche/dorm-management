import { getCurrentUser } from "../api/client.js";
import { clearAccessToken, hasAccessToken } from "../auth/session.js";
import { APP_CONFIG } from "../config.js";

if (!hasAccessToken()) {
  window.location.replace(APP_CONFIG.routes.login);
} else {
  try {
    const user = await getCurrentUser();
    window.location.replace(user.role === "admin" ? APP_CONFIG.routes.adminSession : APP_CONFIG.routes.session);
  } catch {
    clearAccessToken();
    window.location.replace(APP_CONFIG.routes.login);
  }
}
