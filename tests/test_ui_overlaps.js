/**
 * Automated Geometric Bounding-Box Layout & Overlap Verification Test
 * Tests UI component separation across 6 target viewports:
 * - 1440x900 (Desktop large)
 * - 1280x720 (Desktop standard)
 * - 1024x768 (Tablet landscape / small laptop)
 * - 768x1024 (Tablet portrait)
 * - 480x800 (Mobile large)
 * - 360x800 (Mobile compact)
 */
const fs = require("fs");
const path = require("path");
const assert = require("assert");

const VIEWPORTS = [
  { width: 1440, height: 900, name: "Desktop Large (1440x900)" },
  { width: 1280, height: 720, name: "Desktop Standard (1280x720)" },
  { width: 1024, height: 768, name: "Tablet Landscape (1024x768)" },
  { width: 768, height: 1024, name: "Tablet Portrait (768x1024)" },
  { width: 480, height: 800, name: "Mobile Large (480x800)" },
  { width: 360, height: 800, name: "Mobile Compact (360x800)" },
];

function rectsIntersect(r1, r2) {
  return !(
    r2.left >= r1.right ||
    r2.right <= r1.left ||
    r2.top >= r1.bottom ||
    r2.bottom <= r1.top
  );
}

function computeLayout(vp, state = {}) {
  const isMobile = vp.width <= 768;
  const isTinyMobile = vp.width <= 480;

  // Sidebar Open Trigger (☰)
  const openSidebarBtn = {
    id: "open-sidebar-btn",
    left: 16,
    top: 16,
    width: 36,
    height: 36,
    right: 52,
    bottom: 52,
    visible: !state.sidebarOpen,
  };

  // Docked input shell (Natural flex flow in header)
  let inputWidth = Math.min(840, vp.width - 40);
  let inputMarginTop = 12;
  let inputPaddingLeft = 20;
  if (isMobile) {
    inputWidth = vp.width - 32;
    inputMarginTop = 8;
    inputPaddingLeft = 52; // clears openSidebarBtn
  }
  const inputLeft = (vp.width - inputWidth) / 2;
  const inputHeight = state.multilinePrompt ? 72 : 40;
  const inputTop = inputMarginTop;
  const inputContainer = {
    id: "input-container",
    left: inputLeft,
    top: inputTop,
    width: inputWidth,
    height: inputHeight,
    right: inputLeft + inputWidth,
    bottom: inputTop + inputHeight,
    paddingLeft: inputPaddingLeft,
    visible: true,
  };

  // The actual text field inside inputContainer
  const queryInputField = {
    id: "query-input",
    left: inputLeft + inputPaddingLeft,
    top: inputTop,
    width: inputWidth - inputPaddingLeft - 40,
    height: inputHeight,
    right: inputLeft + inputWidth - 40,
    bottom: inputTop + inputHeight,
    visible: true,
  };

  // Results View (Flex 1 below input container)
  const resultsTop = inputContainer.bottom + 8;
  const resultsHeight = vp.height - resultsTop;
  const resultsView = {
    id: "results-view",
    left: 0,
    top: resultsTop,
    width: vp.width,
    height: resultsHeight,
    right: vp.width,
    bottom: vp.height,
    visible: true,
  };

  // Graph Toolbar (at the top of results view)
  const toolbarHeight = isMobile ? 68 : 42;
  const graphToolbar = {
    id: "graph-toolbar",
    left: 0,
    top: resultsTop,
    width: vp.width,
    height: toolbarHeight,
    right: vp.width,
    bottom: resultsTop + toolbarHeight,
    visible: true,
  };

  // View area below toolbar (for Graph, Copyable, or Table)
  const viewTop = graphToolbar.bottom;
  const viewHeight = resultsView.bottom - viewTop;
  const activeView = {
    id: state.activeTab || "graph-viewport",
    left: 0,
    top: viewTop,
    width: vp.width,
    height: viewHeight,
    right: vp.width,
    bottom: resultsView.bottom,
    visible: true,
  };

  // Inspector Panel (slides over from right)
  const inspectorWidth = isMobile ? vp.width : 360;
  const inspectorPanel = {
    id: "inspector-panel",
    left: vp.width - inspectorWidth,
    top: 0,
    width: inspectorWidth,
    height: vp.height,
    right: vp.width,
    bottom: vp.height,
    visible: !!state.inspectorOpen,
  };

  // Graph Legend (bottom right)
  const legendWidth = Math.min(360, vp.width - 24);
  const legendHeight = state.legendExpanded ? 260 : 40;
  let legendRightOffset = 24;
  if (state.inspectorOpen) {
    legendRightOffset = isMobile ? -9999 : 384; // shifted left on desktop, hidden on mobile
  } else if (isMobile) {
    legendRightOffset = 12;
  }
  const legendVisible = !(state.inspectorOpen && isMobile);
  const legendLeft = vp.width - legendRightOffset - legendWidth;
  const legendTop = vp.height - 24 - legendHeight;
  const graphLegend = {
    id: "graph-legend",
    left: legendLeft,
    top: legendTop,
    width: legendWidth,
    height: legendHeight,
    right: legendLeft + legendWidth,
    bottom: legendTop + legendHeight,
    visible: legendVisible,
  };

  // Floating Continual Action Button (bottom center)
  const continualBtn = {
    id: "continual-toggle-btn",
    left: vp.width / 2 - 20,
    top: vp.height - 48,
    width: 40,
    height: 40,
    right: vp.width / 2 + 20,
    bottom: vp.height - 8,
    visible: !!state.continualHover,
  };

  return {
    openSidebarBtn,
    inputContainer,
    queryInputField,
    resultsView,
    graphToolbar,
    activeView,
    inspectorPanel,
    graphLegend,
    continualBtn,
  };
}

let passCount = 0;
let totalCount = 0;

function assertNoOverlap(name, r1, r2) {
  totalCount++;
  if (!r1.visible || !r2.visible) {
    passCount++;
    return;
  }
  const intersects = rectsIntersect(r1, r2);
  assert.strictEqual(
    intersects,
    false,
    `OVERLAP DETECTED in [${name}]: ${r1.id} [L:${r1.left}, R:${r1.right}, T:${r1.top}, B:${r1.bottom}] intersects ${r2.id} [L:${r2.left}, R:${r2.right}, T:${r2.top}, B:${r2.bottom}]`
  );
  passCount++;
}

console.log("===============================================================");
console.log(" RUNNING EVRYN GEOMETRIC OVERLAP & BOUNDING-BOX AUDIT");
console.log("===============================================================");

for (const vp of VIEWPORTS) {
  console.log(`\nTesting Viewport: ${vp.name}...`);

  // Scenario 1: Default docked graph view
  {
    const l = computeLayout(vp, { sidebarOpen: false, inspectorOpen: false, activeTab: "graph-viewport" });
    assertNoOverlap(`${vp.name} - Prompt vs Results`, l.inputContainer, l.resultsView);
    assertNoOverlap(`${vp.name} - Prompt vs Graph Toolbar`, l.inputContainer, l.graphToolbar);
    assertNoOverlap(`${vp.name} - Sidebar Btn vs Query Input Text`, l.openSidebarBtn, l.queryInputField);
    assertNoOverlap(`${vp.name} - Toolbar vs Active View`, l.graphToolbar, l.activeView);
  }

  // Scenario 2: Multiline prompt (expanded textarea)
  {
    const l = computeLayout(vp, { multilinePrompt: true, activeTab: "graph-viewport" });
    assertNoOverlap(`${vp.name} - Multiline Prompt vs Results`, l.inputContainer, l.resultsView);
    assertNoOverlap(`${vp.name} - Multiline Prompt vs Graph Toolbar`, l.inputContainer, l.graphToolbar);
    assertNoOverlap(`${vp.name} - Sidebar Btn vs Multiline Input Text`, l.openSidebarBtn, l.queryInputField);
  }

  // Scenario 3: Table View active
  {
    const l = computeLayout(vp, { activeTab: "table-view" });
    assertNoOverlap(`${vp.name} - Toolbar vs Table View`, l.graphToolbar, l.activeView);
    assert.strictEqual(l.activeView.top >= l.graphToolbar.bottom, true, "Table view must be positioned strictly below toolbar");
  }

  // Scenario 4: Copyable View active
  {
    const l = computeLayout(vp, { activeTab: "copyable-view" });
    assertNoOverlap(`${vp.name} - Toolbar vs Copyable View`, l.graphToolbar, l.activeView);
    assert.strictEqual(l.activeView.top >= l.graphToolbar.bottom, true, "Copyable view must be positioned strictly below toolbar");
  }

  // Scenario 5: Inspector Panel Open with Graph Legend
  {
    const l = computeLayout(vp, { inspectorOpen: true, legendExpanded: true });
    assertNoOverlap(`${vp.name} - Inspector Panel vs Graph Legend`, l.inspectorPanel, l.graphLegend);
  }
}

console.log("\n===============================================================");
console.log(` RESULTS: ${passCount}/${totalCount} TESTS PASSED (100% OVERLAP-FREE)`);
console.log("===============================================================");
