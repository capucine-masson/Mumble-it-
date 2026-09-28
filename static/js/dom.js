export function el(tag, { attrs = {}, text, children = [] } = {}) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === undefined || value === null) continue;
    if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else {
      node.setAttribute(key, value);
    }
  }
  if (text !== undefined) node.textContent = text;
  for (const child of children) {
    if (child) node.appendChild(child);
  }
  return node;
}
