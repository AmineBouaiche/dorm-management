import { ApiError, login } from "../api/client.js";
import { redirectAuthenticatedUser } from "../auth/guards.js";
import { setAccessToken } from "../auth/session.js";
import { APP_CONFIG } from "../config.js";

const form = document.querySelector("[data-login-form]");
const message = document.querySelector("[data-form-message]");
const submit = form?.querySelector('button[type="submit"]');

function setMessage(text = "") {
  if (!message) return;
  message.textContent = text;
  message.hidden = !text;
}

function setSubmitting(active) {
  if (!submit) return;
  submit.disabled = active;
  submit.textContent = active ? "Signing in..." : "Sign in";
}

async function handleSubmit(event) {
  event.preventDefault();
  setMessage();

  const data = new FormData(form);
  const email = String(data.get("email") || "").trim();
  const password = String(data.get("password") || "");

  if (!email || !password) {
    setMessage("Enter your email address and password.");
    return;
  }

  setSubmitting(true);
  try {
    const token = await login(email, password);
    setAccessToken(token.access_token);

    const params = new URLSearchParams(window.location.search);
    const next = params.get("next");
    if (next && next.startsWith("/") && !next.startsWith("//")) {
      window.location.assign(next);
      return;
    }

    window.location.assign(APP_CONFIG.routes.home);
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      setMessage("The email address or password is incorrect.");
    } else {
      setMessage(error.message || "We could not sign you in. Try again.");
    }
  } finally {
    setSubmitting(false);
  }
}

const params = new URLSearchParams(window.location.search);
const registrationMessage = document.querySelector("[data-registration-message]");
if (registrationMessage && params.get("registered") === "1") registrationMessage.hidden = false;

const signedOutMessage = document.querySelector("[data-signed-out-message]");
if (signedOutMessage && params.get("signed_out") === "1") signedOutMessage.hidden = false;

await redirectAuthenticatedUser();
form?.addEventListener("submit", handleSubmit);
