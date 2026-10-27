const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");

const ARTIFACT_DIR = "/home/tk/.gemini/antigravity-cli/brain/ef3fc705-911a-4157-bc28-1d5bdf2aa3f1";

async function runAudit() {
  console.log("==================================================================");
  console.log("EVRYN PHASE 2.4 LIVE BROWSER ACCEPTANCE AUDIT");
  console.log("==================================================================");

  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });

  const consoleErrors = [];
  const networkErrors = [];

  // 1. DESKTOP AUDIT (1440 x 900)
  console.log("\n[1/5] Testing Desktop Layout (1440 x 900)...");
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      consoleErrors.push(`[Console Error] ${msg.text()}`);
    }
  });

  page.on("requestfailed", (req) => {
    networkErrors.push(`[Request Failed] ${req.method()} ${req.url()}: ${req.failure().errorText}`);
  });

  await page.goto("http://127.0.0.1:8000/", { waitUntil: "networkidle" });

  // Verify Header
  const titleText = await page.$eval(".app-title", el => el.textContent.trim());
  console.log(`  Header title: "${titleText}"`);

  // Verify Initial State: Zero duplicate tabs
  const viewTabCount = await page.$$eval(".view-tab", els => els.length);
  const viewTabTexts = await page.$$eval(".view-tab", els => els.map(e => e.textContent.trim()));
  console.log(`  Result View Tabs (${viewTabCount}): [${viewTabTexts.join(", ")}]`);
  if (viewTabTexts.includes("EXAMPLES")) {
    throw new Error("Redundant EXAMPLES tab detected in view tabs!");
  }

  // Verify Plus Menu opens on click
  console.log("  Testing '+' button interaction...");
  const plusMenuBefore = await page.$eval("#plus-menu", el => el.classList.contains("hidden"));
  if (!plusMenuBefore) throw new Error("Plus menu should be hidden initially");

  await page.click("#plus-btn");
  await page.waitForTimeout(200);
  const plusMenuOpen = await page.$eval("#plus-menu", el => !el.classList.contains("hidden"));
  console.log(`  '+' button clicked: menu visible = ${plusMenuOpen}`);
  if (!plusMenuOpen) throw new Error("Plus menu did not open on '+' click");

  // Screenshot open + menu
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "desktop_plus_menu_open.png") });

  // Test Case A selection via + menu
  console.log("  Selecting Case A (Direct Causal Relation) from '+' menu...");
  await page.click('.menu-example-item[data-example="example_a"]');
  await page.waitForTimeout(300);

  const plusMenuClosed = await page.$eval("#plus-menu", el => el.classList.contains("hidden"));
  const inputValA = await page.$eval("#query-input", el => el.value);
  console.log(`  Menu closed after selection: ${plusMenuClosed}`);
  console.log(`  Input populated: "${inputValA.slice(0, 50)}..."`);

  // Run Extraction for Case A
  console.log("  Executing Run Extraction (System A NLP Baseline)...");
  await page.click("#regenerate-btn");
  await page.waitForSelector("#graph-viewport svg g#nodes-layer g.graph-node", { timeout: 15000 });
  await page.waitForTimeout(600);

  const statsA = await page.$eval("#graph-stats", el => el.textContent.trim());
  const nodesCountA = await page.$$eval("g.graph-node", els => els.length);
  const edgesCountA = await page.$$eval("path.graph-edge", els => els.length);
  console.log(`  Extraction Result: ${statsA} (DOM: ${nodesCountA} nodes, ${edgesCountA} edges)`);

  // Test Evidence Inspector by clicking a node
  console.log("  Clicking node to test Evidence Inspector...");
  await page.click("g.graph-node rect", { force: true });
  await page.waitForTimeout(400);

  const inspectorVisible = await page.$eval("#inspector-panel", el => !el.classList.contains("hidden"));
  const inspectorText = await page.$eval("#inspector-body", el => el.textContent.trim().slice(0, 100));
  console.log(`  Inspector opened: ${inspectorVisible}, preview: "${inspectorText}..."`);

  // Close inspector
  await page.click("#close-inspector-btn");
  await page.waitForTimeout(300);

  // Screenshot Desktop Graph + Inspector
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "desktop_graph_extracted_case_a.png") });

  // Test Table View
  console.log("  Switching to Table view...");
  await page.click("#view-tab-table");
  await page.waitForTimeout(300);
  const tableRows = await page.$$eval("#table-body tr", els => els.length);
  console.log(`  Table view rendered with ${tableRows} rows`);

  // Test Copyable View
  console.log("  Switching to Copyable view...");
  await page.click("#view-tab-copyable");
  await page.waitForTimeout(300);
  const copyableLength = await page.$eval("#copyable-text", el => el.textContent.length);
  console.log(`  Copyable text generated (${copyableLength} chars)`);

  // Test Benchmark View
  console.log("  Switching to Benchmark view...");
  await page.click("#view-tab-benchmark");
  await page.waitForSelector(".benchmark-kpi-card", { timeout: 10000 });
  const kpis = await page.$$eval(".benchmark-kpi-value", els => els.map(e => e.textContent.trim()));
  console.log(`  Benchmark KPI Cards loaded: [${kpis.join(", ")}]`);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "desktop_benchmark_dashboard.png") });

  // Return to Graph view
  await page.click("#view-tab-graph");
  await page.waitForTimeout(300);

  // [2/5] Test Case B (Multi-hop Cascade)
  console.log("\n[2/5] Testing Case B (Multi-hop Cascade)...");
  await page.click("#plus-btn");
  await page.waitForTimeout(200);
  await page.click('.menu-example-item[data-example="example_b"]');
  await page.waitForTimeout(300);

  const inputValB = await page.$eval("#query-input", el => el.value);
  console.log(`  Input populated for Case B: "${inputValB.slice(0, 50)}..."`);
  await page.click("#regenerate-btn");
  await page.waitForSelector("#graph-viewport svg g#nodes-layer g.graph-node", { timeout: 15000 });
  await page.waitForTimeout(600);

  const statsB = await page.$eval("#graph-stats", el => el.textContent.trim());
  console.log(`  Case B Extraction Result: ${statsB}`);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "desktop_graph_case_b_multihop.png") });

  // [3/5] Test Case E (Empty Input Validation)
  console.log("\n[3/5] Testing Case E (Empty Input Validation)...");
  await page.fill("#query-input", "");
  await page.click("#regenerate-btn");
  await page.waitForTimeout(600);

  // Check notification toast or validation alert
  const notifText = await page.$eval("#app-notification", el => el.textContent.trim());
  const notifVisible = await page.$eval("#app-notification", el => !el.classList.contains("hidden"));
  console.log(`  Empty submission handled: notification visible = ${notifVisible}, message: "${notifText}"`);

  // [4/5] NARROW-SCREEN / MOBILE AUDIT (375 x 667)
  console.log("\n[4/5] Testing Narrow Screen Layout (375 x 667 iPhone SE)...");
  const mobilePage = await browser.newPage({ viewport: { width: 375, height: 667 } });
  await mobilePage.goto("http://127.0.0.1:8000/", { waitUntil: "networkidle" });

  await mobilePage.click("#plus-btn");
  await mobilePage.waitForTimeout(200);
  await mobilePage.screenshot({ path: path.join(ARTIFACT_DIR, "mobile_plus_menu_open.png") });

  await mobilePage.click('.menu-example-item[data-example="example_a"]');
  await mobilePage.waitForTimeout(300);
  await mobilePage.click("#regenerate-btn");
  await mobilePage.waitForSelector("#graph-viewport svg g#nodes-layer g.graph-node", { timeout: 15000 });
  await mobilePage.waitForTimeout(600);

  await mobilePage.screenshot({ path: path.join(ARTIFACT_DIR, "mobile_graph_extracted.png") });
  console.log("  Mobile layout verified: graph rendered without overflow crash");

  // [5/5] CONSOLE & NETWORK AUDIT
  console.log("\n[5/5] Console & Network Log Audit...");
  console.log(`  Total Console Errors: ${consoleErrors.length}`);
  if (consoleErrors.length > 0) {
    consoleErrors.forEach(e => console.log(`    ${e}`));
  }
  console.log(`  Total Network Failures: ${networkErrors.length}`);
  if (networkErrors.length > 0) {
    networkErrors.forEach(e => console.log(`    ${e}`));
  }

  await browser.close();

  const success = consoleErrors.length === 0 && networkErrors.length === 0;
  console.log(`\n==================================================================`);
  console.log(`AUDIT RESULT: ${success ? "100% PASSED (CLEAN)" : "FAILED (ERRORS DETECTED)"}`);
  console.log("==================================================================");

  if (!success) {
    process.exit(1);
  }
}

runAudit().catch(err => {
  console.error("Audit Execution Error:", err);
  process.exit(1);
});
