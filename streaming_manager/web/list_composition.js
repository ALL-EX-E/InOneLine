/* R06 List + Twitch-chat composition shared by both OBS sources.
   The accepted standalone List motion is reused by both Split and Replace
   command transitions; only the occupied List geometry differs. */
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
    /* Static end state for Replace. During motion Twitch clipping follows
       the shared List WAAPI clock; neither List nor Twitch content fades. */
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

  // Shared monotonic scroll clock for both existing List renderers.
  // The logical phase continues while an OBS source is hidden/parked or
  // Chromium throttles its animation frames. Only visible rows need rAF.
  function createScrollClock(speedPxPerSecond = 19, initialPauseMs = 0) {
    const startAt = performance.now() + Math.max(0, Number(initialPauseMs) || 0);
    let cycleHeight = 0;
    let anchorAt = startAt;
    let anchorOffset = 0;
    const wrap = (value, cycle) => ((value % cycle) + cycle) % cycle;
    function position(at = performance.now()) {
      if (cycleHeight <= 1) return 0;
      return wrap(anchorOffset +
        (Math.max(0, at - anchorAt) / 1000) * speedPxPerSecond, cycleHeight);
    }
    function setCycleHeight(nextHeight) {
      const now = performance.now();
      const next = Number.isFinite(nextHeight) ? Math.max(0, nextHeight) : 0;
      if (next <= 1) {
        cycleHeight = 0;
        anchorOffset = 0;
        anchorAt = now;
        return 0;
      }
      const previousOffset = position(now);
      if (cycleHeight > 1) {
        // Preserve the relative phase if text/font/rows change live.
        anchorOffset = (previousOffset / cycleHeight) * next;
        anchorAt = now;
      } else {
        // First visible measurement still includes ALL offscreen time since
        // source load, instead of silently restarting at the first row.
        anchorOffset = 0;
        anchorAt = startAt;
      }
      cycleHeight = next;
      return position(now);
    }
    return Object.freeze({position, setCycleHeight});
  }

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
    // A newly populated hide-empty chat must animate from 0 even if the
    // main OBS composition was previously parked while both were hidden.
    let lastChatHeight = 0;
    let intrinsicChatHeight = 0;
    let lastEmbeddedChatNeeded = false;
    let lastEmbeddedRefreshAt = -Infinity;
    let embeddedRefreshPending = false;
    let lastGeometry = "";
    let chatResizeSeconds = 1;
    // The standalone List has no Twitch layer. Reuse the same List motion
    // contract, while the independent combined and main sources retain
    // their previously accepted behavior until their own review.
    const standaloneMotion = !noMotion && !iframe && !root.closest("#overlay");
    // Both combined OBS placements instantiate the SAME List/chat component.
    // Its Split + Always Twitch transitions were manually accepted in the
    // standalone source and run in the embedded main slot. Replace reuses
    // the same motion with a full-size List target instead of the split slot.
    const combinedMotion = Boolean(iframe && noMotion);
    const mainEmbedded = Boolean(root.closest("#overlay"));
    let motionDurationMs = 650;
    let commandMotionDurationMs = 650;
    let showDurationMs = 30000;
    let showUntil = 0;
    let slidePhase = "idle"; // idle, enter, hold, exit
    let commandDirection = "top";
    let seenSnapshot = false;
    let motion = null;
    let motionTimeout = null;
    let motionAnimation = null;
    let chatMotionAnimation = null;
    // The existing List WAAPI remains the only motion clock. In hide-empty
    // composition the Twitch occlusion mask follows its ACTUAL painted edge
    // every frame, rather than interpolating an unrelated fixed-height inset.
    let dynamicCommandMotion = false;
    let dynamicMotionFull = false;
    let dynamicMotionDirection = "top";
    let dynamicMaskFrame = null;
    let motionChatTarget = -1;
    let motionListTarget = -1;
    let settlingChatMask = false;

    function stopDynamicMask() {
      if (dynamicMaskFrame !== null) cancelAnimationFrame(dynamicMaskFrame);
      dynamicMaskFrame = null;
      dynamicCommandMotion = false;
      settlingChatMask = false;
      chatLayer.style.clipPath = "";
      listLayer.style.transition = "";
      motionChatTarget = -1;
      motionListTarget = -1;
    }

    function currentDynamicTargets() {
      const available = Math.max(1, root.clientHeight);
      const chatNeeded = chatAvailable && chatHasMessages;
      const natural = chatNeeded ?
        Math.max(0, Math.min(available, measureChat())) : 0;
      const gap = !dynamicMotionFull && chatNeeded ? 12 : 0;
      const targetChat = dynamicMotionFull ? natural :
        Math.min(natural, Math.floor((available - gap) / 2));
      return {natural, targetChat, targetList: available - targetChat - gap};
    }

    function syncDynamicMotionGeometry() {
      if (!dynamicCommandMotion || !motion) return;
      const {natural, targetChat, targetList} = currentDynamicTargets();
      // A command entrance moves the List OVER the existing Twitch frame.
      // Do not shrink a populated hide-empty chat before the List reaches its
      // destination; this was the regression visible on all four directions.
      // New messages may still grow the bottom-anchored frame during motion.
      // The Split height cap is applied only after the entrance completes.
      const wantedChat = natural;
      if (wantedChat !== motionChatTarget) {
        if (motionChatTarget >= 0) {
          // A newly arrived message must resize both boundaries together.
          // Do not keep the original three-second command duration for the
          // chat while the List reacts in the shorter resize duration.
          chatLayer.style.transition = `height ${chatResizeSeconds}s ease`;
        }
        motionChatTarget = wantedChat;
        chatLayer.style.height = wantedChat + "px";
      }
      if (!dynamicMotionFull && targetList !== motionListTarget) {
        motionListTarget = targetList;
        listLayer.style.height = targetList + "px";
        if (onResize) onResize();
      }
      matchEmbeddedChatFrame(chatAvailable && chatHasMessages);
      // Chromium can defer a hidden embedded iframe's own 500-ms polling.
      // Reuse the already accepted parent's targeted HTTP->child-render
      // recovery while the List crosses real Twitch messages. The child
      // renderer compares snapshots and never remounts its iframe.
      recoverEmbeddedChat(chatAvailable && chatHasMessages);
    }

    function paintDynamicChatMask() {
      dynamicMaskFrame = null;
      if (!(dynamicCommandMotion && motion) && !settlingChatMask) return;
      const list = listLayer.getBoundingClientRect();
      const chat = chatLayer.getBoundingClientRect();
      // Intersection of the ACTUALLY painted List surface with the Twitch
      // frame. A Split/Bottom List is revealed by a WAAPI inset, not by
      // translation: its unrevealed upper part must NOT cover Twitch yet.
      let listTop = list.top;
      let listBottom = list.bottom;
      const listClip = getComputedStyle(listLayer).clipPath;
      const inset = /^inset\(\s*([\d.]+)px(?:\s+([\d.]+)px)?(?:\s+([\d.]+)px)?/.exec(listClip);
      if (inset) {
        listTop += Number(inset[1]) || 0;
        if (inset[3]) listBottom -= Number(inset[3]) || 0;
      }
      const l = Math.max(0, list.left - chat.left);
      const r = Math.min(chat.width, list.right - chat.left);
      const t = Math.max(0, listTop - chat.top);
      const b = Math.min(chat.height, listBottom - chat.top);
      const w = chat.width;
      const h = chat.height;
      let mask = "none";
      if (chatAvailable && chatHasMessages && r > l && b > t && w > 0 && h > 0) {
        // Even-odd subtraction clips the entire rectangle under the List,
        // including transparent pixels. Unlike direction-specific inset /
        // polygon masks it handles Split/Bottom's TWO exposed chat regions,
        // horizontal entrances and full-size Replace with one exact edge.
        // The outer rectangle keeps the unoccupied frame and iframe intact.
        mask = `path(evenodd, "M 0 0 H ${w} V ${h} H 0 Z ` +
          `M ${l} ${t} H ${r} V ${b} H ${l} Z")`;
      }
      if (chatLayer.style.clipPath !== mask) chatLayer.style.clipPath = mask;
      // Keep the painted List footprint occluded while the Twitch frame
      // settles into its final Split slot AFTER the command entrance. End the
      // mask when the two layers no longer overlap, without another timer.
      if (settlingChatMask && (r <= l || b <= t)) {
        const {targetChat} = currentDynamicTargets();
        if (Math.abs(h - targetChat) <= 1) {
          settlingChatMask = false;
          chatLayer.style.clipPath = "";
          // The List and chat now have their exact Split flex geometry;
          // release the temporary absolute handoff without moving an edge.
          layout();
          return;
        }
      }
      dynamicMaskFrame = requestAnimationFrame(paintDynamicChatMask);
    }

    function cancelListMotion(preserveDynamicHeight = false) {
      if (motionTimeout !== null) clearTimeout(motionTimeout);
      motionTimeout = null;
      // Keep the painted chat height at the end of an approved command. A
      // pending message-driven height transition must not snap on WAAPI end.
      const preserve = preserveDynamicHeight && dynamicCommandMotion && !chatAlways;
      const paintedChatHeight = preserve ? chatLayer.getBoundingClientRect().height : -1;
      if (motionAnimation) motionAnimation.cancel();
      if (chatMotionAnimation) chatMotionAnimation.cancel();
      motionAnimation = null;
      chatMotionAnimation = null;
      stopDynamicMask();
      if (combinedMotion) {
        // Restore the existing flex geometry on the same frame as the motion
        // finishes. Neither source gets an independently animated container.
        listLayer.style.position = "";
        listLayer.style.top = "";
        listLayer.style.left = "";
        listLayer.style.right = "";
        listLayer.style.height = "";
        listLayer.style.zIndex = "";
        listLayer.style.flex = "";
        chatLayer.style.position = "";
        chatLayer.style.bottom = "";
        chatLayer.style.left = "";
        chatLayer.style.right = "";
        chatLayer.style.zIndex = "";
        chatLayer.style.height = preserve ? paintedChatHeight + "px" : "";
        chatLayer.style.marginTop = "";
        chatLayer.style.transition = preserve ?
          `height ${chatResizeSeconds}s ease, margin-top ${chatResizeSeconds}s ease` : "";
        lastChatHeight = preserve ? paintedChatHeight : -1;
        root.dataset.r06CombinedSync = "idle";
      }
      motion = null;
      root.dataset.r06StandaloneMotionKind = "idle";
      root.classList.remove("r06-standalone-motion");
    }

    function beginHold() {
      // The visible-time countdown starts AFTER all entrance frames finish.
      slidePhase = "hold";
      const holdStart = performance.now();
      showUntil = showDurationMs > 0 ? holdStart + showDurationMs : 0;
      root.dataset.r06StandalonePhase = "hold";
      root.dataset.r06StandaloneHoldStartMs = String(holdStart);
      root.dataset.r06StandaloneHoldDurationMs = String(showDurationMs);
      if (expiryTimer !== null) clearTimeout(expiryTimer);
      expiryTimer = showDurationMs > 0 ? setTimeout(expire, showDurationMs) : null;
    }

    function finishListMotion() {
      if (!motion) return;
      const wasEntering = motion === "enter";
      const wasExiting = motion === "exit";
      const settleSplit = wasEntering && dynamicCommandMotion &&
        !dynamicMotionFull && chatAvailable && chatHasMessages;
      cancelListMotion(true);
      if ((standaloneMotion || combinedMotion) && mode === "slide") {
        if (wasEntering && slidePhase === "enter" && active) beginHold();
        else if (wasExiting && slidePhase === "exit") {
          slidePhase = "idle";
          root.dataset.r06StandalonePhase = "idle";
        }
      }
      lastGeometry = "";
      settlingChatMask = settleSplit;
      layout();
      if (settleSplit) paintDynamicChatMask();
    }

    function reverseZeroCommandMotion(next) {
      // Reuse the running WAAPI animations when a second 0-second Twitch
      // command arrives mid-transition: reverse from the ACTUAL current
      // frame instead of snapping to a target geometry first.
      if (!motionAnimation || (next ? motion !== "exit" : motion !== "enter")) {
        return false;
      }
      active = next;
      motion = next ? "enter" : "exit";
      slidePhase = motion;
      root.dataset.r06StandalonePhase = motion;
      root.dataset.r06StandaloneMotionKind = motion;
      if (combinedMotion) root.dataset.r06CombinedSync = motion;
      if (next) {
        root.dataset.r06StandaloneLastEntrance = commandDirection;
        root.dataset.r06StandaloneEntranceCount =
          String((Number(root.dataset.r06StandaloneEntranceCount) || 0) + 1);
      } else {
        root.dataset.r06StandaloneLastExit = commandDirection;
        root.dataset.r06StandaloneExitCount =
          String((Number(root.dataset.r06StandaloneExitCount) || 0) + 1);
      }
      motionAnimation.reverse();
      if (chatMotionAnimation) chatMotionAnimation.reverse();
      // Zero-second toggle uses the same running List animation; the dynamic
      // chat height retargets without snapping to a stale half/full geometry.
      if (dynamicCommandMotion) syncDynamicMotionGeometry();
      if (motionTimeout !== null) clearTimeout(motionTimeout);
      motionTimeout = setTimeout(() => {
        if (motionAnimation) finishListMotion();
      }, commandMotionDurationMs + 50);
      return true;
    }

    function beginStandaloneListMotion(
      entering, direction, durationMs = motionDurationMs,
      travelDistance = null, skipInitialLayout = false, revealFromY = null
    ) {
      // Shared List movement (same Web Animations timing and opacity contract).
      // Separate List travels across its whole source; in combined mode the
      // approved top entrance travels across the List's own target region.
      if (entering && !skipInitialLayout) layout();
      const width = Math.max(1, root.clientWidth);
      const height = travelDistance === null ?
        Math.max(1, root.clientHeight) : Math.max(1, travelDistance);
      const initial = direction === "left" ? `translateX(${-width}px)` :
        direction === "right" ? `translateX(${width}px)` :
        direction === "bottom" ? `translateY(${height}px)` :
        `translateY(${-height}px)`;
      const from = entering ? initial : "translate(0px,0px)";
      const to = entering ? "translate(0px,0px)" : initial;

      motion = entering ? "enter" : "exit";
      root.dataset.r06StandaloneMotionKind = motion;
      root.dataset.r06StandaloneLastMotionDurationMs = String(durationMs);
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
      // Translate the existing List layer, except for the accepted combined
      // "bottom" variant: reveal upward WITHIN the upper List slot, never by
      // translating the whole panel through the lower Twitch-chat region.
      // Neither method changes opacity, background, or the panel's contents.
      const frames = revealFromY !== null && direction === "bottom" ?
        (entering ?
          [{clipPath: `inset(${revealFromY}px 0 0 0)`}, {clipPath: "inset(0px 0 0 0)"}] :
          [{clipPath: "inset(0px 0 0 0)"}, {clipPath: `inset(${revealFromY}px 0 0 0)`}]) :
        [{transform: from}, {transform: to}];
      const animation = listLayer.animate(
        frames, {duration: durationMs, easing: "ease-in-out", fill: "both"},
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
      }, durationMs + 50);
    }

    function beginCombinedSplitAlwaysMotion(
      entering, direction = "top", commandOverChat = false, replaceFull = false
    ) {
      const interruptedChatHeight = settlingChatMask ?
        chatLayer.getBoundingClientRect().height : null;
      if (settlingChatMask) stopDynamicMask();
      // Reuse the List's accepted motion. Settings-driven Always entrance and
      // exit synchronize the chat edge; a command keeps chat full-height while
      // the List passes above it, restoring static split only after entrance.
      // Only child layers move; iframe and messages remain the same.
      // The chat bottom and the combined source never move.
      const available = Math.max(1, root.clientHeight);
      const chatNeeded = chatAvailable && (chatAlways || chatHasMessages);
      const naturalChat = !chatNeeded ? 0 : chatAlways ? available :
        Math.max(0, Math.min(available, measureChat()));
      const gap = replaceFull || !chatNeeded ? 0 : 12;
      const targetChat = replaceFull || !chatNeeded ? 0 : chatAlways ?
        Math.floor((available - gap) / 2) :
        Math.min(naturalChat, Math.floor((available - gap) / 2));
      // Hide-empty chat never reserves a fixed half; the List fills
      // everything above its current bottom-anchored messages.
      const targetList = available - targetChat - gap;
      // Command entrance and reverse exit share the originally captured
      // duration, even when settings change during the hold.
      const duration = commandOverChat ? commandMotionDurationMs : motionDurationMs;
      root.classList.add("r06-shown");
      root.classList.remove("r06-not-shown", "r06-replace");
      listLayer.style.flex = "none";
      listLayer.style.position = "absolute";
      listLayer.style.top = "0px";
      listLayer.style.left = "0px";
      listLayer.style.right = "0px";
      listLayer.style.height = targetList + "px";
      listLayer.style.zIndex = "2";
      chatLayer.style.position = "absolute";
      chatLayer.style.bottom = "0px";
      chatLayer.style.left = "0px";
      chatLayer.style.right = "0px";
      const dynamicCommand = commandOverChat && !chatAlways;
      chatLayer.style.height = (dynamicCommand ?
        (replaceFull ? naturalChat : entering ? naturalChat :
          interruptedChatHeight === null ? targetChat : interruptedChatHeight) :
        commandOverChat ? available : entering ? naturalChat : targetChat) + "px";
      chatLayer.style.marginTop = "0px";
      chatLayer.style.zIndex = "1";
      chatLayer.style.transition = "none";
      root.dataset.r06CombinedSync = commandOverChat ?
        (replaceFull ? (entering ? "replace-command-enter" : "replace-command-exit") :
          (entering ? "command-enter" : "command-exit")) :
        entering ? "split-enter" : "split-exit";
      if (dynamicCommand) {
        dynamicCommandMotion = true;
        dynamicMotionFull = replaceFull;
        dynamicMotionDirection = direction;
        // Do not resize the iframe to 100% just to crop it afterwards. Keep
        // the frame and messages together at their bottom-anchored height.
        void chatLayer.offsetHeight;
        chatLayer.style.transition = `height ${duration / 1000}s ease-in-out`;
        listLayer.style.transition = `height ${chatResizeSeconds}s ease`;
      } else if (commandOverChat) {
        // Preserve the full-size iframe during entrance, but reveal the
        // underlying overlay background wherever the List actually passes.
        // Without this moving CHAT clip, transparent List backgrounds show
        // Twitch messages beneath the List, followed by a sudden final cut.
        // The clipping edge follows the List's shared ease-in-out clock and
        // includes the accepted 12px separation between the final regions.
        const edge = targetList + gap;
        const topY = edge + "px";
        let fromClip;
        let toClip;
        if (replaceFull) {
          // Replacement masks the incoming List's moving directional edge
          // across the whole source, including hide-empty Twitch messages.
          // The List may have a transparent user-selected background.
          // The List crosses the entire shared source. Clip Twitch behind
          // the same moving List edge and preserve existing message nodes.
          fromClip = "inset(0px 0px 0px 0px)";
          toClip = direction === "left" ?
            `inset(0px 0px 0px ${Math.max(1, root.clientWidth)}px)` :
            direction === "right" ?
            `inset(0px ${Math.max(1, root.clientWidth)}px 0px 0px)` :
            direction === "bottom" ?
            `inset(0px 0px ${available}px 0px)` :
            `inset(${available}px 0px 0px 0px)`;
        } else if (direction === "left") {
          fromClip = `polygon(0% 0%,100% 0%,100% 100%,0% 100%,0% ${topY},0% ${topY})`;
          toClip = `polygon(100% 0%,100% 0%,100% 100%,0% 100%,0% ${topY},100% ${topY})`;
        } else if (direction === "right") {
          fromClip = `polygon(0% 0%,100% 0%,100% ${topY},100% ${topY},100% 100%,0% 100%)`;
          toClip = `polygon(0% 0%,0% 0%,0% ${topY},100% ${topY},100% 100%,0% 100%)`;
        } else if (direction === "bottom") {
          // Two still-visible chat pieces: above the rising List and below
          // its own slot. Both join without a jump when entrance finishes.
          const bottomClip = y =>
            `polygon(0% 0%,100% 0%,100% ${y}px,0% ${y}px,0% ${topY},100% ${topY},100% 100%,0% 100%)`;
          fromClip = bottomClip(edge);
          toClip = bottomClip(0);
        } else {
          fromClip = "inset(0px 0px 0px 0px)";
          toClip = `inset(${topY} 0px 0px 0px)`;
        }
        // Replay the existing chat mask backwards on command expiry, without
        // recreating messages or snapping at the split boundary.
        chatMotionAnimation = chatLayer.animate(
          entering ? [{clipPath: fromClip}, {clipPath: toClip}] :
            [{clipPath: toClip}, {clipPath: fromClip}],
          {duration, easing: "ease-in-out", fill: "both"},
        );
      } else {
        const startChat = entering ? naturalChat : targetChat;
        const endChat = entering ? targetChat : naturalChat;
        chatMotionAnimation = chatLayer.animate(
          [{height: startChat + "px"}, {height: endChat + "px"}],
          {duration, easing: "ease-in-out", fill: "both"},
        );
      }
      // Shared List engine owns the exact same timing for both layers. The
      // final static 50/50 flex geometry replaces the completely clipped
      // full-size chat without an unmasked intermediate frame.
      beginStandaloneListMotion(
        entering, direction, duration, targetList, true,
        commandOverChat && !replaceFull && direction === "bottom" ?
          targetList + gap : null,
      );
      if (dynamicCommand) {
        syncDynamicMotionGeometry();
        paintDynamicChatMask();
      }
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
        // First message expands the existing child; avoid resetting its DOM.
        // Recover only if no chat renderer was initialized.
        let ready = false;
        try {
          ready = typeof iframe.contentWindow?.IOLRenderEmbeddedChatState === "function";
        } catch (_) { /* child not initialized */ }
        if (!ready && chatAlways) {
          // Preserve the previously accepted Always-chat recovery when its
          // child was genuinely suspended before it became ready.
          const src = iframe.getAttribute("src");
          if (src) iframe.setAttribute("src", src);
        } else {
          // Hide-empty may have just been reattached from main OBS parking.
          // Reassigning the same src while that iframe is loading causes a
          // second navigation and loses the first live Twitch messages.
          // Let its own poll/parent render-state recovery revive it instead.
          lastEmbeddedRefreshAt = -Infinity;
        }
      }
      lastEmbeddedChatNeeded = chatNeeded;
      // During an approved hide-empty command entrance, additional Twitch
      // rows must resize the existing bottom-anchored chat immediately.
      // The embedded document's own timer can be throttled while covered
      // by the List. Reuse the existing parent's non-reload resync even if
      // some older message cards are already rendered.
      const movingChat = dynamicCommandMotion && motion === "enter" &&
        !chatAlways && chatHasMessages;
      const refreshIntervalMs = movingChat ? 350 : 1000;
      if (!chatNeeded || !chatHasMessages || embeddedRefreshPending ||
          performance.now() - lastEmbeddedRefreshAt < refreshIntervalMs) return;
      try {
        const childDocument = iframe.contentDocument;
        const messages = childDocument?.getElementById("messages");
        const render = iframe.contentWindow?.IOLRenderEmbeddedChatState;
        if (!messages || (!movingChat && messages.children.length) ||
            typeof render !== "function") return;
        lastEmbeddedRefreshAt = performance.now();
        embeddedRefreshPending = true;
        fetch("/api/multichat", {cache:"no-store"})
          .then(response => response.ok ? response.json() : null)
          .then(snapshot => {
            if (!snapshot || !chatAvailable || !chatHasMessages ||
                iframe.contentDocument !== childDocument) return;
            const rows = childDocument.getElementById("messages");
            if (rows && (movingChat || !rows.children.length)) {
              iframe.contentWindow?.IOLRenderEmbeddedChatState?.(snapshot);
            }
          })
          .catch(() => { /* next parent poll can retry */ })
          .finally(() => { embeddedRefreshPending = false; });
      } catch (_) {
        // A child navigation must not prevent the next normal recovery poll.
        embeddedRefreshPending = false;
      }
    }

    function layout() {
      if (motion !== null) return;
      // Settings Save may switch the joint layout or visibility during the
      // short post-entrance Split handoff. Never leave its old moving mask
      // attached to a newly selected static Replace / Always / hidden mode.
      if (settlingChatMask && (!active || mode !== "slide" ||
          composeMode !== "split" || chatAlways || !chatAvailable ||
          !chatHasMessages)) stopDynamicMask();
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

      // Settle into static layout; dynamic chat grows upward from the bottom
      // in both the main and the independent combined Browser Source.
      const wasReplacing = root.classList.contains("r06-replace");
      root.classList.toggle("r06-shown", active);
      root.classList.toggle("r06-not-shown", !active);
      root.classList.toggle("r06-replace", replacing);
      // Keep a dynamically sized Split List pinned to the upper edge while
      // Twitch shrinks only AFTER the command entrance. An ordinary flex
      // switch made the fully visible List collapse to 0px during that final
      // chat-height transition. Absolute children have the SAME end geometry
      // without moving the outer combined OBS source or fading either layer.
      const dynamicSplit = combinedMotion && split && !chatAlways &&
        settlingChatMask;
      const animateChat = combinedMotion && !chatAlways && lastChatHeight >= 0 &&
        !replacing && !wasReplacing;
      if (dynamicSplit) {
        listLayer.style.flex = "none";
        listLayer.style.position = "absolute";
        listLayer.style.top = "0px";
        listLayer.style.left = "0px";
        listLayer.style.right = "0px";
        listLayer.style.height = (available - desiredChat - gap) + "px";
        listLayer.style.transition = animateChat ?
          `height ${chatResizeSeconds}s ease` : "none";
        chatLayer.style.position = "absolute";
        chatLayer.style.bottom = "0px";
        chatLayer.style.left = "0px";
        chatLayer.style.right = "0px";
        chatLayer.style.marginTop = "0px";
      } else {
        listLayer.style.position = "";
        listLayer.style.top = "";
        listLayer.style.left = "";
        listLayer.style.right = "";
        listLayer.style.height = "";
        listLayer.style.transition = "";
        listLayer.style.flex = replacing ? "none" : active ? "1 1 auto" : "0 0 0px";
        chatLayer.style.position = "";
        chatLayer.style.bottom = "";
        chatLayer.style.left = "";
        chatLayer.style.right = "";
        chatLayer.style.marginTop = gap + "px";
      }
      // Preserve accepted Always layout, timer, and separate List behavior.
      chatLayer.style.transition = animateChat ?
        `height ${chatResizeSeconds}s ease, margin-top ${chatResizeSeconds}s ease` : "none";
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
      if (combinedMotion && seenSnapshot &&
          ((next && reason === "always") ||
           (!next && reason === "hide")) &&
          composeMode === "split" && root.clientHeight > 0) {
        beginCombinedSplitAlwaysMotion(next);
        return;
      }
      if (combinedMotion &&
          ((next && reason === "command") || (!next && reason === "expiry")) &&
          (composeMode === "replace" || composeMode === "split") &&
          seenSnapshot && root.clientHeight > 0) {
        beginCombinedSplitAlwaysMotion(next, direction, true,
          composeMode === "replace");
        return;
      }
      if (standaloneMotion && seenSnapshot && root.clientHeight > 0 &&
          (reason === "hide" || reason === "always" ||
           reason === "command" || reason === "expiry")) {
        beginStandaloneListMotion(
          next, (reason === "command" || reason === "expiry") ? direction : "top",
          reason === "expiry" ? commandMotionDurationMs : motionDurationMs,
        );
        return;
      }
      layout();
    }

    function expire() {
      if (standaloneMotion ||
          (combinedMotion && (composeMode === "replace" || composeMode === "split"))) {
        if (mode === "slide" && slidePhase === "hold" &&
            showUntil && performance.now() >= showUntil) {
          showUntil = 0;
          slidePhase = "exit";
          root.dataset.r06StandalonePhase = "exit";
          // Reverse the command's actual entrance speed too. A settings Save
          // while fully visible must not alter this already-running cycle.
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
      // Expose the saved options actually applied by this browser source.
      // Native Chromium QA must wait for the saved direction/mode before
      // sending a new authenticated Twitch command.
      root.dataset.r06AppliedListDirection = cfg.list_slide_direction || "top";
      root.dataset.r06AppliedComposeMode = composeMode;
      chatAvailable = Boolean(allowChat && chat.enabled);
      chatHasMessages = chat.has_messages === true;
      chatAlways = chat.visibility === "always";
      // Main OBS only: one visual outer frame for the accepted Split +
      // permanent-Twitch composition. The standalone combined source and
      // user-controlled List/chat contents retain their original styling.
      root.classList.toggle("r06-main-split-always-shell",
        mainEmbedded && composeMode === "split" && chatAvailable && chatAlways);
      const seconds = Number(cfg.list_animation_seconds);
      chatResizeSeconds = Number.isFinite(seconds) ?
        Math.max(0.25, Math.min(3, seconds)) : 1;
      if (!chatAvailable || !chatHasMessages) intrinsicChatHeight = 0;

      // Both sources read exactly the SAME List animation control.
      const requestedAnimation = Number(cfg.list_slide_animation_seconds);
      motionDurationMs = Math.round(
        Math.max(0.10, Math.min(10, Number.isFinite(requestedAnimation)
          ? requestedAnimation : 0.65)) * 1000
      );
      if (standaloneMotion ||
          (combinedMotion && (composeMode === "replace" || composeMode === "split"))) {
        // Share the local phase clock with the approved combined command
        // entrance: animation never consumes the fully-visible hold time.
        const requestedShow = Number(cfg.list_slide_duration);
        const nextShowDuration = Math.round(
          Math.max(0, Math.min(120, Number.isFinite(requestedShow)
            ? requestedShow : 30)) * 1000
        );
        const serverHeld = trigger.held === true;
        const sequence = Number(trigger.sequence || 0);
        const remaining = Math.max(0, Number(trigger.remaining_ms || 0));
        const sequenceChanged = lastSequence !== sequence;
        if (sequenceChanged) lastSequence = sequence;

        // A fast (e.g. one-second) command can have remaining_ms=0 by the
        // next 1-second browser poll. A changed sequence after initial load
        // is nevertheless a NEW authenticated Twitch event and must play.
        const newCommand = mode === "slide" && sequenceChanged &&
          (remaining > 0 || serverHeld || (seenSnapshot && sequence > 0));
        if (mode !== "slide") {
          slidePhase = "idle";
          showUntil = 0;
          root.dataset.r06StandalonePhase = "idle";
          if (expiryTimer !== null) clearTimeout(expiryTimer);
          expiryTimer = null;
          const visible = mode === "always";
          changeActive(visible, seenSnapshot ? (visible ? "always" : "hide") : "");
        } else if (newCommand) {
          // Duration 0 is a server-owned toggle, not a zero-length timer.
          // For positive durations keep the accepted repeated-command hold.
          if (expiryTimer !== null) clearTimeout(expiryTimer);
          expiryTimer = null;
          showDurationMs = serverHeld ? 0 : nextShowDuration;
          showUntil = 0;
          if (nextShowDuration === 0 && trigger.held === false) {
            slidePhase = "exit";
            root.dataset.r06StandalonePhase = "exit";
            if (!reverseZeroCommandMotion(false)) {
              changeActive(false, "expiry", commandDirection);
            }
            if (!motion) {
              slidePhase = "idle";
              root.dataset.r06StandalonePhase = "idle";
            }
          } else if (!active) {
            slidePhase = "enter";
            root.dataset.r06StandalonePhase = "enter";
            if (!reverseZeroCommandMotion(true)) {
              // A new entrance takes current settings; a reversed in-flight
              // exit MUST retain the original direction and duration.
              commandDirection = cfg.list_slide_direction || "top";
              commandMotionDurationMs = motionDurationMs;
              changeActive(true, seenSnapshot ? "command" : "", commandDirection);
              if (!motion) beginHold();
            }
          } else if (motion === "enter") {
            slidePhase = "enter";
            root.dataset.r06StandalonePhase = "enter";
            // Timed repeats continue their entrance; toggle repeats above
            // reverse it without snapping or touching the Twitch iframe.
          } else {
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

      // Other combined modes retain server-owned expiry semantics; approved
      // Split Always-chat and Replace reuse the same local animation/hold clock.
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
        (mode === "slide" && (trigger.held === true || deadline > performance.now()));
      if (mode !== previousMode) lastGeometry = "";
      changeActive(shouldShow,
        mode === "always" ? "always" : mode === "hidden" ? "hide" : "");
      layout();
      seenSnapshot = true;

      if (expiryTimer !== null) clearTimeout(expiryTimer);
      expiryTimer = null;
      if (mode === "slide" && deadline) {
        expiryTimer = setTimeout(expire, Math.max(0, deadline - performance.now()));
      }
    }

    // Chat message count/height may change between /api/data updates.
    setInterval(() => {
      expire();
      if (motion && dynamicCommandMotion) syncDynamicMotionGeometry();
      else layout();
    }, 200);
    addEventListener("resize", () => {lastGeometry = ""; layout();});
    root.classList.add("r06-not-shown");
    return {
      apply,
      hasChatSpace: () => chatAvailable && (chatAlways || chatHasMessages),
      listActive: () => active,
      hasListArea: () => active || motion !== null,
    };
  }
  window.IOLListComposition = Object.freeze({create, createScrollClock});
})();
