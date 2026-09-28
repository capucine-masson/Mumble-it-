import { el } from "./dom.js";

let hideTimeoutId = null;

export function showToast(message, { actionLabel, actionHref, duration = 5000 } = {}) {
  const container = document.getElementById("toast");
  if (!container) return;

  container.textContent = "";
  container.appendChild(el("span", { attrs: { class: "toast-message" }, text: message }));
  if (actionLabel && actionHref) {
    container.appendChild(el("a", { attrs: { href: actionHref, class: "toast-action" }, text: actionLabel }));
  }

  container.hidden = false;
  requestAnimationFrame(() => container.classList.add("visible"));

  if (hideTimeoutId) clearTimeout(hideTimeoutId);
  hideTimeoutId = setTimeout(() => {
    container.classList.remove("visible");
    setTimeout(() => { container.hidden = true; }, 250);
  }, duration);
}
