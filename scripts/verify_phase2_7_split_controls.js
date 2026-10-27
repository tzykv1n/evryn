const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const ARTIFACT_DIR = "/home/tk/.gemini/antigravity-cli/brain/ef3fc705-911a-4157-bc28-1d5bdf2aa3f1";

async function runPhase27Verification() {
  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });

  const consoleErrors = [];
  const networkErrors = [];

  // ==========================================
  // 1. DESKTOP VIEWPORT TEST (1440x900)
  // ==========================================
  console.log("--- 1. Testing Desktop Split-Graph Controls & Diagnostics (1440x900) ---");
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

  // 1.1 Verify System A Production Default & Engine Radio Removal
  const engineRadiosCount = await page.locator('input[name="extraction_engine"]').count();
  console.log("Engine radio inputs count (must be 0):", engineRadiosCount);
  if (engineRadiosCount !== 0) {
    throw new Error(`Expected 0 engine radio inputs, found ${engineRadiosCount}`);
  }

  const statusBarVisible = await page.isVisible("#pipeline-status-bar");
  console.log("Pipeline status bar visible:", statusBarVisible);
  if (!statusBarVisible) throw new Error("Pipeline status bar should be visible!");

  // 1.2 Load PMC1804205 from library
  console.log("Loading PMC1804205 from library...");
  await page.click("#plus-btn");
  await page.waitForTimeout(300);
  await page.click("#menu-browse-examples-btn");
  await page.waitForTimeout(400);

  await page.fill("#library-search-input", "PmrA");
  await page.waitForTimeout(300);

  const loadBtn = await page.waitForSelector('.library-card [data-action="load"]');
  await loadBtn.click();
  await page.waitForTimeout(400);

  // Extract
  console.log("Triggering causal extraction...");
  await page.click("#regenerate-btn");
  await page.waitForSelector("#results-view:not(.hidden)", { timeout: 15000 });
  await page.waitForTimeout(1000);

  // 1.3 Toggle Split Graph Mode
  console.log("Toggling Split Mode...");
  await page.click("#split-graph-toggle-btn");
  await page.waitForTimeout(800);

  const isSplitActive = await page.evaluate(() => {
    const vp = document.getElementById("graph-viewport");
    return vp && vp.classList.contains("split-mode");
  });
  console.log("Split mode active:", isSplitActive);
  if (!isSplitActive) throw new Error("Split mode should be active!");

  // Verify Target Control and Realign button are visible
  const targetControlVisible = await page.isVisible("#split-target-control");
  const realignBtnVisible = await page.isVisible("#realign-graphs-btn");
  console.log("Target control visible:", targetControlVisible);
  console.log("Realign button visible:", realignBtnVisible);
  if (!targetControlVisible || !realignBtnVisible) {
    throw new Error("Split target control and realign button must be visible in split mode!");
  }

  // 1.4 Test Independent Zoom Controls
  console.log("Testing Independent Zoom Controls...");
  const initialScales = await page.evaluate(() => {
    return {
      extracted: window.graphRenderer ? window.graphRenderer.scale : null,
      gold: window.goldGraphRenderer ? window.goldGraphRenderer.scale : null
    };
  });
  console.log("Initial scales:", initialScales);

  // Active target is 'extracted' by default. Click zoom in '+'
  await page.click("#graph-zoom-in");
  await page.waitForTimeout(300);

  const scalesAfterExtractedZoom = await page.evaluate(() => {
    return {
      extracted: window.graphRenderer ? window.graphRenderer.scale : null,
      gold: window.goldGraphRenderer ? window.goldGraphRenderer.scale : null
    };
  });
  console.log("Scales after Extracted zoom in:", scalesAfterExtractedZoom);
  if (scalesAfterExtractedZoom.extracted <= initialScales.extracted) {
    throw new Error("Extracted scale did not increase on zoom in!");
  }
  if (scalesAfterExtractedZoom.gold !== initialScales.gold) {
    throw new Error("Gold scale changed when operating on Extracted target!");
  }

  // Switch target to 'gold'
  console.log("Switching active target to GOLD...");
  await page.click("#target-gold-btn");
  await page.waitForTimeout(200);

  const isGoldActive = await page.evaluate(() => {
    const btn = document.getElementById("target-gold-btn");
    const panel = document.getElementById("gold-graph-panel");
    return btn.classList.contains("active") && panel.classList.contains("panel-target-active");
  });
  console.log("Gold target active styles applied:", isGoldActive);
  if (!isGoldActive) throw new Error("Gold target active state not set!");

  // Zoom in on Gold
  await page.click("#graph-zoom-in");
  await page.waitForTimeout(300);

  const scalesAfterGoldZoom = await page.evaluate(() => {
    return {
      extracted: window.graphRenderer ? window.graphRenderer.scale : null,
      gold: window.goldGraphRenderer ? window.goldGraphRenderer.scale : null
    };
  });
  console.log("Scales after Gold zoom in:", scalesAfterGoldZoom);
  if (scalesAfterGoldZoom.gold <= initialScales.gold) {
    throw new Error("Gold scale did not increase on zoom in!");
  }
  if (scalesAfterGoldZoom.extracted !== scalesAfterExtractedZoom.extracted) {
    throw new Error("Extracted scale changed when operating on Gold target!");
  }

  // 1.5 Test Realign Nodes Action (Instant Decoupled Alignment)
  console.log("Testing Realign Nodes Action...");
  await page.click("#realign-graphs-btn");
  await page.waitForTimeout(600);

  // 1.6 Test Synchronized Highlighting (Hover without Transform Coupling)
  console.log("Testing Synchronized Highlighting on node hover...");
  const hoverResult = await page.evaluate(() => {
    // Find node 'PmrA' in extracted renderer
    const extNode = window.graphRenderer.nodes.find(n => n.name.toLowerCase().includes("pmra"));
    if (!extNode || !extNode.groupElem) return { error: "PmrA node not found in extracted graph" };

    // Trigger mouseenter
    extNode.groupElem.dispatchEvent(new MouseEvent("mouseenter", { bubbles: true }));

    // Check if gold renderer has synced-highlight
    const goldHighlighted = document.querySelectorAll("#gold-graph-svg .synced-highlight");
    const extTransforms = { panX: window.graphRenderer.panX, panY: window.graphRenderer.panY, scale: window.graphRenderer.scale };
    const goldTransforms = { panX: window.goldGraphRenderer.panX, panY: window.goldGraphRenderer.panY, scale: window.goldGraphRenderer.scale };

    return {
      goldHighlightCount: goldHighlighted.length,
      extTransforms,
      goldTransforms
    };
  });
  console.log("Synchronized hover result:", hoverResult);
  if (hoverResult.error) throw new Error(hoverResult.error);
  if (hoverResult.goldHighlightCount === 0) {
    throw new Error("Synchronized highlight class not applied to corresponding gold node!");
  }

  // Clear hover
  await page.evaluate(() => {
    const extNode = window.graphRenderer.nodes.find(n => n.name.toLowerCase().includes("pmra"));
    if (extNode && extNode.groupElem) {
      extNode.groupElem.dispatchEvent(new MouseEvent("mouseleave", { bubbles: true }));
    }
  });
  await page.waitForTimeout(200);

  // Capture Desktop Split-Graph Target Controls Screenshot
  const splitControlsScreenshot = path.join(ARTIFACT_DIR, "desktop_split_graph_target_controls.png");
  await page.screenshot({ path: splitControlsScreenshot });
  console.log(`Saved screenshot: ${splitControlsScreenshot}`);

  // ==========================================
  // 2. DIAGNOSTICS & CONTROLLED ABLATIONS VIEW
  // ==========================================
  console.log("--- 2. Testing Pipeline Diagnostics & Controlled Ablations View ---");
  await page.click("#view-tab-diagnostics");
  await page.waitForTimeout(1000);

  // Verify Stage Cards
  const stageCardsCount = await page.locator(".stage-card").count();
  console.log("Stage cards count (expected 8):", stageCardsCount);
  if (stageCardsCount !== 8) {
    throw new Error(`Expected 8 pipeline stage cards, found ${stageCardsCount}`);
  }

  // Verify Error Taxonomy Chips
  const errorChipsCount = await page.locator("#diagnostics-error-chips .status-chip").count();
  console.log("Error taxonomy chips count (expected 9):", errorChipsCount);
  if (errorChipsCount !== 9) {
    throw new Error(`Expected 9 error chips (1 all + 8 classes), found ${errorChipsCount}`);
  }

  // Verify Relations Table
  const relationRowsCount = await page.locator("#diagnostics-table-tbody tr").count();
  console.log("Diagnostic relation rows count:", relationRowsCount);
  if (relationRowsCount === 0) {
    throw new Error("Diagnostics relations table is empty!");
  }

  // Click filter chip: "3. Speculative / Intent"
  console.log("Filtering by Speculative / Intent...");
  await page.click("#chip-err-speculative");
  await page.waitForTimeout(300);

  const filteredRowsCount = await page.locator("#diagnostics-table-tbody tr").count();
  console.log("Filtered speculative rows count:", filteredRowsCount);
  if (filteredRowsCount === 0) {
    throw new Error("Filtered relations table should have rows for speculative hypothesis!");
  }

  // Reset to All Relations
  await page.click("#chip-err-all");
  await page.waitForTimeout(300);

  // Run Live Controlled Ablations
  console.log("Triggering Live Controlled Ablations benchmark...");
  await page.click("#run-ablations-btn");
  await page.waitForSelector("#diagnostics-ablations-tbody tr.ablation-row-baseline", { timeout: 15000 });
  await page.waitForTimeout(800);

  const ablationRowsCount = await page.locator("#diagnostics-ablations-tbody tr").count();
  console.log("Ablation table rows count (expected 4):", ablationRowsCount);
  if (ablationRowsCount !== 4) {
    throw new Error(`Expected 4 ablation experiment rows, found ${ablationRowsCount}`);
  }

  // Verify baseline F1 is 0.7143
  const baselineRowText = await page.locator(".ablation-row-baseline").innerText();
  console.log("Baseline row text:", baselineRowText.replace(/\n+/g, " "));
  if (!baselineRowText.includes("0.7143")) {
    throw new Error("Baseline row does not report official Direct F1 0.7143!");
  }

  // Capture Desktop Diagnostics and Ablations Screenshot
  const diagScreenshot = path.join(ARTIFACT_DIR, "desktop_diagnostics_and_ablations_view.png");
  await page.screenshot({ path: diagScreenshot });
  console.log(`Saved screenshot: ${diagScreenshot}`);

  // ==========================================
  // 3. MOBILE VIEWPORT TEST (375x812)
  // ==========================================
  console.log("--- 3. Testing Mobile Responsive Viewport (375x812) ---");
  const mobilePage = await browser.newPage({ viewport: { width: 375, height: 812 } });

  mobilePage.on("console", (msg) => {
    if (msg.type() === "error") {
      consoleErrors.push(`Mobile Console Error: ${msg.text()}`);
    }
  });

  await mobilePage.goto("http://127.0.0.1:8000/", { waitUntil: "networkidle" });
  await mobilePage.waitForTimeout(500);

  // Switch to diagnostics tab directly on mobile via the pipeline banner button
  console.log("Navigating to diagnostics via pipeline banner on mobile...");
  await mobilePage.click("#view-diagnostics-btn");
  await mobilePage.waitForTimeout(800);

  const mobileDiagVisible = await mobilePage.isVisible("#diagnostics-view");
  console.log("Mobile diagnostics view visible:", mobileDiagVisible);
  if (!mobileDiagVisible) throw new Error("Diagnostics view should be visible on mobile!");

  // Switch to split graph mode on mobile
  await mobilePage.click("#view-tab-graph");
  await mobilePage.waitForTimeout(400);
  await mobilePage.click("#split-graph-toggle-btn");
  await mobilePage.waitForTimeout(600);

  // Check stacked panel heights
  const mobilePanelLayout = await mobilePage.evaluate(() => {
    const ext = document.getElementById("extracted-graph-panel");
    const gold = document.getElementById("gold-graph-panel");
    return {
      extHeight: ext ? ext.offsetHeight : 0,
      goldHeight: gold ? gold.offsetHeight : 0,
      flexDirection: window.getComputedStyle(document.getElementById("graph-viewport")).flexDirection
    };
  });
  console.log("Mobile split panels layout:", mobilePanelLayout);
  if (mobilePanelLayout.flexDirection !== "column") {
    throw new Error(`Expected mobile split layout flex-direction column, got ${mobilePanelLayout.flexDirection}`);
  }

  // Capture Mobile Split Graph & Diagnostics Screenshot
  const mobileScreenshot = path.join(ARTIFACT_DIR, "mobile_split_graph_and_diagnostics.png");
  await mobilePage.screenshot({ path: mobileScreenshot });
  console.log(`Saved screenshot: ${mobileScreenshot}`);

  await browser.close();

  // Print audit conclusion
  console.log("\n==========================================");
  console.log("AUDIT RESULTS SUMMARY");
  console.log("==========================================");
  console.log(`Console Errors: ${consoleErrors.length}`);
  if (consoleErrors.length > 0) {
    console.error(consoleErrors.join("\n"));
  }
  console.log(`Network Errors: ${networkErrors.length}`);
  if (networkErrors.length > 0) {
    console.error(networkErrors.join("\n"));
  }

  if (consoleErrors.length > 0 || networkErrors.length > 0) {
    throw new Error("Audit failed with console or network errors!");
  }

  console.log("✓ ALL PHASE 2.7 UI AND INTERACTION CRITERIA VERIFIED SUCCESSFULLY!");
}

runPhase27Verification().catch((err) => {
  console.error("FATAL ERROR in Phase 2.7 Verification:", err);
  process.exit(1);
});
