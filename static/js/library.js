import { el, svgEl } from "./dom.js";
import { apiFetch, getPseudo } from "./api.js";
import { analyzeRecording } from "./analysis.js";
import { platformLink } from "./platform_icons.js";
import { buildAudioPlayer } from "./audio_player.js";
import { confirmDialog } from "./modal.js";

let pollIntervalId = null;

async function loadData() {
  const recordings = await apiFetch("/recordings");
  render(recordings);
  scheduleNextPollIfNeeded(recordings);
}

function scheduleNextPollIfNeeded(recordings) {
  const hasPending = recordings.some((r) => r.analysis_status === "pending" || r.analysis_status === "none");
  if (pollIntervalId) {
    clearInterval(pollIntervalId);
    pollIntervalId = null;
  }
  if (hasPending) {
    pollIntervalId = setInterval(loadData, 3000);
  }
}

function render(recordings) {
  const container = document.getElementById("recordings-list");
  if (!container) return;
  container.textContent = "";

  if (recordings.length === 0) {
    container.appendChild(el("p", { attrs: { class: "empty-state" }, text: "Aucun fredonnement pour l'instant." }));
    return;
  }

  for (const recording of recordings) {
    container.appendChild(renderRecordingCard(recording));
  }
}

function trashIcon() {
  return svgEl("svg", {
    attrs: { viewBox: "0 0 24 24", width: "13", height: "13", "aria-hidden": "true" },
    children: [
      svgEl("path", { attrs: { d: "M9 3h6l1 2h4v2H4V5h4l1-2z", fill: "currentColor" } }),
      svgEl("path", {
        attrs: { d: "M6 8h12l-1 12a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 8z", fill: "currentColor" },
      }),
    ],
  });
}

function renderRecordingCard(recording) {
  const children = [];

  children.push(
    el("p", { attrs: { class: "recording-date" }, text: new Date(recording.created_at + "Z").toLocaleString("fr-FR") })
  );

  children.push(buildAudioPlayer(`/recordings/${recording.id}/audio?pseudo=${encodeURIComponent(getPseudo())}`));

  const footer = el("div", { attrs: { class: "card-footer" } });

  if (recording.analysis_status === "done") {
    const title = recording.guessed_title || "Inconnu";
    const artist = recording.guessed_artist || "Inconnu";
    children.push(el("p", { attrs: { class: "guess-result" }, text: `${title} — ${artist}` }));

    if (recording.transcript) {
      children.push(el("p", { attrs: { class: "transcript-text" }, text: `« ${recording.transcript} »` }));
    }

    if (recording.guessed_title && recording.guessed_title !== "Inconnu") {
      const links = el("div", { attrs: { class: "platform-links" } });
      const deezer = platformLink("deezer", recording.deezer_link);
      const spotify = platformLink("spotify", recording.spotify_link);
      const youtube = platformLink("youtube", recording.youtube_link);
      for (const link of [deezer, spotify, youtube]) {
        if (link) links.appendChild(link);
      }
      footer.appendChild(links);
    }
  } else if (recording.analysis_status === "error") {
    children.push(
      el("p", { attrs: { class: "status-text error" }, text: recording.analysis_error || "Erreur d'analyse." })
    );
    const retryBtn = el("button", {
      attrs: { type: "button", class: "analyze-btn" },
      text: "Réessayer l'analyse",
    });
    retryBtn.addEventListener("click", () => analyzeRecording(recording.id, retryBtn, () => loadData()));
    footer.appendChild(retryBtn);
  } else {
    children.push(el("p", { attrs: { class: "status-text" }, text: "Analyse en cours..." }));
  }

  const deleteBtn = el("button", {
    attrs: { type: "button", class: "danger-btn", onClick: () => deleteRecording(recording.id) },
    children: [trashIcon(), el("span", { text: "Supprimer" })],
  });
  footer.appendChild(deleteBtn);

  children.push(footer);

  return el("article", { attrs: { class: "recording-card" }, children });
}

async function deleteRecording(recordingId) {
  const confirmed = await confirmDialog("Supprimer ce fredonnement ?");
  if (!confirmed) return;
  try {
    await apiFetch(`/recordings/${recordingId}`, { method: "DELETE" });
    await loadData();
  } catch (err) {
    window.alert(err.message);
  }
}

export function initLibraryPage() {
  const container = document.getElementById("recordings-list");
  if (!container) return;
  loadData();
}
