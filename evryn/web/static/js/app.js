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

  // Synchronized 3-Views DOM Elements
  const viewTabGraph = document.getElementById("view-tab-graph");
  const viewTabCopyable = document.getElementById("view-tab-copyable");
  const viewTabTable = document.getElementById("view-tab-table");
  const graphViewport = document.getElementById("graph-viewport");
  const copyableView = document.getElementById("copyable-view");
  const copyableText = document.getElementById("copyable-text");
  const copyGraphBtn = document.getElementById("copy-graph-btn");
  const tableView = document.getElementById("table-view");
  const tableBody = document.getElementById("table-body");

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

  const demoModal = document.getElementById("demo-modal");
  const demoList = document.getElementById("demo-list");
  const closeDemoBtn = document.getElementById("close-demo-btn");
  const menuDemoBtn = document.getElementById("menu-demo-btn");
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

    viewTabGraph.setAttribute("aria-selected", tabName === "graph");
    viewTabCopyable.setAttribute("aria-selected", tabName === "copyable");
    viewTabTable.setAttribute("aria-selected", tabName === "table");

    graphViewport.classList.toggle("hidden", tabName !== "graph");
    copyableView.classList.toggle("hidden", tabName !== "copyable");
    tableView.classList.toggle("hidden", tabName !== "table");

    if (tabName === "copyable" && activeSessionData) {
      copyableText.textContent = generateCopyableGraphText(activeSessionData);
      graphRenderer.pause();
    } else if (tabName === "table") {
      graphRenderer.pause();
    } else if (tabName === "graph") {
      graphRenderer.resume();
      graphRenderer.fitToView();
    }
  }

  viewTabGraph.addEventListener("click", () => switchView("graph"));
  viewTabCopyable.addEventListener("click", () => switchView("copyable"));
  viewTabTable.addEventListener("click", () => switchView("table"));

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

  menuDemoBtn.addEventListener("click", () => {
    plusMenu.classList.add("hidden");
    plusBtn.setAttribute("aria-expanded", "false");
    openDemoModal();
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
    showProcessing("EXTRACTING CAUSAL RELATIONSHIPS...");

    try {
      const res = await fetch("/api/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text,
          session_id: activeSessionId,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Extraction failed");
      }

      const data = await res.json();
      activeSessionId = data.id;
      renderSession(data);
      refreshSessionList();
    } catch (err) {
      alert("Error: " + err.message);
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
  }

  function undockInput() {
    inputContainer.classList.remove("docked");
    inputContainer.classList.add("centered");
    resultsView.classList.add("hidden");
    batchSection.classList.add("hidden");
    closeInspector();
    sentenceHighlighterBar.innerHTML = "";
    sentenceHighlighterBar.classList.add("hidden");
    regenerateBtn.classList.add("hidden");
    window.EVRYN_BG.setDimmed(false);
    queryInput.value = "";
    autoResize(queryInput);
    queryInput.focus();
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
    undockInput();
  });

  async function refreshSessionList() {
    try {
      const res = await fetch("/api/sessions");
      if (!res.ok) return;
      const sessions = await res.json();
      sessionCountLabel.textContent = `${sessions.length} sessions`;
      sessionList.innerHTML = "";

      for (const s of sessions) {
        const li = document.createElement("li");
        li.className = `session-item ${s.id === activeSessionId ? "active" : ""}`;
        li.innerHTML = `
          <div class="session-info">
            <div class="session-title-text">${s.title}</div>
            <div class="session-meta-text">${s.node_count || 0} nodes &bull; ${s.relation_count || 0} relations &bull; ${s.updated_at.slice(0, 10)}</div>
          </div>
          <button class="session-delete-btn" title="Delete session" aria-label="Delete session">&times;</button>
        `;

        li.querySelector(".session-info").addEventListener("click", () => loadSession(s.id));
        li.querySelector(".session-delete-btn").addEventListener("click", (e) => {
          e.stopPropagation();
          deleteSession(s.id);
        });

        sessionList.appendChild(li);
      }
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
      if (activeSessionId === sessionId) {
        activeSessionId = null;
        undockInput();
      }
      refreshSessionList();
    } catch (err) {
      alert(err.message);
    }
  }

  // Demonstration Examples Modal
  async function openDemoModal() {
    demoModal.classList.remove("hidden");
    demoList.innerHTML = "<p>Loading examples...</p>";

    try {
      const res = await fetch("/api/demo-examples");
      const examples = await res.json();
      demoList.innerHTML = "";

      for (const ex of examples) {
        const item = document.createElement("div");
        item.className = "demo-item";
        item.innerHTML = `
          <div class="demo-item-title">${ex.id}. ${ex.title}</div>
          <div class="demo-item-desc">${ex.test_purpose}</div>
        `;
        item.addEventListener("click", () => {
          demoModal.classList.add("hidden");
          queryInput.value = ex.text;
          autoResize(queryInput);
          submitQuery(ex.text);
        });
        demoList.appendChild(item);
      }
    } catch (err) {
      demoList.innerHTML = `<p>Failed to load demo examples: ${err.message}</p>`;
    }
  }

  closeDemoBtn.addEventListener("click", () => demoModal.classList.add("hidden"));

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
