/* Shared OBS visibility and operator-controlled auction widget motion. */
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

  const slideOffsets = {
    left: "translateX(-100%)",
    right: "translateX(100%)",
    top: "translateY(-100%)",
    bottom: "translateY(100%)",
  };

  function createAuctionMotion(layer) {
    let lastMotionConfig = "";
    return (policy, motion = {}) => {
      const sliding = !preview && policy?.show_mode === "slide" && motion.follow_auction_tab === true;
      const offset = sliding ? slideOffsets[motion.direction] : "";
      const config = offset ? String(motion.duration_seconds) + offset : "";
      // Only the operator's show/hide command animates. Initialization and
      // saved setting changes apply the group's current pose immediately.
      layer.style.transition = config && config === lastMotionConfig
        ? "transform " + motion.duration_seconds + "s ease-in-out"
        : "none";
      layer.style.transform = offset && motion.auction_widgets_visible !== true ? offset : "";
      lastMotionConfig = config;
    };
  }

  // Avoid flashing saved-hidden content before the first existing API poll.
  root.dataset.obsVisible = String(preview);
  root.dataset.obsPolicyReady = "false";
  window.ObsVisibility = Object.freeze({ preview, isVisible, apply, createAuctionMotion });
})();
