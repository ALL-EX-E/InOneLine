/* Presentation only: polling, layout, animation and audio remain widget-owned. */
(() => {
  "use strict";
  const root = document.documentElement;
  const preview = ["1", "true", "yes", "on"].includes(
    (new URLSearchParams(location.search).get("preview") || "").toLowerCase()
  );
  const style = document.createElement("style");
  style.textContent = 'html[data-obs-visible="false"] { opacity: 0 !important; pointer-events: none !important; }';
  document.head.appendChild(style);

  function isVisible(policy = {}) {
    if (preview) return true;
    if (policy.show_mode === "hidden") return false;
    return policy.show_mode !== "context" || policy.context_visible === true;
  }

  function apply(policy = {}) {
    const visible = String(isVisible(policy));
    if (root.dataset.obsVisible !== visible) root.dataset.obsVisible = visible;
    const mode = String(policy.show_mode || "always");
    if (root.dataset.obsShowMode !== mode) root.dataset.obsShowMode = mode;
    if (root.dataset.obsPolicyReady !== "true") root.dataset.obsPolicyReady = "true";
  }

  // Avoid flashing saved-hidden content before the first existing API poll.
  root.dataset.obsVisible = String(preview);
  root.dataset.obsPolicyReady = "false";
  window.ObsVisibility = Object.freeze({ preview, isVisible, apply });
})();
