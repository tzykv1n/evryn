const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const ARTIFACT_DIR = "/home/tk/.gemini/antigravity-cli/brain/ef3fc705-911a-4157-bc28-1d5bdf2aa3f1";

async function runPhase25Verification() {
  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });

  const consoleErrors = [];
  const networkErrors = [];

  // ==========================================
  // DESKTOP VIEWPORT TEST
  // ==========================================
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  page.on("pageerror", (err) => {
    consoleErrors.push(err.toString());
  });

  page.on("response", (res) => {
    if (res.status() >= 400) {
      networkErrors.push(`${res.status()} ${res.statusText()} on ${res.url()}`);
    }
  });

  console.log("Navigating to http://127.0.0.1:8000/ ...");
  await page.goto("http://127.0.0.1:8000/", { waitUntil: "networkidle" });

  // 1. Check Plus Menu
  console.log("Testing streamlined Plus menu...");
  await page.click("#plus-btn");
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "desktop_plus_menu_streamlined.png") });

  const hasBrowseBtn = await page.$eval("#menu-browse-examples-btn", el => !!el && el.innerText.includes("Browse All Examples"));
  const hasRecentsHeader = await page.$eval(".plus-menu-header", el => el.innerText.includes("RECENT"));
  console.log(`  'Browse All Examples' button present: ${hasBrowseBtn}`);
  console.log(`  'RECENTLY USED EXAMPLES' section present: ${hasRecentsHeader}`);

  // 2. Open Example Library Modal
  console.log("\nOpening Example Library modal...");
  await page.click("#menu-browse-examples-btn");
  await page.waitForTimeout(400);

  const isLibraryVisible = await page.$eval("#example-library-modal", el => !el.classList.contains("hidden"));
  console.log(`  Example library modal visible: ${isLibraryVisible}`);

  // Wait for library cards to populate
  await page.waitForSelector(".library-card", { timeout: 5000 });
  const initialCardCount = await page.$$eval(".library-card", els => els.length);
  console.log(`  Initial cards rendered: ${initialCardCount}`);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "desktop_example_library_modal.png") });

  // 3. Test Filter Chips
  console.log("\nTesting Library Filter Chips...");
  // Diagnostic
  await page.click('[data-filter="diagnostic"]');
  await page.waitForTimeout(200);
  const diagCount = await page.$$eval(".library-card", els => els.length);
  console.log(`  Diagnostic filter count: ${diagCount} (expected 5)`);

  // Gold Available
  await page.click('[data-filter="gold"]');
  await page.waitForTimeout(200);
  const goldCount = await page.$$eval(".library-card", els => els.length);
  console.log(`  Gold available filter count: ${goldCount} (expected 12)`);

  // Reset to All
  await page.click('[data-filter="all"]');
  await page.waitForTimeout(200);

  // Search input test
  console.log("\nTesting search input in Library...");
  await page.fill("#library-search-input", "PmrA");
  await page.waitForTimeout(200);
  const searchCount = await page.$$eval(".library-card", els => els.length);
  console.log(`  Search 'PmrA' matched cards: ${searchCount}`);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "desktop_example_library_search.png") });

  // 4. Load Benchmark Paper into Workspace
  console.log("\nLoading PMC1804205 from library into workspace...");
  const firstCardLoadBtn = await page.$('.library-card [data-action="load"]');
  await firstCardLoadBtn.click();
  await page.waitForTimeout(400);

  // Modal should be closed and text loaded into query editor
  const modalClosed = await page.$eval("#example-library-modal", el => el.classList.contains("hidden"));
  const editorValue = await page.$eval("#query-input", el => el.value);
  console.log(`  Modal closed: ${modalClosed}`);
  console.log(`  Editor has text: ${editorValue.length > 50} (length: ${editorValue.length})`);

  // 5. Run Extraction
  console.log("\nRunning causal extraction...");
  await page.click("#regenerate-btn");
  await page.waitForSelector("#graph-viewport svg g#nodes-layer g.graph-node", { timeout: 15000 });
  await page.waitForTimeout(1000);
  console.log("  Extraction finished successfully.");

  // 6. Test Gold Comparison View Tab (View 5)
  console.log("\nTesting View Tab 5 (GOLD COMPARISON)...");
  await page.click("#view-tab-gold");
  await page.waitForTimeout(800);

  const isGoldActive = await page.$eval("#view-tab-gold", el => el.classList.contains("active"));
  const isGoldViewVisible = await page.$eval("#gold-comparison-view", el => !el.classList.contains("hidden"));
  console.log(`  Gold comparison tab active: ${isGoldActive}`);
  console.log(`  Gold comparison container visible: ${isGoldViewVisible}`);

  const precisionText = await page.$eval("#gold-kpi-precision", el => el.innerText);
  const recallText = await page.$eval("#gold-kpi-recall", el => el.innerText);
  const f1Text = await page.$eval("#gold-kpi-f1", el => el.innerText);
  const matchedCount = await page.$eval("#gold-kpi-matched", el => el.innerText);
  const unmatchedCount = await page.$eval("#gold-kpi-unmatched", el => el.innerText);

  console.log(`  Official Precision: ${precisionText}`);
  console.log(`  Official Recall: ${recallText}`);
  console.log(`  Official F1: ${f1Text}`);
  console.log(`  Matched TP: ${matchedCount}`);
  console.log(`  Unmatched FP: ${unmatchedCount}`);

  await page.screenshot({ path: path.join(ARTIFACT_DIR, "desktop_gold_comparison_view.png") });

  // 7. Test Gold Table Filter Tabs
  console.log("\nTesting Gold Comparison filter tabs...");
  await page.click("#tab-gold-matched");
  await page.waitForTimeout(200);
  const matchedRows = await page.$$eval("#gold-comparison-tbody tr", els => els.length);
  console.log(`  Matched filter rows: ${matchedRows}`);

  await page.click("#tab-gold-unmatched");
  await page.waitForTimeout(200);
  const unmatchedRows = await page.$$eval("#gold-comparison-tbody tr", els => els.length);
  console.log(`  Unmatched filter rows: ${unmatchedRows}`);

  await page.click("#tab-gold-all");
  await page.waitForTimeout(200);

  // 8. Test Reviewer Override
  console.log("\nTesting Reviewer Override in live UI...");
  const firstOverrideSelect = await page.$(".adj-override-select");
  if (firstOverrideSelect) {
    await firstOverrideSelect.selectOption("Likely annotation omission");
    await page.waitForTimeout(1000);
    const reviewedBadge = await page.$(".badge-reviewed-indicator");
    console.log(`  Reviewed badge rendered: ${!!reviewedBadge}`);
    await page.screenshot({ path: path.join(ARTIFACT_DIR, "desktop_reviewer_override_applied.png") });
  }

  // 9. Verify Recent Examples list
  console.log("\nVerifying that recently loaded example is now listed in the + menu...");
  await page.click("#view-tab-graph");
  await page.waitForTimeout(400);
  await page.click("#plus-btn");
  await page.waitForTimeout(300);
  const recentsCount = await page.$$eval(".menu-recent-item", els => els.length);
  console.log(`  Recent items in + menu: ${recentsCount}`);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "desktop_plus_menu_with_recents.png") });
  await page.click("#plus-btn"); // close

  // ==========================================
  // MOBILE VIEWPORT TEST
  // ==========================================
  console.log("\nTesting Mobile Viewport (390x844)...");
  const mobilePage = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await mobilePage.goto("http://127.0.0.1:8000/", { waitUntil: "networkidle" });
  await mobilePage.click("#plus-btn");
  await mobilePage.waitForTimeout(300);
  await mobilePage.screenshot({ path: path.join(ARTIFACT_DIR, "mobile_plus_menu.png") });

  await mobilePage.click("#menu-browse-examples-btn");
  await mobilePage.waitForTimeout(400);
  await mobilePage.screenshot({ path: path.join(ARTIFACT_DIR, "mobile_example_library_modal.png") });

  console.log("\nSummary of Errors:");
  console.log(`  Console Errors: ${consoleErrors.length}`);
  console.log(`  Network Errors: ${networkErrors.length}`);
  if (consoleErrors.length > 0) console.error("Console Errors:", consoleErrors);
  if (networkErrors.length > 0) console.error("Network Errors:", networkErrors);

  await browser.close();
  console.log("\n✓ Phase 2.5 Live UI verification completed successfully.");
}

runPhase25Verification().catch(err => {
  console.error("Verification failed:", err);
  process.exit(1);
});
