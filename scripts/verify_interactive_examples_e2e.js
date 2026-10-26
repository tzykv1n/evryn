const { chromium } = require("playwright");

async function runE2EVerification() {
  console.log("=== Launching Headless Chromium for EVRYN E2E Verification ===");
  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const consoleErrors = [];
  const networkErrors = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      // Ignore expected 400 resource response for Example E (intentional validation test)
      if (msg.text().includes("400") || msg.text().includes("example_e")) return;
      consoleErrors.push(msg.text());
    }
  });

  page.on("pageerror", (err) => {
    consoleErrors.push(err.toString());
  });

  page.on("response", (res) => {
    // 400 is expected for Example E validation test
    if (res.status() >= 400 && !res.url().includes("example_e")) {
      networkErrors.push(`${res.status()} ${res.statusText()} on ${res.url()}`);
    }
  });

  // Automatically accept confirmation dialogs (e.g. for Clear All Sessions)
  page.on("dialog", async (dialog) => {
    console.log(`  [Dialog] ${dialog.type()}: "${dialog.message().slice(0, 60)}..." -> Accepting`);
    await dialog.accept();
  });

  console.log("Navigating to http://127.0.0.1:8000/ ...");
  await page.goto("http://127.0.0.1:8000/", { waitUntil: "networkidle" });

  // 1. Initial State Verification
  console.log("\n1. Verifying Pristine Initial Workspace State...");
  const isInputCentered = await page.$eval("#input-container", el => el.classList.contains("centered"));
  const chipsCount = await page.$$eval(".test-example-chip", els => els.length);
  console.log(`   Input centered: ${isInputCentered}`);
  console.log(`   Test example chips found: ${chipsCount}`);
  if (!isInputCentered || chipsCount !== 5) {
    throw new Error("Initial workspace state invalid: expected centered input and 5 test chips.");
  }

  // 2. Test Example A (Direct Causal Relation)
  console.log("\n2. Executing Example A (Direct Causal Relation)...");
  await page.click('.test-example-chip[data-example="example_a"]');
  await page.waitForSelector(".graph-node", { timeout: 10000 });

  const queryValA = await page.$eval("#query-input", el => el.value);
  const statsA = await page.$eval("#graph-stats", el => el.textContent.trim());
  const nodesCountA = await page.$$eval(".graph-node", els => els.length);
  const edgesCountA = await page.$$eval(".graph-edge", els => els.length);
  console.log(`   Query input: "${queryValA.slice(0, 50)}..."`);
  console.log(`   Graph stats: "${statsA}"`);
  console.log(`   Rendered SVG: ${nodesCountA} nodes, ${edgesCountA} edges`);
  if (!queryValA.includes("deletion of gene A") || nodesCountA !== 2 || edgesCountA !== 1) {
    throw new Error("Example A execution failed or did not render 2 nodes and 1 edge.");
  }

  // Check table row for DOWNREGULATES
  await page.click("#view-tab-table");
  await page.waitForTimeout(300);
  const tableTextA = await page.$eval("#table-body", el => el.textContent);
  console.log(`   Table row contains DOWNREGULATES: ${tableTextA.includes("DOWNREGULATES")}`);
  if (!tableTextA.includes("DOWNREGULATES")) {
    throw new Error("Example A did not display DOWNREGULATES in Table view.");
  }

  // 3. Test Reset Action
  console.log("\n3. Testing Reset Action (#reset-workspace-btn)...");
  await page.click("#view-tab-graph");
  await page.click("#reset-workspace-btn");
  await page.waitForTimeout(500);

  const isResetCentered = await page.$eval("#input-container", el => el.classList.contains("centered"));
  const queryValReset = await page.$eval("#query-input", el => el.value);
  console.log(`   Input returned to centered: ${isResetCentered}`);
  console.log(`   Query input cleared: "${queryValReset}"`);
  if (!isResetCentered || queryValReset !== "") {
    throw new Error("Reset action failed to restore pristine centered input.");
  }

  // 4. Test Example B (Multi-Transition Causal Chain)
  console.log("\n4. Executing Example B (Multi-Transition Causal Chain)...");
  await page.click('.test-example-chip[data-example="example_b"]');
  await page.waitForSelector(".graph-node", { timeout: 10000 });

  const statsB = await page.$eval("#graph-stats", el => el.textContent.trim());
  console.log(`   Graph stats: "${statsB}"`);
  if (!statsB.includes("3 NODES") || !statsB.includes("2 CAUSAL RELATIONS")) {
    throw new Error(`Example B failed: expected 3 nodes and 2 relations, got ${statsB}`);
  }

  // 5. Test Example C (Negation and Directionality)
  console.log("\n5. Executing Example C (Negation & Directionality)...");
  await page.click('.test-example-chip[data-example="example_c"]');
  await page.waitForSelector(".graph-node", { timeout: 10000 });

  await page.click("#view-tab-table");
  await page.waitForTimeout(300);
  const tableTextC = await page.$eval("#table-body", el => el.textContent);
  console.log(`   Table contains [NEGATED]: ${tableTextC.includes("[NEGATED]")}`);
  if (!tableTextC.includes("[NEGATED]")) {
    throw new Error("Example C failed: relation was not tagged [NEGATED].");
  }

  // 6. Test Example D (Invalid Transitive Path - Context Mismatch)
  console.log("\n6. Executing Example D (Context Invariant Path Validation)...");
  await page.click('.test-example-chip[data-example="example_d"]');
  await page.waitForSelector(".graph-node", { timeout: 10000 });

  const statsD = await page.$eval("#graph-stats", el => el.textContent.trim());
  console.log(`   Graph stats: "${statsD}"`);
  if (!statsD.includes("4 NODES") || !statsD.includes("2 CAUSAL RELATIONS")) {
    throw new Error(`Example D failed: expected 4 nodes and 2 relations, got ${statsD}`);
  }

  // 7. Test Example E (Malformed / Empty Input)
  console.log("\n7. Executing Example E (Empty Input Validation)...");
  await page.click('.test-example-chip[data-example="example_e"]');
  await page.waitForTimeout(800);

  const emptyStateVisible = await page.$eval("#graph-empty-state", el => !el.classList.contains("hidden"));
  const emptyHeading = await page.$eval("#graph-empty-state .empty-state-heading", el => el.textContent.trim());
  console.log(`   #graph-empty-state visible: ${emptyStateVisible}`);
  console.log(`   Empty state heading: "${emptyHeading}"`);
  if (!emptyStateVisible || !emptyHeading.includes("Validation Succeeded")) {
    throw new Error("Example E failed: empty state diagnostic was not displayed.");
  }

  // 8. Test Examples Tab Navigation & Subnav Test Cases
  console.log("\n8. Navigating to Examples Tab -> TEST CASES (A-E)...");
  await page.click("#view-tab-examples");
  await page.waitForTimeout(500);
  await page.click("#subnav-testcases");
  await page.waitForSelector(".testcase-card", { timeout: 5000 });

  const testCardsCount = await page.$$eval(".testcase-card", els => els.length);
  console.log(`   Test case cards rendered in subnav: ${testCardsCount}`);
  if (testCardsCount !== 5) {
    throw new Error(`Expected 5 test case cards, found ${testCardsCount}`);
  }

  // Click Run Test Case on first card
  console.log("   Clicking 'Run Test Case in Workspace' from card...");
  await page.click('.testcase-card [data-action="run-testcase"]');
  await page.waitForSelector(".graph-node", { timeout: 10000 });

  const statsFromCard = await page.$eval("#graph-stats", el => el.textContent.trim());
  console.log(`   Returned to workspace with stats: "${statsFromCard}"`);

  // 9. Test Session Management & Clear All Sessions
  console.log("\n9. Testing Session Sidebar & Clear All Sessions...");
  await page.click("#open-sidebar-btn");
  await page.waitForTimeout(500);

  const sessionCountBefore = await page.$$eval(".session-item", els => els.length);
  console.log(`   Active sessions in sidebar before clear: ${sessionCountBefore}`);
  if (sessionCountBefore === 0) {
    throw new Error("Expected active sessions in sidebar after running test cases.");
  }

  console.log("   Clicking Clear All button (#session-clear-all-btn)...");
  await page.click("#session-clear-all-btn");
  await page.waitForTimeout(1500);

  const sessionCountAfter = await page.$$eval(".session-item", els => els.length);
  console.log(`   Active sessions in sidebar after clear: ${sessionCountAfter}`);
  if (sessionCountAfter !== 0) {
    throw new Error(`Clear All Sessions failed: expected 0 sessions, found ${sessionCountAfter}`);
  }

  // 10. Console and Network Verification
  console.log("\n10. Checking Console & Network Errors...");
  console.log(`    Console errors: ${consoleErrors.length}`);
  if (consoleErrors.length > 0) {
    consoleErrors.forEach((err, i) => console.log(`      [Error ${i + 1}] ${err}`));
  }
  console.log(`    Unexpected network errors: ${networkErrors.length}`);
  if (networkErrors.length > 0) {
    networkErrors.forEach((err, i) => console.log(`      [NetError ${i + 1}] ${err}`));
  }

  await browser.close();

  const passed = consoleErrors.length === 0 && networkErrors.length === 0;
  console.log(`\n=== E2E VERIFICATION RESULT: ${passed ? "ALL CHECKS PASSED (100% CLEAN)" : "FAILED"} ===\n`);
  if (!passed) process.exit(1);
}

runE2EVerification().catch((err) => {
  console.error("E2E Verification failed:", err);
  process.exit(1);
});
