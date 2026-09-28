import { apiFetch } from "./api.js";

export async function analyzeRecording(id, button, onDone) {
  if (button.disabled) return;
  button.disabled = true;
  const originalText = button.textContent;
  button.textContent = "Analyse en cours...";
  try {
    const result = await apiFetch(`/recordings/${id}/analyze`, { method: "POST" });
    onDone(result);
  } catch (err) {
    window.alert(err.message || "Erreur lors de l'analyse.");
    onDone(null);
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}
