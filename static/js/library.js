import { el } from "./dom.js";
import { apiFetch } from "./api.js";
import { analyzeRecording } from "./analysis.js";
import { platformLink } from "./platform_icons.js";
import { buildAudioPlayer } from "./audio_player.js";

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

function renderRecordingCard(recording) {
  const children = [];

  children.push(
    el("p", { attrs: { class: "recording-date" }, text: new Date(recording.created_at + "Z").toLocaleString("fr-FR") })
  );

  children.push(buildAudioPlayer(`/recordings/${recording.id}/audio`));

  if (recording.analysis_status === "done") {
    const title = recording.guessed_title || "Inconnu";
    const artist = recording.guessed_artist || "Inconnu";
    children.push(el("p", { attrs: { class: "guess-result" }, text: `${title} — ${artist}` }));

    if (recording.transcript) {
      children.push(el("p", { attrs: { class: "transcript-text" }, text: `« ${recording.transcript} »` }));
    }

    const links = el("div", { attrs: { class: "platform-links" } });
    const deezer = platformLink("deezer", recording.deezer_link);
    const spotify = platformLink("spotify", recording.spotify_link);
    const youtube = platformLink("youtube", recording.youtube_link);
    for (const link of [deezer, spotify, youtube]) {
      if (link) links.appendChild(link);
    }
    children.push(links);
  } else if (recording.analysis_status === "error") {
    children.push(
      el("p", { attrs: { class: "status-text error" }, text: recording.analysis_error || "Erreur d'analyse." })
    );
    const retryBtn = el("button", {
      attrs: { type: "button", class: "analyze-btn" },
      text: "Réessayer l'analyse",
    });
    retryBtn.addEventListener("click", () => analyzeRecording(recording.id, retryBtn, () => loadData()));
    children.push(retryBtn);
  } else {
    children.push(el("p", { attrs: { class: "status-text" }, text: "Analyse en cours..." }));
  }

  children.push(
    el("button", {
      attrs: { type: "button", class: "danger-btn", onClick: () => deleteRecording(recording.id) },
      text: "Supprimer",
    })
  );

  return el("article", { attrs: { class: "recording-card" }, children });
}

async function deleteRecording(recordingId) {
  if (!window.confirm("Supprimer ce fredonnement ?")) return;
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
