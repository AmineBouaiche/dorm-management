import { ApiError, registerStudent } from "../api/client.js";
import { redirectAuthenticatedUser } from "../auth/guards.js";
import { APP_CONFIG } from "../config.js";

const form = document.querySelector("[data-register-form]");
const message = document.querySelector("[data-form-message]");
const submit = form?.querySelector('button[type="submit"]');

function setMessage(text = "") {
  if (!message) return;
  message.textContent = text;
  message.hidden = !text;
}

function setFieldError(name, text = "") {
  const input = form?.elements.namedItem(name);
  const error = document.querySelector(`[data-error-for="${name}"]`);
  if (input instanceof HTMLElement) input.setAttribute("aria-invalid", text ? "true" : "false");
  if (error) {
    error.textContent = text;
    error.hidden = !text;
  }
}

function clearErrors() {
  ["first_name", "last_name", "student_id", "email", "password", "confirm_password"].forEach((name) => setFieldError(name));
  setMessage();
}

function setSubmitting(active) {
  if (!submit) return;
  submit.disabled = active;
  submit.textContent = active ? "Creating account..." : "Create account";
}

function validate(data) {
  let valid = true;
  if (!data.first_name) { setFieldError("first_name", "Enter your first name."); valid = false; }
  if (!data.last_name) { setFieldError("last_name", "Enter your last name."); valid = false; }
  if (!data.student_id) { setFieldError("student_id", "Enter your student ID."); valid = false; }
  if (!data.email) { setFieldError("email", "Enter your email address."); valid = false; }
  if (data.password.length < 8) { setFieldError("password", "Use at least 8 characters."); valid = false; }
  if (data.password !== data.confirm_password) { setFieldError("confirm_password", "Passwords do not match."); valid = false; }
  return valid;
}

async function handleSubmit(event) {
  event.preventDefault();
  clearErrors();

  const raw = new FormData(form);
  const data = {
    first_name: String(raw.get("first_name") || "").trim(),
    last_name: String(raw.get("last_name") || "").trim(),
    student_id: String(raw.get("student_id") || "").trim(),
    email: String(raw.get("email") || "").trim(),
    password: String(raw.get("password") || ""),
    confirm_password: String(raw.get("confirm_password") || ""),
  };

  if (!validate(data)) return;

  setSubmitting(true);
  try {
    await registerStudent({
      first_name: data.first_name,
      last_name: data.last_name,
      student_id: data.student_id,
      email: data.email,
      password: data.password,
    });
    const query = new URLSearchParams({ registered: "1" });
    window.location.assign(`${APP_CONFIG.routes.login}?${query}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      setMessage("An account with this email address or student ID already exists.");
    } else {
      setMessage(error.message || "We could not create your account. Try again.");
    }
  } finally {
    setSubmitting(false);
  }
}

await redirectAuthenticatedUser();
form?.addEventListener("submit", handleSubmit);
