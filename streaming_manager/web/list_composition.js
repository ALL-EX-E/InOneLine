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
      opacity:1!important;transform:none!important;
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
    // The standalone List has no Twitch layer. Reuse the same List motion
    // contract, while the independent combined and main sources retain
    // their previously accepted behavior until their own review.
    const standaloneMotion = !noMotion && !iframe && !root.closest("#overlay");
    let motionDurationMs = 650;
    let showDurationMs = 30000;
    let showUntil = 0;
    let slidePhase = "idle"; // idle, enter, hold, exit
    let commandDirection = "top";
    let seenSnapshot = false;
    let motion = null;
    let motionTimeout = null;
    let motionAnimation = null;

    function cancelListMotion() {
      if (motionTimeout !== null) clearTimeout(motionTimeout);
      motionTimeout = null;
      if (motionAnimation) motionAnimation.cancel();
      motionAnimation = null;
      motion = null;
      root.dataset.r06StandaloneMotionKind = "idle";
      root.classList.remove("r06-standalone-motion");
    }

    function beginHold() {
      // The visible-time countdown starts AFTER all entrance frames finish.
      slidePhase = "hold";
      const holdStart = performance.now();
      showUntil = holdStart + showDurationMs;
      root.dataset.r06StandalonePhase = "hold";
      root.dataset.r06StandaloneHoldStartMs = String(holdStart);
      root.dataset.r06StandaloneHoldDurationMs = String(showDurationMs);
      if (expiryTimer !== null) clearTimeout(expiryTimer);
      expiryTimer = setTimeout(expire, showDurationMs);
    }

    function finishListMotion() {
      if (!motion) return;
      const wasEntering = motion === "enter";
      const wasExiting = motion === "exit";
      cancelListMotion();
      if (standaloneMotion && mode === "slide") {
        if (wasEntering && slidePhase === "enter" && active) beginHold();
        else if (wasExiting && slidePhase === "exit") {
          slidePhase = "idle";
          root.dataset.r06StandalonePhase = "idle";
        }
      }
      lastGeometry = "";
      layout();
    }

    function beginStandaloneListMotion(entering, direction) {
      // The standalone List's own region is its whole Browser Source.
      // With no chat, the bottom entrance starts at this region's bottom.
      if (entering) layout();
      const width = Math.max(1, root.clientWidth);
      const height = Math.max(1, root.clientHeight);
      const initial = direction === "left" ? `translateX(${-width}px)` :
        direction === "right" ? `translateX(${width}px)` :
        direction === "bottom" ? `translateY(${height}px)` :
        `translateY(${-height}px)`;
      const from = entering ? initial : "translate(0px,0px)";
      const to = entering ? "translate(0px,0px)" : initial;

      motion = entering ? "enter" : "exit";
      root.dataset.r06StandaloneMotionKind = motion;
      root.dataset.r06StandaloneLastMotionDurationMs = String(motionDurationMs);
      if (!entering) root.dataset.r06StandaloneLastExit = direction;
      root.classList.add("r06-standalone-motion");
      if (entering) {
        root.dataset.r06StandaloneLastEntrance = direction;
        root.dataset.r06StandaloneEntranceCount =
          String((Number(root.dataset.r06StandaloneEntranceCount) || 0) + 1);
      } else {
        root.dataset.r06StandaloneExitCount =
          String((Number(root.dataset.r06StandaloneExitCount) || 0) + 1);
      }
      // Translate only the List layer. Root clipping hides its motion outside
      // the OBS source; opacity, panel background and border stay unchanged.
      const animation = listLayer.animate(
        [{transform: from}, {transform: to}],
        {duration: motionDurationMs, easing: "ease-in-out", fill: "both"},
      );
      motionAnimation = animation;
      // In case WebEngine delays the finish callback while hidden, keep the
      // same bounded fallback. The duration is captured for this transition:
      // changing the UI will only affect the NEXT entrance/exit.
      animation.onfinish = () => {
        if (motionAnimation === animation) finishListMotion();
      };
      motionTimeout = setTimeout(() => {
        if (motionAnimation === animation) finishListMotion();
      }, motionDurationMs + 50);
    }

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

    function changeActive(next, reason = "", direction = "top") {
      if (active === next) return;
      if (motion !== null) {
        cancelListMotion();
        layout();
      }
      active = next;
      lastGeometry = "";
      if (standaloneMotion && seenSnapshot && root.clientHeight > 0 &&
          (reason === "hide" || reason === "always" ||
           reason === "command" || reason === "expiry")) {
        beginStandaloneListMotion(next, reason === "command" ? direction : "top");
        return;
      }
      layout();
    }

    function expire() {
      if (standaloneMotion) {
        if (mode === "slide" && slidePhase === "hold" &&
            showUntil && performance.now() >= showUntil) {
          showUntil = 0;
          slidePhase = "exit";
          root.dataset.r06StandalonePhase = "exit";
          changeActive(false, "expiry", commandDirection);
          if (!motion) {
            slidePhase = "idle";
            root.dataset.r06StandalonePhase = "idle";
          }
        }
        return;
      }
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
      // Standalone List is not allowed to activate a legacy replacement layer.
      composeMode = allowChat && cfg.list_chat_layout === "replace" ? "replace" : "split";
      chatAvailable = Boolean(allowChat && chat.enabled);
      chatHasMessages = chat.has_messages === true;
      chatAlways = chat.visibility === "always";
      const seconds = Number(cfg.list_animation_seconds);
      chatResizeSeconds = Number.isFinite(seconds) ?
        Math.max(0.25, Math.min(3, seconds)) : 1;
      if (!chatAvailable || !chatHasMessages) intrinsicChatHeight = 0;

      if (standaloneMotion) {
        // Independent List uses a local phase clock: entrance time never
        // consumes the saved fully-visible hold time.
        const requestedAnimation = Number(cfg.list_slide_animation_seconds);
        motionDurationMs = Math.round(
          Math.max(0.10, Math.min(10, Number.isFinite(requestedAnimation)
            ? requestedAnimation : 0.65)) * 1000
        );
        const requestedShow = Number(cfg.list_slide_duration);
        const nextShowDuration = Math.round(
          Math.max(1, Math.min(120, Number.isFinite(requestedShow)
            ? requestedShow : 30)) * 1000
        );
        const sequence = Number(trigger.sequence || 0);
        const remaining = Math.max(0, Number(trigger.remaining_ms || 0));
        const sequenceChanged = lastSequence !== sequence;
        if (sequenceChanged) lastSequence = sequence;

        // A fast (e.g. one-second) command can have remaining_ms=0 by the
        // next 1-second browser poll. A changed sequence after initial load
        // is nevertheless a NEW authenticated Twitch event and must play.
        const newCommand = mode === "slide" && sequenceChanged &&
          (remaining > 0 || (seenSnapshot && sequence > 0));
        if (mode !== "slide") {
          slidePhase = "idle";
          showUntil = 0;
          root.dataset.r06StandalonePhase = "idle";
          if (expiryTimer !== null) clearTimeout(expiryTimer);
          expiryTimer = null;
          const visible = mode === "always";
          changeActive(visible, seenSnapshot ? (visible ? "always" : "hide") : "");
        } else if (newCommand) {
          // Capture duration and direction for this entire command. A later
          // settings Save cannot redirect an exit half-way through the cycle.
          if (expiryTimer !== null) clearTimeout(expiryTimer);
          expiryTimer = null;
          showDurationMs = nextShowDuration;
          showUntil = 0;
          if (!active) {
            // The reverse exit must use the boundary the List ACTUALLY
            // entered from. Repeated commands while visible refresh only
            // the hold, even if the user changed the direction meanwhile.
            commandDirection = cfg.list_slide_direction || "top";
            slidePhase = "enter";
            root.dataset.r06StandalonePhase = "enter";
            changeActive(true, seenSnapshot ? "command" : "",
                         commandDirection);
            // Initial page load may intentionally show without motion.
            if (!motion) beginHold();
          } else if (motion === "enter") {
            slidePhase = "enter";
            root.dataset.r06StandalonePhase = "enter";
            // A second command during entrance continues the same entrance;
            // a fresh full hold begins once the animation finishes.
          } else {
            // Already fully visible. Restart the hold timer, not the entrance.
            beginHold();
          }
        } else if (mode !== previousMode) {
          // Switching into Slide without a new command leaves it hidden.
          slidePhase = "idle";
          root.dataset.r06StandalonePhase = "idle";
          showUntil = 0;
          if (expiryTimer !== null) clearTimeout(expiryTimer);
          expiryTimer = null;
          changeActive(false);
        }
        layout();
        seenSnapshot = true;
        return;
      }

      // Main and independent combined sources retain their old server-owned
      // expiry semantics until their separate interaction review.
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
