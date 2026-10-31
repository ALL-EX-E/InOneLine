/* R06 presentation state shared by main and independent list. No Twitch adapter. */
(() => {
  "use strict";
  const css = `
    .r06-compose {position:relative;display:flex;flex-direction:column;justify-content:flex-end;width:100%;height:100%;min-width:0;min-height:0;overflow:hidden}
    .r06-list-layer {flex:1 1 auto;min-height:0;min-width:0;overflow:hidden;position:relative}
    .r06-compose .r06-list-layer > #list-panel {width:100%;height:100%;min-height:0;
      transition:transform var(--r06-list-transition,1000ms) ease,opacity var(--r06-list-transition,1000ms) ease}
    .r06-chat-layer {height:0;flex:0 0 auto;min-height:0;overflow:hidden;position:relative;
      box-sizing:border-box;border-radius:8px;
      transition:height var(--r06-list-transition,1000ms) ease}
    .r06-chat-layer iframe {position:absolute;inset:0;width:100%;height:100%;border:0;pointer-events:none}
    .r06-compose.r06-not-shown #list-panel {opacity:0;transform:var(--r06-hidden-transform,translateX(105%))}
    .r06-compose.r06-shown #list-panel {opacity:1;transform:translate3d(0,0,0)}
    /* Replacement is a real directional wipe, never an immediate fade of
       the chat. The chat stays alive behind the moving list; its clipped
       visible portion shrinks in sync with the moving panel. */
    .r06-compose.r06-replace .r06-chat-layer {
      position:absolute;inset:0;height:100%!important;width:100%;z-index:1;
      clip-path:inset(0 0 0 0);
      transition:clip-path var(--r06-list-transition,1000ms) ease
    }
    .r06-compose.r06-replace.r06-shown .r06-chat-layer {
      clip-path:var(--r06-chat-covered-clip,inset(0 100% 0 0))
    }
    .r06-compose.r06-replace .r06-list-layer {
      position:absolute;inset:0;width:100%;height:100%;z-index:2;flex:none
    }
    .r06-compose.r06-replace .r06-list-layer > #list-panel {
      opacity:1;
      transition:transform var(--r06-list-transition,1000ms) ease
    }
    /* During simultaneous Split exit in any direction, the outgoing panel
       stays visually opaque. Mask only the portion of the chat beneath it. */
    .r06-compose.r06-split-exit .r06-list-layer > #list-panel {
      opacity:1;
      transition:transform var(--r06-list-transition,1000ms) ease
    }
    /* T01: when chat fills the freed area, keep the outgoing List immediately
       above it in normal flex flow. The ONLY animated dimension is chat height.
       List movement is then identical to chat-top movement by construction. */
    .r06-compose.r06-flow-exit .r06-list-layer > #list-panel {
      opacity:1!important;transform:none!important;transition:none!important
    }
    /* T02: the inverse of the accepted T01 exit. In Split, a fixed-size
       List immediately precedes the shrinking chat in the SAME flex flow:
       the two moving edges are identical at every animation frame. */
    .r06-compose.r06-flow-enter .r06-list-layer > #list-panel {
      opacity:1!important;transform:none!important;transition:none!important
    }
    /* No shrinking chat: enter from the top at the final List size, without
       fading the List items or painting an opaque background. */
    .r06-compose.r06-top-enter .r06-list-layer > #list-panel {
      opacity:1!important;
      transition:none!important
    }
    /* A List which is already visible NEVER leaves the stage and re-enters.
       Only its reserved flex size changes, the chat stays bottom-anchored. */
    .r06-compose.r06-always-resize .r06-list-layer {
      transition:flex-basis var(--r06-list-transition,1000ms) ease
    }
    .r06-compose.r06-always-resize .r06-list-layer > #list-panel {
      opacity:1!important;transform:none!important;transition:none!important
    }
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
    let outgoingFlowExit = false;
    let outgoingFlowHeight = 0;
    let transitionDirection = direction;
    let animationMs = 1000;
    let intrinsicChatHeight = 0;
    let outgoingMaskFrame = null;
    let outgoingChatHeightHandler = null;
    let incomingAlways = null;
    let incomingAlwaysTimer = null;
    let incomingTopAnimation = null;
    let pendingAlwaysEntry = null;
    let lastEmbeddedChatNeeded = false;

    function clearTransition() {
      if (transitionTimer !== null) clearTimeout(transitionTimer);
      transitionTimer = null;
    }
    function hiddenTransform() {
      // In Split the list can be only half as tall as the composition.
      // Moving it down by 105% of its OWN height leaves it partly on-screen
      // and causes an abrupt disappearance when the outgoing layer is freed.
      const bottom = composeMode === "split"
        ? "translateY(" + (root.clientHeight + 12) + "px)"
        : "translateY(105%)";
      // An explicit "Не показывать" always exits upward. The frozen List
      // panel and the growing chat partition release precisely one List
      // height. Moving 105% made its bottom boundary outrun the chat top,
      // even though both animations used the same easing and duration.
      const top = mode === "hidden" ? "translateY(-100%)" : "translateY(-105%)";
      return {left:"translateX(-105%)",right:"translateX(105%)",
        top,bottom}[transitionDirection];
    }
    function coveredChatClip() {
      return {left:"inset(0 0 0 100%)",right:"inset(0 100% 0 0)",
        top:"inset(100% 0 0 0)",bottom:"inset(0 0 100% 0)"}[transitionDirection];
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
    function matchEmbeddedChatFrame(visible) {
      // The list and the embedded chat must use the same OUTER geometry and
      // frame styling. The embedded iframe only paints chat messages/media;
      // the standalone multichat source keeps its independent appearance.
      const panelStyle = getComputedStyle(listPanel);
      const frame = visible ? panelStyle.border : "none";
      const shadow = visible ? panelStyle.boxShadow : "none";
      if (chatLayer.style.border !== frame) chatLayer.style.border = frame;
      if (chatLayer.style.boxShadow !== shadow) chatLayer.style.boxShadow = shadow;
      if (chatLayer.style.borderRadius !== panelStyle.borderRadius) {
        chatLayer.style.borderRadius = panelStyle.borderRadius;
      }
    }
    function resetAlwaysEntry() {
      if (incomingAlwaysTimer !== null) clearTimeout(incomingAlwaysTimer);
      incomingAlwaysTimer = null;
      if (incomingTopAnimation !== null) incomingTopAnimation.cancel();
      incomingTopAnimation = null;
      listPanel.style.transform = "";
      incomingAlways = null;
      root.classList.remove("r06-flow-enter", "r06-top-enter",
                            "r06-always-resize");
      listLayer.style.flex = "";
      listLayer.style.height = "";
    }
    function layout() {
      const available = root.clientHeight;
      if (available <= 0) return;
      if (pendingAlwaysEntry && mode === "always") {
        // /overlay can briefly have ZERO height while its responsive
        // slot is recalculated. A mode change is observed only once by
        // apply(), so never discard the inverse entry in that frame.
        // Layout's existing 200ms poll completes it at the first valid
        // size, preserving the original visible/hidden starting state.
        const pending = pendingAlwaysEntry;
        pendingAlwaysEntry = null;
        beginAlwaysEntry(pending.wasVisible, pending.wasReplace);
      }
      const replacing = composeMode === "replace" && mode === "slide";
      const listAllocated = mode === "always" || reserved;
      const chatNeeded = chatAvailable && (chatAlways || chatHasMessages);
      // Qt/OBS Chromium may suspend a nested iframe's 500ms polling while
      // an empty Twitch chat has no allocated space. The /api/multichat
      // response remains correct, but the child can stay stale after the
      // first new message. Wake it ONCE on false->true visibility, rather
      // than refreshing continuously or touching the Twitch event state.
      if (chatNeeded && !lastEmbeddedChatNeeded && chatHasMessages) {
        const embeddedFrame = chatLayer.querySelector('iframe');
        if (embeddedFrame) {
          const url = embeddedFrame.getAttribute('src');
          if (url) embeddedFrame.setAttribute('src', url);
        }
      }
      lastEmbeddedChatNeeded = chatNeeded;
      matchEmbeddedChatFrame(chatNeeded);
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
      if (outgoingFlowExit) {
        listLayer.style.flex = "0 0 " + outgoingFlowHeight + "px";
      } else if (incomingAlways && incomingAlways.type === "flow") {
        listLayer.style.flex = "0 0 " + incomingAlways.targetHeight + "px";
      } else if (incomingAlways && incomingAlways.type === "resize") {
        listLayer.style.flex = "0 0 " + incomingAlways.targetHeight + "px";
      } else if (!replacing) {
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
      root.style.setProperty("--r06-chat-covered-clip", coveredChatClip());
      root.classList.toggle("r06-shown", visualActive);
      root.classList.toggle("r06-not-shown", !visualActive);
    }
    function updateOutgoingMask() {
      outgoingMaskFrame = null;
      if (!outgoingOverlay || outgoingFlowExit || composeMode !== "split") return;
      const p = listPanel.getBoundingClientRect();
      const c = chatLayer.getBoundingClientRect();
      const x0 = Math.max(c.left, p.left), x1 = Math.min(c.right, p.right);
      const y0 = Math.max(c.top, p.top), y1 = Math.min(c.bottom, p.bottom);
      chatLayer.style.maskImage = "";
      chatLayer.style.webkitMaskImage = "";
      chatLayer.style.clipPath = "";
      if (x1 > x0 && y1 > y0 && c.width > 0 && c.height > 0) {
        // The outgoing list occupies the top of the expanding, bottom-anchored
        // chat. Clip the exact overlap instead of fading the entire iframe.
        const scaleX = chatLayer.clientWidth / c.width;
        const scaleY = chatLayer.clientHeight / c.height;
        const left = Math.max(0, (x0 - c.left) * scaleX);
        const right = Math.min(chatLayer.clientWidth, (x1 - c.left) * scaleX);
        const top = Math.max(0, (y0 - c.top) * scaleY);
        const bottom = Math.min(chatLayer.clientHeight, (y1 - c.top) * scaleY);
        const w = chatLayer.clientWidth, h = chatLayer.clientHeight;
        if (transitionDirection === "left" || transitionDirection === "right") {
          // During a horizontal exit the overlap touches the chat's top
          // edge and one side: the uncovered region is an L-shaped polygon.
          const exposed = transitionDirection === "right"
            ? `polygon(0 0,${left}px 0,${left}px ${bottom}px,${w}px ${bottom}px,${w}px ${h}px,0 ${h}px)`
            : `polygon(${right}px 0,${w}px 0,${w}px ${h}px,0 ${h}px,0 ${bottom}px,${right}px ${bottom}px)`;
          chatLayer.style.clipPath = exposed;
        } else {
          // For vertical motion a full-width band may cross the chat.
          const mask = `linear-gradient(to bottom,#000 0px,#000 ${top}px,transparent ${top}px,transparent ${bottom}px,#000 ${bottom}px,#000 100%)`;
          chatLayer.style.maskImage = mask;
          chatLayer.style.webkitMaskImage = mask;
        }
      }
      outgoingMaskFrame = requestAnimationFrame(updateOutgoingMask);
    }
    function resetOutgoingOverlay() {
      if (outgoingChatHeightHandler !== null) {
        chatLayer.removeEventListener("transitionend", outgoingChatHeightHandler);
        outgoingChatHeightHandler = null;
      }
      if (outgoingMaskFrame !== null) cancelAnimationFrame(outgoingMaskFrame);
      outgoingMaskFrame = null;
      chatLayer.style.maskImage = "";
      chatLayer.style.webkitMaskImage = "";
      chatLayer.style.clipPath = "";
      root.classList.remove("r06-split-exit", "r06-flow-exit");
      outgoingFlowExit = false;
      outgoingFlowHeight = 0;
      if (!outgoingOverlay) return;
      outgoingOverlay = false;
      for (const name of ["position","height","width","top","left","right","zIndex","pointerEvents","flex"]) {
        listLayer.style[name] = "";
      }
    }
    function freezeOutgoingFlowListLayer() {
      // With an expanding full-height Twitch chat, animate only chat HEIGHT.
      // A fixed-height, non-shrinking List remains the preceding flex child.
      // Flex-end alignment makes its lower boundary EXACTLY chat's upper
      // boundary at every frame (including fractional CSS pixels).
      // This source can be responsively scaled, so CSS layout measurements
      // must be in unscaled local coordinates (never getBoundingClientRect).
      const localHeight = listLayer.offsetHeight;
      if (localHeight <= 0) return false;
      outgoingOverlay = true;
      outgoingFlowExit = true;
      outgoingFlowHeight = localHeight;
      root.classList.add("r06-flow-exit");
      listLayer.style.position = "relative";
      listLayer.style.flex = "0 0 " + localHeight + "px";
      listLayer.style.height = localHeight + "px";
      return true;
    }
    function freezeOutgoingListLayer() {
      // Keep the outgoing content physically on-screen until the list exit
      // ends. Release its flex space at the SAME instant the chat expands;
      // both transitions use the saved duration and a single timeline.
      // offsetHeight is in the element's own CSS coordinate system.
      // getBoundingClientRect() includes the main overlay's responsive
      // scale and would shrink the outgoing layer a second time.
      const height = listLayer.offsetHeight;
      if (height <= 0) return false;
      outgoingOverlay = true;
      root.classList.add("r06-split-exit");
      Object.assign(listLayer.style, {
        position:"absolute",height:height+"px",width:"100%",
        top:"0",left:"0",right:"0",zIndex:"2",pointerEvents:"none",
      });
      if (outgoingMaskFrame !== null) cancelAnimationFrame(outgoingMaskFrame);
      outgoingMaskFrame = requestAnimationFrame(updateOutgoingMask);
      return true;
    }
    function beginAlwaysEntry(wasVisible, wasReplace) {
      resetAlwaysEntry();
      // The previous composition is still rendered here. Reading client
      // sizes rather than bounding boxes avoids responsive double-scaling.
      const available = root.clientHeight;
      if (available <= 0) return;
      const chatNeeded = chatAvailable && (chatAlways || chatHasMessages);
      const currentChat = chatLayer.offsetHeight;
      const targetChat = chatNeeded ? Math.min(
        chatAlways ? available : measureChat(),
        Math.floor((available - 12) / 2)) : 0;
      const targetHeight = available - targetChat;
      const currentList = listLayer.offsetHeight;
      if (!wasVisible) {
        if (currentChat > targetChat + 2) {
          incomingAlways = {type:"flow", targetHeight};
          root.classList.add("r06-flow-enter");
          // The panel starts completely above the composition. As the chat
          // contracts, its top edge pulls the fixed-height List into view.
          listLayer.style.flex = "0 0 " + targetHeight + "px";
        } else {
          incomingAlways = {type:"top", targetHeight};
          // The old List flex slot can still be ZERO when mode changes.
          // Prepare it off-screen now, but begin the animation in a
          // microtask AFTER changeActive/layout assigns its final height.
          // Web Animations run on the Chromium compositor even if inactive
          // OBS pages throttle requestAnimationFrame and CSS keyframe starts.
          root.classList.add("r06-top-enter");
          listPanel.style.transform = "translateY(-100%)";
          Promise.resolve().then(() => {
            if (!incomingAlways || incomingAlways.type !== "top" ||
                mode !== "always") return;
            // Force final layout before Web Animations resolves %-translation.
            listPanel.offsetHeight;
            incomingTopAnimation = listPanel.animate([
              {transform:"translateY(-100%)"},
              {transform:"translate3d(0,0,0)"},
            ], {duration:animationMs, easing:"ease", fill:"both"});
            root.dataset.r06TopEnterStarted = String(
              Number(root.dataset.r06TopEnterStarted || 0) + 1);
            incomingTopAnimation.onfinish = () => {
              root.dataset.r06TopEnterFinished = String(
                Number(root.dataset.r06TopEnterFinished || 0) + 1);
              // Unlike a timeout, onfinish follows Chromium's actual
              // compositor time when OBS/Qt throttles a hidden source.
              finish();
            };
          });
        }
      } else {
        // With a visible slide/replace List, no show-again animation. Move
        // its existing boundary to the Always destination through geometry.
        if (Math.abs(currentList - targetHeight) <= 2 &&
            !wasReplace) return;
        incomingAlways = {type:"resize", targetHeight};
        root.classList.add("r06-always-resize");
        if (wasReplace) {
          // Replace had a full-screen absolute List and a covered full-size
          // chat. The visible starting geometry is List=100%, chat=0.
          // Convert to the SAME normal-flow geometry without changing
          // pixels: only then animate the two shared boundaries to 50/50.
          root.classList.remove("r06-replace");
          chatLayer.style.transition = "none";
          chatLayer.style.height = "0px";
          chatLayer.offsetHeight;
          chatLayer.style.transition = "";
          lastChatHeight = 0;
        }
        listLayer.style.flex = "0 0 " + currentList + "px";
        // Install the initial flex-basis before the target is applied.
        listLayer.offsetHeight;
      }
      const finish = () => {
        if (mode !== "always") return;
        listPanel.style.transition = "";
        listPanel.style.opacity = "";
        listPanel.style.transform = "";
        resetAlwaysEntry();
        layout();
        if (onResize) onResize();
      };
      // The top-entry compositor can start late in an occluded OBS
      // window. Never cancel a still-running animation at duration+180ms.
      // The shared flex-flow and resize transitions keep their bounded
      // timing; top-entry completes via WAAPI.onfinish above.
      incomingAlwaysTimer = setTimeout(finish, incomingAlways?.type === "top"
        ? Math.max(20000, animationMs * 10) : animationMs + 180);
    }
    function changeActive(next) {
      if (active === next) return;
      active = next;
      clearTransition();
      if (next) resetOutgoingOverlay();
      else {
        pendingAlwaysEntry = null;
        if (incomingAlways) resetAlwaysEntry();
      }
      // "Не показывать" is a vertical collapse, not a command slide.
      // A saved earlier slide direction must never rotate this transition.
      transitionDirection = mode === "hidden" || mode === "always"
        ? "top" : direction;
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
        if (staged && mode !== "always") {
          visualActive = false;
          layout();
          transitionTimer = setTimeout(() => {
            transitionTimer = null;
            if (active) {
              visualActive = true;
              applyVisual();
              if (onResize) onResize();
            }
          }, animationMs);
        } else {
          visualActive = true;
        }
      } else {
        // Always retain the outgoing content for a full transition.
        // Otherwise flex-basis=0 instantly clips a still-animated panel.
        reserved = true;
        const chatFillsArea = chatAvailable &&
          (chatAlways || (chatHasMessages && measureChat() >= available - 1));
        if (mode === "hidden" && composeMode === "split" &&
            chatFillsArea && freezeOutgoingFlowListLayer()) {
          // The List is a fixed-size flex predecessor of chat. Its visual
          // motion is driven solely by chat height, never a second clock.
          reserved = false;
        } else if ((composeMode === "split" || mode === "hidden") &&
                   freezeOutgoingListLayer()) {
          // Fallback for absent/short chat and other List exit directions.
          reserved = false;
        }
        visualActive = false;
        const finishExit = () => {
          transitionTimer = null;
          if (!active) {
            reserved = false;
            resetOutgoingOverlay();
            layout();
            if (onResize) onResize();
          }
        };
        if (outgoingFlowExit) {
          // Preserve flex geometry until the actual CSS HEIGHT animation ends.
          // A timer started before Chromium's next style frame can run slightly
          // early and create a visible final one-frame snap.
          outgoingChatHeightHandler = event => {
            if (event.target !== chatLayer || event.propertyName !== "height") return;
            clearTransition();
            finishExit();
          };
          chatLayer.addEventListener("transitionend", outgoingChatHeightHandler);
        }
        // Safety fallback if CSS transitionend is suppressed (background OBS
        // tab, resize or interrupted transition). Normal exits are unchanged.
        transitionTimer = setTimeout(finishExit, animationMs +
          (outgoingFlowExit ? 250 : 0));
      }
      applyVisual();
      layout();
      if (onResize) setTimeout(onResize,
        (staged ? animationMs * 2 : animationMs) + 60);
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
      const becomingAlways = newMode === "always" && mode !== "always";
      const previouslyVisible = active && visualActive;
      const previousReplace = composeMode === "replace" && mode === "slide";
      if (becomingAlways && outgoingOverlay) {
        resetOutgoingOverlay();
      }
      mode = newMode;
      direction = newDirection;
      composeMode = newCompose;
      // A hidden-mode exit is preserved even if the previously displayed
      // command List used the Replace composition instead of Split.
      if (outgoingOverlay && composeMode !== "split" && mode !== "hidden") {
        resetOutgoingOverlay();
      }
      animationMs = nextAnimationMs;
      // The operator may change speed while a list is already visible.
      // Do not wait for another visibility toggle to update either CSS
      // transition: both must always share the latest saved duration.
      root.style.setProperty("--r06-list-transition", animationMs + "ms");
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
      if (becomingAlways) {
        pendingAlwaysEntry = {
          wasVisible: previouslyVisible, wasReplace: previousReplace
        };
        // T02 regression: a hidden command List may still carry the previous
        // left/right/bottom transform. Prepare the universal top/flow entry
        // BEFORE changeActive() makes it visible. Otherwise Chromium starts
        // the old slide transition for one frame before layout() corrects it.
        // The zero-height /overlay slot is handled by layout() as before.
        if (root.clientHeight > 0) {
          const pending = pendingAlwaysEntry;
          pendingAlwaysEntry = null;
          beginAlwaysEntry(pending.wasVisible, pending.wasReplace);
        }
      } else if (mode !== "always") {
        pendingAlwaysEntry = null;
        if (incomingAlways) resetAlwaysEntry();
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
      hasChatSpace: () => chatAvailable && (chatAlways || chatHasMessages),
      listActive: () => active,
      hasListArea: () => active || reserved || outgoingOverlay,
    };
  }
  window.IOLListComposition = Object.freeze({create});
})();
