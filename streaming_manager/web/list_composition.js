/* R06 presentation state shared by main and independent list. No Twitch adapter. */
(() => {
  "use strict";
  const css = `
    .r06-compose {position:relative;display:flex;flex-direction:column;width:100%;height:100%;min-width:0;min-height:0;overflow:hidden}
    .r06-list-layer {flex:1 1 auto;min-height:0;min-width:0;overflow:hidden;position:relative}
    .r06-compose .r06-list-layer > #list-panel {width:100%;height:100%;min-height:0;
      transition:transform var(--r06-list-transition,1000ms) ease,opacity var(--r06-list-transition,1000ms) ease}
    .r06-chat-layer {height:0;flex:0 0 auto;min-height:0;overflow:hidden;position:relative;
      transition:height .45s ease}
    .r06-chat-layer iframe {position:absolute;inset:0;width:100%;height:100%;border:0;pointer-events:none}
    .r06-compose.r06-not-shown #list-panel {opacity:0;transform:var(--r06-hidden-transform,translateX(105%))}
    .r06-compose.r06-shown #list-panel {opacity:1;transform:translate3d(0,0,0)}
    .r06-compose.r06-replace .r06-chat-layer {position:absolute;inset:0;height:100%!important;width:100%}
    .r06-compose.r06-replace .r06-list-layer {position:absolute;inset:0;width:100%;height:100%;
      z-index:2;flex:none}
    .r06-compose.r06-replace .r06-chat-layer iframe {transition:opacity .45s ease}
    .r06-compose.r06-replace.r06-shown .r06-chat-layer iframe {opacity:0}
  `;
  const sheet = document.createElement("style");
  sheet.textContent = css;
  document.head.appendChild(sheet);

  function create(root, listLayer, listPanel, chatLayer, onResize, previewEnabled = false) {
    const iframe = chatLayer.querySelector("iframe");
    let mode = "always";
    let direction = "right";
    let composeMode = "split";
    let active = false;
    let visualActive = false;
    let reserved = false;
    let chatAvailable = false;
    let chatHasMessages = false;
    let chatAlways = false;
    let lastSequence = null;
    let deadline = 0;
    let transitionTimer = null;
    let expiryTimer = null;
    let lastChatHeight = -1;
    let outgoingOverlay = false;
    let transitionDirection = direction;
    let animationMs = 1000;
    let intrinsicChatHeight = 0;

    function clearTransition() {
      if (transitionTimer !== null) clearTimeout(transitionTimer);
      transitionTimer = null;
    }
    function hiddenTransform() {
      return {left:"translateX(-105%)",right:"translateX(105%)",
        top:"translateY(-105%)",bottom:"translateY(105%)"}[transitionDirection];
    }
    function measureChat() {
      if (!chatAvailable || !chatHasMessages) return 0;
      if (chatAlways) return root.clientHeight;
      try {
        const doc = iframe.contentDocument;
        const messages = doc && doc.getElementById("messages");
        if (messages && messages.children.length) {
          // The iframe height is the *result* of this calculation. Its
          // scrollHeight is clipped by #shell/#messages and feeds back into
          // itself, pinning the chat to one short row (or oscillating).
          // Measure the individual non-shrinking cards instead; this stays
          // intrinsic even if the surrounding iframe is currently 44px tall.
          let cardsHeight = 0;
          for (const card of messages.children) {
            const css = doc.defaultView.getComputedStyle(card);
            cardsHeight += card.getBoundingClientRect().height +
              (parseFloat(css.marginTop) || 0) + (parseFloat(css.marginBottom) || 0);
          }
          if (cardsHeight > 0) {
            intrinsicChatHeight = Math.ceil(cardsHeight + 24);
            return intrinsicChatHeight;
          }
        }
      } catch (_) { /* same-origin frame may not be ready yet */ }
      // An iframe may update one poll after /api/data. Preserve its last
      // intrinsic height so that a transient empty DOM never flashes closed.
      return Math.max(44, intrinsicChatHeight);
    }
    function layout() {
      const available = root.clientHeight;
      if (available <= 0) return;
      const replacing = composeMode === "replace" && mode === "slide";
      const listAllocated = mode === "always" || reserved;
      const chatNeeded = chatAvailable && (chatAlways || chatHasMessages);
      const natural = chatAlways ? available : measureChat();
      const splitCap = listAllocated ? Math.floor((available - 12) / 2) : available;
      const desiredChat = replacing
        ? (chatNeeded ? available : 0)
        : chatNeeded ? Math.min(natural, splitCap) : 0;
      if (Math.abs(desiredChat - lastChatHeight) > 2) {
        chatLayer.style.height = desiredChat + "px";
        lastChatHeight = desiredChat;
      }
      root.classList.toggle("r06-replace", replacing);
      if (!replacing) {
        listLayer.style.flex = listAllocated ? "1 1 auto" : "0 0 0px";
      } else {
        listLayer.style.flex = "none";
      }
      if (!chatNeeded && !listAllocated && !replacing) {
        chatLayer.style.height = "0px";
      }
    }
    function applyVisual() {
      root.style.setProperty("--r06-list-transition", animationMs + "ms");
      root.style.setProperty("--r06-hidden-transform", hiddenTransform());
      root.classList.toggle("r06-shown", visualActive);
      root.classList.toggle("r06-not-shown", !visualActive);
    }
    function resetOutgoingOverlay() {
      if (!outgoingOverlay) return;
      outgoingOverlay = false;
      for (const name of ["position","height","width","top","left","right","zIndex","pointerEvents"]) {
        listLayer.style[name] = "";
      }
    }
    function freezeOutgoingVerticalLayer() {
      // Keep the outgoing content physically on-screen until the list exit ends
      // while the flex column is freed for the expanding chat below it.
      const height = listLayer.getBoundingClientRect().height;
      if (height <= 0) return false;
      outgoingOverlay = true;
      Object.assign(listLayer.style, {
        position:"absolute",height:height+"px",width:"100%",
        top:"0",left:"0",right:"0",zIndex:"2",pointerEvents:"none",
      });
      return true;
    }
    function changeActive(next) {
      if (active === next) return;
      active = next;
      clearTransition();
      if (next) resetOutgoingOverlay();
      transitionDirection = direction;
      const horizontalSplit = composeMode === "split" &&
        mode === "slide" && ["left","right"].includes(direction);
      const available = Math.max(0, root.clientHeight);
      const half = Math.max(0, Math.floor((available - 12) / 2));
      const currentChat = Math.max(0, lastChatHeight);
      const needsResize = chatAvailable && (chatAlways || measureChat() > half) &&
        (next ? currentChat > half : currentChat >= half);
      const staged = horizontalSplit && needsResize;
      if (next) {
        reserved = true;
        if (staged) {
          visualActive = false;
          layout();
          transitionTimer = setTimeout(() => {
            transitionTimer = null;
            if (active) {
              visualActive = true;
              applyVisual();
              if (onResize) onResize();
            }
          }, 450);
        } else {
          visualActive = true;
        }
      } else {
        // Always retain the outgoing content for a full transition.
        // Otherwise flex-basis=0 instantly clips a still-animated panel.
        reserved = true;
        const vertical = ["top","bottom"].includes(direction);
        if (vertical && composeMode === "split" && freezeOutgoingVerticalLayer()) {
          // The outgoing layer floats above the chat, so both transitions
          // can run together while the chat reclaims the available height.
          reserved = false;
        }
        visualActive = false;
        transitionTimer = setTimeout(() => {
          transitionTimer = null;
          if (!active) {
            reserved = false;
            resetOutgoingOverlay();
            layout();
            if (onResize) onResize();
          }
        }, animationMs);
      }
      applyVisual();
      layout();
      if (onResize) setTimeout(onResize, 450 + animationMs + 60);
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
      const newMode = ["hidden","always","slide"].includes(vis.show_mode) ?
        vis.show_mode : "always";
      const newDirection = ["left","right","top","bottom"].includes(cfg.list_slide_direction) ?
        cfg.list_slide_direction : "right";
      const newCompose = cfg.list_chat_layout === "replace" ? "replace" : "split";
      const seconds = Number(cfg.list_animation_seconds);
      const nextAnimationMs = Math.round((Number.isFinite(seconds) && seconds > 0
        ? Math.max(0.25, Math.min(3, seconds)) : 1) * 1000);
      const changedGeometry = direction !== newDirection || composeMode !== newCompose;
      mode = newMode;
      direction = newDirection;
      composeMode = newCompose;
      animationMs = nextAnimationMs;
      chatAvailable = Boolean(allowChat && chat.enabled);
      chatHasMessages = chat.has_messages === true;
      chatAlways = chat.visibility === "always";
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
      // Keep an in-progress exit on its old trajectory. New geometry is
      // used for the *next* transition; changing a saved direction does
      // not interrupt or teleport the current one.
      // Preview must follow the same state/timer as the real OBS source.
      const shouldShow = mode === "always" || (mode === "slide" && deadline > performance.now());
      changeActive(shouldShow);
      layout();
      if (expiryTimer) clearTimeout(expiryTimer);
      if (mode === "slide" && deadline) {
        expiryTimer = setTimeout(expire, Math.max(0, deadline - performance.now()));
      }
    }
    setInterval(() => {expire();layout();}, 200);
    addEventListener("resize", () => {lastChatHeight = -1;layout();});
    root.classList.add("r06-not-shown");
    return {
      apply,
      hasChatSpace: () => chatAvailable && (chatAlways || chatHasMessages),
      listActive: () => active,
      hasListArea: () => active || reserved || outgoingOverlay,
    };
  }
  window.IOLListComposition = Object.freeze({create});
})();
