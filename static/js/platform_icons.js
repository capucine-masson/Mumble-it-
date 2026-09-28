import { el } from "./dom.js";

const ICON_SRC = {
  youtube: "/static/img/youtube-logo.png",
  spotify: "/static/img/file-spotify-logo-png-4.png",
  deezer: "/static/img/Deezer_Logo.jpg",
};

const LABELS = {
  youtube: "Chercher sur YouTube",
  spotify: "Écouter sur Spotify",
  deezer: "Écouter sur Deezer",
};

export function platformLink(kind, href) {
  if (!href) return null;
  return el("a", {
    attrs: {
      href,
      target: "_blank",
      rel: "noopener",
      class: "platform-link",
      title: LABELS[kind],
      "aria-label": LABELS[kind],
    },
    children: [el("img", { attrs: { src: ICON_SRC[kind], alt: LABELS[kind] } })],
  });
}
