/* InOneLine D41 DOM inspector. Chrome DevTools -> Sources -> Snippets.
 * No requests, no cookies, no token access, no message or username capture.
 * Export includes only structure, counts, and session-local hashed IDs.
 */
(() => {
  "use strict";
  if (window.iolChatDiag) {
    console.warn("InOneLine inspector is already running. Execute iolChatDiag.stop() first.");
    return;
  }
  const started = Date.now(), platform = /(^|\.)youtube\.com$/.test(location.hostname) ? "youtube"
    : /(^|\.)twitch\.tv$/.test(location.hostname) ? "twitch" : "other";
  const selectors = [
    "yt-live-chat-text-message-renderer",
    "yt-live-chat-paid-message-renderer",
    "yt-live-chat-membership-item-renderer",
    "yt-live-chat-deleted-message-renderer",
    ".chat-line__message",
    '[data-test-selector="chat-line-message"]',
    '[data-a-target="chat-deleted-message"]'
  ];
  const rowSelector = selectors.join(",");
  const deletions = /message (was )?deleted|message removed|deleted by moderator|сообщени[ея] (было )?удален[оы]/i;
  const random = (Math.random() * 0xffffffff) >>> 0;
  const references = new WeakMap(), records = [], counts = {adds:0,removes:0,attributes:0,text:0};
  let sequence = 0, dropped = 0, active = true;
  function ref(node) {
    if (!node) return null;
    if (!references.has(node)) references.set(node, "element-" + (++sequence));
    return references.get(node);
  }
  function safeHash(id) {
    if (!id) return null;
    let h = (2166136261 ^ random) >>> 0;
    for (let i=0; i<id.length; i++) h = Math.imul(h ^ id.charCodeAt(i), 16777619);
    return (h >>> 0).toString(16);
  }
  function element(node) {
    return node && (node.nodeType === 1 ? node : node.parentElement);
  }
  function rows(root) {
    const out = [];
    if (!root) return out;
    try {
      if (root.matches(rowSelector)) out.push(root);
      for (const item of root.querySelectorAll(rowSelector)) {
        if (out.length >= 8) break;
        out.push(item);
      }
    } catch (_) {}
    return out;
  }
  function detail(node) {
    const rawId = node.getAttribute("id") || node.getAttribute("data-id") ||
      node.getAttribute("data-message-id") || "";
    const message = (node.innerText || node.textContent || "").trim();
    const attributes = ["id","class","is-deleted","deleted","hidden",
      "aria-hidden","data-id","data-message-id","data-a-target","data-test-selector"];
    return {
      ref: ref(node), tag: node.tagName.toLowerCase(), hashedId: safeHash(rawId),
      attrs: attributes.filter(name => node.hasAttribute(name)),
      classes: Array.from(node.classList || []).filter(x => /^[a-zA-Z0-9_-]{1,45}$/.test(x)).slice(0,8),
      textLength: message.length, looksDeleted: deletions.test(message),
      deletionFlag: node.hasAttribute("is-deleted") || node.hasAttribute("deleted") ||
        !!node.querySelector('[is-deleted],#deleted-state,yt-live-chat-deleted-message-renderer'),
      hasMessageRegion: !!node.querySelector('#message,[data-a-target="chat-message-text"]')
    };
  }
  function snapshot() {
    const found = {};
    for (const selector of selectors) {
      try { found[selector] = document.querySelectorAll(selector).length; }
      catch (_) { found[selector] = -1; }
    }
    return {
      host: location.hostname,
      pageKind: /live_chat/.test(location.pathname) ? "live_chat"
        : /popout/.test(location.pathname) ? "popout" : "other",
      documentState: document.readyState, visibility: document.visibilityState,
      iframeCount: document.querySelectorAll("iframe").length,
      elementCounts: found,
      sampleRows: rows(document.documentElement).slice(0,8).map(detail)
    };
  }
  function record(kind, extra) {
    if (!active) return;
    if (records.length >= 400) { records.shift(); dropped++; }
    records.push({atMs: Date.now()-started, kind, ...extra});
  }
  const observer = new MutationObserver(changes => {
    for (const change of changes) {
      if (change.type === "childList") {
        for (const n of change.addedNodes) {
          const found = rows(element(n));
          if (found.length) { counts.adds += found.length; record("added",{rows:found.map(detail)}); }
        }
        for (const n of change.removedNodes) {
          const found = rows(element(n));
          if (found.length) { counts.removes += found.length; record("removed",{rows:found.map(detail)}); }
        }
      } else if (change.type === "attributes") {
        const node = element(change.target), row = node && node.closest(rowSelector);
        if (row) { counts.attributes++; record("attribute",{name:change.attributeName,row:detail(row)}); }
      } else if (change.type === "characterData") {
        const node = element(change.target), row = node && node.closest(rowSelector);
        if (row) { counts.text++; record("text-changed",{row:detail(row)}); }
      }
    }
  });
  observer.observe(document.documentElement,{
    subtree:true,childList:true,characterData:true,attributes:true,
    attributeFilter:["id","class","is-deleted","deleted","hidden","aria-hidden",
      "data-id","data-message-id","data-a-target","data-test-selector"]
  });
  record("started",{platform,snapshot:snapshot()});
  const timer = setInterval(() => record("snapshot",{snapshot:snapshot()}),10000);
  const api = {
    mark(label) {
      record("manual-mark",{label:String(label || "mark").replace(/[^a-zA-Z0-9 _-]/g,"").slice(0,50),
        snapshot:snapshot()});
      console.log("InOneLine marked:",label);
    },
    stop() {
      record("stopped",{snapshot:snapshot()});
      active = false;
      observer.disconnect(); clearInterval(timer);
      const json = JSON.stringify({
        tool:"InOneLine-D41-DOM-v2", platform, durationMs:Date.now()-started,
        notice:"Structural metadata only, verify file before sharing.",
        counts,dropped,records
      }, null, 2);
      try {
        const url = URL.createObjectURL(new Blob([json],{type:"application/json"}));
        const a = document.createElement("a");
        a.href=url;
        a.download="InOneLine_D41_"+platform+"_dom_diagnostic.json";
        document.body.appendChild(a);
        a.click(); a.remove();
        setTimeout(()=>URL.revokeObjectURL(url),2000);
      } catch (_) {
        console.warn("Download blocked. Use DevTools: copy(iolChatDiag.stop()) on a new run.");
      }
      delete window.iolChatDiag;
      return json;
    }
  };
  Object.defineProperty(window,"iolChatDiag",{value:api,configurable:true});
  console.log("InOneLine DOM inspector running for",platform,
    "Run iolChatDiag.mark('sent') after sending, iolChatDiag.mark('deleted') after deletion, then iolChatDiag.stop().");
})();