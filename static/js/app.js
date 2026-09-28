import { Recorder } from "./recorder.js";
import { apiFetch } from "./api.js";

function initRecordPage() {
  const button = document.getElementById("record-button");
  const status = document.getElementById("record-status");
  const ring = document.getElementById("record-ring");
  if (!button) return;

  const setStatus = (text) => {
    status.textContent = text;
  };

  const recorder = new Recorder({
    onStart: () => {
      button.classList.add("recording");
      setStatus("Enregistrement... clique pour arrêter.");
      if (ring) ring.style.setProperty("--progress", "0");
    },
    onTick: (elapsed, max) => {
      if (ring) ring.style.setProperty("--progress", String(Math.min(elapsed / max, 1)));
    },
    onStop: async (blob) => {
      button.classList.remove("recording");
      button.disabled = true;
      setStatus("Envoi en cours...");
      try {
        const formData = new FormData();
        formData.append("audio", blob, "recording.webm");
        await apiFetch("/recordings", { method: "POST", body: formData, isForm: true });
        setStatus("Fredonnement enregistré !");
      } catch (err) {
        setStatus(err.message || "Erreur lors de l'envoi.");
      } finally {
        button.disabled = false;
      }
    },
    onError: (err) => {
      setStatus(err.message);
    },
  });

  button.addEventListener("click", () => {
    if (recorder.isRecording) {
      recorder.stop();
    } else {
      recorder.start();
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initRecordPage();
});
