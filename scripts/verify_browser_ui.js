const { chromium } = require("playwright");

async function runBrowserVerification() {
  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });

  const page = await browser.newPage();
  const consoleErrors = [];
  const consoleWarnings = [];
  const networkErrors = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      consoleErrors.push(msg.text());
    } else if (msg.type() === "warning") {
      consoleWarnings.push(msg.text());
    }
  });

  page.on("pageerror", (err) => {
    consoleErrors.push(err.toString());
  });

  page.on("response", (res) => {
    if (res.status() >= 400 && !res.url().includes("/api/demo-examples")) {
      networkErrors.push(`${res.status()} ${res.statusText()} on ${res.url()}`);
    }
  });

  console.log("Navigating to http://127.0.0.1:8000/ ...");
  await page.goto("http://127.0.0.1:8000/", { waitUntil: "networkidle" });

  // 1. Check absence of legacy demo terms
  const pageContent = await page.content();
  const hasDemoHeading = pageContent.includes("DEMONSTRATION EXAMPLES");
  const hasDemoItemClass = (await page.$$(".demo-item")).length > 0;
  const hasDemoExamplesEndpoint = pageContent.includes("/api/demo-examples");

  console.log("Legacy Audit:");
  console.log(`  'DEMONSTRATION EXAMPLES' present: ${hasDemoHeading}`);
  console.log(`  '.demo-item' elements present: ${hasDemoItemClass}`);
  console.log(`  '/api/demo-examples' in DOM: ${hasDemoExamplesEndpoint}`);

  // 2. Open Examples Tab via Plus Menu or Tab Switcher
  console.log("\nOpening plus menu (#plus-btn)...");
  await page.click("#plus-btn");
  await page.waitForTimeout(300);

  console.log("Clicking 'Browse Real-Paper Examples' (#menu-examples-btn)...");
  await page.click("#menu-examples-btn");
  await page.waitForTimeout(1000);

  const examplesViewVisible = await page.$eval("#examples-view", el => !el.classList.contains("hidden"));
  console.log(`  #examples-view visible: ${examplesViewVisible}`);

  // 3. Inspect PDF Subview
  console.log("\nInspecting PDF subview (#pdf-cards-grid)...");
  await page.waitForSelector(".pdf-card", { timeout: 5000 });
  const pdfCardsCount = await page.$$eval(".pdf-card", els => els.length);
  const firstPdfTitle = await page.$eval(".pdf-card .pdf-card-title", el => el.textContent.trim());
  const firstPdfPmcid = await page.$eval(".pdf-card [data-pmcid]", el => el.getAttribute("data-pmcid"));
  const firstPdfF1 = await page.$eval(".pdf-card .f1-badge", el => el.textContent.trim());

  console.log(`  PDF Cards rendered: ${pdfCardsCount}`);
  console.log(`  First card PMCID: ${firstPdfPmcid}`);
  console.log(`  First card Title: ${firstPdfTitle}`);
  console.log(`  First card Direct F1 badge: ${firstPdfF1}`);

  // 4. Test Paper Modal Inspection on PMC1804205
  console.log(`\nOpening Paper Detail Modal for ${firstPdfPmcid}...`);
  const inspectBtn = await page.$(`.pdf-card [data-action="inspect"][data-pmcid="${firstPdfPmcid}"]`);
  await inspectBtn.click();
  await page.waitForTimeout(1000);

  const modalVisible = await page.$eval("#paper-modal", el => !el.classList.contains("hidden"));
  const modalTitle = await page.$eval("#paper-modal-title", el => el.textContent.trim());
  const modalBadge = await page.$eval("#paper-modal-badge", el => el.textContent.trim());
  console.log(`  #paper-modal visible: ${modalVisible}`);
  console.log(`  Modal Title: ${modalTitle}`);
  console.log(`  Modal Badge: ${modalBadge}`);

  // Switch to Causal Comparison tab in modal
  await page.click("#paper-tab-causal");
  await page.waitForTimeout(500);
  const causalRowsCount = await page.$$eval("#paper-causal-wrap tr", els => els.length);
  console.log(`  Causal Comparison rows rendered: ${causalRowsCount}`);

  // Close modal
  await page.click("#close-paper-modal-btn");
  await page.waitForTimeout(500);
  const modalClosed = await page.$eval("#paper-modal", el => el.classList.contains("hidden"));
  console.log(`  Modal closed successfully: ${modalClosed}`);

  // 5. Inspect Text Subview and Interactive Passage Testing
  console.log("\nSwitching to Text subview (#subnav-text)...");
  await page.click("#subnav-text");
  await page.waitForSelector(".text-card", { timeout: 5000 });
  const textCardsCount = await page.$$eval(".text-card", els => els.length);
  const firstTextPassage = await page.$eval(".text-card .text-passage", el => el.textContent.trim().slice(0, 80));
  const firstTextCause = await page.$eval(".text-card .comp-val", el => el.textContent.trim());

  console.log(`  Text Cards rendered: ${textCardsCount}`);
  console.log(`  First passage quote preview: "${firstTextPassage}..."`);
  console.log(`  First gold cause: ${firstTextCause}`);

  // Test opening full paper modal from Text card
  console.log("  Testing 'View Full Paper' from text card...");
  await page.click('.text-card [data-action="open-paper"]');
  await page.waitForTimeout(1000);
  const textModalVisible = await page.$eval("#paper-modal", el => !el.classList.contains("hidden"));
  const textSectionsCount = await page.$$eval("#paper-text-wrap .paper-section-block", els => els.length);
  console.log(`    Paper modal opened from text card: ${textModalVisible}, structured sections: ${textSectionsCount}`);
  await page.click("#close-paper-modal-btn");
  await page.waitForTimeout(500);

  // 6. Inspect Multipage Subview and Multipage Verification
  console.log("\nSwitching to Multipage subview (#subnav-multipage)...");
  await page.click("#subnav-multipage");
  await page.waitForSelector(".multipage-card", { timeout: 5000 });
  const multiCardsCount = await page.$$eval(".multipage-card", els => els.length);
  const firstMultiCause = await page.$eval(".multipage-card .chain-node-concept", el => el.textContent.trim());
  const firstMultiMech = await page.$eval(".multipage-card div[style*='font-size: 11px']", el => el.textContent.trim().replace(/\s+/g, " "));

  console.log(`  Multipage Cards rendered: ${multiCardsCount}`);
  console.log(`  First upstream cause: ${firstMultiCause}`);
  console.log(`  First bridge description: ${firstMultiMech.slice(0, 100)}...`);

  // Test opening PDF viewer modal from Multipage card
  console.log("  Testing 'View Multi-Page PDF' from multipage card...");
  await page.click('.multipage-card [data-action="view-pdf"]');
  await page.waitForTimeout(1000);
  const multiModalVisible = await page.$eval("#paper-modal", el => !el.classList.contains("hidden"));
  const iframeSrc = await page.$eval("#paper-pdf-iframe", el => el.getAttribute("src"));
  console.log(`    Paper modal opened from multipage card: ${multiModalVisible}, iframe src: ${iframeSrc}`);
  await page.click("#close-paper-modal-btn");
  await page.waitForTimeout(500);

  // 7. Test Loading a Passage into Workspace
  console.log("\nTesting 'Test Passage in Workspace' interaction...");
  await page.click("#view-tab-examples");
  await page.waitForTimeout(300);
  await page.click("#subnav-text");
  await page.waitForSelector(".text-card", { timeout: 5000 });
  await page.click('.text-card [data-action="load-text"]');
  await page.waitForTimeout(2500);

  const graphTabActive = await page.$eval("#view-tab-graph", el => el.classList.contains("active"));
  const queryInputValue = await page.$eval("#query-input", el => el.value);
  const graphStatsText = await page.$eval("#graph-stats", el => el.textContent.trim());
  console.log(`  Workspace Graph View active: ${graphTabActive}`);
  console.log(`  Query input populated: ${queryInputValue.slice(0, 60)}...`);
  console.log(`  Graph stats: ${graphStatsText}`);

  // 7. Verify console logs
  console.log("\nBrowser Console Verification:");
  console.log(`  Console Errors: ${consoleErrors.length}`);
  if (consoleErrors.length > 0) {
    consoleErrors.forEach((e, i) => console.log(`    [Error ${i + 1}] ${e}`));
  }
  console.log(`  Network Errors: ${networkErrors.length}`);
  if (networkErrors.length > 0) {
    networkErrors.forEach((e, i) => console.log(`    [NetError ${i + 1}] ${e}`));
  }

  await browser.close();

  const success =
    !hasDemoHeading &&
    !hasDemoItemClass &&
    examplesViewVisible &&
    pdfCardsCount > 0 &&
    modalVisible &&
    modalClosed &&
    textCardsCount > 0 &&
    multiCardsCount > 0 &&
    consoleErrors.length === 0;

  console.log(`\nOverall Browser Verification Result: ${success ? "PASSED (100% CLEAN)" : "FAILED"}`);
  if (!success) {
    process.exit(1);
  }
}

runBrowserVerification().catch((err) => {
  console.error("Verification script error:", err);
  process.exit(1);
});
