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
  const graphWrapper = document.getElementById("graph-wrapper");
  const workspaceResearch = document.getElementById("workspace-research");
  const navModeExplore = document.getElementById("nav-mode-explore");
  const navModeResearch = document.getElementById("nav-mode-research");
  const graphStats = document.getElementById("graph-stats");
  const batchSection = document.getElementById("batch-section");
  const batchCards = document.getElementById("batch-cards");
  const toggleCombinedBtn = document.getElementById("toggle-combined-btn");

  // Synchronized 4-Views DOM Elements
  const viewTabGraph = document.getElementById("view-tab-graph");
  const viewTabCopyable = document.getElementById("view-tab-copyable");
  const viewTabTable = document.getElementById("view-tab-table");
  const viewTabExamples = document.getElementById("view-tab-examples");
  const viewTabBenchmark = document.getElementById("view-tab-benchmark");
  const viewTabGold = document.getElementById("view-tab-gold");
  const viewTabDiagnostics = document.getElementById("view-tab-diagnostics");
  const viewTabChains = document.getElementById("view-tab-chains");
  const viewDiagnosticsBtn = document.getElementById("view-diagnostics-btn");
  const graphViewport = document.getElementById("graph-viewport");
  const graphEmptyState = document.getElementById("graph-empty-state");
  const copyableView = document.getElementById("copyable-view");
  const copyableText = document.getElementById("copyable-text");
  const copyGraphBtn = document.getElementById("copy-graph-btn");
  const tableView = document.getElementById("table-view");
  const tableBody = document.getElementById("table-body");
  const examplesView = document.getElementById("examples-view");
  const benchmarkView = document.getElementById("benchmark-view");
  const goldComparisonView = document.getElementById("gold-comparison-view");
  const diagnosticsView = document.getElementById("diagnostics-view");
  const chainsView = document.getElementById("chains-view");
  const goldCompTitle = document.getElementById("gold-comp-title");
  const goldCompSubtitle = document.getElementById("gold-comp-subtitle");
  const goldProvenanceTag = document.getElementById("gold-provenance-tag");
  const goldCompReloadBtn = document.getElementById("gold-comp-reload-btn");
  const goldCompUnavailable = document.getElementById("gold-comp-unavailable");
  const goldCompContent = document.getElementById("gold-comp-content");
  const goldLoadSampleBtn = document.getElementById("gold-load-sample-btn");
  const goldComparisonTbody = document.getElementById("gold-comparison-tbody");
  const goldKpiPrecision = document.getElementById("gold-kpi-precision");
  const goldKpiRecall = document.getElementById("gold-kpi-recall");
  const goldKpiF1 = document.getElementById("gold-kpi-f1");
  const goldKpiMatched = document.getElementById("gold-kpi-matched");
  const goldKpiUnmatched = document.getElementById("gold-kpi-unmatched");
  const goldKpiMissed = document.getElementById("gold-kpi-missed");
  const goldKpiExploratory = document.getElementById("gold-kpi-exploratory");
  const adjBreakdownCounts = document.getElementById("adj-breakdown-counts");

  // Example Library Modal Elements
  const menuBrowseExamplesBtn = document.getElementById("menu-browse-examples-btn");
  const exampleLibraryModal = document.getElementById("example-library-modal");
  const closeExampleLibraryBtn = document.getElementById("close-example-library-btn");
  const librarySearchInput = document.getElementById("library-search-input");
  const libraryFilterChips = document.getElementById("library-filter-chips");
  const libraryCardsContainer = document.getElementById("library-cards-container");
  const libraryCountTag = document.getElementById("library-count-tag");
  const plusMenuRecents = document.getElementById("plus-menu-recents");

  const benchmarkSplitSelect = document.getElementById("benchmark-split-select");
  const benchmarkReloadBtn = document.getElementById("benchmark-reload-btn");
  const benchmarkCardsRow = document.getElementById("benchmark-cards-row");
  const benchmarkSummaryTbody = document.getElementById("benchmark-summary-tbody");
  const benchmarkPerpaperTbody = document.getElementById("benchmark-perpaper-tbody");
  const drilldownEngineChips = document.getElementById("drilldown-engine-chips");

  // Unified Examples Controls
  const exampleDropdown = document.getElementById("example-dropdown");
  const loadExampleBtn = document.getElementById("load-example-btn");

  // Legacy subnav hooks (gracefully optional)
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

  // Synchronized Highlighting (Cross-Panel Hover without Viewport Transform Coupling)
  function onHoverExtractedNode(node, isEnter) {
    if (!isSplitGraphMode || !goldGraphRenderer) return;
    const name = node ? (node.canonical_name || node.name) : null;
    if (isEnter && name) {
      goldGraphRenderer.highlightNode(name);
    } else {
      goldGraphRenderer.clearNodeHighlight();
    }
  }

  function onHoverGoldNode(node, isEnter) {
    if (!isSplitGraphMode || !graphRenderer) return;
    const name = node ? (node.canonical_name || node.name) : null;
    if (isEnter && name) {
      graphRenderer.highlightNode(name);
    } else {
      graphRenderer.clearNodeHighlight();
    }
  }

  // Initialize Graph Renderer (Pass extracted wrapper to calculate bounding box correctly)
  const extractedContainerId = document.getElementById("extracted-svg-wrapper") ? "extracted-svg-wrapper" : "graph-viewport";
  graphRenderer = new CausalGraphRenderer(
    extractedContainerId,
    "causal-graph-svg",
    onSelectRelation,
    onSelectNode,
    onLayoutChanged,
    onHoverExtractedNode
  );
  window.graphRenderer = graphRenderer;

  // Split-Graph Extracted / Gold Elements & Renderer
  const splitGraphToggleBtn = document.getElementById("split-graph-toggle-btn");
  const extractedGraphPanel = document.getElementById("extracted-graph-panel");
  const extractedPanelHeader = document.getElementById("extracted-panel-header");
  const extractedPanelBadge = document.getElementById("extracted-panel-badge");
  const goldGraphPanel = document.getElementById("gold-graph-panel");
  const goldPanelBadge = document.getElementById("gold-panel-badge");
  const goldPanelPmcid = document.getElementById("gold-panel-pmcid");
  const goldGraphUnavailable = document.getElementById("gold-graph-unavailable");

  // Shared Toolbar Controls & Split Target Selector
  const splitTargetControl = document.getElementById("split-target-control");
  const targetExtractedBtn = document.getElementById("target-extracted-btn");
  const targetGoldBtn = document.getElementById("target-gold-btn");
  const realignGraphsBtn = document.getElementById("realign-graphs-btn");
  const resetLayoutBtn = document.getElementById("reset-layout-btn");

  let isSplitGraphMode = false;
  let activeGraphTarget = "extracted"; // "extracted" | "gold"

  function setActiveGraphTarget(target) {
    activeGraphTarget = target === "gold" ? "gold" : "extracted";
    if (targetExtractedBtn) targetExtractedBtn.classList.toggle("active", activeGraphTarget === "extracted");
    if (targetGoldBtn) targetGoldBtn.classList.toggle("active", activeGraphTarget === "gold");
    if (extractedGraphPanel) extractedGraphPanel.classList.toggle("panel-target-active", activeGraphTarget === "extracted");
    if (goldGraphPanel) goldGraphPanel.classList.toggle("panel-target-active", activeGraphTarget === "gold");
  }

  if (targetExtractedBtn) {
    targetExtractedBtn.addEventListener("click", () => setActiveGraphTarget("extracted"));
  }
  if (targetGoldBtn) {
    targetGoldBtn.addEventListener("click", () => setActiveGraphTarget("gold"));
  }

  const extractedSvgWrapper = document.getElementById("extracted-svg-wrapper");
  const goldSvgWrapper = document.getElementById("gold-svg-wrapper");
  if (extractedSvgWrapper) {
    extractedSvgWrapper.addEventListener("mousedown", () => {
      if (isSplitGraphMode && activeGraphTarget !== "extracted") setActiveGraphTarget("extracted");
    });
  }
  if (goldSvgWrapper) {
    goldSvgWrapper.addEventListener("mousedown", () => {
      if (isSplitGraphMode && activeGraphTarget !== "gold") setActiveGraphTarget("gold");
    });
  }

  function getActiveRenderer() {
    if (isSplitGraphMode && activeGraphTarget === "gold" && goldGraphRenderer) {
      return goldGraphRenderer;
    }
    return graphRenderer;
  }

  // Setup Shared Toolbar Controls Routed to Active Renderer
  document.getElementById("graph-fit-btn").addEventListener("click", () => {
    const r = getActiveRenderer();
    if (r) r.fitToView();
  });
  document.getElementById("graph-zoom-in").addEventListener("click", () => {
    const r = getActiveRenderer();
    if (r) r.zoomIn();
  });
  document.getElementById("graph-zoom-out").addEventListener("click", () => {
    const r = getActiveRenderer();
    if (r) r.zoomOut();
  });
  if (resetLayoutBtn) {
    resetLayoutBtn.addEventListener("click", () => {
      const r = getActiveRenderer();
      if (r && typeof r.resetLayout === "function") {
        r.resetLayout();
      }
    });
  }
  if (realignGraphsBtn) {
    realignGraphsBtn.addEventListener("click", () => {
      if (!isSplitGraphMode || !goldGraphRenderer || !graphRenderer) return;
      // Realign instantaneous node positions without permanent coupling
      if (activeGraphTarget === "gold") {
        goldGraphRenderer.alignLayoutWith(graphRenderer, true);
      } else {
        graphRenderer.alignLayoutWith(goldGraphRenderer, true);
      }
    });
  }

  let goldGraphRenderer = new CausalGraphRenderer(
    "gold-svg-wrapper",
    "gold-graph-svg",
    onSelectGoldRelation,
    onSelectGoldNode,
    null,
    onHoverGoldNode
  );
  window.goldGraphRenderer = goldGraphRenderer;
  let cachedGoldStandards = new Map();

  function onSelectGoldRelation(relData) {
    if (!relData) return;
    const isTransitive = !!relData.is_transitive;
    const isMatched = !!relData.is_matched;
    const evidenceInspector = document.getElementById("evidence-inspector");
    if (!evidenceInspector) return;

    evidenceInspector.innerHTML = `
      <div class="evidence-panel-header">
        <span class="evidence-tag gold-badge">${isTransitive ? "CROSS-PAGE GOLD" : "DIRECT GOLD"}</span>
        <span class="evidence-status-pill ${isMatched ? "status-matched" : "status-missed"}">${isMatched ? "MATCHED (TP)" : "MISSED (FN)"}</span>
        <span class="evidence-title">${escapeHtml(relData.cause_name || relData.source)} ➔ ${escapeHtml(relData.effect_name || relData.target)}</span>
      </div>
      <div class="evidence-panel-body">
        <div class="evidence-row"><strong>Standard Source:</strong> ${escapeHtml(currentLoadedPmcid || "Reference Ground Truth")} Ground Truth</div>
        <div class="evidence-row"><strong>Relation Category:</strong> ${isTransitive ? "Cross-page inferred ground-truth dependency" : "Direct reference biochemical relation"}</div>
        <div class="evidence-row"><strong>Adjudication Status:</strong> ${isMatched ? "Extracted by system as true positive." : "Reference annotation absent from current predictions."}</div>
      </div>
    `;
    evidenceInspector.classList.remove("hidden");
  }

  function onSelectGoldNode(nodeData) {
    if (!nodeData) return;
    const evidenceInspector = document.getElementById("evidence-inspector");
    if (!evidenceInspector) return;

    evidenceInspector.innerHTML = `
      <div class="evidence-panel-header">
        <span class="evidence-tag gold-badge">GOLD ENTITY</span>
        <span class="evidence-title">${escapeHtml(nodeData.canonical_name || nodeData.name)}</span>
      </div>
      <div class="evidence-panel-body">
        <div class="evidence-row"><strong>Canonical Name:</strong> ${escapeHtml(nodeData.canonical_name || nodeData.name)}</div>
        <div class="evidence-row"><strong>Paper:</strong> ${escapeHtml(currentLoadedPmcid || "Benchmark Reference")}</div>
      </div>
    `;
    evidenceInspector.classList.remove("hidden");
  }

  async function updateSplitGraphView() {
    if (!graphViewport) return;
    graphViewport.classList.toggle("split-mode", isSplitGraphMode);
    if (splitGraphToggleBtn) {
      splitGraphToggleBtn.classList.toggle("active", isSplitGraphMode);
      splitGraphToggleBtn.textContent = isSplitGraphMode ? "SPLIT: ON" : "SPLIT: EXTRACTED / GOLD";
    }

    if (extractedPanelHeader) extractedPanelHeader.classList.toggle("hidden", !isSplitGraphMode);
    if (goldGraphPanel) goldGraphPanel.classList.toggle("hidden", !isSplitGraphMode);
    if (splitTargetControl) splitTargetControl.classList.toggle("hidden", !isSplitGraphMode);
    if (realignGraphsBtn) realignGraphsBtn.classList.toggle("hidden", !isSplitGraphMode);
    if (!isSplitGraphMode) {
      setActiveGraphTarget("extracted");
    }

    if (isSplitGraphMode) {
      let detectedPmcid = currentLoadedPmcid;
      if (!detectedPmcid && activeSessionData && activeSessionData.title) {
        const m = activeSessionData.title.match(/PMC\d+/i);
        if (m) detectedPmcid = m[0].toUpperCase();
      }
      if (!detectedPmcid && queryInput && queryInput.value) {
        const m = queryInput.value.match(/PMC\d+/i);
        if (m) detectedPmcid = m[0].toUpperCase();
      }

      if (detectedPmcid) {
        try {
          let gt = cachedGoldStandards.get(detectedPmcid);
          if (!gt) {
            const res = await fetch(`/api/examples/gold/${detectedPmcid}`);
            if (res.ok) {
              const resData = await res.json();
              gt = resData.ground_truth || resData;
              cachedGoldStandards.set(detectedPmcid, gt);
            }
          }

          if (gt) {
            if (goldGraphUnavailable) goldGraphUnavailable.classList.add("hidden");
            if (goldPanelPmcid) goldPanelPmcid.textContent = `${detectedPmcid} REFERENCE STANDARD`;

            const entities = gt.canonical_entities || [];
            const directEdges = gt.direct_edges || [];
            const crossEdges = gt.cross_page_edges || [];

            const extractedRels = activeSessionData && activeSessionData.relations ? activeSessionData.relations : [];
            const norm = (s) => (s || "").toLowerCase().replace(/[^a-z0-9]/g, "");

            function isMatchedInExtracted(src, tgt) {
              const sN = norm(src);
              const tN = norm(tgt);
              return extractedRels.some(r => {
                const rS = norm(r.cause_name || r.source || r.cause);
                const rT = norm(r.effect_name || r.target || r.effect);
                return (rS === sN || rS.includes(sN) || sN.includes(rS)) &&
                       (rT === tN || rT.includes(tN) || tN.includes(rT));
              });
            }

            const goldNodes = entities.map((name, idx) => {
              const extractedNode = graphRenderer && graphRenderer.nodeMap ? graphRenderer.nodeMap.get(name) : null;
              return {
                id: `gold_node_${idx}`,
                name: name,
                canonical_name: name,
                label: name,
                category: "Gene/Protein",
                x: extractedNode ? extractedNode.x : null,
                y: extractedNode ? extractedNode.y : null,
              };
            });

            const goldEdges = [];
            let matchedCount = 0;
            directEdges.forEach(([src, tgt], idx) => {
              const matched = isMatchedInExtracted(src, tgt);
              if (matched) matchedCount++;
              goldEdges.push({
                id: `gold_dir_${idx}`,
                cause_name: src,
                effect_name: tgt,
                source: src,
                target: tgt,
                is_transitive: false,
                edge_style: "solid",
                is_matched: matched,
                edge_color: matched ? "#16a34a" : "#64748b",
                marker_id: matched ? "gold-arrowhead-matched" : "gold-arrowhead-missed",
                confidence: 1.0,
                evidence_quote: "Direct ground truth annotation",
              });
            });

            crossEdges.forEach(([src, tgt], idx) => {
              const matched = isMatchedInExtracted(src, tgt);
              if (matched) matchedCount++;
              goldEdges.push({
                id: `gold_cross_${idx}`,
                cause_name: src,
                effect_name: tgt,
                source: src,
                target: tgt,
                is_transitive: true,
                edge_style: "dashed",
                is_matched: matched,
                edge_color: matched ? "#16a34a" : "#94a3b8",
                marker_id: matched ? "gold-arrowhead-matched" : "gold-arrowhead-missed",
                confidence: 1.0,
                evidence_quote: "Cross-page inferred ground truth reference",
              });
            });

            if (goldPanelBadge) {
              goldPanelBadge.textContent = `${goldEdges.length} GOLD EDGES (${matchedCount} MATCHED)`;
            }

            goldGraphRenderer.setData(goldNodes, goldEdges);
            goldGraphRenderer.alignLayoutWith(graphRenderer);
            goldGraphRenderer.fitToView();
          } else {
            showGoldUnavailable(detectedPmcid);
          }
        } catch (e) {
          console.warn("Gold split view fetch error:", e);
          showGoldUnavailable(detectedPmcid);
        }
      } else {
        showGoldUnavailable(null);
      }
    }

    setTimeout(() => {
      if (graphRenderer) {
        graphRenderer.handleResize();
        graphRenderer.fitToView();
      }
      if (isSplitGraphMode && goldGraphRenderer) {
        goldGraphRenderer.handleResize();
        goldGraphRenderer.fitToView();
      }
    }, 80);
  }

  function showGoldUnavailable(pmcid) {
    if (goldGraphUnavailable) goldGraphUnavailable.classList.remove("hidden");
    if (goldPanelBadge) goldPanelBadge.textContent = "0 RELATIONS";
    if (goldPanelPmcid) goldPanelPmcid.textContent = pmcid ? `${pmcid} (NO REFERENCE GOLD)` : "NO REFERENCE GOLD";
    if (goldGraphRenderer) goldGraphRenderer.clear();
  }

  if (splitGraphToggleBtn) {
    splitGraphToggleBtn.addEventListener("click", () => {
      isSplitGraphMode = !isSplitGraphMode;
      updateSplitGraphView();
    });
  }

  // 3-Activity Workspace State (Explore, Evaluate, Research)
  let currentMode = "explore";
  let currentExploreTab = "graph";
  let currentResearchTab = "chains";

  function switchMode(mode) {
    currentMode = mode;
    if (navModeExplore) {
      navModeExplore.classList.toggle("active", mode === "explore");
      navModeExplore.setAttribute("aria-selected", mode === "explore");
    }
    if (viewTabGold) {
      viewTabGold.classList.toggle("active", mode === "evaluate");
      viewTabGold.setAttribute("aria-selected", mode === "evaluate");
    }
    if (navModeResearch) {
      navModeResearch.classList.toggle("active", mode === "research");
      navModeResearch.setAttribute("aria-selected", mode === "research");
    }

    if (mode === "explore") {
      if (graphWrapper) graphWrapper.classList.remove("hidden");
      if (goldComparisonView) goldComparisonView.classList.add("hidden");
      if (workspaceResearch) workspaceResearch.classList.add("hidden");
      inputContainer.classList.remove("hidden");
      if (!activeSessionData) {
        if (currentExploreTab === "graph") {
          resultsView.classList.remove("hidden");
        } else {
          resultsView.classList.add("hidden");
        }
      } else {
        dockInput();
      }
      switchExploreTab(currentExploreTab || "graph");
    } else if (mode === "evaluate") {
      if (graphWrapper) graphWrapper.classList.add("hidden");
      if (goldComparisonView) goldComparisonView.classList.remove("hidden");
      if (workspaceResearch) workspaceResearch.classList.add("hidden");
      inputContainer.classList.add("hidden");
      if (graphRenderer) graphRenderer.pause();
      resultsView.classList.remove("hidden");
      loadGoldComparisonData();
    } else if (mode === "research") {
      if (graphWrapper) graphWrapper.classList.add("hidden");
      if (goldComparisonView) goldComparisonView.classList.add("hidden");
      if (workspaceResearch) workspaceResearch.classList.remove("hidden");
      inputContainer.classList.add("hidden");
      if (graphRenderer) graphRenderer.pause();
      resultsView.classList.remove("hidden");
      switchResearchTab(currentResearchTab || "chains");
    }
  }

  function switchExploreTab(tabName) {
    currentExploreTab = tabName;
    if (viewTabGraph) {
      viewTabGraph.classList.toggle("active", tabName === "graph");
      viewTabGraph.setAttribute("aria-selected", tabName === "graph");
    }
    if (viewTabCopyable) {
      viewTabCopyable.classList.toggle("active", tabName === "copyable");
      viewTabCopyable.setAttribute("aria-selected", tabName === "copyable");
    }
    if (viewTabTable) {
      viewTabTable.classList.toggle("active", tabName === "table");
      viewTabTable.setAttribute("aria-selected", tabName === "table");
    }

    if (graphViewport) graphViewport.classList.toggle("hidden", tabName !== "graph");
    if (copyableView) copyableView.classList.toggle("hidden", tabName !== "copyable");
    if (tableView) tableView.classList.toggle("hidden", tabName !== "table");

    if (tabName === "copyable") {
      if (activeSessionData) {
        copyableText.textContent = generateCopyableGraphText(activeSessionData);
      }
      if (graphRenderer) graphRenderer.pause();
    } else if (tabName === "table") {
      if (graphRenderer) graphRenderer.pause();
    } else if (tabName === "graph") {
      if (graphRenderer) {
        graphRenderer.resume();
        graphRenderer.fitToView();
      }
    }
  }

  function switchResearchTab(tabName) {
    currentResearchTab = tabName;
    if (viewTabChains) {
      viewTabChains.classList.toggle("active", tabName === "chains");
      viewTabChains.setAttribute("aria-selected", tabName === "chains");
    }
    if (viewTabBenchmark) {
      viewTabBenchmark.classList.toggle("active", tabName === "benchmark");
      viewTabBenchmark.setAttribute("aria-selected", tabName === "benchmark");
    }
    if (viewTabDiagnostics) {
      viewTabDiagnostics.classList.toggle("active", tabName === "diagnostics");
      viewTabDiagnostics.setAttribute("aria-selected", tabName === "diagnostics");
    }

    if (chainsView) chainsView.classList.toggle("hidden", tabName !== "chains");
    if (benchmarkView) benchmarkView.classList.toggle("hidden", tabName !== "benchmark");
    if (diagnosticsView) diagnosticsView.classList.toggle("hidden", tabName !== "diagnostics");

    if (tabName === "chains") {
      loadChainsData();
    } else if (tabName === "benchmark") {
      loadBenchmarkData();
    } else if (tabName === "diagnostics") {
      loadDiagnosticsData();
    }
  }

  // Unified Multi-View / Mode Router
  function switchView(tabName) {
    if (tabName === "graph" || tabName === "copyable" || tabName === "table") {
      currentExploreTab = tabName;
      switchMode("explore");
    } else if (tabName === "gold") {
      switchMode("evaluate");
    } else if (tabName === "chains" || tabName === "benchmark" || tabName === "diagnostics") {
      currentResearchTab = tabName;
      switchMode("research");
    }
  }

  if (navModeExplore) navModeExplore.addEventListener("click", () => switchMode("explore"));
  if (navModeResearch) navModeResearch.addEventListener("click", () => switchMode("research"));
  if (viewTabGraph) viewTabGraph.addEventListener("click", () => switchView("graph"));
  if (viewTabCopyable) viewTabCopyable.addEventListener("click", () => switchView("copyable"));
  if (viewTabTable) viewTabTable.addEventListener("click", () => switchView("table"));
  if (viewTabExamples) viewTabExamples.addEventListener("click", () => switchView("examples"));
  if (viewTabBenchmark) viewTabBenchmark.addEventListener("click", () => switchView("benchmark"));
  if (viewTabGold) viewTabGold.addEventListener("click", () => switchView("gold"));
  if (viewTabDiagnostics) viewTabDiagnostics.addEventListener("click", () => switchView("diagnostics"));
  if (viewDiagnosticsBtn) viewDiagnosticsBtn.addEventListener("click", () => switchView("diagnostics"));
  if (viewTabChains) viewTabChains.addEventListener("click", () => switchView("chains"));

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
    const r = getActiveRenderer();
    if (r && typeof r.setPhysicsPreset === "function") {
      r.setPhysicsPreset(preset);
    }
    if (activeSessionId && activeGraphTarget === "extracted") {
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
    const r = getActiveRenderer();
    if (!r || typeof r.tightenEdge !== "function") return;
    const newTension = r.tightenEdge(selectedRelation.id);
    updateTensionBadge(newTension);
    if (activeSessionId && activeGraphTarget === "extracted") {
      fetch(`/api/sessions/${activeSessionId}/physics`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tensions: { [selectedRelation.id]: newTension } }),
      }).catch(console.warn);
    }
  });

  loosenEdgeBtn.addEventListener("click", () => {
    if (!selectedRelation) return;
    const r = getActiveRenderer();
    if (!r || typeof r.loosenEdge !== "function") return;
    const newTension = r.loosenEdge(selectedRelation.id);
    updateTensionBadge(newTension);
    if (activeSessionId && activeGraphTarget === "extracted") {
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
    if (isHidden) {
      renderRecentExamples();
    }
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

  if (menuBrowseExamplesBtn) {
    menuBrowseExamplesBtn.addEventListener("click", () => {
      openExampleLibrary();
    });
  }

  if (closeExampleLibraryBtn) {
    closeExampleLibraryBtn.addEventListener("click", () => {
      closeExampleLibrary();
    });
  }

  if (exampleLibraryModal) {
    exampleLibraryModal.addEventListener("click", (e) => {
      if (e.target === exampleLibraryModal) closeExampleLibrary();
    });
  }

  if (librarySearchInput) {
    librarySearchInput.addEventListener("input", () => {
      renderExampleLibraryCards();
    });
  }

  if (libraryFilterChips) {
    libraryFilterChips.querySelectorAll(".status-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        libraryFilterChips.querySelectorAll(".status-chip").forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        currentLibraryFilter = chip.dataset.filter || "all";
        renderExampleLibraryCards();
      });
    });
  }

  if (menuContinualBtn) {
    menuContinualBtn.addEventListener("click", () => {
      plusMenu.classList.add("hidden");
      plusBtn.setAttribute("aria-expanded", "false");
      openContinualCard();
    });
  }

  if (menuEvalBtn) {
    menuEvalBtn.addEventListener("click", () => {
      plusMenu.classList.add("hidden");
      plusBtn.setAttribute("aria-expanded", "false");
      resultsView.classList.remove("hidden");
      switchView("benchmark");
      runBenchmarkVerification();
    });
  }

  if (goldCompReloadBtn) {
    goldCompReloadBtn.addEventListener("click", () => {
      loadGoldComparisonData();
    });
  }

  if (goldLoadSampleBtn) {
    goldLoadSampleBtn.addEventListener("click", () => {
      openExampleLibrary();
    });
  }

  // Gold Filter Tabs
  document.querySelectorAll("[data-gold-tab]").forEach((tabBtn) => {
    tabBtn.addEventListener("click", () => {
      document.querySelectorAll("[data-gold-tab]").forEach((b) => b.classList.remove("active"));
      tabBtn.classList.add("active");
      activeGoldTab = tabBtn.dataset.goldTab;
      renderGoldTableRows();
    });
  });

  if (resetWorkspaceBtn) {
    resetWorkspaceBtn.addEventListener("click", () => resetWorkspace());
  }

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
    const selectedEngine = "nlp_baseline";
    showProcessing("EXTRACTING CAUSAL RELATIONSHIPS [SYSTEM A: NLP ENGINE]...");

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

  const VERIFIED_EXAMPLES = {
    example_a: {
      id: "example_a",
      title: "Example A — Direct Causal Relation",
      category: "Diagnostic Test Suite",
      source: "Diagnostic Test Suite",
      input_text: "The deletion of gene A reduced expression of protein B.",
      expected: "Direct downregulation relation (gene A -> protein B) with negative polarity."
    },
    example_b: {
      id: "example_b",
      title: "Example B — Multi-Transition Causal Chain",
      category: "Diagnostic Test Suite",
      source: "Diagnostic Test Suite",
      input_text: "Activation of gene A increased expression of protein B.\nExpression of protein B activated pathway C.",
      expected: "Extracts direct cascade edges (gene A -> protein B, protein B -> pathway C) without ungrounded shortcuts."
    },
    example_c: {
      id: "example_c",
      title: "Example C — Negation and Directionality",
      category: "Diagnostic Test Suite",
      source: "Diagnostic Test Suite",
      input_text: "Deletion of gene A did not reduce virulence.",
      expected: "Refutation / negation assertion detected; suppresses false positive virulence reduction."
    },
    example_d: {
      id: "example_d",
      title: "Example D — Invalid Transitive Path (Context Mismatch)",
      category: "Diagnostic Test Suite",
      source: "Diagnostic Test Suite",
      input_text: "Treatment A increased marker B in organism X.\nMarker B was associated with outcome C in organism Y.",
      expected: "Organism context boundary enforced; cross-organism transitive leaps blocked."
    },
    example_e: {
      id: "example_e",
      title: "Example E — Malformed or Empty Input",
      category: "Diagnostic Test Suite",
      source: "Diagnostic Test Suite",
      input_text: "   ",
      expected: "Rejects empty input gracefully with descriptive validation error."
    },
    pmc1804205: {
      id: "pmc1804205",
      title: "Acid pH activation of PmrA/PmrB system",
      category: "Verified Literature Benchmark",
      source: "PMC1804205 • Mol Microbiol 2007",
      input_text: "Growth in mild acid (pH 5.8) promotes transcription of genes activated by the response regulator PmrA. This activation requires both PmrA's cognate sensor kinase PmrB and PmrA's post-translational activator PmrD. Activation of PmrA mediates resistance to the antibiotic polymyxin B.",
      expected: "PmrB and PmrD mediated PmrA activation and polymyxin B resistance."
    },
    pmc1874608: {
      id: "pmc1874608",
      title: "Mlc regulation of Salmonella pathogenicity",
      category: "Verified Literature Benchmark",
      source: "PMC1874608 • J Bacteriol 2007",
      input_text: "Glucose represses hilA and invF transcription through the glucose-specific phosphotransferase system. Overexpression of the global regulator Mlc represses hilA expression and decreases Salmonella invasion of epithelial cells.",
      expected: "Inhibitory transcriptional repression of hilA by Glucose and Mlc."
    },
    pmc1974823: {
      id: "pmc1974823",
      title: "P. gingivalis short fimbriae regulation",
      category: "Verified Literature Benchmark",
      source: "PMC1974823 • J Bacteriol 2007",
      input_text: "FimA expression promotes bacterial adhesion, whereas Mfa1 is required for microcolony development. FimS sensor kinase phosphorylates FimR to activate fimA transcription, promoting biofilm formation.",
      expected: "FimS/FimR phosphorylation activating fimbriae and biofilm development."
    },
    pmc2242835: {
      id: "pmc2242835",
      title: "Control of M. tuberculosis ESAT-6 secretion",
      category: "Verified Literature Benchmark",
      source: "PMC2242835 • Mol Microbiol 2008",
      input_text: "The PhoP response regulator directly activates espA transcription. EspA is required for ESX-1 dependent secretion of ESAT-6, and ESAT-6 secretion stimulates T-cell recognition.",
      expected: "PhoP activation of espA, ESX-1 dependent secretion, and T-cell recognition."
    },
    pmc2430206: {
      id: "pmc2430206",
      title: "GraRS regulatory system & LL-37 resistance",
      category: "Verified Literature Benchmark",
      source: "PMC2430206 • J Bacteriol 2008",
      input_text: "The GraRS two-component system directly activates transcription of the dltABCD operon and mprF. GraRS activation promotes resistance to human antimicrobial peptide LL-37 and increases S. aureus virulence.",
      expected: "GraRS direct activation of dltABCD/mprF and LL-37 resistance."
    }
  };

  const RECENTS_KEY = "evryn_recent_examples";
  const MAX_RECENTS = 5;

  function getRecentExamples() {
    try {
      const raw = localStorage.getItem(RECENTS_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  function recordRecentExample(ex) {
    if (!ex || (!ex.id && !ex.code)) return;
    try {
      const exId = (ex.id || ex.code).toLowerCase();
      let recents = getRecentExamples();
      recents = recents.filter((r) => r.id !== exId);
      recents.unshift({
        id: exId,
        title: ex.title || ex.code || exId,
        category: ex.category || "Benchmark",
        timestamp: Date.now(),
      });
      if (recents.length > MAX_RECENTS) {
        recents = recents.slice(0, MAX_RECENTS);
      }
      localStorage.setItem(RECENTS_KEY, JSON.stringify(recents));
      renderRecentExamples();
    } catch (e) {
      console.warn("Could not save recent example:", e);
    }
  }

  const DEFAULT_STARTER_RECENTS = [
    { id: "example_a", title: "Case A: Direct Causal Relation", category: "Diagnostic Suite" },
    { id: "example_b", title: "Case B: Multi-Transition Cascade", category: "Diagnostic Suite" },
    { id: "example_c", title: "Case C: Negation & Directionality", category: "Diagnostic Suite" },
  ];

  function renderRecentExamples() {
    const container = document.getElementById("plus-menu-recents");
    if (!container) return;
    let recents = getRecentExamples();
    const existingIds = new Set(recents.map(r => r.id));
    for (const starter of DEFAULT_STARTER_RECENTS) {
      if (recents.length >= 3) break;
      if (!existingIds.has(starter.id)) {
        recents.push({ ...starter, timestamp: Date.now() });
        existingIds.add(starter.id);
      }
    }
    container.innerHTML = "";
    recents.forEach((r) => {
      const btn = document.createElement("button");
      btn.className = "menu-recent-item menu-example-item";
      btn.role = "menuitem";
      btn.dataset.example = r.id;
      const timeStr = r.timestamp ? new Date(r.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "Default";
      btn.innerHTML = `
        <span class="menu-recent-title">${escapeHtml(r.title)}</span>
        <span class="menu-recent-meta">${escapeHtml(r.category)} • ${timeStr}</span>
      `;
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (plusMenu) {
          plusMenu.classList.add("hidden");
          plusBtn.setAttribute("aria-expanded", "false");
        }
        loadExampleById(r.id);
      });
      container.appendChild(btn);
    });
  }

  let fullLibraryCatalog = [];
  let currentLibraryFilter = "all";

  async function openExampleLibrary() {
    if (plusMenu) {
      plusMenu.classList.add("hidden");
      plusBtn.setAttribute("aria-expanded", "false");
    }
    if (exampleLibraryModal) exampleLibraryModal.classList.remove("hidden");
    if (fullLibraryCatalog.length === 0) {
      showProcessing("LOADING EXAMPLE LIBRARY...");
      try {
        const res = await fetch("/api/examples/library");
        if (res.ok) {
          const data = await res.json();
          const diagnostic = (data.diagnostic_suite || []).map((d) => ({
            ...d,
            type: "diagnostic",
            split: "diagnostic",
            gold_available: false,
          }));
          const papers = (data.benchmark_papers || []).map((p) => ({
            ...p,
            type: "benchmark",
          }));
          fullLibraryCatalog = [...diagnostic, ...papers];
        }
      } catch (e) {
        console.warn("Could not load library from server:", e);
      } finally {
        hideProcessing();
      }
    }
    renderExampleLibraryCards();
    if (librarySearchInput) {
      librarySearchInput.value = "";
      librarySearchInput.focus();
    }
  }

  function closeExampleLibrary() {
    if (exampleLibraryModal) exampleLibraryModal.classList.add("hidden");
  }

  function renderExampleLibraryCards() {
    if (!libraryCardsContainer) return;
    const query = (librarySearchInput ? librarySearchInput.value : "").trim().toLowerCase();

    let filtered = fullLibraryCatalog.filter((item) => {
      if (currentLibraryFilter === "diagnostic" && item.type !== "diagnostic") return false;
      if (currentLibraryFilter === "dev" && item.split !== "dev") return false;
      if (currentLibraryFilter === "locked_test" && item.split !== "locked_test") return false;
      if (currentLibraryFilter === "external" && item.split !== "external") return false;
      if (currentLibraryFilter === "gold" && !item.gold_available) return false;

      if (query) {
        const textToSearch = `${item.title} ${item.code || ""} ${item.journal || ""} ${item.description || ""} ${(item.authors || []).join(" ")}`.toLowerCase();
        if (!textToSearch.includes(query)) return false;
      }
      return true;
    });

    if (libraryCountTag) {
      libraryCountTag.textContent = `${filtered.length} OF ${fullLibraryCatalog.length} EXAMPLES`;
    }

    if (filtered.length === 0) {
      libraryCardsContainer.innerHTML = '<div class="menu-empty-hint" style="grid-column: 1 / -1; padding: 30px; text-align: center;">No matching examples or benchmark papers found.</div>';
      return;
    }

    libraryCardsContainer.innerHTML = "";
    filtered.forEach((item) => {
      const card = document.createElement("div");
      card.className = "library-card";

      const badgeSplit = item.split ? `<span class="badge-split">${item.split.toUpperCase()}</span>` : "";
      const badgeGold = item.gold_available ? '<span class="badge-gold-match" title="Frozen Ground Truth Annotations Available">GOLD STANDARD</span>' : "";

      card.innerHTML = `
        <div class="library-card-header">
          <div class="library-card-title">${escapeHtml(item.title)}</div>
          <div class="library-card-badges">
            ${badgeSplit}
            ${badgeGold}
          </div>
        </div>
        <div class="library-card-meta">${escapeHtml(item.code || "")} • ${escapeHtml(item.journal || item.category || "")}</div>
        <div class="library-card-desc">${escapeHtml(item.description || "")}</div>
        <div class="library-card-actions">
          <button class="btn-card-action" data-action="load">LOAD INTO WORKSPACE</button>
          ${item.code && item.code.toUpperCase().startsWith("PMC") ? `<button class="btn-card-action-secondary" data-action="preview">VIEW PAPER PDF</button>` : ""}
          ${item.gold_available ? `<button class="btn-card-action-secondary" data-action="gold">VIEW GOLD STANDARD</button>` : ""}
        </div>
      `;

      card.querySelector('[data-action="load"]').addEventListener("click", () => {
        closeExampleLibrary();
        loadExampleById(item.id || item.code);
      });

      const previewBtn = card.querySelector('[data-action="preview"]');
      if (previewBtn) {
        previewBtn.addEventListener("click", () => {
          closeExampleLibrary();
          openPaperModal(item.code, "pdf");
        });
      }

      const goldBtn = card.querySelector('[data-action="gold"]');
      if (goldBtn) {
        goldBtn.addEventListener("click", () => {
          closeExampleLibrary();
          loadExampleById(item.id || item.code);
          setTimeout(() => switchView("gold"), 250);
        });
      }

      libraryCardsContainer.appendChild(card);
    });
  }

  async function loadExampleById(exampleId) {
    if (VERIFIED_EXAMPLES[exampleId]) {
      const ex = VERIFIED_EXAMPLES[exampleId];
      recordRecentExample(ex);
      selectExample(exampleId);
      return;
    }

    showProcessing(`LOADING ${exampleId.toUpperCase()}...`);
    try {
      const isBenchmark = exampleId.toLowerCase().startsWith("pmc");
      if (isBenchmark) {
        const pmcid = exampleId.toUpperCase();
        const res = await fetch(`/api/examples/paper/${pmcid}`);
        if (!res.ok) throw new Error(`Paper ${pmcid} not found`);
        const pdata = await res.json();

        let fullText = pdata.title + "\n\n";
        if (pdata.sections) {
          pdata.sections.forEach((s) => {
            if (s.title && s.title.toLowerCase().includes("abstract")) {
              fullText += s.paragraphs.join("\n\n") + "\n\n";
            }
          });
          if (fullText.length < 200 && pdata.sections.length > 0) {
            fullText += pdata.sections.slice(0, 2).map((s) => s.paragraphs.join("\n\n")).join("\n\n");
          }
        }

        queryInput.value = fullText.trim();
        autoResize(queryInput);
        dockInput();
        activeSessionId = null;
        activeSessionData = null;
        currentLoadedPmcid = pmcid;
        closeInspector();

        recordRecentExample({
          id: exampleId.toLowerCase(),
          title: pdata.title,
          category: `Benchmark (${pdata.split || "dev"}`.toUpperCase() + ")",
        });

        resultsView.classList.remove("hidden");
        switchView("graph");
        showNotification(`Loaded ${pmcid} text into editor. Click RUN EXTRACTION to evaluate.`, "info", 3500);
      } else {
        const res = await fetch(`/api/test-examples/${exampleId}`);
        if (!res.ok) throw new Error("Example not found");
        const tdata = await res.json();
        queryInput.value = tdata.input_text;
        autoResize(queryInput);
        dockInput();
        activeSessionId = null;
        activeSessionData = null;
        closeInspector();
        recordRecentExample(tdata);
        resultsView.classList.remove("hidden");
        switchView("graph");
        showNotification(`Loaded "${tdata.title}". Click RUN EXTRACTION to extract.`, "info", 3000);
      }
    } catch (err) {
      showNotification("Failed to load example: " + err.message, "error", 4000);
    } finally {
      hideProcessing();
    }
  }

  function selectExample(exampleId) {
    const ex = VERIFIED_EXAMPLES[exampleId];
    if (!ex) return;

    recordRecentExample(ex);
    activeSessionId = null;
    activeSessionData = null;
    currentLoadedPmcid = exampleId.toLowerCase().startsWith("pmc") ? exampleId.toUpperCase() : null;
    closeInspector();

    queryInput.value = ex.input_text;
    autoResize(queryInput);

    dockInput();
    regenerateBtn.classList.remove("hidden");
    regenerateBtn.textContent = "RUN EXTRACTION";

    if (plusMenu) {
      plusMenu.classList.add("hidden");
      plusBtn.setAttribute("aria-expanded", "false");
    }

    resultsView.classList.remove("hidden");
    switchView("graph");

    showNotification(`Loaded "${ex.title}". Click RUN EXTRACTION to extract.`, "info", 3000);
  }

  async function loadAndRunTestCase(exampleId) {
    document.querySelectorAll(".test-example-chip").forEach(c => {
      c.classList.toggle("active", c.dataset.example === exampleId);
    });

    activeSessionId = null;
    activeSessionData = null;
    currentLoadedPmcid = exampleId.toLowerCase().startsWith("pmc") ? exampleId.toUpperCase() : null;
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

    const highConfCount = relations.filter(r => (r.confidence || 0) >= 0.8).length;
    const highConfPct = relations.length > 0 ? Math.round((highConfCount / relations.length) * 100) : 0;
    graphStats.textContent = `${relations.length} EXTRACTED RELATIONS  •  ${highConfCount} HIGH-CONFIDENCE (${highConfPct}%)  •  ${nodes.length} GROUNDED ENTITIES`;

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

    if (extractedPanelBadge) {
      extractedPanelBadge.textContent = `${relations.length} EXTRACTED RELATIONS`;
    }
    if (isSplitGraphMode) {
      updateSplitGraphView();
    }

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

  // Phase 2.3 Engine Selection Sync
  document.querySelectorAll(".engine-toggle-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".engine-toggle-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const radio = btn.querySelector('input[type="radio"]');
      if (radio) {
        radio.checked = true;
      }
    });
  });

  // Phase 2.3 Benchmark Evaluation Logic
  let cachedBenchmarkResults = null;
  let activeDrilldownEngine = "nlp_baseline";

  if (benchmarkSplitSelect) {
    benchmarkSplitSelect.addEventListener("change", () => renderBenchmarkView());
  }
  if (benchmarkReloadBtn) {
    benchmarkReloadBtn.addEventListener("click", () => {
      cachedBenchmarkResults = null;
      loadBenchmarkData();
    });
  }
  if (drilldownEngineChips) {
    drilldownEngineChips.querySelectorAll(".status-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        drilldownEngineChips.querySelectorAll(".status-chip").forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        activeDrilldownEngine = chip.dataset.drilldownSys || "nlp_baseline";
        renderBenchmarkView();
      });
    });
  }

  async function loadBenchmarkData() {
    if (!cachedBenchmarkResults) {
      try {
        const res = await fetch("/api/benchmark/results");
        if (res.ok) {
          cachedBenchmarkResults = await res.json();
        }
      } catch (err) {
        console.error("Failed to load benchmark results:", err);
      }
    }
    renderBenchmarkView();
  }

  function renderBenchmarkView() {
    if (!cachedBenchmarkResults || !cachedBenchmarkResults.results) return;
    const splitKey = benchmarkSplitSelect?.value || "dev";
    const splitData = cachedBenchmarkResults.results[splitKey];
    if (!splitData) return;

    const nlpData = splitData["nlp_baseline"] || {};
    const nlpMacro = nlpData.macro_metrics || {};
    const nlpMicroD = (nlpData.micro_metrics && nlpData.micro_metrics.direct) || {};
    const nlpMicroC = (nlpData.micro_metrics && nlpData.micro_metrics.cross_page) || {};

    if (benchmarkCardsRow) {
      benchmarkCardsRow.innerHTML = `
        <div class="benchmark-kpi-card primary-card">
          <div class="benchmark-kpi-label">Direct Macro F1</div>
          <div class="benchmark-kpi-value">${(nlpMacro.direct_f1_mean || 0).toFixed(4)}</div>
          <div class="benchmark-kpi-sub">95% CI: [${(nlpMacro.direct_f1_ci?.[0] || 0).toFixed(4)}, ${(nlpMacro.direct_f1_ci?.[1] || 0).toFixed(4)}]</div>
        </div>
        <div class="benchmark-kpi-card primary-card">
          <div class="benchmark-kpi-label">Cross-Page Macro F1</div>
          <div class="benchmark-kpi-value">${(nlpMacro.cross_f1_mean || 0).toFixed(4)}</div>
          <div class="benchmark-kpi-sub">95% CI: [${(nlpMacro.cross_f1_ci?.[0] || 0).toFixed(4)}, ${(nlpMacro.cross_f1_ci?.[1] || 0).toFixed(4)}]</div>
        </div>
        <div class="benchmark-kpi-card primary-card">
          <div class="benchmark-kpi-label">Invariant Integrity</div>
          <div class="benchmark-kpi-value">${((nlpMacro.direction_accuracy_mean || 1.0) * 100).toFixed(1)}%</div>
          <div class="benchmark-kpi-sub">False Transitive Jumps: ${nlpData.micro_metrics?.total_false_transitive_jumps || 0}</div>
        </div>
      `;
    }

    const systemsList = [
      { key: "nlp_baseline", label: "System A (Repaired NLP Baseline)" },
      { key: "llm_only", label: "System B (LLM Only Candidate)" },
      { key: "hybrid", label: "System C (Hybrid Validated)" },
    ];

    if (benchmarkSummaryTbody) {
      let summaryHtml = "";
      for (const sys of systemsList) {
        const sData = splitData[sys.key];
        if (!sData) continue;
        const m = sData.macro_metrics || {};
        const md = sData.micro_metrics?.direct || {};
        const mc = sData.micro_metrics?.cross_page || {};
        const isTop = sys.key === "nlp_baseline";
        summaryHtml += `
          <tr class="${isTop ? 'highlight-row' : ''}">
            <td><strong>${sys.label}</strong> ${isTop ? '<span class="badge-top-sys">PRODUCTION</span>' : ''}</td>
            <td><strong>${(m.direct_f1_mean || 0).toFixed(4)}</strong> <span style="font-size:10px; color:#64748b;">[${(m.direct_f1_ci?.[0]||0).toFixed(4)}, ${(m.direct_f1_ci?.[1]||0).toFixed(4)}]</span></td>
            <td>${(md.precision || 0).toFixed(3)} / ${(md.recall || 0).toFixed(3)} / <strong>${(md.f1 || 0).toFixed(3)}</strong></td>
            <td><strong>${(m.cross_f1_mean || 0).toFixed(4)}</strong> <span style="font-size:10px; color:#64748b;">[${(m.cross_f1_ci?.[0]||0).toFixed(4)}, ${(m.cross_f1_ci?.[1]||0).toFixed(4)}]</span></td>
            <td>${(mc.precision || 0).toFixed(3)} / ${(mc.recall || 0).toFixed(3)} / <strong>${(mc.f1 || 0).toFixed(3)}</strong></td>
            <td>${((m.direction_accuracy_mean || 0) * 100).toFixed(1)}%</td>
            <td>${sData.micro_metrics?.total_false_transitive_jumps || 0}</td>
            <td>${(m.structural_match_mean || 0).toFixed(4)}</td>
            <td>${(sData.total_runtime_seconds || 0).toFixed(2)}s</td>
          </tr>
        `;
      }
      benchmarkSummaryTbody.innerHTML = summaryHtml;
    }

    if (benchmarkPerpaperTbody) {
      const activeSysData = splitData[activeDrilldownEngine] || {};
      const perPaper = activeSysData.per_paper || [];
      let perPaperHtml = "";
      for (const p of perPaper) {
        perPaperHtml += `
          <tr>
            <td><code style="font-weight:700;">${p.pmcid}</code></td>
            <td title="${p.title}">${p.title ? p.title.substring(0, 36) + '...' : ''}</td>
            <td>${p.gold_direct}</td>
            <td>${p.pred_direct}</td>
            <td>${p.tp_direct} / ${p.fp_direct} / ${p.fn_direct}</td>
            <td><strong style="color:${p.f1_direct >= 0.6 ? '#0d9488' : '#334155'};">${p.f1_direct.toFixed(4)}</strong></td>
            <td>${p.gold_cross}</td>
            <td>${p.pred_cross}</td>
            <td>${p.tp_cross} / ${p.fp_cross} / ${p.fn_cross}</td>
            <td><strong style="color:${p.f1_cross >= 0.6 ? '#0d9488' : '#334155'};">${p.f1_cross.toFixed(4)}</strong></td>
            <td>${p.false_transitive_jumps}</td>
            <td>${p.runtime_seconds.toFixed(2)}s</td>
          </tr>
        `;
      }
      benchmarkPerpaperTbody.innerHTML = perPaperHtml;
    }
  }

  // ==========================================================================
  // Phase 2.5: Gold Standard Comparison & Adjudication View
  // ==========================================================================
  let activeGoldReport = null;
  let activeGoldTab = "all";
  let currentLoadedPmcid = null;

  async function loadGoldComparisonData() {
    if (!activeSessionId && !activeSessionData) {
      if (goldCompUnavailable) goldCompUnavailable.classList.remove("hidden");
      if (goldCompContent) goldCompContent.classList.add("hidden");
      return;
    }

    try {
      showProcessing("COMPARING WITH GOLD STANDARD...");
      const detectedPmcid = currentLoadedPmcid || (activeSessionData && activeSessionData.title && activeSessionData.title.match(/PMC\d+/i) ? activeSessionData.title.match(/PMC\d+/i)[0].toUpperCase() : null);
      const res = await fetch("/api/benchmark/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: activeSessionId || "temp_session",
          pmcid: detectedPmcid,
          session_data: activeSessionData || null,
        }),
      });

      if (!res.ok) throw new Error("Could not evaluate comparison");
      const data = await res.json();
      activeGoldReport = data;
      renderGoldComparisonView(data);
    } catch (e) {
      showNotification("Gold comparison error: " + e.message, "error", 4000);
    } finally {
      hideProcessing();
    }
  }

  function renderGoldComparisonView(report) {
    if (!report || !report.gold_available) {
      if (goldCompUnavailable) goldCompUnavailable.classList.remove("hidden");
      if (goldCompContent) goldCompContent.classList.add("hidden");
      if (goldProvenanceTag) goldProvenanceTag.textContent = "NO GOLD AVAILABLE";
      if (goldUnavailableMsg && report && report.message) {
        goldUnavailableMsg.textContent = report.message;
      }
      return;
    }

    if (goldCompUnavailable) goldCompUnavailable.classList.add("hidden");
    if (goldCompContent) goldCompContent.classList.remove("hidden");

    if (goldProvenanceTag) goldProvenanceTag.textContent = `PMCID: ${report.pmcid} (${report.annotation_source || "Frozen Standard"})`;
    if (goldCompSubtitle) goldCompSubtitle.textContent = `Benchmark Reference: ${report.paper_title || report.pmcid}`;

    const m = report.official_metrics || {};
    if (goldKpiPrecision) goldKpiPrecision.textContent = `${((m.precision || 0) * 100).toFixed(1)}%`;
    if (goldKpiRecall) goldKpiRecall.textContent = `${((m.recall || 0) * 100).toFixed(1)}%`;
    if (goldKpiF1) goldKpiF1.textContent = (m.f1 || 0).toFixed(4);

    const counts = report.counts || {};
    if (goldKpiMatched) goldKpiMatched.textContent = counts.tp || 0;
    if (goldKpiUnmatched) goldKpiUnmatched.textContent = counts.fp || 0;
    if (goldKpiMissed) goldKpiMissed.textContent = counts.fn || 0;

    const adj = report.adjudicated_analysis || {};
    if (goldKpiExploratory) goldKpiExploratory.textContent = `${((adj.exploratory_precision_with_omissions || m.precision || 0) * 100).toFixed(1)}%`;

    const summary = adj.summary || {};
    if (adjBreakdownCounts) {
      adjBreakdownCounts.textContent = `${summary.gold_match || 0} Matched • ${summary.likely_annotation_omission || 0} Likely Omissions • ${summary.genuine_false_positive || 0} False Positives • ${summary.unsupported_inference || 0} Unsupported Jumps`;
    }

    const matchedList = report.matched_relations || [];
    const unmatchedList = report.unmatched_predictions || [];
    const missedList = report.missed_gold || [];
    const totalRelations = matchedList.length + unmatchedList.length + missedList.length;

    const cntAll = document.getElementById("cnt-gold-all");
    const cntMatched = document.getElementById("cnt-gold-matched");
    const cntUnmatched = document.getElementById("cnt-gold-unmatched");
    const cntMissed = document.getElementById("cnt-gold-missed");
    const cntGoldOnly = document.getElementById("cnt-gold-gold_only");
    const cntExtractedOnly = document.getElementById("cnt-gold-extracted_only");

    if (cntAll) cntAll.textContent = totalRelations;
    if (cntMatched) cntMatched.textContent = matchedList.length;
    if (cntUnmatched) cntUnmatched.textContent = unmatchedList.length;
    if (cntMissed) cntMissed.textContent = missedList.length;
    if (cntGoldOnly) cntGoldOnly.textContent = matchedList.length + missedList.length;
    if (cntExtractedOnly) cntExtractedOnly.textContent = matchedList.length + unmatchedList.length;

    renderGoldTableRows();
  }

  function renderGoldTableRows() {
    if (!activeGoldReport || !goldComparisonTbody) return;
    const matchedList = activeGoldReport.matched_relations || [];
    const unmatchedList = activeGoldReport.unmatched_predictions || [];
    const missedList = activeGoldReport.missed_gold || [];

    let rowsToDisplay = [];

    if (activeGoldTab === "all") {
      rowsToDisplay = [
        ...matchedList.map((r) => ({ ...r, row_type: "matched" })),
        ...unmatchedList.map((r) => ({ ...r, row_type: "unmatched" })),
        ...missedList.map((r) => ({ ...r, row_type: "missed" })),
      ];
    } else if (activeGoldTab === "matched") {
      rowsToDisplay = matchedList.map((r) => ({ ...r, row_type: "matched" }));
    } else if (activeGoldTab === "unmatched") {
      rowsToDisplay = unmatchedList.map((r) => ({ ...r, row_type: "unmatched" }));
    } else if (activeGoldTab === "missed") {
      rowsToDisplay = missedList.map((r) => ({ ...r, row_type: "missed" }));
    } else if (activeGoldTab === "gold_only") {
      rowsToDisplay = [
        ...matchedList.map((r) => ({ ...r, row_type: "matched" })),
        ...missedList.map((r) => ({ ...r, row_type: "missed" })),
      ];
    } else if (activeGoldTab === "extracted_only") {
      rowsToDisplay = [
        ...matchedList.map((r) => ({ ...r, row_type: "matched" })),
        ...unmatchedList.map((r) => ({ ...r, row_type: "unmatched" })),
      ];
    }

    if (rowsToDisplay.length === 0) {
      goldComparisonTbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 24px; color: #64748b;">No relations matching this filter.</td></tr>';
      return;
    }

    goldComparisonTbody.innerHTML = "";
    rowsToDisplay.forEach((item) => {
      const tr = document.createElement("tr");

      let statusBadge = "";
      let catBadge = "";
      let overrideSelect = "";

      if (item.row_type === "matched") {
        statusBadge = '<span class="badge-status badge-verified">MATCHED TP</span>';
        catBadge = '<span class="badge-gold-match">Gold match</span>';
        overrideSelect = '<span style="color:#64748b; font-size:11px;">Verified</span>';
      } else if (item.row_type === "unmatched") {
        statusBadge = '<span class="badge-status badge-conflict">UNMATCHED FP</span>';
        const cat = item.adjudication_category || "Ambiguous";
        if (cat === "Likely annotation omission") catBadge = '<span class="badge-omission">Likely omission</span>';
        else if (cat === "Genuine false positive") catBadge = '<span class="badge-fp">False positive</span>';
        else if (cat === "Unsupported inference") catBadge = '<span class="badge-unsupported">Unsupported jump</span>';
        else if (cat === "Duplicate or normalization issue") catBadge = '<span class="badge-duplicate">Normalization</span>';
        else catBadge = '<span class="badge-ambiguous">Ambiguous</span>';

        const reviewedFlag = item.is_reviewed ? '<br><span class="badge-reviewed-indicator">REVIEWED</span>' : "";

        overrideSelect = `
          <select class="adj-override-select" data-rel-id="${escapeHtml(item.relation_id)}">
            <option value="" disabled ${!item.is_reviewed ? "selected" : ""}>Classify...</option>
            <option value="Likely annotation omission" ${cat === "Likely annotation omission" ? "selected" : ""}>Likely omission</option>
            <option value="Genuine false positive" ${cat === "Genuine false positive" ? "selected" : ""}>False positive</option>
            <option value="Unsupported inference" ${cat === "Unsupported inference" ? "selected" : ""}>Unsupported jump</option>
            <option value="Duplicate or normalization issue" ${cat === "Duplicate or normalization issue" ? "selected" : ""}>Normalization</option>
            <option value="Ambiguous" ${cat === "Ambiguous" ? "selected" : ""}>Ambiguous</option>
          </select>
          ${reviewedFlag}
        `;
      } else if (item.row_type === "missed") {
        statusBadge = '<span class="badge-status" style="background:#fee2e2; color:#991b1b; border:1px solid #f87171;">MISSED FN</span>';
        catBadge = '<span class="badge-status badge-omitted">Reference Standard</span>';
        overrideSelect = '<span style="color:#64748b; font-size:11px;">Gold Reference</span>';
      }

      const relationText = `<strong>${escapeHtml(item.cause)}</strong> &rarr; <strong>${escapeHtml(item.effect)}</strong>`;
      const scopeText = item.is_transitive || item.gold_type === "cross_page"
        ? '<span class="edge-badge-inferred" style="margin:0;">CROSS-PAGE</span>'
        : '<span class="edge-badge-direct" style="margin:0;">DIRECT</span>';

      const quoteSnippet = item.evidence_quote
        ? `<div style="font-size:11px; color:#334155; margin-bottom:4px; font-style:italic;">"${escapeHtml(item.evidence_quote.slice(0, 150))}${item.evidence_quote.length > 150 ? "..." : ""}"</div>`
        : "";
      const expSnippet = item.adjudication_explanation
        ? `<div style="font-size:10px; color:#64748b;">${escapeHtml(item.adjudication_explanation)}</div>`
        : "";

      tr.innerHTML = `
        <td>${relationText}</td>
        <td>${scopeText}</td>
        <td>${statusBadge}</td>
        <td>${catBadge}</td>
        <td>${quoteSnippet}${expSnippet}</td>
        <td>${overrideSelect}</td>
      `;

      const sel = tr.querySelector(".adj-override-select");
      if (sel) {
        sel.addEventListener("change", async (e) => {
          const newCat = e.target.value;
          const relId = e.target.dataset.relId;
          try {
            await fetch("/api/benchmark/adjudicate", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                session_id: activeSessionId || "temp_session",
                relation_id: relId,
                category: newCat,
                note: "User manual classification override",
              }),
            });
            showNotification(`Updated adjudication to: ${newCat}`, "success", 2000);
            loadGoldComparisonData();
          } catch (err) {
            showNotification("Failed to update classification: " + err.message, "error", 4000);
          }
        });
      }

      goldComparisonTbody.appendChild(tr);
    });
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

    const isTransitive = Boolean(rel.is_transitive);
    let hopsHtml = "";
    if (isTransitive && rel.constituent_edges && rel.constituent_edges.length > 0) {
      hopsHtml = `
        <div style="font-weight:700; font-size:11px; font-family:var(--font-mono); margin:12px 0 6px 0; color:#8b5cf6;">
          CONSTITUENT REASONING HOPS (${rel.constituent_edges.length}):
        </div>
      `;
      for (const hop of rel.constituent_edges) {
        hopsHtml += `
          <div class="constituent-hop-card">
            <div style="font-weight:700; font-family:var(--font-mono); font-size:10px; color:#64748b; margin-bottom:2px;">
              HOP ${hop.hop}: ${hop.source} &rarr; ${hop.target} (Page ${hop.page_number}, ${hop.section_title})
            </div>
            <div style="font-style:italic; color:#1e293b; margin-bottom:2px;">“${hop.evidence_quote}”</div>
            <div style="font-family:var(--font-mono); font-size:9.5px; color:#64748b;">Confidence: ${(hop.confidence * 100).toFixed(0)}%</div>
          </div>
        `;
      }
    }

    const polarityColor = isTransitive ? "#8b5cf6" : (rel.effect_polarity === "negative" ? "#dc2626" : (rel.effect_polarity === "association" ? "#64748b" : "#0d9488"));
    const polarityLabel = isTransitive
      ? `INFERRED CROSS-PAGE PATH (${rel.linking_mechanism || "Transitive"})`
      : (rel.effect_polarity === "negative"
        ? "NEGATIVE EFFECT (causes reduction / inverse)"
        : (rel.effect_polarity === "association" ? "ASSOCIATION (non-directional correlation)" : "DIRECT EMPIRICAL EVIDENCE"));

    inspectorBody.innerHTML = `
      <div style="margin-bottom:16px;">
        <div class="${isTransitive ? 'edge-badge-inferred' : 'edge-badge-direct'}">
          ${polarityLabel}
        </div>
        <div style="font-size:16px; font-weight:700;">
          ${rel.cause_name}${rel.source_state ? ` <span style="font-size:12px; font-weight:500; color:#555;">[State: ${rel.source_state}]</span>` : ""}
        </div>
        <div style="font-family:var(--font-mono); font-size:11px; margin:4px 0; color:#444;">
          ${rel.is_negated ? "[REFUTED / NEGATED] " : ""}${rel.relation_type} &bull; ${isTransitive ? "INFERRED CROSS-PAGE" : "DIRECT LOCAL"}
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
      ${hopsHtml}
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
      currentLoadedPmcid = (pmcid || "").toUpperCase();
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

  // ==========================================================================
  // Phase 2.7 Pipeline Diagnostics, Error Breakdown, and Controlled Ablations
  // ==========================================================================
  let cachedDiagnosticsData = null;
  let activeErrorFilter = "all";

  async function loadDiagnosticsData() {
    const diagGrid = document.getElementById("diagnostics-stages-grid");
    const provenanceTag = document.getElementById("diagnostics-provenance-tag");

    let pmcid = currentLoadedPmcid;
    if (!pmcid && activeSessionData && activeSessionData.title) {
      const m = activeSessionData.title.match(/PMC\d+/i);
      if (m) pmcid = m[0].toUpperCase();
    }
    if (!pmcid && queryInput && queryInput.value) {
      const m = queryInput.value.match(/PMC\d+/i);
      if (m) pmcid = m[0].toUpperCase();
    }
    if (!pmcid) pmcid = "PMC1804205";

    if (provenanceTag) provenanceTag.textContent = `PMCID: ${pmcid}`;

    if (diagGrid) {
      diagGrid.innerHTML = `<div style="grid-column: 1/-1; padding: 20px; text-align: center; color: #64748b; font-family: var(--font-mono);">ANALYZING 8 PIPELINE STAGES &amp; EXTRACTED RELATIONS...</div>`;
    }

    try {
      const res = await fetch(`/api/diagnostics/pipeline/${encodeURIComponent(pmcid)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      cachedDiagnosticsData = data;
      renderDiagnosticsUI(data);
    } catch (err) {
      console.error("Diagnostics load error:", err);
      if (diagGrid) {
        diagGrid.innerHTML = `<div style="grid-column: 1/-1; padding: 14px; color: #dc2626; font-family: var(--font-mono);">Failed to load diagnostics: ${escapeHtml(err.message)}</div>`;
      }
    }
  }

  function renderDiagnosticsUI(data) {
    if (!data) return;

    // 1. Render Stages Grid
    const diagGrid = document.getElementById("diagnostics-stages-grid");
    if (diagGrid && data.stage_breakdown) {
      diagGrid.innerHTML = data.stage_breakdown.map(s => `
        <div class="stage-card">
          <div class="stage-card-header">
            <span class="stage-card-num">STAGE ${s.stage}</span>
            <span class="stage-card-status">${escapeHtml((s.status || "ACTIVE").toUpperCase())}</span>
          </div>
          <div class="stage-card-name">${escapeHtml(s.name)}</div>
          <div class="stage-card-metric">
            <span class="stage-card-count">${s.count}</span>
            <span class="stage-card-unit">${escapeHtml(s.unit || "")}</span>
          </div>
        </div>
      `).join("");
    }

    // 2. Update error counts & badges
    const counts = data.error_counts || {};
    const totalRelations = (data.diagnostic_relations || []).length;

    const setCnt = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val || 0;
    };
    setCnt("cnt-err-all", totalRelations);
    setCnt("cnt-err-direction", counts["direction_inversion"]);
    setCnt("cnt-err-negation", counts["negation_polarity"]);
    setCnt("cnt-err-speculative", counts["speculative_hypothesis"]);
    setCnt("cnt-err-alias", counts["alias_merging"]);
    setCnt("cnt-err-duplicate", counts["duplicate_normalization"]);
    setCnt("cnt-err-missing", counts["missing_direct"]);
    setCnt("cnt-err-transitive", counts["unsupported_transitive"]);
    setCnt("cnt-err-preamble", counts["citation_preamble"]);

    renderDiagnosticsTable(data.diagnostic_relations || []);
  }

  function renderDiagnosticsTable(relations) {
    const tbody = document.getElementById("diagnostics-table-tbody");
    if (!tbody) return;

    const filtered = relations.filter(r => {
      if (activeErrorFilter === "all") return true;
      return r.error_class === activeErrorFilter;
    });

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #64748b; padding: 24px; font-family: var(--font-mono);">No relations in selected category.</td></tr>`;
      return;
    }

    const badgeClassMap = {
      "direction_inversion": "badge-err-direction",
      "negation_polarity": "badge-err-negation",
      "speculative_hypothesis": "badge-err-speculative",
      "alias_merging": "badge-err-alias",
      "duplicate_normalization": "badge-err-duplicate",
      "missing_direct": "badge-err-missing",
      "unsupported_transitive": "badge-err-transitive",
      "citation_preamble": "badge-err-preamble"
    };

    tbody.innerHTML = filtered.map(r => {
      const badgeCls = badgeClassMap[r.error_class] || "badge-err-duplicate";
      return `
        <tr>
          <td>
            <strong>${escapeHtml(r.cause)}</strong> ➔ <strong>${escapeHtml(r.effect)}</strong>
            <div style="font-size: 10px; color: #64748b; margin-top: 2px;">Type: ${escapeHtml(r.relation_type || "causes")}</div>
          </td>
          <td>
            <span class="status-chip" style="font-size: 9px; padding: 1px 4px;">${r.is_cross ? "CROSS-PAGE" : "DIRECT"}</span>
          </td>
          <td>
            <span class="badge-err ${badgeCls}">${escapeHtml(r.error_class_name || r.error_class)}</span>
          </td>
          <td style="font-size: 11px;">
            <div style="font-style: italic; color: #1e293b; margin-bottom: 4px;">"${escapeHtml(r.evidence_quote || "N/A")}"</div>
            <div style="font-size: 10px; color: #64748b;">Page: ${r.page_number || "N/A"} &bull; Rule: ${escapeHtml(r.rule_source || "Syntax Clause")}</div>
          </td>
          <td style="font-size: 11px; color: #334155;">
            ${escapeHtml(r.rationale || "Diagnostic analysis performed.")}
          </td>
        </tr>
      `;
    }).join("");
  }

  // Error Filter Chips Click
  const errorChipsContainer = document.getElementById("diagnostics-error-chips");
  if (errorChipsContainer) {
    errorChipsContainer.addEventListener("click", (e) => {
      const chip = e.target.closest(".status-chip");
      if (!chip) return;
      const filter = chip.dataset.errorFilter;
      if (!filter) return;
      activeErrorFilter = filter;
      errorChipsContainer.querySelectorAll(".status-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      if (cachedDiagnosticsData) {
        renderDiagnosticsTable(cachedDiagnosticsData.diagnostic_relations || []);
      }
    });
  }

  // Diagnostics Reload
  const diagReloadBtn = document.getElementById("diagnostics-reload-btn");
  if (diagReloadBtn) {
    diagReloadBtn.addEventListener("click", () => {
      loadDiagnosticsData();
    });
  }

  // Live Controlled Ablations Button & Runner
  const runAblationsBtn = document.getElementById("run-ablations-btn");
  if (runAblationsBtn) {
    runAblationsBtn.addEventListener("click", async () => {
      const tbody = document.getElementById("diagnostics-ablations-tbody");
      if (tbody) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #64748b; padding: 20px; font-family: var(--font-mono);">RUNNING CONTROLLED ABLATION EXPERIMENTS ON REFERENCE PAPERS...</td></tr>`;
      }
      runAblationsBtn.disabled = true;
      runAblationsBtn.textContent = "RUNNING...";

      try {
        const res = await fetch("/api/diagnostics/ablations");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        renderAblationsTable(data.ablations || []);
      } catch (err) {
        console.error("Ablations run error:", err);
        if (tbody) {
          tbody.innerHTML = `<tr><td colspan="6" style="color: #dc2626; padding: 14px;">Ablation benchmark failed: ${escapeHtml(err.message)}</td></tr>`;
        }
      } finally {
        runAblationsBtn.disabled = false;
        runAblationsBtn.textContent = "▶ RUN LIVE ABLATIONS";
      }
    });
  }

  function renderAblationsTable(ablations) {
    const tbody = document.getElementById("diagnostics-ablations-tbody");
    if (!tbody) return;

    tbody.innerHTML = ablations.map(a => {
      const isBase = a.variant === "baseline";
      const rowCls = isBase ? "ablation-row-baseline" : "";
      return `
        <tr class="${rowCls}">
          <td>
            <strong>${escapeHtml(a.name)}</strong>
            <div style="font-size: 10px; color: #64748b;">${escapeHtml(a.variant)}</div>
          </td>
          <td>
            <div>${(a.direct_precision * 100).toFixed(1)}% / ${(a.direct_recall * 100).toFixed(1)}%</div>
            <strong style="font-size: 12px;">F1: ${a.direct_f1.toFixed(4)}</strong>
            <div style="font-size: 9px; color: #64748b;">TP:${a.direct_tp} FP:${a.direct_fp} FN:${a.direct_fn}</div>
          </td>
          <td>
            <div>${(a.cross_precision * 100).toFixed(1)}% / ${(a.cross_recall * 100).toFixed(1)}%</div>
            <strong style="font-size: 12px;">F1: ${a.cross_f1.toFixed(4)}</strong>
            <div style="font-size: 9px; color: #64748b;">TP:${a.cross_tp} FP:${a.cross_fp} FN:${a.cross_fn}</div>
          </td>
          <td>
            <strong style="font-size: 13px; color: ${a.false_transitive_jumps > 3 ? '#dc2626' : '#0f172a'};">${a.false_transitive_jumps}</strong>
          </td>
          <td>${a.runtime_seconds.toFixed(2)}s</td>
          <td style="font-size: 11px;">
            ${escapeHtml(a.empirical_finding || a.impact || "")}
          </td>
        </tr>
      `;
    }).join("");
  }

  async function loadChainsData() {
    const cpTbody = document.getElementById("cross-paper-tbody");
    const ablTbody = document.getElementById("phase3-ablation-tbody");
    if (cpTbody) {
      cpTbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #64748b; padding: 18px; font-family: var(--font-mono);">LOADING VERIFIED CROSS-PAPER BRIDGES...</td></tr>`;
    }
    if (ablTbody) {
      ablTbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #64748b; padding: 18px; font-family: var(--font-mono);">LOADING 8-WAY ABLATION MATRIX...</td></tr>`;
    }

    try {
      const [resResults, resBridges] = await Promise.all([
        fetch("/api/phase3/results"),
        fetch("/api/phase3/cross-paper-links")
      ]);

      if (resResults.ok) {
        const data = await resResults.json();
        renderPhase3Results(data);
      }
      if (resBridges.ok) {
        const bridgesData = await resBridges.json();
        renderCrossPaperBridges(bridgesData);
      }
    } catch (err) {
      console.error("Error loading Phase 3 data:", err);
      if (cpTbody) cpTbody.innerHTML = `<tr><td colspan="6" style="color: #dc2626; padding: 12px;">Failed to load Phase 3 data: ${escapeHtml(err.message)}</td></tr>`;
    }
  }

  const chainsReloadBtn = document.getElementById("chains-reload-btn");
  if (chainsReloadBtn) {
    chainsReloadBtn.addEventListener("click", () => loadChainsData());
  }

  function renderCrossPaperBridges(bridgesList) {
    const cpTbody = document.getElementById("cross-paper-tbody");
    if (!cpTbody) return;

    let allBridges = [];
    bridgesList.forEach(item => {
      (item.bridges || []).forEach(b => {
        allBridges.push({ ...b, pair_desc: item.description });
      });
    });

    if (allBridges.length === 0) {
      cpTbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #64748b; padding: 16px;">No cross-paper bridges discovered yet.</td></tr>`;
      return;
    }

    cpTbody.innerHTML = allBridges.map(b => `
      <tr>
        <td>
          <strong>${escapeHtml(b.source_entity)}</strong>
          <div style="font-size: 10px; color: #64748b;">${escapeHtml(b.source_doc_id)} (p. ${b.page_doc1})</div>
        </td>
        <td>
          <span class="status-chip active" style="font-size: 11px;">${escapeHtml(b.pivot_entity)}</span>
          <div style="font-size: 9px; color: #64748b; margin-top: 3px;">${escapeHtml(b.pair_desc)}</div>
        </td>
        <td>
          <strong>${escapeHtml(b.target_entity)}</strong>
          <div style="font-size: 10px; color: #64748b;">${escapeHtml(b.target_doc_id)} (p. ${b.page_doc2})</div>
        </td>
        <td>
          <span style="display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; background: ${b.mechanism_compatibility === 'COMPATIBLE' ? '#ecfdf5; color: #047857;' : '#fef2f2; color: #b91c1c;'}">
            ${escapeHtml(b.mechanism_compatibility)}
          </span>
        </td>
        <td>
          <strong style="font-family: var(--font-mono); font-size: 12px;">${b.confidence.toFixed(4)}</strong>
        </td>
        <td style="font-size: 11px;">
          <div style="margin-bottom: 4px;"><strong>Doc 1:</strong> "${escapeHtml((b.evidence_doc1 || '').slice(0, 75))}..."</div>
          <div><strong>Doc 2:</strong> "${escapeHtml((b.evidence_doc2 || '').slice(0, 75))}..."</div>
        </td>
      </tr>
    `).join("");
  }

  function renderPhase3Results(data) {
    if (!data) return;

    // Dynamically update KPI cards from canonical data
    const full = data.full_evaluation || {};
    const splits = full.splits || {};

    let totalChains = 0;
    let directSupported = 0;
    let multiHopSupported = 0;
    let plausibleComposed = 0;
    let unsupportedShortcuts = 0;
    let indeterminate = 0;

    Object.values(splits).forEach(s => {
      const dist = s.composition_class_distribution || {};
      directSupported += (dist.DIRECT_SUPPORTED || 0);
      multiHopSupported += (dist.MULTI_HOP_SUPPORTED || 0);
      plausibleComposed += (dist.PLAUSIBLE_COMPOSED || 0);
      unsupportedShortcuts += (dist.UNSUPPORTED_SHORTCUT || 0);
      indeterminate += (dist.INDETERMINATE || 0);
    });
    totalChains = directSupported + multiHopSupported + plausibleComposed + unsupportedShortcuts + indeterminate;

    const kpiTotal = document.getElementById("chains-kpi-total");
    if (kpiTotal && totalChains > 0) kpiTotal.textContent = totalChains;

    const kpiSupported = document.getElementById("chains-kpi-supported");
    if (kpiSupported && totalChains > 0) kpiSupported.textContent = (directSupported + multiHopSupported + plausibleComposed);

    const kpiShortcuts = document.getElementById("chains-kpi-shortcuts");
    if (kpiShortcuts && totalChains > 0) kpiShortcuts.textContent = unsupportedShortcuts;

    const devSplit = splits.dev || {};
    const kpiDev = document.getElementById("chains-kpi-f1-dev");
    if (kpiDev && devSplit.direct_f1_mean !== undefined) {
      kpiDev.textContent = devSplit.direct_f1_mean.toFixed(4);
    }

    const extSplit = splits.external || {};
    const kpiExt = document.getElementById("chains-kpi-f1-ext");
    if (kpiExt && extSplit.cross_f1_mean !== undefined) {
      kpiExt.textContent = extSplit.cross_f1_mean.toFixed(4);
    }

    // Dynamic Cross-Paper Bridges KPI
    const crossPairs = full.cross_paper_linking || [];
    const totalBridges = crossPairs.reduce((acc, p) => acc + (p.bridges_discovered_count || 0), 0);
    const kpiBridges = document.getElementById("chains-kpi-bridges");
    if (kpiBridges && totalBridges > 0) {
      kpiBridges.textContent = totalBridges;
    }

    const ablTbody = document.getElementById("phase3-ablation-tbody");
    if (ablTbody && data.ablation_matrix) {
      ablTbody.innerHTML = data.ablation_matrix.map(row => {
        const isFull = row.configuration.includes("Full");
        const isBase = row.configuration.includes("Baseline");
        const cls = isFull ? "ablation-row-phase3" : (isBase ? "ablation-row-baseline" : "");
        const s = row.scores || {};
        return `
          <tr class="${cls}">
            <td>
              <strong>${escapeHtml(row.configuration)}</strong>
            </td>
            <td>
              <div>${s.dev?.direct_f1?.toFixed(4) || "-"} / ${s.dev?.cross_f1?.toFixed(4) || "-"}</div>
              <div style="font-size: 9px; color: #64748b;">FJ: ${s.dev?.false_jumps ?? "-"}</div>
            </td>
            <td>
              <div>${s.train?.direct_f1?.toFixed(4) || "-"} / ${s.train?.cross_f1?.toFixed(4) || "-"}</div>
              <div style="font-size: 9px; color: #64748b;">FJ: ${s.train?.false_jumps ?? "-"}</div>
            </td>
            <td>
              <div>${s.locked_test?.direct_f1?.toFixed(4) || "-"} / ${s.locked_test?.cross_f1?.toFixed(4) || "-"}</div>
              <div style="font-size: 9px; color: #64748b;">FJ: ${s.locked_test?.false_jumps ?? "-"}</div>
            </td>
            <td>
              <div>${s.external?.direct_f1?.toFixed(4) || "-"} / ${s.external?.cross_f1?.toFixed(4) || "-"}</div>
              <div style="font-size: 9px; color: #64748b;">FJ: ${s.external?.false_jumps ?? "-"}</div>
            </td>
          </tr>
        `;
      }).join("");
    }
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
  renderRecentExamples();
})();
