import { APP_CONFIG } from "../config.js";

const TOKEN_KEY = "residence.access_token";

export function getAccessToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token) {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearAccessToken() {
  sessionStorage.removeItem(TOKEN_KEY);
}

export function hasAccessToken() {
  return Boolean(getAccessToken());
}

export function signOut() {
  clearAccessToken();
  window.location.assign(`${APP_CONFIG.routes.login}?signed_out=1`);
}
