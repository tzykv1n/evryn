const { chromium } = require("playwright");

async function verify() {
  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });

  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("pageerror", (err) => consoleErrors.push(err.toString()));

  console.log("Navigating to http://127.0.0.1:8000/ ...");
  await page.goto("http://127.0.0.1:8000/", { waitUntil: "networkidle" });

  // 1. Initial State: inputContainer should be visible (not hidden)
  const isInputHiddenInitially = await page.$eval("#input-container", el => el.classList.contains("hidden"));
  console.log("1. Initial inputContainer hidden:", isInputHiddenInitially);
  if (isInputHiddenInitially) throw new Error("inputContainer should NOT be hidden initially");

  // 2. Switch to Examples Tab via Plus Menu: inputContainer MUST be hidden
  console.log("2. Switching to Examples tab via + menu...");
  await page.click("#plus-btn");
  await page.waitForTimeout(200);
  await page.click("#menu-examples-btn");
  await page.waitForTimeout(400);

  const isInputHiddenOnExamples = await page.$eval("#input-container", el => el.classList.contains("hidden"));
  console.log("   inputContainer hidden on Examples tab:", isInputHiddenOnExamples);
  if (!isInputHiddenOnExamples) throw new Error("inputContainer MUST be hidden on Examples tab!");

  const isExamplesViewVisible = await page.$eval("#examples-view", el => !el.classList.contains("hidden"));
  console.log("   Examples view visible:", isExamplesViewVisible);
  if (!isExamplesViewVisible) throw new Error("view-examples should be visible");

  // 3. Switch back to Graph Tab: inputContainer MUST be restored
  console.log("3. Switching back to Graph tab...");
  await page.click("#view-tab-graph");
  await page.waitForTimeout(400);

  const isInputHiddenAfterGraph = await page.$eval("#input-container", el => el.classList.contains("hidden"));
  console.log("   inputContainer hidden after switching to Graph:", isInputHiddenAfterGraph);
  if (isInputHiddenAfterGraph) throw new Error("inputContainer should be visible on Graph tab");

  // 4. Test Sidebar and Session Bulk Management Controls
  console.log("4. Testing Sidebar and Bulk Session Controls...");
  await page.click("#open-sidebar-btn");
  await page.waitForTimeout(400);

  const hasToolbar = await page.$eval("#sidebar-session-actions", el => el !== null);
  console.log("   Sidebar session actions toolbar present:", hasToolbar);

  const sessionItemsCount = await page.$$eval(".session-item", els => els.length);
  console.log(`   Session items rendered: ${sessionItemsCount}`);
  if (sessionItemsCount === 0) throw new Error("No session items rendered");

  const checkboxesCount = await page.$$eval(".session-select-cb", els => els.length);
  console.log(`   Session checkboxes rendered: ${checkboxesCount}`);
  if (checkboxesCount !== sessionItemsCount) throw new Error("Checkbox count does not match session items count");

  // Check Select All
  await page.click("#session-select-all-cb");
  await page.waitForTimeout(200);

  const bulkDeleteText = await page.$eval("#session-bulk-delete-btn", el => el.textContent);
  const bulkDeleteDisabled = await page.$eval("#session-bulk-delete-btn", el => el.disabled);
  console.log(`   Bulk delete button text: "${bulkDeleteText}", disabled: ${bulkDeleteDisabled}`);
  if (bulkDeleteDisabled || !bulkDeleteText.includes(String(sessionItemsCount))) {
    throw new Error(`Bulk delete button should say Delete (${sessionItemsCount}) and not be disabled`);
  }

  // Deselect All
  await page.click("#session-select-all-cb");
  await page.waitForTimeout(200);
  const bulkDeleteDisabledAfter = await page.$eval("#session-bulk-delete-btn", el => el.disabled);
  console.log(`   Bulk delete button disabled after deselect: ${bulkDeleteDisabledAfter}`);
  if (!bulkDeleteDisabledAfter) throw new Error("Bulk delete button should be disabled when nothing selected");

  // Select first item checkbox
  await page.click(".session-select-cb");
  await page.waitForTimeout(200);
  const singleDeleteText = await page.$eval("#session-bulk-delete-btn", el => el.textContent);
  console.log(`   Bulk delete button text with 1 selected: "${singleDeleteText}"`);
  if (!singleDeleteText.includes("1")) throw new Error("Bulk delete button should say Delete (1)");

  // 5. Test loading an example into workspace
  console.log("5. Testing Load Paper into Workspace from Examples...");
  await page.click("#toggle-sidebar-btn");
  await page.waitForTimeout(200);
  await page.click("#plus-btn");
  await page.waitForTimeout(200);
  await page.click("#menu-examples-btn");
  await page.waitForTimeout(400);

  // Click 'Load into Workspace' on first card
  const loadBtn = await page.waitForSelector('.pdf-card [data-action="load-workspace"]');
  await loadBtn.click();
  console.log("   Clicked 'Load into Workspace', waiting for graph...");
  await page.waitForSelector("#graph-viewport svg g", { timeout: 15000 });

  const inputContainerAfterLoad = await page.$eval("#input-container", el => ({
    hidden: el.classList.contains("hidden"),
    docked: el.classList.contains("docked")
  }));
  console.log("   inputContainer after paper load:", inputContainerAfterLoad);
  if (inputContainerAfterLoad.hidden || !inputContainerAfterLoad.docked) {
    throw new Error("inputContainer must be visible and docked after loading paper");
  }

  console.log("\nConsole Errors detected:", consoleErrors);
  if (consoleErrors.length > 0) throw new Error("Console errors detected in browser!");

  console.log("\n=== ALL BROWSER & SESSION & TEXTBOX VERIFICATIONS PASSED SUCCESSFULLY ===");
  await browser.close();
}

verify().catch((err) => {
  console.error("Verification failed:", err);
  process.exit(1);
});
