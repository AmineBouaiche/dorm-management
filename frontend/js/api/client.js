import { APP_CONFIG } from "../config.js";
import { clearAccessToken, getAccessToken } from "../auth/session.js";

export class ApiError extends Error {
  constructor(message, status, payload = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

function errorMessage(payload, fallback) {
  if (payload && typeof payload === "object") {
    if (typeof payload.detail === "string") return payload.detail;
    if (Array.isArray(payload.detail) && payload.detail[0]?.msg) return payload.detail[0].msg;
  }
  return fallback;
}

export async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = getAccessToken();

  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response;
  try {
    response = await fetch(`${APP_CONFIG.apiBaseUrl}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new ApiError("We could not connect to Residence. Check your connection and try again.", 0);
  }

  const payload = await parseResponse(response);

  if (!response.ok) {
    if (response.status === 401 && path !== "/auth/login") clearAccessToken();
    throw new ApiError(errorMessage(payload, "The request could not be completed."), response.status, payload);
  }

  return payload;
}

export function getCurrentUser() {
  return apiRequest("/auth/me");
}

export function registerStudent(data) {
  return apiRequest("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function login(email, password) {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  return apiRequest("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
}

export function listRooms() {
  return apiRequest("/rooms");
}

export function listAvailableRooms(startDate, endDate) {
  const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
  return apiRequest(`/rooms/available?${params}`);
}

export function getRoom(roomId) {
  return apiRequest(`/rooms/${roomId}`);
}
