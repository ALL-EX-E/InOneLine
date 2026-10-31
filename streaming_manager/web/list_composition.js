/* R06 ZERO. Static list + Twitch-chat composition shared by both OBS sources.
   The old entrance/exit/resize animation engine was intentionally removed.
   This module owns visibility and geometry only; unrelated widgets and the
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
      opacity:1!important;transform:none!important;
      transition:none!important;animation:none!important
    }
    .r06-chat-layer {
      height:0;flex:0 0 auto;min-height:0;overflow:hidden;position:relative;
      box-sizing:border-box;border-radius:8px;
      transition:none!important;animation:none!important
    }
    .r06-chat-layer iframe {
      position:absolute;inset:0;width:100%;height:100%;
      border:0;pointer-events:none
    }
    .r06-compose.r06-not-shown .r06-list-layer {
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
  `;
  const sheet = document.createElement("style");
  sheet.textContent = css;
  document.head.appendChild(sheet);

  function create(root, listLayer, listPanel, chatLayer, onResize, previewEnabled = false) {
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

    function layout() {
      const available = root.clientHeight;
      if (available <= 0) return;
      const chatNeeded = chatAvailable && (chatAlways || chatHasMessages);
      const replacing = active && mode === "slide" && composeMode === "replace";
      recoverEmbeddedChat(chatNeeded);
      matchEmbeddedChatFrame(chatNeeded);
      const natural = chatAlways ? available : measureChat();
      const chatCap = active ? Math.max(0, Math.floor((available - 12) / 2)) : available;
      const desiredChat = !chatNeeded ? 0 :
        replacing ? available : Math.max(0, Math.min(natural, chatCap));

      // ZERO baseline: visibility, size, and replacement change atomically;
      // no old animation state can persist across mode changes.
      root.classList.toggle("r06-shown", active);
      root.classList.toggle("r06-not-shown", !active);
      root.classList.toggle("r06-replace", replacing);
      listLayer.style.flex = replacing ? "none" : active ? "1 1 auto" : "0 0 0px";
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

    function changeActive(next) {
      if (active === next) return;
      active = next;
      lastGeometry = "";
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
      const nextMode = ["hidden","always","slide"].includes(vis.show_mode) ?
        vis.show_mode : "always";
      const previousMode = mode;
      mode = nextMode;
      composeMode = cfg.list_chat_layout === "replace" ? "replace" : "split";
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
      const shouldShow = mode === "always" ||
        (mode === "slide" && deadline > performance.now());
      if (mode !== previousMode) lastGeometry = "";
      changeActive(shouldShow);
      layout();

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
      hasListArea: () => active,
    };
  }
  window.IOLListComposition = Object.freeze({create});
})();
