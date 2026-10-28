/* R06 presentation state shared by main and independent list. No Twitch adapter. */
(() => {
  "use strict";
  const css = `
    .r06-compose {position:relative;display:flex;flex-direction:column;width:100%;height:100%;min-width:0;min-height:0;overflow:hidden}
    .r06-list-layer {flex:1 1 auto;min-height:0;min-width:0;overflow:hidden;position:relative}
    .r06-compose .r06-list-layer > #list-panel {width:100%;height:100%;min-height:0;
      transition:transform .45s ease,opacity .45s ease}
    .r06-chat-layer {height:0;flex:0 0 auto;min-height:0;overflow:hidden;position:relative;
      transition:height .45s ease}
    .r06-chat-layer iframe {position:absolute;inset:0;width:100%;height:100%;border:0;pointer-events:none}
    .r06-compose.r06-not-shown #list-panel {opacity:0;transform:var(--r06-hidden-transform,translateX(105%))}
    .r06-compose.r06-shown #list-panel {opacity:1;transform:translate3d(0,0,0)}
    .r06-compose.r06-replace .r06-chat-layer {position:absolute;inset:0;height:100%!important;width:100%}
    .r06-compose.r06-replace .r06-list-layer {position:absolute;inset:0;width:100%;height:100%;
      z-index:2;flex:none}
    .r06-compose.r06-replace #list-panel {background-color:rgba(10,13,16,.99)}
  `;
  const sheet = document.createElement("style");
  sheet.textContent = css;
  document.head.appendChild(sheet);

  function create(root, listLayer, listPanel, chatLayer, onResize) {
    const iframe = chatLayer.querySelector("iframe");
    let mode = "always";
    let direction = "right";
    let composeMode = "split";
    let active = false;
    let visualActive = false;
    let reserved = false;
    let chatAvailable = false;
    let chatAlways = false;
    let lastSequence = null;
    let deadline = 0;
    let transitionTimer = null;
    let expiryTimer = null;
    let lastChatHeight = -1;

    function clearTransition() {
      if (transitionTimer !== null) clearTimeout(transitionTimer);
      transitionTimer = null;
    }
    function hiddenTransform() {
      return {left:"translateX(-105%)",right:"translateX(105%)",
        top:"translateY(-105%)",bottom:"translateY(105%)"}[direction];
    }
    function measureChat() {
      if (!chatAvailable) return 0;
      if (chatAlways) return root.clientHeight;
      try {
        const doc = iframe.contentDocument;
        const messages = doc && doc.getElementById("messages");
        if (messages) return Math.max(0, messages.scrollHeight + 24);
      } catch (_) { /* local same-origin frame not yet available */ }
      return 0;
    }
    function layout() {
      const available = root.clientHeight;
      if (available <= 0) return;
      const replacing = composeMode === "replace" && mode === "slide";
      const listAllocated = mode === "always" || (mode === "slide" && reserved);
      const chatNeeded = chatAvailable && (chatAlways || measureChat() > 0);
      const natural = chatAlways ? available : measureChat();
      const splitCap = listAllocated ? Math.floor((available - 12) / 2) : available;
      const desiredChat = replacing
        ? (chatNeeded ? available : 0)
        : chatNeeded ? Math.min(natural, splitCap) : 0;
      if (Math.abs(desiredChat - lastChatHeight) > 1) {
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
      root.style.setProperty("--r06-hidden-transform", hiddenTransform());
      root.classList.toggle("r06-shown", visualActive);
      root.classList.toggle("r06-not-shown", !visualActive);
    }
    function changeActive(next) {
      if (active === next) return;
      active = next;
      clearTransition();
      const horizontalSplit = composeMode === "split" &&
        mode === "slide" && ["left","right"].includes(direction);
      if (next) {
        reserved = true;
        if (horizontalSplit) {
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
        visualActive = false;
        if (horizontalSplit) {
          transitionTimer = setTimeout(() => {
            transitionTimer = null;
            if (!active) {
              reserved = false;
              layout();
              if (onResize) onResize();
            }
          }, 450);
        } else {
          reserved = false;
        }
      }
      applyVisual();
      layout();
      if (onResize) setTimeout(onResize, 500);
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
      const changedGeometry = direction !== newDirection || composeMode !== newCompose;
      mode = newMode;
      direction = newDirection;
      composeMode = newCompose;
      chatAvailable = Boolean(allowChat && chat.enabled);
      chatAlways = chat.visibility === "always";
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
      if (changedGeometry) {
        clearTransition();
        reserved = active;
        applyVisual();
      }
      const shouldShow = mode === "always" || (mode === "slide" && deadline > performance.now());
      if (changedGeometry && active && shouldShow) {
        // A changed direction is applied without hiding a currently visible list.
        visualActive = true;
        applyVisual();
      }
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
      hasChatSpace: () => chatAvailable && (chatAlways || measureChat() > 0),
      listActive: () => active,
    };
  }
  window.IOLListComposition = Object.freeze({create});
})();
