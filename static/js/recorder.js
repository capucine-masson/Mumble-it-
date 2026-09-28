const MIME_CANDIDATES = ["audio/webm;codecs=opus", "audio/ogg;codecs=opus", ""];
const MAX_DURATION_MS = 20000;

function pickMimeType() {
  for (const type of MIME_CANDIDATES) {
    if (type === "" || (window.MediaRecorder && MediaRecorder.isTypeSupported(type))) {
      return type;
    }
  }
  return "";
}

export class Recorder {
  constructor({ onStart, onStop, onError, onTick } = {}) {
    this.onStart = onStart;
    this.onStop = onStop;
    this.onError = onError;
    this.onTick = onTick;
    this.mediaRecorder = null;
    this.chunks = [];
    this.stream = null;
    this.timerId = null;
    this.autoStopId = null;
    this.startedAt = null;
  }

  get isRecording() {
    return Boolean(this.mediaRecorder && this.mediaRecorder.state === "recording");
  }

  async start() {
    if (this.isRecording) return;
    if (!navigator.mediaDevices || !window.MediaRecorder) {
      this.onError && this.onError(new Error("L'enregistrement audio n'est pas supporté par ce navigateur."));
      return;
    }

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      this.onError && this.onError(new Error("Micro refusé ou indisponible."));
      return;
    }

    const mimeType = pickMimeType();
    this.mediaRecorder = mimeType ? new MediaRecorder(this.stream, { mimeType }) : new MediaRecorder(this.stream);
    this.chunks = [];

    this.mediaRecorder.addEventListener("dataavailable", (event) => {
      if (event.data && event.data.size > 0) this.chunks.push(event.data);
    });

    this.mediaRecorder.addEventListener("stop", () => {
      this._cleanupTimers();
      this.stream.getTracks().forEach((track) => track.stop());
      const blob = new Blob(this.chunks, { type: this.mediaRecorder.mimeType || "audio/webm" });
      this.onStop && this.onStop(blob);
    });

    this.mediaRecorder.start();
    this.startedAt = Date.now();
    this.onStart && this.onStart();

    this.timerId = setInterval(() => {
      const elapsed = Date.now() - this.startedAt;
      this.onTick && this.onTick(elapsed, MAX_DURATION_MS);
    }, 200);

    this.autoStopId = setTimeout(() => this.stop(), MAX_DURATION_MS);
  }

  stop() {
    if (!this.isRecording) return;
    this.mediaRecorder.stop();
  }

  _cleanupTimers() {
    if (this.timerId) clearInterval(this.timerId);
    if (this.autoStopId) clearTimeout(this.autoStopId);
    this.timerId = null;
    this.autoStopId = null;
  }
}
