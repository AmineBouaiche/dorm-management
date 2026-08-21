import { requireAuthentication } from "../auth/guards.js";
import { signOut } from "../auth/session.js";
import { renderPrimaryNavigation } from "../components/navigation.js";

const page = document.querySelector("[data-account-page]");
const content = document.querySelector("[data-account-content]");
const user = await requireAuthentication();

if (user && page) {
  const isAdmin = user.role === "admin";
  renderPrimaryNavigation({ currentPath: "/account", role: user.role });
  renderAccount(user, isAdmin);
  page.hidden = false;
}

function renderAccount(user, isAdmin) {
  if (isAdmin) {
    content.innerHTML = `<section><h2>Account information</h2><dl class="detail-list"><dt>Email</dt><dd>${user.email}</dd><dt>Role</dt><dd>Administrator</dd></dl></section><div class="account-actions"><button class="button button--secondary" type="button" data-sign-out>Sign out</button></div>`;
  } else {
    const student = user.student;
    content.innerHTML = `<section><h2>Personal information</h2><dl class="detail-list"><dt>First name</dt><dd>${student.first_name}</dd><dt>Last name</dt><dd>${student.last_name}</dd><dt>Student ID</dt><dd>${student.student_id}</dd><dt>Email</dt><dd>${user.email}</dd></dl></section><section class="section"><h2>Account</h2><dl class="detail-list"><dt>Role</dt><dd>Student</dd></dl></section><div class="account-actions"><button class="button button--secondary" type="button" data-sign-out>Sign out</button></div>`;
  }
  content.querySelector("[data-sign-out]")?.addEventListener("click", signOut);
}
