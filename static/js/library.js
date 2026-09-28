import { el } from "./dom.js";
import { apiFetch } from "./api.js";
import { analyzeRecording } from "./analysis.js";

let folders = [];
let recordings = [];
let currentFolderId = "all"; // "all" | "none" | number

async function loadData() {
  [folders, recordings] = await Promise.all([apiFetch("/folders"), apiFetch("/recordings")]);
  render();
}

function render() {
  renderFolderFilter();
  renderRecordingsList();
}

function filteredRecordings() {
  if (currentFolderId === "all") return recordings;
  if (currentFolderId === "none") return recordings.filter((r) => r.folder_id === null);
  return recordings.filter((r) => r.folder_id === currentFolderId);
}

function renderFolderFilter() {
  const container = document.getElementById("folder-list");
  if (!container) return;
  container.textContent = "";

  const chipClass = (id) => (currentFolderId === id ? "folder-chip active" : "folder-chip");

  container.appendChild(
    el("button", {
      attrs: { type: "button", class: chipClass("all"), onClick: () => { currentFolderId = "all"; render(); } },
      text: "Tous",
    })
  );

  container.appendChild(
    el("button", {
      attrs: { type: "button", class: chipClass("none"), onClick: () => { currentFolderId = "none"; render(); } },
      text: "Sans dossier",
    })
  );

  for (const folder of folders) {
    container.appendChild(
      el("span", {
        attrs: { class: "folder-chip-group" },
        children: [
          el("button", {
            attrs: { type: "button", class: chipClass(folder.id), onClick: () => { currentFolderId = folder.id; render(); } },
            text: folder.name,
          }),
          el("button", {
            attrs: { type: "button", class: "icon-btn", title: "Renommer", onClick: () => renameFolder(folder) },
            text: "✎",
          }),
          el("button", {
            attrs: { type: "button", class: "icon-btn", title: "Supprimer", onClick: () => deleteFolder(folder) },
            text: "✕",
          }),
        ],
      })
    );
  }
}

function renderRecordingsList() {
  const container = document.getElementById("recordings-list");
  if (!container) return;
  container.textContent = "";

  const list = filteredRecordings();
  if (list.length === 0) {
    container.appendChild(el("p", { attrs: { class: "empty-state" }, text: "Aucun fredonnement ici pour l'instant." }));
    return;
  }

  for (const recording of list) {
    container.appendChild(renderRecordingCard(recording));
  }
}

function renderRecordingCard(recording) {
  const children = [];

  children.push(
    el("p", { attrs: { class: "recording-date" }, text: new Date(recording.created_at + "Z").toLocaleString("fr-FR") })
  );

  children.push(
    el("audio", { attrs: { controls: "true", preload: "none", src: `/recordings/${recording.id}/audio` } })
  );

  if (recording.analysis_status === "done") {
    const title = recording.guessed_title || "Inconnu";
    const artist = recording.guessed_artist || "Inconnu";
    children.push(el("p", { attrs: { class: "guess-result" }, text: `${title} — ${artist}` }));

    if (recording.transcript) {
      children.push(el("p", { attrs: { class: "transcript-text" }, text: `« ${recording.transcript} »` }));
    }

    const links = el("div", { attrs: { class: "link-row" } });
    if (recording.deezer_link) {
      links.appendChild(
        el("a", {
          attrs: { href: recording.deezer_link, target: "_blank", rel: "noopener", class: "link-btn deezer" },
          text: "Écouter sur Deezer",
        })
      );
    }
    if (recording.youtube_link) {
      links.appendChild(
        el("a", {
          attrs: { href: recording.youtube_link, target: "_blank", rel: "noopener", class: "link-btn youtube" },
          text: "Chercher sur YouTube",
        })
      );
    }
    children.push(links);
  } else if (recording.analysis_status === "pending") {
    children.push(el("p", { attrs: { class: "status-text" }, text: "Analyse en cours..." }));
  } else if (recording.analysis_status === "error") {
    children.push(
      el("p", { attrs: { class: "status-text error" }, text: recording.analysis_error || "Erreur d'analyse." })
    );
  }

  const analyzeBtn = el("button", {
    attrs: { type: "button", class: "analyze-btn" },
    text: recording.analysis_status === "done" ? "Réanalyser" : "Deviner la chanson",
  });
  analyzeBtn.addEventListener("click", () =>
    analyzeRecording(recording.id, analyzeBtn, () => loadData())
  );
  children.push(analyzeBtn);

  const folderSelect = el("select", {
    attrs: {
      class: "folder-select",
      onChange: (e) => moveToFolder(recording.id, e.target.value === "" ? null : Number(e.target.value)),
    },
    children: [
      el("option", { attrs: { value: "" }, text: "Sans dossier" }),
      ...folders.map((f) => el("option", { attrs: { value: String(f.id) }, text: f.name })),
    ],
  });
  folderSelect.value = recording.folder_id ? String(recording.folder_id) : "";
  children.push(folderSelect);

  children.push(
    el("button", {
      attrs: { type: "button", class: "danger-btn", onClick: () => deleteRecording(recording.id) },
      text: "Supprimer",
    })
  );

  return el("article", { attrs: { class: "recording-card" }, children });
}

async function moveToFolder(recordingId, folderId) {
  try {
    await apiFetch(`/recordings/${recordingId}/folder`, { method: "PUT", body: { folder_id: folderId } });
    await loadData();
  } catch (err) {
    window.alert(err.message);
  }
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

async function deleteFolder(folder) {
  if (!window.confirm(`Supprimer le dossier "${folder.name}" ? Les fredonnements qu'il contient deviendront sans dossier.`)) return;
  try {
    await apiFetch(`/folders/${folder.id}`, { method: "DELETE" });
    if (currentFolderId === folder.id) currentFolderId = "all";
    await loadData();
  } catch (err) {
    window.alert(err.message);
  }
}

async function renameFolder(folder) {
  const name = window.prompt("Nouveau nom du dossier :", folder.name);
  if (!name || !name.trim()) return;
  try {
    await apiFetch(`/folders/${folder.id}`, { method: "PUT", body: { name: name.trim() } });
    await loadData();
  } catch (err) {
    window.alert(err.message);
  }
}

export function initLibraryPage() {
  const newFolderForm = document.getElementById("new-folder-form");
  if (!newFolderForm) return;

  newFolderForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = document.getElementById("new-folder-name");
    const name = input.value.trim();
    if (!name) return;
    try {
      await apiFetch("/folders", { method: "POST", body: { name } });
      input.value = "";
      await loadData();
    } catch (err) {
      window.alert(err.message);
    }
  });

  loadData();
}
