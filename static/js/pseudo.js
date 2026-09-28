import { getPseudo, setPseudo } from "./api.js";
import { el } from "./dom.js";

export function renderPseudoBar() {
  const container = document.getElementById("pseudo-bar");
  if (!container) return;
  container.textContent = "";

  const current = getPseudo();
  const label = el("span", {
    attrs: { class: "pseudo-label" },
    text: current === "anonyme" ? "Anonyme" : current,
  });

  const changeBtn = el("button", {
    attrs: { type: "button", class: "pseudo-btn" },
    text: "Changer de pseudo",
  });
  changeBtn.addEventListener("click", () => {
    const next = window.prompt("Choisis un pseudo :", current === "anonyme" ? "" : current);
    if (next === null) return;
    const trimmed = next.trim();
    setPseudo(trimmed || "anonyme");
    location.reload();
  });

  container.appendChild(label);
  container.appendChild(changeBtn);
}
