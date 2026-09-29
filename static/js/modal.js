import { el } from "./dom.js";

export function confirmDialog(message, { confirmLabel = "Supprimer", cancelLabel = "Annuler" } = {}) {
  return new Promise((resolve) => {
    let onKeydown;

    const close = (result) => {
      overlay.remove();
      document.removeEventListener("keydown", onKeydown);
      resolve(result);
    };

    onKeydown = (e) => {
      if (e.key === "Escape") close(false);
    };

    const cancelBtn = el("button", {
      attrs: { type: "button", class: "modal-btn modal-btn-cancel" },
      text: cancelLabel,
    });
    cancelBtn.addEventListener("click", () => close(false));

    const confirmBtn = el("button", {
      attrs: { type: "button", class: "modal-btn modal-btn-confirm" },
      text: confirmLabel,
    });
    confirmBtn.addEventListener("click", () => close(true));

    const card = el("div", {
      attrs: { class: "modal-card" },
      children: [
        el("p", { attrs: { class: "modal-message" }, text: message }),
        el("div", { attrs: { class: "modal-actions" }, children: [cancelBtn, confirmBtn] }),
      ],
    });

    const overlay = el("div", { attrs: { class: "modal-overlay" }, children: [card] });
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) close(false);
    });

    document.addEventListener("keydown", onKeydown);
    document.body.appendChild(overlay);
    confirmBtn.focus();
  });
}

export function promptDialog(message, { defaultValue = "", confirmLabel = "OK", cancelLabel = "Annuler", placeholder = "" } = {}) {
  return new Promise((resolve) => {
    let onKeydown;

    const close = (result) => {
      overlay.remove();
      document.removeEventListener("keydown", onKeydown);
      resolve(result);
    };

    const input = el("input", {
      attrs: { type: "text", class: "modal-input", value: defaultValue, placeholder },
    });

    onKeydown = (e) => {
      if (e.key === "Escape") close(null);
      if (e.key === "Enter") close(input.value);
    };

    const cancelBtn = el("button", {
      attrs: { type: "button", class: "modal-btn modal-btn-cancel" },
      text: cancelLabel,
    });
    cancelBtn.addEventListener("click", () => close(null));

    const confirmBtn = el("button", {
      attrs: { type: "button", class: "modal-btn modal-btn-confirm" },
      text: confirmLabel,
    });
    confirmBtn.addEventListener("click", () => close(input.value));

    const card = el("div", {
      attrs: { class: "modal-card" },
      children: [
        el("p", { attrs: { class: "modal-message" }, text: message }),
        input,
        el("div", { attrs: { class: "modal-actions" }, children: [cancelBtn, confirmBtn] }),
      ],
    });

    const overlay = el("div", { attrs: { class: "modal-overlay" }, children: [card] });
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) close(null);
    });

    document.addEventListener("keydown", onKeydown);
    document.body.appendChild(overlay);
    input.focus();
    input.select();
  });
}
