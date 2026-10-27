const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const ARTIFACT_DIR = "/home/tk/.gemini/antigravity-cli/brain/ef3fc705-911a-4157-bc28-1d5bdf2aa3f1";

async function runPhase26Verification() {
  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });

  const consoleErrors = [];
  const networkErrors = [];

  // ==========================================
  // 1. DESKTOP VIEWPORT TEST (1440x900)
  // ==========================================
  console.log("--- 1. Testing Desktop Split-Graph View (1440x900) ---");
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      consoleErrors.push(`Console Error: ${msg.text()}`);
    }
  });

  page.on("pageerror", (err) => {
    consoleErrors.push(`Page Error: ${err.message}`);
  });

  page.on("requestfailed", (req) => {
    networkErrors.push(`Failed Request: ${req.url()} (${req.failure() ? req.failure().errorText : "failed"})`);
  });

  await page.goto("http://127.0.0.1:8000/", { waitUntil: "networkidle" });

  // Verify single-graph view is default
  const isSplitInitially = await page.evaluate(() => {
    const vp = document.getElementById("graph-viewport");
    return vp && vp.classList.contains("split-mode");
  });
  console.log("Initial single-graph view default:", !isSplitInitially);
  if (isSplitInitially) throw new Error("Graph view should default to single graph!");

  // Load PMC1804205 example via Plus Menu -> Library
  console.log("Loading PMC1804205 from library...");
  await page.click("#plus-btn");
  await page.waitForTimeout(300);
  await page.click("#menu-browse-examples-btn");
  await page.waitForTimeout(400);

  // Search for PmrA (PMC1804205)
  await page.fill("#library-search-input", "PmrA");
  await page.waitForTimeout(300);

  const loadBtn = await page.waitForSelector('.library-card [data-action="load"]');
  await loadBtn.click();
  await page.waitForTimeout(400);

  // Click RUN EXTRACTION
  await page.click("#regenerate-btn");
  await page.waitForTimeout(1500);

  // Toggle Split View ON
  console.log("Toggling Split View ON...");
  const splitBtn = await page.waitForSelector("#split-graph-toggle-btn");
  await splitBtn.click();
  await page.waitForTimeout(1000);

  // Verify split mode active
  const isSplitActive = await page.evaluate(() => {
    const vp = document.getElementById("graph-viewport");
    const goldPanel = document.getElementById("gold-graph-panel");
    const extHeader = document.getElementById("extracted-panel-header");
    return vp.classList.contains("split-mode") &&
           !goldPanel.classList.contains("hidden") &&
           !extHeader.classList.contains("hidden");
  });
  console.log("Split mode container active:", isSplitActive);
  if (!isSplitActive) throw new Error("Split mode failed to activate!");

  // Verify gold edges and nodes exist
  const goldStats = await page.evaluate(() => {
    const nodes = document.querySelectorAll("#gold-nodes-layer .graph-node").length;
    const edges = document.querySelectorAll("#gold-edges-layer .graph-edge").length;
    const badge = document.getElementById("gold-panel-badge") ? document.getElementById("gold-panel-badge").textContent : "";
    return { nodes, edges, badge };
  });
  console.log("Gold standard graph stats:", goldStats);
  if (goldStats.edges === 0) throw new Error("Gold graph edges were not rendered!");

  // Screenshot desktop split view
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "desktop_split_graph_pmc1804205.png") });
  console.log("Saved desktop_split_graph_pmc1804205.png");

  // Click a gold edge to verify evidence inspection
  console.log("Inspecting gold edge...");
  await page.evaluate(() => {
    const firstEdge = document.querySelector("#gold-edges-layer .graph-edge");
    if (firstEdge) firstEdge.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  });
  await page.waitForTimeout(400);

  const inspectorText = await page.evaluate(() => {
    const ins = document.getElementById("evidence-inspector");
    return ins ? ins.innerText : "";
  });
  console.log("Evidence inspector text preview:", inspectorText.slice(0, 100));
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "desktop_split_graph_gold_edge_inspected.png") });
  console.log("Saved desktop_split_graph_gold_edge_inspected.png");

  // Toggle Split View OFF
  console.log("Toggling Split View OFF...");
  await splitBtn.click();
  await page.waitForTimeout(500);

  const isSplitOff = await page.evaluate(() => {
    const vp = document.getElementById("graph-viewport");
    const goldPanel = document.getElementById("gold-graph-panel");
    return !vp.classList.contains("split-mode") && goldPanel.classList.contains("hidden");
  });
  console.log("Split view correctly reverted to single mode:", isSplitOff);
  if (!isSplitOff) throw new Error("Failed to revert to single graph mode!");

  // Test non-benchmark document (empty / unavailable state)
  console.log("Testing ad-hoc snippet without reference gold...");
  await page.click("#plus-btn");
  await page.waitForTimeout(300);
  await page.click('.menu-example-item[data-example="example_a"]');
  await page.waitForTimeout(300);
  await page.click("#regenerate-btn");
  await page.waitForTimeout(1200);

  // Toggle Split View for ad-hoc snippet
  await splitBtn.click();
  await page.waitForTimeout(600);

  const unavailableShown = await page.evaluate(() => {
    const unav = document.getElementById("gold-graph-unavailable");
    return unav && !unav.classList.contains("hidden");
  });
  console.log("Gold unavailable clean state shown for ad-hoc snippet:", unavailableShown);
  if (!unavailableShown) throw new Error("Unavailable state should be displayed when gold is not present!");

  await page.screenshot({ path: path.join(ARTIFACT_DIR, "desktop_split_graph_unavailable_state.png") });
  console.log("Saved desktop_split_graph_unavailable_state.png");

  // ==========================================
  // 2. MOBILE VIEWPORT TEST (390x844)
  // ==========================================
  console.log("--- 2. Testing Mobile Stacked Split-Graph View (390x844) ---");
  const mobilePage = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await mobilePage.goto("http://127.0.0.1:8000/", { waitUntil: "networkidle" });

  await mobilePage.click("#plus-btn");
  await mobilePage.waitForTimeout(300);
  await mobilePage.click("#menu-browse-examples-btn");
  await mobilePage.waitForTimeout(400);

  await mobilePage.fill("#library-search-input", "PmrA");
  await mobilePage.waitForTimeout(300);

  const mobileLoadBtn = await mobilePage.waitForSelector('.library-card [data-action="load"]');
  await mobileLoadBtn.click();
  await mobilePage.waitForTimeout(400);

  await mobilePage.click("#regenerate-btn");
  await mobilePage.waitForTimeout(1500);

  const mobileSplitBtn = await mobilePage.waitForSelector("#split-graph-toggle-btn");
  await mobileSplitBtn.click();
  await mobilePage.waitForTimeout(800);

  const mobileLayout = await mobilePage.evaluate(() => {
    const vp = document.getElementById("graph-viewport");
    const style = window.getComputedStyle(vp);
    const ext = document.getElementById("extracted-graph-panel");
    const gold = document.getElementById("gold-graph-panel");
    return {
      flexDirection: style.flexDirection,
      extHeight: ext ? ext.getBoundingClientRect().height : 0,
      goldHeight: gold ? gold.getBoundingClientRect().height : 0,
    };
  });
  console.log("Mobile layout metrics:", mobileLayout);

  await mobilePage.screenshot({ path: path.join(ARTIFACT_DIR, "mobile_split_graph_stacked.png") });
  console.log("Saved mobile_split_graph_stacked.png");

  await browser.close();

  // Audit results summary
  console.log("\n================ AUDIT SUMMARY ================");
  console.log("Console Errors:", consoleErrors.length === 0 ? "0 (CLEAN)" : consoleErrors);
  console.log("Network Errors:", networkErrors.length === 0 ? "0 (CLEAN)" : networkErrors);

  if (consoleErrors.length > 0 || networkErrors.length > 0) {
    throw new Error(`Audit discovered errors: Console=${consoleErrors.length}, Network=${networkErrors.length}`);
  }

  console.log("✓ Phase 2.6 Live Split-Graph UI Acceptance Audit PASSED!");
}

runPhase26Verification().catch((err) => {
  console.error("Audit Execution Error:", err);
  process.exit(1);
});
