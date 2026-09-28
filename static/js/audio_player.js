import { el } from "./dom.js";

function formatTime(seconds) {
  if (!isFinite(seconds) || seconds < 0) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0");
  return `${m}:${s}`;
}

export function buildAudioPlayer(src) {
  const audio = new Audio(src);
  audio.preload = "none";

  const playBtn = el("button", { attrs: { type: "button", class: "play-btn", "aria-label": "Écouter" } });
  const progress = el("input", {
    attrs: { type: "range", class: "audio-progress", min: "0", max: "100", value: "0", step: "0.1" },
  });
  const timeLabel = el("span", { attrs: { class: "audio-time" }, text: "0:00" });

  const setIcon = () => {
    playBtn.textContent = audio.paused ? "▶" : "❚❚";
  };
  setIcon();

  playBtn.addEventListener("click", () => {
    if (audio.paused) {
      audio.play().catch(() => {});
    } else {
      audio.pause();
    }
  });

  audio.addEventListener("play", setIcon);
  audio.addEventListener("pause", setIcon);
  audio.addEventListener("ended", () => {
    setIcon();
    progress.value = "0";
  });
  audio.addEventListener("timeupdate", () => {
    if (audio.duration) {
      progress.value = String((audio.currentTime / audio.duration) * 100);
      timeLabel.textContent = formatTime(audio.currentTime);
    }
  });
  audio.addEventListener("loadedmetadata", () => {
    timeLabel.textContent = formatTime(audio.duration);
  });

  progress.addEventListener("input", () => {
    if (audio.duration) {
      audio.currentTime = (Number(progress.value) / 100) * audio.duration;
    }
  });

  return el("div", { attrs: { class: "audio-player" }, children: [playBtn, progress, timeLabel] });
}
