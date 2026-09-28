const PSEUDO_KEY = "mumble_pseudo";

export function getPseudo() {
  try {
    return localStorage.getItem(PSEUDO_KEY) || "anonyme";
  } catch {
    return "anonyme";
  }
}

export function setPseudo(pseudo) {
  try {
    localStorage.setItem(PSEUDO_KEY, pseudo);
  } catch {
    // localStorage indisponible (navigation privée, etc.) : le pseudo reste "anonyme" pour cette session.
  }
}

export async function apiFetch(path, { method = "GET", body, isForm = false } = {}) {
  const headers = { "X-Mumble-Pseudo": getPseudo() };
  let payload = body;
  if (body !== undefined && !isForm) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const response = await fetch(path, { method, headers, body: payload });

  if (!response.ok) {
    let detail = `Erreur ${response.status}`;
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch {
      // pas de corps JSON exploitable, on garde le message par défaut
    }
    throw new Error(detail);
  }

  if (response.status === 204) return null;
  return response.json();
}
