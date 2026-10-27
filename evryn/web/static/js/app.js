/**
 * EVRYN Main Application Controller
 * Coordinates minimal workspace, auto-sizing central input, file uploads, session persistence, and inspector.
 */
(function () {
  let activeSessionId = null;
  let activeSessionData = null;
  let graphRenderer = null;

  // DOM Elements
  const queryInput = document.getElementById("query-input");
  const regenerateBtn = document.getElementById("regenerate-btn");
  const resetWorkspaceBtn = document.getElementById("reset-workspace-btn");
  const testExamplesBar = document.getElementById("test-examples-bar");
  const appNotification = document.getElementById("app-notification");
  const sentenceHighlighterBar = document.getElementById("sentence-highlighter-bar");
  const plusBtn = document.getElementById("plus-btn");
  const plusMenu = document.getElementById("plus-menu");
  const fileInput = document.getElementById("file-input");
  const inputContainer = document.getElementById("input-container");
  const processingIndicator = document.getElementById("processing-indicator");
  const processingText = document.getElementById("processing-text");
  const resultsView = document.getElementById("results-view");
  const graphStats = document.getElementById("graph-stats");
  const batchSection = document.getElementById("batch-section");
  const batchCards = document.getElementById("batch-cards");
  const toggleCombinedBtn = document.getElementById("toggle-combined-btn");

  // Synchronized 4-Views DOM Elements
  const viewTabGraph = document.getElementById("view-tab-graph");
  const viewTabCopyable = document.getElementById("view-tab-copyable");
  const viewTabTable = document.getElementById("view-tab-table");
  const viewTabExamples = document.getElementById("view-tab-examples");
  const graphViewport = document.getElementById("graph-viewport");
  const graphEmptyState = document.getElementById("graph-empty-state");
  const copyableView = document.getElementById("copyable-view");
  const copyableText = document.getElementById("copyable-text");
  const copyGraphBtn = document.getElementById("copy-graph-btn");
  const tableView = document.getElementById("table-view");
  const tableBody = document.getElementById("table-body");
  const examplesView = document.getElementById("examples-view");

  // Examples Tab Subviews & Controls
  const subnavTestcases = document.getElementById("subnav-testcases");
  const subnavPdf = document.getElementById("subnav-pdf");
  const subnavText = document.getElementById("subnav-text");
  const subnavMultipage = document.getElementById("subnav-multipage");
  const subviewTestcases = document.getElementById("subview-testcases-container");
  const subviewPdf = document.getElementById("subview-pdf-container");
  const subviewText = document.getElementById("subview-text-container");
  const subviewMultipage = document.getElementById("subview-multipage-container");
  const splitFilterSelect = document.getElementById("split-filter-select");
  const examplesSearchInput = document.getElementById("examples-search-input");
  const testcasesCardsList = document.getElementById("testcases-cards-list");
  const pdfCardsGrid = document.getElementById("pdf-cards-grid");
  const textCardsList = document.getElementById("text-cards-list");
  const multipageCardsList = document.getElementById("multipage-cards-list");

  // Paper Detail & PDF Modal Elements
  const paperModal = document.getElementById("paper-modal");
  const paperModalTitle = document.getElementById("paper-modal-title");
  const paperModalBadge = document.getElementById("paper-modal-badge");
  const closePaperModalBtn = document.getElementById("close-paper-modal-btn");
  const paperTabPdf = document.getElementById("paper-tab-pdf");
  const paperTabText = document.getElementById("paper-tab-text");
  const paperTabCausal = document.getElementById("paper-tab-causal");
  const paperPdfFrameWrap = document.getElementById("paper-pdf-frame-wrap");
  const paperPdfIframe = document.getElementById("paper-pdf-iframe");
  const paperTextWrap = document.getElementById("paper-text-wrap");
  const paperCausalWrap = document.getElementById("paper-causal-wrap");
  const loadPaperWorkspaceBtn = document.getElementById("load-paper-workspace-btn");

  // Physics & Tighten Controls
  const physicsPresetSelect = document.getElementById("physics-preset-select");
  const tightenEdgeBtn = document.getElementById("tighten-edge-btn");
  const tensionBadge = document.getElementById("tension-badge");
  const loosenEdgeBtn = document.getElementById("loosen-edge-btn");

  // Expandable Legend
  const graphLegend = document.getElementById("graph-legend");
  const legendHeader = document.getElementById("legend-header");
  const toggleLegendBtn = document.getElementById("toggle-legend-btn");
  const legendCollapsedSummary = document.getElementById("legend-collapsed-summary");
  const legendExpandedBody = document.getElementById("legend-expanded-body");
  const toggleNegatedEdges = document.getElementById("toggle-negated-edges");

  // Continual Learning Floating Elements
  const continualWrapper = document.getElementById("continual-wrapper");
  const continualHoverZone = document.getElementById("continual-hover-zone");
  const continualToggleBtn = document.getElementById("continual-toggle-btn");
  const continualCard = document.getElementById("continual-card");
  const continualInput = document.getElementById("continual-input");
  const continualSubmitBtn = document.getElementById("continual-submit-btn");
  const closeContinualBtn = document.getElementById("close-continual-btn");

  const inspectorPanel = document.getElementById("inspector-panel");
  const inspectorBody = document.getElementById("inspector-body");
  const closeInspectorBtn = document.getElementById("close-inspector-btn");

  const sidebar = document.getElementById("sidebar");
  const toggleSidebarBtn = document.getElementById("toggle-sidebar-btn");
  const openSidebarBtn = document.getElementById("open-sidebar-btn");
  const sidebarBackdrop = document.getElementById("sidebar-backdrop");
  const sessionList = document.getElementById("session-list");
  const sessionCountLabel = document.getElementById("session-count-label");
  const newSessionBtn = document.getElementById("new-session-btn");
  const sessionSelectAllCb = document.getElementById("session-select-all-cb");
  const sessionDedupBtn = document.getElementById("session-dedup-btn");
  const sessionBulkDeleteBtn = document.getElementById("session-bulk-delete-btn");
  const sessionClearAllBtn = document.getElementById("session-clear-all-btn");
  const selectedSessionIds = new Set();

  const menuTestCasesBtn = document.getElementById("menu-test-cases-btn");
  const menuExamplesBtn = document.getElementById("menu-examples-btn");
  const menuUploadBtn = document.getElementById("menu-upload-btn");
  const menuEvalBtn = document.getElementById("menu-eval-btn");
  const menuContinualBtn = document.getElementById("menu-continual-btn");

  const dropOverlay = document.getElementById("drop-overlay");
  let selectedRelation = null;
  let isSubmitting = false;

  // Initialize Graph Renderer
  graphRenderer = new CausalGraphRenderer(
    "graph-viewport",
    "causal-graph-svg",
    onSelectRelation,
    onSelectNode,
    onLayoutChanged
  );

  // Setup Toolbar Controls
  document.getElementById("graph-fit-btn").addEventListener("click", () => graphRenderer.fitToView());
  document.getElementById("graph-zoom-in").addEventListener("click", () => graphRenderer.zoomIn());
  document.getElementById("graph-zoom-out").addEventListener("click", () => graphRenderer.zoomOut());

  // 3-View Tab Switcher
  function switchView(tabName) {
    viewTabGraph.classList.toggle("active", tabName === "graph");
    viewTabCopyable.classList.toggle("active", tabName === "copyable");
    viewTabTable.classList.toggle("active", tabName === "table");
    if (viewTabExamples) viewTabExamples.classList.toggle("active", tabName === "examples");

    viewTabGraph.setAttribute("aria-selected", tabName === "graph");
    viewTabCopyable.setAttribute("aria-selected", tabName === "copyable");
    viewTabTable.setAttribute("aria-selected", tabName === "table");
    if (viewTabExamples) viewTabExamples.setAttribute("aria-selected", tabName === "examples");

    graphViewport.classList.toggle("hidden", tabName !== "graph");
    copyableView.classList.toggle("hidden", tabName !== "copyable");
    tableView.classList.toggle("hidden", tabName !== "table");
    if (examplesView) examplesView.classList.toggle("hidden", tabName !== "examples");

    if (tabName === "examples") {
      inputContainer.classList.add("hidden");
      graphRenderer.pause();
      resultsView.classList.remove("hidden");
      switchExamplesSubnav(activeExamplesSubnav || "pdf");
    } else {
      inputContainer.classList.remove("hidden");
      if (!activeSessionData) {
        resultsView.classList.add("hidden");
        undockInput();
      } else {
        dockInput();
        if (tabName === "copyable") {
          copyableText.textContent = generateCopyableGraphText(activeSessionData);
          graphRenderer.pause();
        } else if (tabName === "table") {
          graphRenderer.pause();
        } else if (tabName === "graph") {
          graphRenderer.resume();
          graphRenderer.fitToView();
        }
      }
    }
  }

  viewTabGraph.addEventListener("click", () => switchView("graph"));
  viewTabCopyable.addEventListener("click", () => switchView("copyable"));
  viewTabTable.addEventListener("click", () => switchView("table"));
  if (viewTabExamples) viewTabExamples.addEventListener("click", () => switchView("examples"));

  // 1-Click Copy Graph Button
  copyGraphBtn.addEventListener("click", () => {
    if (!copyableText.textContent) return;
    navigator.clipboard.writeText(copyableText.textContent).then(() => {
      const orig = copyGraphBtn.textContent;
      copyGraphBtn.textContent = "COPIED ✓";
      setTimeout(() => { copyGraphBtn.textContent = orig; }, 1800);
    }).catch(err => {
      console.warn("Clipboard write failed:", err);
    });
  });

  // Physics Preset Selector
  physicsPresetSelect.addEventListener("change", (e) => {
    const preset = e.target.value;
    graphRenderer.setPhysicsPreset(preset);
    if (activeSessionId) {
      fetch(`/api/sessions/${activeSessionId}/physics`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ preset }),
      }).catch(console.warn);
    }
  });

  // Edge Tightening Button (T)
  tightenEdgeBtn.addEventListener("click", () => {
    if (!selectedRelation) {
      alert("Please click and select an edge in the graph first to tighten its tension.");
      return;
    }
    const newTension = graphRenderer.tightenEdge(selectedRelation.id);
    updateTensionBadge(newTension);
    if (activeSessionId) {
      fetch(`/api/sessions/${activeSessionId}/physics`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tensions: { [selectedRelation.id]: newTension } }),
      }).catch(console.warn);
    }
  });

  loosenEdgeBtn.addEventListener("click", () => {
    if (!selectedRelation) return;
    const newTension = graphRenderer.loosenEdge(selectedRelation.id);
    updateTensionBadge(newTension);
    if (activeSessionId) {
      fetch(`/api/sessions/${activeSessionId}/physics`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tensions: { [selectedRelation.id]: newTension } }),
      }).catch(console.warn);
    }
  });

  function updateTensionBadge(tension) {
    if (!tension || tension <= 1) {
      tensionBadge.classList.add("hidden");
      loosenEdgeBtn.classList.add("hidden");
    } else {
      tensionBadge.textContent = tension;
      tensionBadge.classList.remove("hidden");
      loosenEdgeBtn.classList.remove("hidden");
    }
  }

  // Expandable Legend Toggle
  function toggleLegend() {
    const isExpanded = graphLegend.classList.contains("expanded");
    if (isExpanded) {
      graphLegend.classList.remove("expanded");
      graphLegend.classList.add("collapsed");
      legendCollapsedSummary.classList.remove("hidden");
      legendExpandedBody.classList.add("hidden");
      toggleLegendBtn.textContent = "▲";
    } else {
      graphLegend.classList.remove("collapsed");
      graphLegend.classList.add("expanded");
      legendCollapsedSummary.classList.add("hidden");
      legendExpandedBody.classList.remove("hidden");
      toggleLegendBtn.textContent = "▼";
    }
  }

  legendHeader.addEventListener("click", toggleLegend);
  toggleLegendBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleLegend();
  });

  toggleNegatedEdges.addEventListener("change", (e) => {
    graphRenderer.setShowNegatedEdges(e.target.checked);
  });

  // Continual Learning Floating Flyout Handlers
  function openContinualCard() {
    continualWrapper.classList.add("card-open");
    continualCard.classList.remove("hidden");
    continualToggleBtn.setAttribute("aria-expanded", "true");
    continualToggleBtn.classList.add("revealed");
    continualInput.focus();
  }

  function closeContinualCard() {
    continualWrapper.classList.remove("card-open");
    continualCard.classList.add("hidden");
    continualToggleBtn.setAttribute("aria-expanded", "false");
    continualToggleBtn.classList.remove("revealed");
  }

  function toggleContinualCard() {
    if (continualCard.classList.contains("hidden")) {
      openContinualCard();
    } else {
      closeContinualCard();
    }
  }

  continualToggleBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleContinualCard();
  });

  if (continualHoverZone) {
    continualHoverZone.addEventListener("click", (e) => {
      if (e.target === continualHoverZone) {
        openContinualCard();
      }
    });
    continualHoverZone.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openContinualCard();
      }
    });
  }

  closeContinualBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    closeContinualCard();
  });

  continualCard.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      e.stopPropagation();
      closeContinualCard();
      continualToggleBtn.focus();
    }
  });

  continualSubmitBtn.addEventListener("click", () => {
    submitContinualKnowledge();
  });

  continualInput.addEventListener("keydown", (e) => {
    if (e.isComposing || e.keyCode === 229) {
      return;
    }
    if (e.key === "Enter") {
      if (e.shiftKey) {
        return; // Allow Shift+Enter for newline
      }
      e.preventDefault();
      submitContinualKnowledge();
    }
  });

  async function submitContinualKnowledge() {
    if (isSubmitting) return;
    const incText = continualInput.value.trim();
    if (!incText) return;

    if (!activeSessionId) {
      closeContinualCard();
      submitQuery(incText);
      continualInput.value = "";
      return;
    }

    isSubmitting = true;
    showProcessing("APPENDING EVIDENCE & REGENERATING GRAPH...");
    try {
      const res = await fetch(`/api/sessions/${activeSessionId}/continual`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ incremental_text: incText }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Continual learning failed");
      }
      const data = await res.json();
      continualInput.value = "";
      closeContinualCard();
      renderSession(data);
      refreshSessionList();
    } catch (err) {
      alert("Continual error: " + err.message);
    } finally {
      isSubmitting = false;
      hideProcessing();
    }
  }

  // Sidebar State Management
  function openSidebar() {
    sidebar.classList.remove("collapsed");
    openSidebarBtn.classList.add("hidden");
    openSidebarBtn.setAttribute("aria-expanded", "true");
    if (sidebarBackdrop) {
      sidebarBackdrop.classList.remove("hidden");
    }
    if (typeof window !== "undefined" && window.innerWidth <= 768) {
      closeInspector();
    }
    refreshSessionList();
  }

  function closeSidebar() {
    sidebar.classList.add("collapsed");
    openSidebarBtn.classList.remove("hidden");
    openSidebarBtn.setAttribute("aria-expanded", "false");
    if (sidebarBackdrop) {
      sidebarBackdrop.classList.add("hidden");
    }
  }

  function openInspector() {
    inspectorPanel.classList.remove("hidden");
    if (typeof document !== "undefined" && document.body) {
      document.body.classList.add("inspector-open");
    }
    if (typeof window !== "undefined" && window.innerWidth <= 768) {
      closeSidebar();
    }
  }

  function closeInspector() {
    inspectorPanel.classList.add("hidden");
    if (typeof document !== "undefined" && document.body) {
      document.body.classList.remove("inspector-open");
    }
  }

  function autoCloseSidebar() {
    closeSidebar();
  }

  queryInput.addEventListener("focus", autoCloseSidebar);
  queryInput.addEventListener("click", autoCloseSidebar);
  sidebar.addEventListener("click", (e) => {
    e.stopPropagation();
  });

  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener("click", () => {
      closeSidebar();
    });
  }

  // Outside click listener: clicking outside the open sidebar and toggle closes it
  document.addEventListener("click", (e) => {
    if (sidebar.classList.contains("collapsed")) return;

    // Do not close if clicking inside sidebar, or on toggle/open button
    if (sidebar.contains(e.target) || (openSidebarBtn && openSidebarBtn.contains(e.target))) {
      return;
    }

    // Do not close while selecting text
    const selection = window.getSelection ? window.getSelection().toString() : "";
    if (selection && selection.length > 0) {
      return;
    }

    closeSidebar();
  });

  // Escape key closes open sidebar and restores focus
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !sidebar.classList.contains("collapsed")) {
      closeSidebar();
      if (openSidebarBtn) {
        openSidebarBtn.focus();
      }
    }
  });

  // Primary Prompt Execution & Regeneration Handler
  function executePrimaryAction() {
    if (isSubmitting) return;
    const text = queryInput.value.trim();
    if (!text) return;

    if (activeSessionId) {
      regeneratePrimaryPrompt();
    } else {
      submitQuery(text);
    }
  }

  regenerateBtn.addEventListener("click", () => {
    executePrimaryAction();
  });

  async function regeneratePrimaryPrompt() {
    if (isSubmitting) return;
    const text = queryInput.value.trim();
    if (!text) return;
    if (!activeSessionId) {
      submitQuery(text);
      return;
    }
    isSubmitting = true;
    showProcessing("REGENERATING GRAPH FROM SPECIFICATION...");
    try {
      const res = await fetch(`/api/sessions/${activeSessionId}/regenerate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text, primary_prompt: text }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Regeneration failed");
      }
      const data = await res.json();
      renderSession(data);
      refreshSessionList();
    } catch (err) {
      alert("Regeneration failed: " + err.message);
    } finally {
      isSubmitting = false;
      hideProcessing();
    }
  }

  // Auto-resize textarea
  function autoResize(el) {
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 180) + "px";
  }

  queryInput.addEventListener("input", () => autoResize(queryInput));

  // Enter to Execute Primary Action, Shift+Enter for newline
  queryInput.addEventListener("keydown", (e) => {
    if (e.isComposing || e.keyCode === 229) {
      return;
    }
    if (e.key === "Enter") {
      if (e.shiftKey) {
        return; // Allow Shift+Enter to insert a newline
      }
      e.preventDefault();
      executePrimaryAction();
    }
  });

  // Plus Control Popover
  plusBtn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    const isHidden = plusMenu.classList.contains("hidden");
    plusMenu.classList.toggle("hidden", !isHidden);
    plusBtn.setAttribute("aria-expanded", isHidden ? "true" : "false");
  });

  plusBtn.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      e.stopPropagation();
      plusBtn.click();
    } else if (e.key === "Escape") {
      plusMenu.classList.add("hidden");
      plusBtn.setAttribute("aria-expanded", "false");
    }
  });

  document.addEventListener("click", (e) => {
    if (!plusMenu.contains(e.target) && e.target !== plusBtn) {
      plusMenu.classList.add("hidden");
      plusBtn.setAttribute("aria-expanded", "false");
    }
  });

  menuUploadBtn.addEventListener("click", () => {
    plusMenu.classList.add("hidden");
    plusBtn.setAttribute("aria-expanded", "false");
    fileInput.click();
  });

  if (menuContinualBtn) {
    menuContinualBtn.addEventListener("click", () => {
      plusMenu.classList.add("hidden");
      plusBtn.setAttribute("aria-expanded", "false");
      openContinualCard();
    });
  }

  if (menuTestCasesBtn) {
    menuTestCasesBtn.addEventListener("click", () => {
      plusMenu.classList.add("hidden");
      plusBtn.setAttribute("aria-expanded", "false");
      switchView("examples");
      switchExamplesSubnav("testcases");
    });
  }

  if (menuExamplesBtn) {
    menuExamplesBtn.addEventListener("click", () => {
      plusMenu.classList.add("hidden");
      plusBtn.setAttribute("aria-expanded", "false");
      switchView("examples");
    });
  }

  if (resetWorkspaceBtn) {
    resetWorkspaceBtn.addEventListener("click", () => resetWorkspace());
  }

  // Quick test example chips
  document.querySelectorAll(".test-example-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const exId = chip.dataset.example;
      if (exId) loadAndRunTestCase(exId);
    });
  });

  menuEvalBtn.addEventListener("click", () => {
    plusMenu.classList.add("hidden");
    plusBtn.setAttribute("aria-expanded", "false");
    runBenchmarkVerification();
  });

  // File Upload Handlers
  fileInput.addEventListener("change", (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      uploadFiles(files);
    }
  });

  // Drag and Drop
  window.addEventListener("dragenter", (e) => {
    e.preventDefault();
    dropOverlay.classList.remove("hidden");
  });

  dropOverlay.addEventListener("dragover", (e) => e.preventDefault());
  dropOverlay.addEventListener("dragleave", (e) => {
    if (e.relatedTarget === null) {
      dropOverlay.classList.add("hidden");
    }
  });

  dropOverlay.addEventListener("drop", (e) => {
    e.preventDefault();
    dropOverlay.classList.add("hidden");
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      uploadFiles(files);
    }
  });

  // Query Submission
  async function submitQuery(text) {
    dockInput();
    const selectedEngine = document.querySelector('input[name="extraction_engine"]:checked')?.value || "nlp_baseline";
    showProcessing(`EXTRACTING CAUSAL RELATIONSHIPS [${selectedEngine.toUpperCase()}]...`);

    try {
      const res = await fetch("/api/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text,
          session_id: activeSessionId,
          system_mode: selectedEngine,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        showNotification(err.detail || "Extraction failed", "error", 5000);
        return;
      }

      const data = await res.json();
      activeSessionId = data.id;
      renderSession(data);
      refreshSessionList();
    } catch (err) {
      showNotification("Error: " + err.message, "error", 5000);
    } finally {
      hideProcessing();
    }
  }

  // Continuation Submission
  async function submitContinuation(text) {
    if (!activeSessionId) return;
    showProcessing("UPDATING CAUSAL KNOWLEDGE & EVIDENCE...");

    try {
      const res = await fetch(`/api/sessions/${activeSessionId}/continue`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Continuation failed");
      }

      const data = await res.json();
      renderSession(data);
      refreshSessionList();
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      hideProcessing();
    }
  }

  // Upload Files (Single or Batch)
  async function uploadFiles(files) {
    dockInput();
    showProcessing(`PARSING & EXTRACTING FROM ${files.length} DOCUMENT(S)...`);

    const formData = new FormData();
    for (const f of files) {
      formData.append("files", f);
    }
    if (activeSessionId) {
      formData.append("session_id", activeSessionId);
    }

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed");
      }

      const batchData = await res.json();
      activeSessionId = batchData.session_id;

      // If multiple documents, render batch cards
      if (batchData.documents && batchData.documents.length > 1) {
        renderBatchCards(batchData.documents, batchData.combined_graph);
      } else {
        batchSection.classList.add("hidden");
      }

      renderSession(batchData.combined_graph);
      refreshSessionList();
    } catch (err) {
      alert("Upload failed: " + err.message);
    } finally {
      hideProcessing();
      fileInput.value = "";
    }
  }

  function dockInput() {
    inputContainer.classList.remove("centered");
    inputContainer.classList.add("docked");
    regenerateBtn.classList.remove("hidden");
    if (resetWorkspaceBtn) resetWorkspaceBtn.classList.remove("hidden");
  }

  function undockInput() {
    inputContainer.classList.remove("hidden");
    inputContainer.classList.remove("docked");
    inputContainer.classList.add("centered");
    resultsView.classList.add("hidden");
    batchSection.classList.add("hidden");
    closeInspector();
    sentenceHighlighterBar.innerHTML = "";
    sentenceHighlighterBar.classList.add("hidden");
    regenerateBtn.classList.add("hidden");
    if (resetWorkspaceBtn) resetWorkspaceBtn.classList.add("hidden");
    if (graphEmptyState) graphEmptyState.classList.add("hidden");
    window.EVRYN_BG.setDimmed(false);
    queryInput.value = "";
    autoResize(queryInput);
    queryInput.focus();
  }

  let notificationTimeout = null;
  function showNotification(msg, type = "info", duration = 4000) {
    if (!appNotification) return;
    if (notificationTimeout) clearTimeout(notificationTimeout);
    appNotification.textContent = msg;
    appNotification.className = `app-notification ${type}`;
    appNotification.classList.remove("hidden");
    if (duration > 0) {
      notificationTimeout = setTimeout(() => {
        appNotification.classList.add("hidden");
      }, duration);
    }
  }

  function resetWorkspace() {
    activeSessionId = null;
    activeSessionData = null;
    undockInput();
    if (graphRenderer) graphRenderer.setData([], []);
    if (graphEmptyState) graphEmptyState.classList.add("hidden");
    if (tableBody) tableBody.innerHTML = "";
    if (copyableText) copyableText.textContent = "";
    if (graphStats) graphStats.textContent = "0 NODES | 0 CAUSAL RELATIONS";
    document.querySelectorAll(".test-example-chip").forEach(c => c.classList.remove("active"));
    showNotification("Workspace reset. Ready for new exploration.", "info", 2500);
  }

  async function clearAllSessionsPrompt() {
    const ok = confirm("Are you sure you want to clear ALL application sessions?\n\nA recoverable JSON and SQLite snapshot will be automatically saved to ~/.evryn/backups/.");
    if (!ok) return;

    showProcessing("CLEARING ALL APPLICATION SESSIONS...");
    try {
      const res = await fetch("/api/sessions/clear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirm: true, backup: true })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to clear sessions");
      }
      const data = await res.json();
      resetWorkspace();
      await refreshSessionList();
      showNotification(`Cleared ${data.deleted_sessions_count} sessions. Backup saved.`, "success", 4000);
    } catch (err) {
      showNotification("Error clearing sessions: " + err.message, "error", 4000);
    } finally {
      hideProcessing();
    }
  }

  async function loadAndRunTestCase(exampleId) {
    document.querySelectorAll(".test-example-chip").forEach(c => {
      c.classList.toggle("active", c.dataset.example === exampleId);
    });

    activeSessionId = null;
    activeSessionData = null;
    closeInspector();

    dockInput();
    showProcessing(`RUNNING TEST CASE [${exampleId.toUpperCase()}] THROUGH CAUSAL PIPELINE...`);

    try {
      const res = await fetch(`/api/test-examples/${exampleId}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });

      const data = await res.json();

      if (!res.ok) {
        // E.g. Example E empty input validation
        queryInput.value = data.example ? data.example.input_text : "   ";
        autoResize(queryInput);
        if (graphRenderer) graphRenderer.setData([], []);
        if (graphStats) graphStats.textContent = "0 NODES | 0 CAUSAL RELATIONS";
        if (graphEmptyState) {
          graphEmptyState.classList.remove("hidden");
          const heading = graphEmptyState.querySelector(".empty-state-heading");
          const text = graphEmptyState.querySelector(".empty-state-text");
          if (heading) heading.textContent = "Validation Succeeded: Rejected Malformed Input";
          if (text) text.textContent = `Server correctly returned HTTP 400: "${data.detail || "Input text cannot be empty."}". UI remains responsive and free of stale state.`;
        }
        showNotification(`[TEST PASS] Rejected empty input: ${data.detail || "Validation Error"}`, "warning", 5000);
        return;
      }

      if (data.example && data.example.input_text) {
        queryInput.value = data.example.input_text;
        autoResize(queryInput);
      }

      if (data.session) {
        activeSessionId = data.session.id;
        renderSession(data.session);
        refreshSessionList();
        switchView("graph");
      }

      if (data.diagnostics && data.diagnostics.observations) {
        const obs = data.diagnostics.observations.join(" ");
        const isPassed = data.diagnostics.passed;
        showNotification(`[${data.example.title}] ${obs}`, isPassed ? "success" : "warning", 6000);
      }
    } catch (err) {
      showNotification(`Test execution failed: ${err.message}`, "error", 5000);
    } finally {
      hideProcessing();
    }
  }

  function showProcessing(msg) {
    processingText.textContent = msg;
    processingIndicator.classList.remove("hidden");
  }

  function hideProcessing() {
    processingIndicator.classList.add("hidden");
  }

  // Normalize API and session state data at the boundary
  function normalizeSessionData(data) {
    if (!data || typeof data !== "object") {
      return {
        id: null,
        nodes: [],
        relations: [],
        sentences: [],
        primary_prompt: "",
        physics_preset: "rubber_band",
        physics_tensions: {},
      };
    }

    const rawNodes = Array.isArray(data.nodes) ? data.nodes : [];
    const nodes = rawNodes.map((n, idx) => {
      const name = n.canonical_name || n.name || n.display_name || `node_${idx}`;
      return {
        ...n,
        id: n.id || `node_${idx}`,
        name: name,
        canonical_name: name,
        display_name: n.display_name || n.name || name,
        category: n.category || "Unclassified",
        category_confidence: typeof n.category_confidence === "number" ? n.category_confidence : 0.85,
        category_rationale: n.category_rationale || "",
        state: n.state || null,
        stateDelta: typeof n.state_delta === "number" ? n.state_delta : (typeof n.stateDelta === "number" ? n.stateDelta : null),
        evidence_sentence_ids: Array.isArray(n.evidence_sentence_ids) ? n.evidence_sentence_ids : [],
        in_degree: typeof n.in_degree === "number" ? n.in_degree : 0,
        out_degree: typeof n.out_degree === "number" ? n.out_degree : 0,
        fixed: !!n.fixed,
      };
    });

    const rawRelations = Array.isArray(data.relations) ? data.relations : [];
    const relations = rawRelations.map((r, idx) => {
      const cause = r.cause_name || r.source || r.cause || "Unknown";
      const effect = r.effect_name || r.target || r.effect || "Unknown";
      return {
        ...r,
        id: r.id || `rel_${idx}`,
        cause_name: cause,
        effect_name: effect,
        relation_type: r.relation_type || "causes",
        effect_polarity: r.effect_polarity || (r.is_negated ? "association" : "positive"),
        source_state: r.source_state || null,
        source_delta: typeof r.source_delta === "number" ? r.source_delta : null,
        target_state: r.target_state || null,
        target_delta: typeof r.target_delta === "number" ? r.target_delta : null,
        assertion_status: r.assertion_status || (r.is_negated ? "refuted" : "asserted"),
        status: r.status || (r.is_negated ? "REFUTED_NEGATION" : "MEASURED_FACT"),
        confidence: typeof r.confidence === "number" ? r.confidence : 0.85,
        uncertainty_score: typeof r.uncertainty_score === "number" ? r.uncertainty_score : 0.05,
        is_negated: !!r.is_negated,
        is_suppressed: !!r.is_suppressed,
        is_transitive: !!r.is_transitive,
        has_contradiction: !!r.has_contradiction,
        evidence: Array.isArray(r.evidence) ? r.evidence : [],
        evidence_sentence_ids: Array.isArray(r.evidence_sentence_ids) ? r.evidence_sentence_ids : [],
        tension_level: typeof r.tension_level === "number" ? r.tension_level : 1,
      };
    });

    return {
      ...data,
      nodes,
      relations,
      sentences: Array.isArray(data.sentences) ? data.sentences : [],
      physics_preset: data.physics_preset || "rubber_band",
      physics_tensions: data.physics_tensions && typeof data.physics_tensions === "object" ? data.physics_tensions : {},
    };
  }

  // Generate plain-text representation of the extracted graph
  function generateCopyableGraphText(data) {
    if (!data) return "No causal knowledge extracted yet.";
    const norm = normalizeSessionData(data);
    const lines = [];
    lines.push("================================================================================");
    lines.push(" EVRYN CAUSAL KNOWLEDGE EXTRACTION SUMMARY");
    lines.push("================================================================================");
    lines.push(`Session ID: ${norm.id || "N/A"}`);
    if (norm.primary_prompt) {
      lines.push(`Primary Specification:\n"${norm.primary_prompt}"`);
    } else if (norm.inputs && norm.inputs.length > 0) {
      lines.push(`Primary Specification:\n"${norm.inputs[0].content}"`);
    }
    const nodes = norm.nodes || [];
    const relations = norm.relations || [];
    lines.push(`Summary: ${nodes.length} Entities | ${relations.length} Causal Relations`);
    lines.push("");
    lines.push("--------------------------------------------------------------------------------");
    lines.push(" 1. CAUSAL RELATIONSHIPS");
    lines.push("--------------------------------------------------------------------------------");
    if (relations.length === 0) {
      lines.push("No causal relationships extracted.");
    } else {
      relations.forEach((r, idx) => {
        const pol = (r.effect_polarity || "positive").toUpperCase();
        const neg = r.is_negated ? "[NEGATED / DOES NOT CAUSE] " : "";
        const supp = r.is_suppressed ? " [DEFAULT: SUPPRESSED FROM GRAPH]" : "";
        lines.push(`${idx + 1}. ${r.cause_name} --> ${r.effect_name}`);
        lines.push(`   Assertion: ${neg}${r.relation_type} (${pol})${supp}`);
        lines.push(`   Status: ${r.status} | Confidence: ${(r.confidence * 100).toFixed(1)}% | Tension: ${r.tension_level || 1}`);
        if (r.directional_trend) {
          lines.push(`   Trend: ${r.directional_trend}`);
        }
        if (r.evidence && r.evidence.length > 0) {
          lines.push(`   Evidence: "${r.evidence[0].sentence_text}" (Page ${r.evidence[0].page_number || 1})`);
        }
        lines.push("");
      });
    }
    lines.push("--------------------------------------------------------------------------------");
    lines.push(" 2. EXTRACTED ENTITIES & CATEGORIES");
    lines.push("--------------------------------------------------------------------------------");
    if (nodes.length === 0) {
      lines.push("No entities identified.");
    } else {
      nodes.forEach((n) => {
        const cat = n.category || "Unclassified";
        const conf = ((n.category_confidence || 0.85) * 100).toFixed(0);
        const nodeName = n.canonical_name || n.name || n.display_name || "Unknown";
        let line = `- ${nodeName}: [${cat}] (Confidence: ${conf}%)`;
        if (n.state) {
          const dVal = typeof n.stateDelta === "number" ? n.stateDelta : (typeof n.state_delta === "number" ? n.state_delta : null);
          const deltaStr = (dVal != null && !isNaN(dVal)) ? ` (Δ = ${dVal > 0 ? "+" : ""}${dVal})` : "";
          line += ` | State: ${n.state}${deltaStr}`;
        }
        lines.push(line);
        if (n.category_rationale) {
          lines.push(`  Rationale: ${n.category_rationale}`);
        }
      });
    }
    lines.push("================================================================================");
    return lines.join("\n");
  }

  // Render Session Graph & Table
  function renderSession(data) {
    activeSessionData = normalizeSessionData(data);
    data = activeSessionData;
    resultsView.classList.remove("hidden");
    window.EVRYN_BG.setDimmed(true);

    // Synchronize query input with primary prompt
    if (data.primary_prompt) {
      queryInput.value = data.primary_prompt;
    } else if (data.inputs && data.inputs.length > 0) {
      queryInput.value = data.inputs[0].content;
    }
    autoResize(queryInput);
    regenerateBtn.classList.remove("hidden");

    // Render interactive sentence chips
    sentenceHighlighterBar.innerHTML = "";
    if (data.sentences && data.sentences.length > 0) {
      sentenceHighlighterBar.classList.remove("hidden");
      data.sentences.forEach((s) => {
        const chip = document.createElement("span");
        chip.className = "sentence-chip";
        chip.dataset.sentenceId = s.id;
        if (s.pastel_color) {
          chip.style.backgroundColor = s.pastel_color;
        }
        chip.textContent = `[S${s.sentence_index + 1}] ${s.text}`;
        chip.title = `Sentence ${s.sentence_index + 1}: Click/hover to highlight related graph nodes & edges`;

        chip.addEventListener("mouseenter", () => {
          chip.classList.add("active");
          graphRenderer.highlightSentenceElements(s.id);
        });
        chip.addEventListener("mouseleave", () => {
          chip.classList.remove("active");
          if (!chip.classList.contains("selected")) {
            graphRenderer.clearSentenceHighlights();
          }
        });
        chip.addEventListener("click", () => {
          const wasSelected = chip.classList.contains("selected");
          document.querySelectorAll(".sentence-chip").forEach(c => c.classList.remove("selected"));
          if (!wasSelected) {
            chip.classList.add("selected");
            graphRenderer.highlightSentenceElements(s.id);
          } else {
            graphRenderer.clearSentenceHighlights();
          }
        });
        sentenceHighlighterBar.appendChild(chip);
      });
    } else {
      sentenceHighlighterBar.classList.add("hidden");
    }

    // Sync physics preset if available
    if (data.physics_preset && physicsPresetSelect) {
      physicsPresetSelect.value = data.physics_preset;
      graphRenderer.setPhysicsPreset(data.physics_preset);
    }
    if (data.physics_tensions && graphRenderer.edgeTensions) {
      for (const [relId, tVal] of Object.entries(data.physics_tensions)) {
        graphRenderer.edgeTensions.set(relId, Number(tVal));
      }
    }

    const nodes = data.nodes || [];
    const relations = data.relations || [];

    if (nodes.length === 0) {
      if (graphEmptyState) {
        graphEmptyState.classList.remove("hidden");
        const heading = graphEmptyState.querySelector(".empty-state-heading");
        const text = graphEmptyState.querySelector(".empty-state-text");
        if (heading) heading.textContent = "No Causal Relations Extracted";
        if (text) text.textContent = "The provided specification yielded 0 extracted relations. Try testing an interactive case (Cases A–E) or expanding the text.";
      }
    } else {
      if (graphEmptyState) {
        graphEmptyState.classList.add("hidden");
      }
    }

    graphStats.textContent = `${nodes.length} NODES  |  ${relations.length} CAUSAL RELATIONS`;

    // Populate Table View (matches exactly all 9 <thead> columns)
    tableBody.innerHTML = "";
    for (const r of relations) {
      const tr = document.createElement("tr");
      const polarityBadge = r.effect_polarity === "negative"
        ? "<span style='color:#dc2626; font-weight:600;'>[NEGATIVE]</span>"
        : (r.effect_polarity === "association" ? "<span style='color:#64748b; font-weight:600;'>[ASSOC]</span>" : "<span style='color:#0f172a; font-weight:600;'>[POSITIVE]</span>");

      const suppressedNote = r.is_suppressed ? " <span style='color:#94a3b8; font-size:10px;'>[SUPPRESSED]</span>" : "";
      const assertionBadge = r.is_negated
        ? "<span style='color:#64748b; font-weight:600;'>[NEGATED]</span>"
        : "<span style='color:#16a34a; font-weight:600;'>[AFFIRMED]</span>";

      tr.innerHTML = `
        <td><strong>${r.cause_name}</strong></td>
        <td>${r.source_state ? `<span class="state-chip">${r.source_state}</span>` : "<span style='color:#94a3b8;'>—</span>"}</td>
        <td><strong>${r.is_negated ? "DOES NOT " : ""}${r.relation_type}</strong>${suppressedNote}</td>
        <td><strong>${r.effect_name}</strong></td>
        <td>${r.target_state ? `<span class="state-chip">${r.target_state}</span>` : "<span style='color:#94a3b8;'>—</span>"}</td>
        <td>${polarityBadge}</td>
        <td>${assertionBadge}</td>
        <td>${(r.confidence * 100).toFixed(0)}%</td>
        <td>${r.evidence ? r.evidence.length : 0} citation${(r.evidence && r.evidence.length === 1) ? "" : "s"}</td>
      `;
      tr.style.cursor = "pointer";
      tr.addEventListener("click", () => onSelectRelation(r));
      tableBody.appendChild(tr);
    }

    graphRenderer.setData(nodes, relations, {
      tensions: data.physics_tensions || {},
      preset: data.physics_preset || "rubber_band",
    });

    // If currently on copyable view, update text immediately
    if (!copyableView.classList.contains("hidden")) {
      copyableText.textContent = generateCopyableGraphText(data);
    }
  }

  // Render Batch Cards
  function renderBatchCards(docCards, combinedGraph) {
    batchSection.classList.remove("hidden");
    batchCards.innerHTML = "";

    for (const d of docCards) {
      const card = document.createElement("div");
      card.className = "doc-card";
      card.innerHTML = `
        <div class="doc-card-title" title="${d.filename}">${d.filename}</div>
        <div class="doc-card-meta">${d.relation_count} relations &bull; ${d.page_count} pages</div>
      `;
      card.addEventListener("click", () => {
        document.querySelectorAll(".doc-card").forEach((c) => c.classList.remove("active"));
        card.classList.add("active");
        graphRenderer.setData(d.nodes, d.relations);
        graphStats.textContent = `[${d.filename}] ${d.nodes.length} NODES  |  ${d.relations.length} RELATIONS`;
      });
      batchCards.appendChild(card);
    }

    toggleCombinedBtn.onclick = () => {
      document.querySelectorAll(".doc-card").forEach((c) => c.classList.remove("active"));
      renderSession(combinedGraph);
    };
  }

  // Selection Callbacks
  function onSelectRelation(rel) {
    selectedRelation = rel;
    const curTension = graphRenderer.getEdgeTension(rel.id);
    updateTensionBadge(curTension);

    // Highlight incident sentence chips
    document.querySelectorAll(".sentence-chip").forEach((c) => c.classList.remove("highlighted"));
    if (rel.evidence_sentence_ids && rel.evidence_sentence_ids.length > 0) {
      rel.evidence_sentence_ids.forEach((sid) => {
        const chip = sentenceHighlighterBar.querySelector(`[data-sentence-id="${sid}"]`);
        if (chip) chip.classList.add("highlighted");
      });
    }

    openInspector();
    let evHtml = "";

    const evList = rel.evidence || [];
    if (evList.length === 0) {
      evHtml = "<p style='color:#666;'>No textual citations recorded.</p>";
    } else {
      for (const ev of evList) {
        evHtml += `
          <div class="evidence-card">
            <div class="evidence-header">
              <span>${ev.filename || "Input"} &bull; Page ${ev.page_number}</span>
              <span>${ev.evidence_status}</span>
            </div>
            <div class="evidence-quote">“${ev.sentence_text}”</div>
            <div class="evidence-meta">Section: ${ev.section_title || "Results"} &bull; Offsets: [${ev.char_start}:${ev.char_end}]</div>
          </div>
        `;
      }
    }

    const polarityColor = rel.effect_polarity === "negative" ? "#dc2626" : (rel.effect_polarity === "association" ? "#64748b" : "#0f172a");
    const polarityLabel = rel.effect_polarity === "negative"
      ? "NEGATIVE EFFECT (causes reduction / inverse)"
      : (rel.effect_polarity === "association" ? "ASSOCIATION (non-directional correlation)" : "POSITIVE EFFECT (causes induction / direct)");

    inspectorBody.innerHTML = `
      <div style="margin-bottom:16px;">
        <div style="display:inline-block; font-size:10px; font-weight:700; font-family:var(--font-mono); color:${polarityColor}; padding:2px 6px; border:1px solid ${polarityColor}; border-radius:3px; margin-bottom:8px;">
          ${polarityLabel}
        </div>
        <div style="font-size:16px; font-weight:700;">
          ${rel.cause_name}${rel.source_state ? ` <span style="font-size:12px; font-weight:500; color:#555;">[State: ${rel.source_state}]</span>` : ""}
        </div>
        <div style="font-family:var(--font-mono); font-size:11px; margin:4px 0; color:#444;">
          ${rel.is_negated ? "[REFUTED / NEGATED] " : ""}${rel.relation_type} &bull; ${rel.is_transitive ? "TRANSITIVE" : "DIRECT"}
        </div>
        <div style="font-size:16px; font-weight:700;">
          &darr; ${rel.effect_name}${rel.target_state ? ` <span style="font-size:12px; font-weight:500; color:#555;">[State: ${rel.target_state}]</span>` : ""}
        </div>
      </div>
      <div style="font-size:11px; font-family:var(--font-mono); margin-bottom:12px;">
        Confidence: ${(rel.confidence * 100).toFixed(1)}% &bull; Uncertainty: ${rel.uncertainty_score} &bull; Tension: ${curTension}
        ${rel.is_suppressed ? "<br/><span style='color:#64748b; font-weight:600;'>[SUPPRESSED FROM GRAPH: Negated claim]</span>" : ""}
        ${rel.has_contradiction ? "<br/><span style='color:#dc2626; font-weight:700;'>[CONTRADICTORY EVIDENCE DETECTED]</span>" : ""}
      </div>
      <hr style="border:none; border-top:1px solid #e2e8f0; margin:12px 0;" />
      <div style="font-weight:700; font-size:11px; font-family:var(--font-mono); margin-bottom:8px;">GROUNDED EVIDENCE (${evList.length}):</div>
      ${evHtml}
    `;
  }

  function onSelectNode(node) {
    selectedRelation = null;
    updateTensionBadge(1);

    // Highlight incident sentence chips
    document.querySelectorAll(".sentence-chip").forEach((c) => c.classList.remove("highlighted"));
    if (node.evidence_sentence_ids && node.evidence_sentence_ids.length > 0) {
      node.evidence_sentence_ids.forEach((sid) => {
        const chip = sentenceHighlighterBar.querySelector(`[data-sentence-id="${sid}"]`);
        if (chip) chip.classList.add("highlighted");
      });
    }

    openInspector();

    const nodeName = node.canonical_name || node.name || node.display_name || "Unknown";
    const inc = ((activeSessionData && activeSessionData.relations) || []).filter((r) => r.effect_name === nodeName);
    const out = ((activeSessionData && activeSessionData.relations) || []).filter((r) => r.cause_name === nodeName);

    let incHtml = inc.map((r) => `<li>${r.cause_name} &rarr; <em>${r.relation_type}</em></li>`).join("");
    let outHtml = out.map((r) => `<li><em>${r.relation_type}</em> &rarr; ${r.effect_name}</li>`).join("");

    const currentCat = node.category || "Unclassified";
    const categories = [
      "Measured Outcome",
      "Environmental Factor",
      "Experimental Condition",
      "Gene/Protein",
      "Chemical",
      "Biological Process",
      "Phenotype",
      "Unclassified",
    ];

    const catOptions = categories
      .map((c) => `<option value="${c}" ${c === currentCat ? "selected" : ""}>${c}</option>`)
      .join("");

    const dVal = typeof node.stateDelta === "number" ? node.stateDelta : (typeof node.state_delta === "number" ? node.state_delta : null);
    const deltaStr = (dVal != null && !isNaN(dVal)) ? ` (Δ = ${dVal > 0 ? "+" : ""}${dVal})` : "";
    const stateBadge = node.state ? `<span style="font-size:10px; font-weight:700; font-family:var(--font-mono); background:#fef2f2; color:#b91c1c; padding:2px 6px; border-radius:3px;">STATE: ${node.state}${deltaStr}</span>` : "";

    inspectorBody.innerHTML = `
      <div style="margin-bottom:8px;">
        <div style="display:flex; align-items:center; gap:6px; margin-bottom:6px;">
          <span style="font-size:10px; font-weight:700; font-family:var(--font-mono); color:#475569;">CATEGORY:</span>
          <select id="node-cat-override-select" class="toolbar-select" style="font-size:11px; padding:2px 4px;">
            ${catOptions}
          </select>
        </div>
        ${node.category_confidence ? `<div style="font-family:var(--font-mono); font-size:10px; color:#64748b; margin-bottom:4px;">Confidence: ${(node.category_confidence * 100).toFixed(0)}% ${node.category_rationale ? `&bull; ${node.category_rationale}` : ""}</div>` : ""}
        ${stateBadge}
      </div>
      <div style="font-size:18px; font-weight:700; margin-bottom:4px;">${nodeName}</div>
      <div style="font-family:var(--font-mono); font-size:11px; color:#555; margin-bottom:12px;">
        In-Degree: ${inc.length} &bull; Out-Degree: ${out.length}
      </div>
      <hr style="border:none; border-top:1px solid #e2e8f0; margin:12px 0;" />
      <div style="font-weight:700; font-size:11px; font-family:var(--font-mono); margin-bottom:6px;">INCOMING CAUSAL INFLUENCES:</div>
      <ul style="padding-left:18px; margin-bottom:16px; font-size:12px;">${incHtml || "<li>None</li>"}</ul>
      <div style="font-weight:700; font-size:11px; font-family:var(--font-mono); margin-bottom:6px;">OUTGOING CAUSAL TARGETS:</div>
      <ul style="padding-left:18px; font-size:12px;">${outHtml || "<li>None</li>"}</ul>
    `;

    const catSelect = document.getElementById("node-cat-override-select");
    if (catSelect) {
      catSelect.addEventListener("change", async (e) => {
        const newCat = e.target.value;
        if (!activeSessionId) return;
        try {
          const res = await fetch(`/api/nodes/${activeSessionId}/${encodeURIComponent(node.canonical_name || node.name)}/override-category`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ category: newCat, rationale: "User manual override" }),
          });
          if (res.ok) {
            const updated = await res.json();
            renderSession(updated);
          }
        } catch (err) {
          console.warn("Category override failed:", err);
        }
      });
    }
  }

  closeInspectorBtn.addEventListener("click", () => closeInspector());

  // Layout Persistence Callback
  async function onLayoutChanged(posMap) {
    if (!activeSessionId) return;
    try {
      await fetch(`/api/sessions/${activeSessionId}/layout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ positions: posMap }),
      });
    } catch (e) {
      console.warn("Failed to persist layout:", e);
    }
  }

  // Sidebar & Sessions
  toggleSidebarBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    closeSidebar();
  });

  openSidebarBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    openSidebar();
  });

  newSessionBtn.addEventListener("click", () => {
    activeSessionId = null;
    activeSessionData = null;
    switchView("graph");
    undockInput();
  });

  function updateBulkDeleteState() {
    const count = selectedSessionIds.size;
    if (sessionBulkDeleteBtn) {
      sessionBulkDeleteBtn.disabled = count === 0;
      sessionBulkDeleteBtn.textContent = `Delete (${count})`;
    }
    const allBoxes = sessionList.querySelectorAll(".session-select-cb");
    if (sessionSelectAllCb && allBoxes.length > 0) {
      sessionSelectAllCb.checked = count === allBoxes.length;
      sessionSelectAllCb.indeterminate = count > 0 && count < allBoxes.length;
    }
  }

  if (sessionSelectAllCb) {
    sessionSelectAllCb.addEventListener("change", () => {
      const allBoxes = sessionList.querySelectorAll(".session-select-cb");
      if (sessionSelectAllCb.checked) {
        allBoxes.forEach(cb => {
          cb.checked = true;
          selectedSessionIds.add(cb.dataset.id);
        });
      } else {
        allBoxes.forEach(cb => {
          cb.checked = false;
        });
        selectedSessionIds.clear();
      }
      updateBulkDeleteState();
    });
  }

  if (sessionDedupBtn) {
    sessionDedupBtn.addEventListener("click", async () => {
      showProcessing("DEDUPLICATING SESSIONS...");
      try {
        const res = await fetch("/api/sessions/deduplicate", { method: "POST" });
        if (!res.ok) throw new Error("Deduplication failed");
        const data = await res.json();
        if (data.deleted_ids && data.deleted_ids.includes(activeSessionId)) {
          activeSessionId = null;
          undockInput();
        }
        selectedSessionIds.clear();
        await refreshSessionList();
      } catch (err) {
        alert("Deduplication failed: " + err.message);
      } finally {
        hideProcessing();
      }
    });
  }

  if (sessionBulkDeleteBtn) {
    sessionBulkDeleteBtn.addEventListener("click", async () => {
      const count = selectedSessionIds.size;
      if (count === 0) return;
      if (!confirm(`Are you sure you want to delete ${count} selected session(s)? This action cannot be undone.`)) {
        return;
      }
      showProcessing(`DELETING ${count} SESSIONS...`);
      try {
        const res = await fetch("/api/sessions/bulk-delete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_ids: Array.from(selectedSessionIds) }),
        });
        if (!res.ok) throw new Error("Bulk delete failed");
        if (selectedSessionIds.has(activeSessionId)) {
          activeSessionId = null;
          undockInput();
        }
        selectedSessionIds.clear();
        await refreshSessionList();
      } catch (err) {
        alert("Bulk delete failed: " + err.message);
      } finally {
        hideProcessing();
      }
    });
  }

  if (sessionClearAllBtn) {
    sessionClearAllBtn.addEventListener("click", clearAllSessionsPrompt);
  }

  async function refreshSessionList() {
    try {
      const res = await fetch("/api/sessions");
      if (!res.ok) return;
      const sessions = await res.json();
      sessionCountLabel.textContent = `${sessions.length} sessions`;
      sessionList.innerHTML = "";

      const existingIds = new Set(sessions.map(s => s.id));
      for (const id of Array.from(selectedSessionIds)) {
        if (!existingIds.has(id)) {
          selectedSessionIds.delete(id);
        }
      }

      for (const s of sessions) {
        const li = document.createElement("li");
        const isChecked = selectedSessionIds.has(s.id);
        li.className = `session-item ${s.id === activeSessionId ? "active" : ""}`;
        li.innerHTML = `
          <input type="checkbox" class="session-select-cb" data-id="${s.id}" ${isChecked ? "checked" : ""} aria-label="Select session ${escapeHtml(s.title)}">
          <div class="session-info">
            <div class="session-title-text">${escapeHtml(s.title)}</div>
            <div class="session-meta-text">${s.node_count || 0} nodes &bull; ${s.relation_count || 0} relations &bull; ${s.updated_at.slice(0, 10)}</div>
          </div>
          <button class="session-delete-btn" title="Delete session" aria-label="Delete session">&times;</button>
        `;

        const cb = li.querySelector(".session-select-cb");
        cb.addEventListener("click", (e) => {
          e.stopPropagation();
          if (cb.checked) {
            selectedSessionIds.add(s.id);
          } else {
            selectedSessionIds.delete(s.id);
          }
          updateBulkDeleteState();
        });

        li.querySelector(".session-info").addEventListener("click", () => loadSession(s.id));
        li.querySelector(".session-delete-btn").addEventListener("click", (e) => {
          e.stopPropagation();
          deleteSession(s.id);
        });

        sessionList.appendChild(li);
      }
      updateBulkDeleteState();
    } catch (e) {
      console.warn("Failed to load sessions:", e);
    }
  }

  async function loadSession(sessionId) {
    showProcessing("RESTORING SESSION GRAPH & EVIDENCE...");
    try {
      const res = await fetch(`/api/sessions/${sessionId}`);
      if (!res.ok) throw new Error("Could not load session");
      const data = await res.json();
      activeSessionId = data.id;
      dockInput();
      renderSession(data);
      refreshSessionList();
    } catch (err) {
      alert(err.message);
    } finally {
      hideProcessing();
    }
  }

  async function deleteSession(sessionId) {
    try {
      const res = await fetch(`/api/sessions/${sessionId}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete session");
      selectedSessionIds.delete(sessionId);
      if (activeSessionId === sessionId) {
        activeSessionId = null;
        undockInput();
      }
      refreshSessionList();
    } catch (err) {
      alert(err.message);
    }
  }

  // ==========================================================================
  // Phase 2: Real-Paper Causal Evaluation Examples Tab & Preview Modal
  // ==========================================================================

  let activeExamplesSubnav = "pdf";
  let cachedPdfExamples = [];
  let cachedTextExamples = [];
  let cachedMultipageExamples = [];
  let activeModalPaperId = null;

  function switchExamplesSubnav(subnav) {
    activeExamplesSubnav = subnav;
    if (subnavTestcases) subnavTestcases.classList.toggle("active", subnav === "testcases");
    if (subnavPdf) subnavPdf.classList.toggle("active", subnav === "pdf");
    if (subnavText) subnavText.classList.toggle("active", subnav === "text");
    if (subnavMultipage) subnavMultipage.classList.toggle("active", subnav === "multipage");

    if (subviewTestcases) subviewTestcases.classList.toggle("hidden", subnav !== "testcases");
    if (subviewPdf) subviewPdf.classList.toggle("hidden", subnav !== "pdf");
    if (subviewText) subviewText.classList.toggle("hidden", subnav !== "text");
    if (subviewMultipage) subviewMultipage.classList.toggle("hidden", subnav !== "multipage");

    loadExamplesSection(subnav);
  }

  if (subnavTestcases) subnavTestcases.addEventListener("click", () => switchExamplesSubnav("testcases"));
  if (subnavPdf) subnavPdf.addEventListener("click", () => switchExamplesSubnav("pdf"));
  if (subnavText) subnavText.addEventListener("click", () => switchExamplesSubnav("text"));
  if (subnavMultipage) subnavMultipage.addEventListener("click", () => switchExamplesSubnav("multipage"));

  if (splitFilterSelect) {
    splitFilterSelect.addEventListener("change", () => loadExamplesSection(activeExamplesSubnav));
  }

  if (examplesSearchInput) {
    examplesSearchInput.addEventListener("input", () => filterCurrentExamples());
  }

  function renderTestcasesCards(examples) {
    if (!testcasesCardsList) return;
    testcasesCardsList.innerHTML = "";
    examples.forEach((ex) => {
      const card = document.createElement("div");
      card.className = "testcase-card";
      card.innerHTML = `
        <div class="testcase-card-header">
          <span class="testcase-card-title">${escapeHtml(ex.title)}</span>
          <span class="testcase-card-cat">${escapeHtml(ex.category)}</span>
        </div>
        <div class="testcase-passage">${escapeHtml(ex.input_text.trim() || "[EMPTY STRING / MALFORMED INPUT]")}</div>
        <div class="testcase-meta-row">
          <div><strong>TEST PURPOSE:</strong> ${escapeHtml(ex.description)}</div>
          <div><strong>EXPECTED BEHAVIOR:</strong> ${escapeHtml(ex.expected_behavior)}</div>
          <div><strong>SCIENTIFIC CONTEXT:</strong> ${escapeHtml(ex.scientific_context)}</div>
        </div>
        <div class="pdf-card-actions">
          <button class="btn-card-action btn-card-primary" data-action="run-testcase">⚡ Run Test Case in Workspace</button>
        </div>
      `;
      card.querySelector('[data-action="run-testcase"]').addEventListener("click", () => {
        loadAndRunTestCase(ex.id);
      });
      testcasesCardsList.appendChild(card);
    });
  }

  function safeExtractList(data, key) {
    if (Array.isArray(data)) return data;
    if (data && typeof data === "object") {
      if (key && Array.isArray(data[key])) return data[key];
      if (Array.isArray(data.papers)) return data.papers;
      if (Array.isArray(data.items)) return data.items;
      if (Array.isArray(data.examples)) return data.examples;
    }
    return [];
  }

  function renderLoadError(container, msg, retryFn) {
    if (!container) return;
    container.innerHTML = `
      <div class="empty-state error-state" style="padding: 24px; text-align: center;">
        <p style="color: #dc2626; font-weight: 500; margin-bottom: 12px;">Failed to load real-paper benchmark examples: ${escapeHtml(msg || "Network error")}</p>
        <button class="action-btn-primary retry-btn" style="padding: 6px 16px; font-size: 12px; cursor: pointer;">Retry Loading</button>
      </div>
    `;
    const btn = container.querySelector(".retry-btn");
    if (btn && retryFn) {
      btn.addEventListener("click", retryFn);
    }
  }

  async function loadExamplesSection(subnav) {
    const split = splitFilterSelect ? splitFilterSelect.value : "all";
    const splitQuery = split !== "all" ? `?split=${split}` : "";

    try {
      if (subnav === "testcases") {
        if (testcasesCardsList) testcasesCardsList.innerHTML = `<div class="loading-state">Loading diagnostic test suite...</div>`;
        const res = await fetch("/api/test-examples");
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        const data = await res.json();
        renderTestcasesCards(data.examples || []);
      } else if (subnav === "pdf") {
        if (pdfCardsGrid) pdfCardsGrid.innerHTML = `<div class="loading-state">Loading authentic real-paper benchmarks...</div>`;
        const res = await fetch(`/api/examples/pdf${splitQuery}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        const data = await res.json();
        cachedPdfExamples = safeExtractList(data, "papers");
        renderPdfCards(cachedPdfExamples);
      } else if (subnav === "text") {
        if (textCardsList) textCardsList.innerHTML = `<div class="loading-state">Loading annotated passage examples...</div>`;
        const res = await fetch(`/api/examples/text${splitQuery}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        const data = await res.json();
        cachedTextExamples = safeExtractList(data, "examples");
        renderTextCards(cachedTextExamples);
      } else if (subnav === "multipage") {
        if (multipageCardsList) multipageCardsList.innerHTML = `<div class="loading-state">Loading cross-sentence & cross-page examples...</div>`;
        const res = await fetch(`/api/examples/multipage${splitQuery}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        const data = await res.json();
        cachedMultipageExamples = safeExtractList(data, "examples");
        renderMultipageCards(cachedMultipageExamples);
      }
    } catch (err) {
      console.error("Failed to load examples section:", err);
      const targetContainer = subnav === "testcases" ? testcasesCardsList : (subnav === "pdf" ? pdfCardsGrid : (subnav === "text" ? textCardsList : multipageCardsList));
      renderLoadError(targetContainer, err.message, () => loadExamplesSection(subnav));
    }
  }

  function filterCurrentExamples() {
    const q = (examplesSearchInput ? examplesSearchInput.value : "").toLowerCase().trim();
    if (activeExamplesSubnav === "pdf") {
      const filtered = cachedPdfExamples.filter(p =>
        !q || p.pmcid.toLowerCase().includes(q) || p.title.toLowerCase().includes(q) || (p.doi && p.doi.toLowerCase().includes(q))
      );
      renderPdfCards(filtered);
    } else if (activeExamplesSubnav === "text") {
      const filtered = cachedTextExamples.filter(t =>
        !q || t.pmcid.toLowerCase().includes(q) || t.passage_text.toLowerCase().includes(q) || t.gold_cause.toLowerCase().includes(q) || t.gold_effect.toLowerCase().includes(q)
      );
      renderTextCards(filtered);
    } else if (activeExamplesSubnav === "multipage") {
      const filtered = cachedMultipageExamples.filter(m =>
        !q || m.pmcid.toLowerCase().includes(q) || m.cause_concept.toLowerCase().includes(q) || m.effect_concept.toLowerCase().includes(q)
      );
      renderMultipageCards(filtered);
    }
  }

  function renderPdfCards(papers) {
    if (!pdfCardsGrid) return;
    if (!papers || papers.length === 0) {
      pdfCardsGrid.innerHTML = `<div class="empty-state">No papers found matching criteria.</div>`;
      return;
    }

    pdfCardsGrid.innerHTML = "";
    papers.forEach(p => {
      const card = document.createElement("div");
      card.className = "pdf-card";

      const authorsStr = p.authors && p.authors.length ? p.authors.slice(0, 3).join(", ") + (p.authors.length > 3 ? " et al." : "") : "Research Team";
      const dm = p.direct_metrics || { precision: 0, recall: 0, f1: 0, tp: 0, fp: 0, fn: 0 };
      const cm = p.cross_page_metrics || { precision: 0, recall: 0, f1: 0, tp: 0, fp: 0, fn: 0 };

      card.innerHTML = `
        <div>
          <div class="pdf-card-header">
            <div>
              <span class="pdf-card-journal">${escapeHtml(p.journal || "PubMed Central")} &bull; ${p.page_count} PAGES</span>
              <div class="pdf-card-title">${escapeHtml(p.title)}</div>
              <div class="pdf-card-authors">${escapeHtml(authorsStr)}</div>
            </div>
            <span class="badge-split split-${p.split}">${p.split.replace("_", " ")}</span>
          </div>

          <table class="pdf-metrics-table" style="margin-top: 10px;">
            <thead>
              <tr>
                <th>METRIC EVALUATION</th>
                <th>PRECISION</th>
                <th>RECALL</th>
                <th>F1 SCORE</th>
                <th>DENOMINATOR COUNTS</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><b>Direct Causal F1</b></td>
                <td>${(dm.precision * 100).toFixed(1)}%</td>
                <td>${(dm.recall * 100).toFixed(1)}%</td>
                <td><span class="f1-badge ${dm.f1 > 0.6 ? 'f1-high' : 'f1-med'}">${dm.f1.toFixed(4)}</span></td>
                <td><small>${dm.denominator_explanation || `TP=${dm.tp}`}</small></td>
              </tr>
              <tr>
                <td><b>Cross-Page Causal F1</b></td>
                <td>${(cm.precision * 100).toFixed(1)}%</td>
                <td>${(cm.recall * 100).toFixed(1)}%</td>
                <td><span class="f1-badge ${cm.f1 > 0.5 ? 'f1-high' : 'f1-med'}">${cm.f1.toFixed(4)}</span></td>
                <td><small>${cm.denominator_explanation || `TP=${cm.tp}`}</small></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="pdf-card-actions">
          <button class="btn-card-action btn-card-primary" data-action="view-pdf" data-pmcid="${p.pmcid}">📄 View Multi-Page PDF</button>
          <button class="btn-card-action" data-action="inspect" data-pmcid="${p.pmcid}">🔍 Inspect Relations</button>
          <button class="btn-card-action" data-action="load-workspace" data-pmcid="${p.pmcid}">⚡ Load into Workspace</button>
        </div>
      `;

      card.querySelector('[data-action="view-pdf"]').addEventListener("click", () => openPaperModal(p.pmcid, "pdf"));
      card.querySelector('[data-action="inspect"]').addEventListener("click", () => openPaperModal(p.pmcid, "causal"));
      card.querySelector('[data-action="load-workspace"]').addEventListener("click", () => loadPaperToWorkspace(p.pmcid, p.title));

      pdfCardsGrid.appendChild(card);
    });
  }

  function renderTextCards(passages) {
    if (!textCardsList) return;
    if (!passages || passages.length === 0) {
      textCardsList.innerHTML = `<div class="empty-state">No passage examples found matching criteria.</div>`;
      return;
    }

    textCardsList.innerHTML = "";
    passages.forEach(t => {
      const card = document.createElement("div");
      card.className = "text-card";

      const isTp = t.match_status === "TRUE_POSITIVE";
      const pillClass = isTp ? "pill-tp" : "pill-fn";
      const pillLabel = isTp ? "TRUE POSITIVE MATCH" : "FALSE NEGATIVE / UNMATCHED";

      card.innerHTML = `
        <div class="text-card-header">
          <div>
            <span class="pdf-card-journal">${escapeHtml(t.pmcid)} &bull; Section: ${escapeHtml(t.section)}</span>
            <span class="badge-split split-${t.split}" style="margin-left: 6px;">${t.split}</span>
          </div>
          <span class="pill-match ${pillClass}">${pillLabel}</span>
        </div>

        <div class="text-passage">"${escapeHtml(t.passage_text)}"</div>

        <div class="gold-comparison-row">
          <div class="comp-col">
            <span class="comp-label">GOLD CAUSE:</span>
            <span class="comp-val">${escapeHtml(t.gold_cause)}</span>
          </div>
          <div class="comp-col">
            <span class="comp-label">GOLD EFFECT:</span>
            <span class="comp-val">${escapeHtml(t.gold_effect)}</span>
          </div>
          <div class="comp-col">
            <span class="comp-label">RELATION TYPE:</span>
            <span class="comp-val">${escapeHtml(t.gold_relation_type)}</span>
          </div>
          <div class="comp-col">
            <span class="comp-label">EVRYN EXTRACTION:</span>
            <span class="comp-val">${escapeHtml(t.model_prediction)}</span>
          </div>
        </div>

        <div style="font-size: 11px; color: #64748b;">
          <b>Diagnostic:</b> ${escapeHtml(t.diagnostic)}
        </div>

        <div class="pdf-card-actions">
          <button class="btn-card-action btn-card-primary" data-action="load-text">⚡ Test Passage in Workspace</button>
          <button class="btn-card-action" data-action="open-paper" data-pmcid="${t.pmcid}">📄 View Full Paper (${t.pmcid})</button>
        </div>
      `;

      card.querySelector('[data-action="load-text"]').addEventListener("click", () => {
        activeSessionId = null;
        queryInput.value = t.passage_text;
        autoResize(queryInput);
        switchView("graph");
        submitQuery(t.passage_text);
      });

      card.querySelector('[data-action="open-paper"]').addEventListener("click", () => {
        openPaperModal(t.pmcid, "text");
      });

      textCardsList.appendChild(card);
    });
  }

  function renderMultipageCards(chains) {
    if (!multipageCardsList) return;
    if (!chains || chains.length === 0) {
      multipageCardsList.innerHTML = `<div class="empty-state">No multipage relations found matching criteria.</div>`;
      return;
    }

    multipageCardsList.innerHTML = "";
    chains.forEach(m => {
      const card = document.createElement("div");
      card.className = "multipage-card";

      card.innerHTML = `
        <div class="text-card-header">
          <div>
            <span class="pdf-card-journal">${escapeHtml(m.pmcid)} &bull; ${escapeHtml(m.paper_title)}</span>
            <span class="badge-split split-${m.split}" style="margin-left: 6px;">${m.split}</span>
          </div>
          <span class="pill-match pill-tp">${m.example_type.replace('_', ' ').toUpperCase()}</span>
        </div>

        <div class="multipage-chain-wrap">
          <div class="chain-node-box">
            <div class="chain-node-header">
              <span>UPSTREAM CAUSE</span>
              <span>${escapeHtml(m.cause_location)}</span>
            </div>
            <div class="chain-node-concept">${escapeHtml(m.cause_concept)}</div>
            <div class="chain-node-passage">"${escapeHtml(m.cause_passage)}"</div>
          </div>

          <div class="chain-arrow">⤏</div>

          <div class="chain-node-box">
            <div class="chain-node-header">
              <span>DISTAL EFFECT</span>
              <span>${escapeHtml(m.effect_location)}</span>
            </div>
            <div class="chain-node-concept">${escapeHtml(m.effect_concept)}</div>
            <div class="chain-node-passage">"${escapeHtml(m.effect_passage)}"</div>
          </div>
        </div>

        <div style="font-size: 11px; color: #334155;">
          <b>Bridge Mechanism:</b> ${escapeHtml(m.bridge_mechanism)}
          <br>
          <b>Diagnostic:</b> ${escapeHtml(m.diagnostic)}
        </div>

        <div class="pdf-card-actions">
          <button class="btn-card-action btn-card-primary" data-action="view-pdf" data-pmcid="${m.pmcid}">📄 View Multi-Page PDF</button>
          <button class="btn-card-action" data-action="load-workspace" data-pmcid="${m.pmcid}">⚡ Load Paper into Workspace</button>
        </div>
      `;

      card.querySelector('[data-action="view-pdf"]').addEventListener("click", () => openPaperModal(m.pmcid, "pdf"));
      card.querySelector('[data-action="load-workspace"]').addEventListener("click", () => loadPaperToWorkspace(m.pmcid, m.paper_title));

      multipageCardsList.appendChild(card);
    });
  }

  // Paper Detail & PDF Modal Logic
  async function openPaperModal(pmcid, initialTab = "pdf") {
    activeModalPaperId = pmcid;
    if (!paperModal) return;

    paperModal.classList.remove("hidden");
    if (paperModalTitle) paperModalTitle.textContent = `Loading ${pmcid}...`;

    if (paperPdfIframe) {
      paperPdfIframe.src = `/api/examples/paper/${pmcid}/pdf`;
    }

    switchPaperModalTab(initialTab);

    try {
      const res = await fetch(`/api/examples/paper/${pmcid}`);
      const data = await res.json();

      if (paperModalTitle) paperModalTitle.textContent = `${pmcid}: ${data.metadata.title}`;
      if (paperModalBadge) {
        paperModalBadge.className = `badge-split split-${data.metadata.split}`;
        paperModalBadge.textContent = data.metadata.split.toUpperCase();
      }

      // Populate Section Text
      if (paperTextWrap) {
        paperTextWrap.innerHTML = data.sections.map(s => `
          <div style="margin-bottom: 14px;">
            <h4 style="font-size: 13px; font-weight: 700; color: #0f172a; margin-bottom: 6px;">${escapeHtml(s.title)} (${s.type})</h4>
            ${s.paragraphs.map(p => `<p style="font-size: 12px; line-height: 1.5; color: #334155; margin-bottom: 6px;">${escapeHtml(p)}</p>`).join("")}
          </div>
        `).join("");
      }

      // Populate Causal Comparison
      if (paperCausalWrap) {
        const goldRows = data.gold_relations.map(r => `
          <tr>
            <td><b>${escapeHtml(r.cause)}</b></td>
            <td>&rarr;</td>
            <td><b>${escapeHtml(r.effect)}</b></td>
            <td>${escapeHtml(r.rel_type)}</td>
            <td>${escapeHtml(r.section)}</td>
          </tr>
        `).join("");

        const predRows = data.predicted_assertions.map(a => `
          <tr>
            <td><b>${escapeHtml(a.cause)}</b></td>
            <td>&rarr;</td>
            <td><b>${escapeHtml(a.effect)}</b></td>
            <td>${escapeHtml(a.polarity)}</td>
            <td>${(a.confidence * 100).toFixed(0)}%</td>
          </tr>
        `).join("");

        paperCausalWrap.innerHTML = `
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
            <div>
              <h4 style="font-size: 12px; font-weight: 700; color: #0f172a; margin-bottom: 8px;">GOLD ANNOTATIONS (${data.gold_relations.length})</h4>
              <table class="pdf-metrics-table">
                <thead><tr><th>Cause</th><th></th><th>Effect</th><th>Type</th><th>Section</th></tr></thead>
                <tbody>${goldRows || '<tr><td colspan="5">No annotated relations.</td></tr>'}</tbody>
              </table>
            </div>
            <div>
              <h4 style="font-size: 12px; font-weight: 700; color: #0f172a; margin-bottom: 8px;">EVRYN MODEL EXTRACTIONS (${data.predicted_assertions.length})</h4>
              <table class="pdf-metrics-table">
                <thead><tr><th>Cause</th><th></th><th>Effect</th><th>Polarity</th><th>Conf</th></tr></thead>
                <tbody>${predRows || '<tr><td colspan="5">No extractions.</td></tr>'}</tbody>
              </table>
            </div>
          </div>
        `;
      }
    } catch (err) {
      console.error("Failed to load paper details:", err);
    }
  }

  function switchPaperModalTab(tab) {
    if (paperTabPdf) paperTabPdf.classList.toggle("active", tab === "pdf");
    if (paperTabText) paperTabText.classList.toggle("active", tab === "text");
    if (paperTabCausal) paperTabCausal.classList.toggle("active", tab === "causal");

    if (paperPdfFrameWrap) paperPdfFrameWrap.classList.toggle("hidden", tab !== "pdf");
    if (paperTextWrap) paperTextWrap.classList.toggle("hidden", tab !== "text");
    if (paperCausalWrap) paperCausalWrap.classList.toggle("hidden", tab !== "causal");
  }

  if (paperTabPdf) paperTabPdf.addEventListener("click", () => switchPaperModalTab("pdf"));
  if (paperTabText) paperTabText.addEventListener("click", () => switchPaperModalTab("text"));
  if (paperTabCausal) paperTabCausal.addEventListener("click", () => switchPaperModalTab("causal"));

  if (closePaperModalBtn) {
    closePaperModalBtn.addEventListener("click", () => {
      if (paperModal) paperModal.classList.add("hidden");
      if (paperPdfIframe) paperPdfIframe.src = "";
    });
  }

  async function loadPaperToWorkspace(pmcid, title) {
    showProcessing(`INGESTING & EXTRACTING REAL PAPER ${pmcid}...`);
    if (paperModal) paperModal.classList.add("hidden");

    try {
      const res = await fetch("/api/examples/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pmcid, title }),
      });
      if (!res.ok) throw new Error("Failed to load paper to workspace");
      const data = await res.json();
      activeSessionId = data.session_id;
      activeSessionData = data;
      dockInput();
      renderSession(data);
      refreshSessionList();
      switchView("graph");
    } catch (err) {
      showNotification("Failed to load paper to workspace: " + err.message, "error", 5000);
    } finally {
      hideProcessing();
    }
  }

  if (loadPaperWorkspaceBtn) {
    loadPaperWorkspaceBtn.addEventListener("click", () => {
      if (activeModalPaperId) {
        loadPaperToWorkspace(activeModalPaperId, `Paper ${activeModalPaperId}`);
      }
    });
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  // Benchmark Verification Action
  async function runBenchmarkVerification() {
    showProcessing("EVALUATING MODEL AGAINST PMC BENCHMARK...");
    try {
      const res = await fetch("/api/evaluate", { method: "POST" });
      const data = await res.json();
      alert(
        `Benchmark Evaluation Complete:\n\n` +
        `Direct F1: ${data.metrics.direct_f1.toFixed(4)}\n` +
        `Cross-Page F1: ${data.metrics.cross_page_f1.toFixed(4)}\n` +
        `Exact Structural Match: ${data.metrics.exact_structural_match.toFixed(4)}\n` +
        `Provenance Grounding: ${(data.metrics.provenance_grounding_rate * 100).toFixed(0)}%\n` +
        `False Transitive Reduction: ${data.metrics.false_transitive_jumps_reduced_pct.toFixed(1)}%\n\n` +
        `Status: ${data.acceptance_status}`
      );
    } catch (err) {
      alert("Evaluation failed: " + err.message);
    } finally {
      hideProcessing();
    }
  }

  // Initial load
  refreshSessionList();
})();
