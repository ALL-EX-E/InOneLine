/* R06 List + Twitch-chat composition shared by both OBS sources.
   Split-mode content-sized chat boundaries may resize smoothly; the old
   list entrance/exit animation engine remains removed. This module owns
   visibility and geometry only; unrelated widgets and the
   list's content scrolling retain their existing independent behavior. */
(() => {
  "use strict";

  const css = `
    .r06-compose {
      position:relative;display:flex;flex-direction:column;justify-content:flex-end;
      width:100%;height:100%;min-width:0;min-height:0;overflow:hidden
    }
    .r06-list-layer {
      flex:1 1 auto;min-height:0;min-width:0;overflow:hidden;position:relative
    }
    .r06-compose .r06-list-layer > #list-panel {
      width:100%;height:100%;min-height:0;box-sizing:border-box;
      opacity:1!important;transform:none;
      transition:none!important;animation:none!important
    }
    .r06-chat-layer {
      height:0;flex:0 0 auto;min-height:0;overflow:hidden;position:relative;
      box-sizing:border-box;border-radius:8px;
      animation:none!important
    }
    .r06-chat-layer iframe {
      position:absolute;inset:0;width:100%;height:100%;
      border:0;pointer-events:none
    }
    .r06-compose.r06-not-shown:not(.r06-split-motion):not(.r06-overlay-motion) .r06-list-layer {
      flex:0 0 0px!important;height:0;overflow:hidden
    }
    /* Static replacement: the List covers the chat only while shown.
       No wipe, opacity interpolation, moving mask, or retained exit layer. */
    .r06-compose.r06-replace .r06-chat-layer {
      position:absolute;inset:0;height:100%!important;width:100%;z-index:1;
      clip-path:inset(0 100% 0 0);transition:none!important
    }
    .r06-compose.r06-replace .r06-list-layer {
      position:absolute;inset:0;width:100%;height:100%;z-index:2;flex:none
    }
    /* Motion is confined to the two children, never to the composition. */
    .r06-compose.r06-split-motion .r06-list-layer {
      flex:0 0 auto!important
    }
    .r06-compose.r06-split-motion.r06-split-no-chat {
      justify-content:flex-start
    }
    .r06-compose.r06-overlay-motion .r06-list-layer {
      position:absolute!important;top:0;left:0;
      width:100%!important;height:var(--r06-overlay-list-height)!important;
      flex:none!important;z-index:2;overflow:visible
    }
    .r06-compose.r06-overlay-motion .r06-chat-layer {
      position:absolute!important;inset:0;
      width:100%;height:100%!important;margin-top:0!important;
      flex:none!important;z-index:1;clip-path:none!important
    }
    /* "From bottom" starts at the bottom of the List's own upper region. */
    .r06-compose.r06-overlay-motion.r06-own-bottom .r06-list-layer {
      overflow:hidden!important
    }
  `;
  const sheet = document.createElement("style");
  sheet.textContent = css;
  document.head.appendChild(sheet);

  function create(root, listLayer, listPanel, chatLayer, onResize, previewEnabled = false, noMotion = false) {
    const iframe = chatLayer.querySelector("iframe");
    let mode = "always";
    let composeMode = "split";
    let active = false;
    let chatAvailable = false;
    let chatHasMessages = false;
    let chatAlways = false;
    let lastSequence = null;
    let deadline = 0;
    let expiryTimer = null;
    let lastChatHeight = -1;
    let intrinsicChatHeight = 0;
    let lastEmbeddedChatNeeded = false;
    let lastEmbeddedRefreshAt = -Infinity;
    let lastGeometry = "";
    let chatResizeSeconds = 1;
    // Only the composition embedded in the MAIN overlay gets the new
    // preview motion. Both independent OBS URLs retain their accepted modes.
    const mainMotion = noMotion && Boolean(root.closest("#overlay"));
    const motionDurationMs = 650; // Provisional QA duration, not a new setting.
    let seenSnapshot = false;
    let motion = null;
    let motionId = 0;
    let motionTimeout = null;
    let pendingFrame = null;
    let motionAnimations = [];


    function measureChat() {
      if (!chatAvailable || !chatHasMessages) return 0;
      if (chatAlways) return root.clientHeight;
      try {
        const doc = iframe.contentDocument;
        const messages = doc && doc.getElementById("messages");
        if (messages && messages.children.length) {
          let cardsHeight = 0;
          for (const card of messages.children) {
            const style = doc.defaultView.getComputedStyle(card);
            cardsHeight += card.getBoundingClientRect().height +
              (parseFloat(style.marginTop) || 0) +
              (parseFloat(style.marginBottom) || 0);
          }
          if (cardsHeight > 0) {
            intrinsicChatHeight = Math.ceil(cardsHeight + 24);
            return intrinsicChatHeight;
          }
        }
      } catch (_) { /* iframe may be reloading */ }
      // Avoid flicker if the parent state arrives before the iframe cards.
      return Math.max(44, intrinsicChatHeight);
    }

    function matchEmbeddedChatFrame(visible) {
      const panelStyle = getComputedStyle(listPanel);
      const frame = visible ? panelStyle.border : "none";
      const shadow = visible ? panelStyle.boxShadow : "none";
      if (chatLayer.style.border !== frame) chatLayer.style.border = frame;
      if (chatLayer.style.boxShadow !== shadow) chatLayer.style.boxShadow = shadow;
      if (chatLayer.style.borderRadius !== panelStyle.borderRadius) {
        chatLayer.style.borderRadius = panelStyle.borderRadius;
      }
    }

    function recoverEmbeddedChat(chatNeeded) {
      if (chatNeeded && !lastEmbeddedChatNeeded && chatHasMessages) {
        // If the child was suspended while its space was zero, re-open it
        // once, as in the previously tested non-animation chat recovery.
        const src = iframe.getAttribute("src");
        if (src) iframe.setAttribute("src", src);
      }
      lastEmbeddedChatNeeded = chatNeeded;
      if (!chatNeeded || !chatHasMessages ||
          performance.now() - lastEmbeddedRefreshAt < 1000) return;
      try {
        const messages = iframe.contentDocument?.getElementById("messages");
        const render = iframe.contentWindow?.IOLRenderEmbeddedChatState;
        if (!messages || messages.children.length || typeof render !== "function") return;
        lastEmbeddedRefreshAt = performance.now();
        fetch("/api/multichat", {cache:"no-store"})
          .then(response => response.ok ? response.json() : null)
          .then(snapshot => {
            const rows = iframe.contentDocument?.getElementById("messages");
            if (snapshot && chatAvailable && chatHasMessages &&
                rows && !rows.children.length) {
              iframe.contentWindow?.IOLRenderEmbeddedChatState?.(snapshot);
            }
          })
          .catch(() => { /* next parent poll can retry */ });
      } catch (_) { /* child can be navigating */ }
    }

    function motionGeometry(visible) {
      const available = root.clientHeight;
      const chatNeeded = chatAvailable && (chatAlways || chatHasMessages);
      const replacing = visible && mode === "slide" && composeMode === "replace";
      const natural = chatAlways ? available : measureChat();
      const gap = visible && !replacing && chatNeeded ? 12 : 0;
      const cap = visible ? Math.max(0, Math.floor((available - gap) / 2)) : available;
      const chat = !chatNeeded ? 0 :
        replacing ? available : Math.max(0, Math.min(natural, cap));
      return {
        available, chatNeeded, chat, gap,
        list: visible ? (replacing ? available : Math.max(0, available - chat - gap)) : 0,
      };
    }

    function cancelMotion() {
      motionId += 1;
      if (pendingFrame !== null) cancelAnimationFrame(pendingFrame);
      pendingFrame = null;
      root.style.visibility = "";
      if (motionTimeout !== null) clearTimeout(motionTimeout);
      motionTimeout = null;
      for (const animation of motionAnimations) animation.cancel();
      motionAnimations = [];
      motion = null;
      root.classList.remove("r06-split-motion", "r06-split-no-chat", "r06-overlay-motion", "r06-own-bottom");
      root.style.removeProperty("--r06-overlay-list-height");
      listLayer.style.flex = "";
      listLayer.style.height = "";
      listLayer.style.overflow = "";
      listPanel.style.height = "";
      listPanel.style.flex = "";
      chatLayer.style.transition = "none";
    }

    function finishMotion(id) {
      if (motionId !== id) return;
      cancelMotion();
      lastGeometry = "";
      layout();
    }

    function runMotion(animations) {
      motionAnimations = animations;
      const id = ++motionId;
      motionTimeout = setTimeout(() => finishMotion(id), motionDurationMs + 50);
    }

    function beginSplitMotion(visible) {
      const beforeList = listLayer.getBoundingClientRect().height;
      const beforeChat = chatLayer.getBoundingClientRect().height;
      const beforeGap = parseFloat(chatLayer.style.marginTop) || 0;
      const target = motionGeometry(visible);
      const maxList = Math.max(1, beforeList, target.list);
      const timing = {duration: motionDurationMs, easing: "ease-in-out", fill: "both"};

      motion = "split";
      root.classList.add("r06-split-motion");
      root.classList.toggle("r06-split-no-chat",
        beforeChat <= 1 && target.chat <= 1);
      root.classList.toggle("r06-shown", visible);
      root.classList.toggle("r06-not-shown", !visible);
      root.classList.remove("r06-replace");
      listLayer.style.flex = "0 0 auto";
      listLayer.style.height = target.list + "px";
      listLayer.style.overflow = "hidden";
      listPanel.style.height = maxList + "px";
      listPanel.style.flex = "none";
      chatLayer.style.transition = "none";
      chatLayer.style.height = target.chat + "px";
      chatLayer.style.marginTop = target.gap + "px";

      // Equal timelines keep the shared boundary together. The panel slides
      // while its viewport closes/opens; opacity remains unchanged.
      runMotion([
        listLayer.animate([
          {height: beforeList + "px"}, {height: target.list + "px"},
        ], timing),
        chatLayer.animate([
          {height: beforeChat + "px", marginTop: beforeGap + "px"},
          {height: target.chat + "px", marginTop: target.gap + "px"},
        ], timing),
        listPanel.animate([
          {transform: visible ? "translateY(" + (-maxList) + "px)" : "translateY(0px)"},
          {transform: visible ? "translateY(0px)" : "translateY(" + (-maxList) + "px)"},
        ], timing),
      ]);
    }

    function beginOverlayMotion(entering, direction = "top") {
      const target = motionGeometry(true);
      const listHeight = entering ? target.list : listLayer.getBoundingClientRect().height;
      const width = root.clientWidth;
      const height = Math.max(1, listHeight);
      const timing = {duration: motionDurationMs, easing: "ease-in-out", fill: "both"};

      motion = "overlay";
      if (entering) {
        // Persistent native-Chromium diagnostic: short entrances must be
        // observable even if a Qt JS callback arrives after the 650 ms motion.
        root.dataset.r06LastEntrance = direction;
        root.dataset.r06EntranceCount =
          String((Number(root.dataset.r06EntranceCount) || 0) + 1);
      }
      root.style.setProperty("--r06-overlay-list-height", height + "px");
      root.classList.add("r06-overlay-motion");
      root.classList.toggle("r06-shown", entering);
      root.classList.toggle("r06-not-shown", !entering);
      root.classList.remove("r06-replace");
      chatLayer.style.transition = "none";

      if (entering && direction === "bottom") {
        root.classList.add("r06-own-bottom");
        // The List is clipped at the bottom of its OWN destination region,
        // so it does not start off-screen below the Twitch chat.
        runMotion([
          listPanel.animate([
            {transform: "translateY(" + height + "px)"},
            {transform: "translateY(0px)"},
          ], timing),
        ]);
        return;
      }

      const initial = entering ? (
        direction === "left" ? "translateX(" + (-width) + "px)" :
        direction === "right" ? "translateX(" + width + "px)" :
        "translateY(" + (-height) + "px)"
      ) : "translateY(0px)";
      const final = entering ? "translate(0px,0px)" : "translateY(" + (-height) + "px)";
      runMotion([
        listLayer.animate([{transform: initial}, {transform: final}], timing),
      ]);
    }

    function layout() {
      if (motion !== null) return;
      const available = root.clientHeight;
      if (available <= 0) return;
      const chatNeeded = chatAvailable && (chatAlways || chatHasMessages);
      const replacing = active && mode === "slide" && composeMode === "replace";
      recoverEmbeddedChat(chatNeeded);
      matchEmbeddedChatFrame(chatNeeded);
      const natural = chatAlways ? available : measureChat();
      const split = active && !replacing && chatNeeded;
      const gap = split ? 12 : 0;
      const chatCap = active ? Math.max(0, Math.floor((available - gap) / 2)) : available;
      const desiredChat = !chatNeeded ? 0 :
        replacing ? available : Math.max(0, Math.min(natural, chatCap));

      // List visibility and replacement remain immediate. Only a content-
      // sized chat in Split mode may animate its allocated height.
      root.classList.toggle("r06-shown", active);
      root.classList.toggle("r06-not-shown", !active);
      root.classList.toggle("r06-replace", replacing);
      listLayer.style.flex = replacing ? "none" : active ? "1 1 auto" : "0 0 0px";
      // Only a content-sized chat in Split mode animates its boundary. An
      // Always chat starts at its full allocated height and never rises from
      // the bottom when a message arrives.
      const animateChat = !noMotion && split && !chatAlways && lastChatHeight >= 0;
      chatLayer.style.transition = animateChat ?
        `height ${chatResizeSeconds}s ease, margin-top ${chatResizeSeconds}s ease` : "none";
      chatLayer.style.marginTop = gap + "px";
      if (desiredChat !== lastChatHeight) {
        chatLayer.style.height = desiredChat + "px";
        lastChatHeight = desiredChat;
      }

      const key = [active, replacing, desiredChat, available].join(":");
      if (key !== lastGeometry) {
        lastGeometry = key;
        if (onResize) onResize();
      }
    }

    function changeActive(next, reason = "", previousReplacing = false, direction = "top") {
      if (active === next) return;
      if (motion !== null) {
        cancelMotion();
        layout();
      }
      active = next;
      lastGeometry = "";
      if (mainMotion && next && (reason === "always" || reason === "command") &&
          root.clientHeight <= 0) {
        // The main overlay parks the combined region when both children are
        // hidden. Defer the entrance until its parent layout re-attaches it.
        // Never show one instantaneous frame before the entrance animation.
        motion = "pending";
        root.style.visibility = "hidden";
        const ticket = ++motionId;
        pendingFrame = requestAnimationFrame(() => {
          pendingFrame = null;
          if (ticket !== motionId || motion !== "pending") return;
          root.style.visibility = "";
          motion = null;
          if (root.clientHeight <= 0) {
            layout();
            return;
          }
          // Reconstruct the genuinely hidden starting geometry in the
          // reattached slot, then animate toward the newly visible List.
          active = false;
          layout();
          active = true;
          if (reason === "always") beginSplitMotion(true);
          else beginOverlayMotion(true, direction);
        });
        return;
      }
      if (mainMotion && root.clientHeight > 0) {
        if (reason === "hide") {
          if (previousReplacing) beginOverlayMotion(false, "top");
          else beginSplitMotion(false);
          return;
        }
        if (reason === "always") {
          beginSplitMotion(true);
          return;
        }
        if (reason === "command") {
          beginOverlayMotion(true, direction);
          return;
        }
      }
      layout();
    }

    function expire() {
      if (mode === "slide" && deadline && performance.now() >= deadline) {
        deadline = 0;
        changeActive(false);
      }
    }

    function apply(data, allowChat) {
      const cfg = data.overlay || {};
      const vis = data.visibility && data.visibility.list || {};
      const chat = data.multichat || {};
      const trigger = data.list_show || {};
      const previousReplacing = active && mode === "slide" && composeMode === "replace";
      const nextMode = ["hidden","always","slide"].includes(vis.show_mode) ?
        vis.show_mode : "always";
      const previousMode = mode;
      mode = nextMode;
      // Standalone List is not allowed to activate a legacy replacement layer.
      composeMode = allowChat && cfg.list_chat_layout === "replace" ? "replace" : "split";
      chatAvailable = Boolean(allowChat && chat.enabled);
      chatHasMessages = chat.has_messages === true;
      chatAlways = chat.visibility === "always";
      const seconds = Number(cfg.list_animation_seconds);
      chatResizeSeconds = Number.isFinite(seconds) ?
        Math.max(0.25, Math.min(3, seconds)) : 1;
      if (!chatAvailable || !chatHasMessages) intrinsicChatHeight = 0;

      const sequence = Number(trigger.sequence || 0);
      const remaining = Math.max(0, Number(trigger.remaining_ms || 0));
      if (mode === "slide") {
        if (lastSequence !== sequence) {
          lastSequence = sequence;
          deadline = remaining > 0 ? performance.now() + remaining : 0;
        } else if (!deadline && remaining > 0) {
          deadline = performance.now() + remaining;
        } else if (remaining <= 0) {
          deadline = 0;
        }
      } else {
        deadline = 0;
      }
      const shouldShow = mode === "always" ||
        (mode === "slide" && deadline > performance.now());
      if (mode !== previousMode) lastGeometry = "";
      let reason = "";
      if (mainMotion && seenSnapshot && shouldShow !== active) {
        if (nextMode === "hidden" && active) reason = "hide";
        else if (nextMode === "always" && !active) reason = "always";
        else if (nextMode === "slide" && shouldShow && composeMode === "split")
          reason = "command";
      }
      changeActive(shouldShow, reason, previousReplacing,
        cfg.list_slide_direction || "top");
      layout();
      seenSnapshot = true;

      if (expiryTimer !== null) clearTimeout(expiryTimer);
      expiryTimer = null;
      if (mode === "slide" && deadline) {
        expiryTimer = setTimeout(expire, Math.max(0, deadline - performance.now()));
      }
    }

    // Chat message count/height may change between /api/data updates.
    setInterval(() => {expire(); layout();}, 200);
    addEventListener("resize", () => {lastGeometry = ""; layout();});
    root.classList.add("r06-not-shown");
    return {
      apply,
      hasChatSpace: () => chatAvailable && (chatAlways || chatHasMessages),
      listActive: () => active,
      hasListArea: () => active || motion !== null,
    };
  }
  window.IOLListComposition = Object.freeze({create});
})();
