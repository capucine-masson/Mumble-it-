import { el, svgEl } from "./dom.js";

function iconCircle(fill, inner) {
  return svgEl("svg", {
    attrs: { viewBox: "0 0 24 24", width: "22", height: "22", "aria-hidden": "true" },
    children: [svgEl("circle", { attrs: { cx: "12", cy: "12", r: "12", fill } }), ...inner],
  });
}

function youtubeIcon() {
  return iconCircle("#FF0000", [
    svgEl("polygon", { attrs: { points: "10,7.5 17,12 10,16.5", fill: "#fff" } }),
  ]);
}

function spotifyIcon() {
  return iconCircle("#1DB954", [
    svgEl("path", {
      attrs: {
        d: "M6.5 9.8c3.2-1 7.3-.8 10 .9M7 13c2.6-.8 6-.6 8.3.8M7.5 16c2.1-.6 4.8-.5 6.7.7",
        stroke: "#fff",
        "stroke-width": "1.6",
        "stroke-linecap": "round",
        fill: "none",
      },
    }),
  ]);
}

function deezerIcon() {
  return iconCircle("#9E0059", [
    svgEl("rect", { attrs: { x: "6.5", y: "11", width: "2.2", height: "6", rx: "1", fill: "#fff" } }),
    svgEl("rect", { attrs: { x: "10.9", y: "7", width: "2.2", height: "10", rx: "1", fill: "#fff" } }),
    svgEl("rect", { attrs: { x: "15.3", y: "13", width: "2.2", height: "4", rx: "1", fill: "#fff" } }),
  ]);
}

const ICONS = {
  youtube: youtubeIcon,
  spotify: spotifyIcon,
  deezer: deezerIcon,
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
    children: [ICONS[kind]()],
  });
}
