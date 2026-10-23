const { chromium } = require("playwright");
const path = require("path");

const ARTIFACT_DIR = "/home/tk/.gemini/antigravity-cli/brain/ef3fc705-911a-4157-bc28-1d5bdf2aa3f1";

async function capture() {
  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });

  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto("http://127.0.0.1:8000/", { waitUntil: "networkidle" });

  // 1. Sidebar with session bulk management controls
  await page.click("#open-sidebar-btn");
  await page.waitForTimeout(400);
  await page.click("#session-select-all-cb");
  await page.waitForTimeout(200);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "phase1_sidebar_bulk_session_management.png") });
  console.log("Captured: phase1_sidebar_bulk_session_management.png");

  // Deselect and close sidebar
  await page.click("#session-select-all-cb");
  await page.waitForTimeout(200);
  await page.click("#toggle-sidebar-btn");
  await page.waitForTimeout(300);

  // 2. Examples tab without textbox
  await page.click("#plus-btn");
  await page.waitForTimeout(200);
  await page.click("#menu-examples-btn");
  await page.waitForTimeout(600);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "phase1_examples_tab_no_textbox.png") });
  console.log("Captured: phase1_examples_tab_no_textbox.png");

  // 3. Workspace with real paper loaded
  const loadBtn = await page.waitForSelector('.pdf-card [data-action="load-workspace"]');
  await loadBtn.click();
  await page.waitForSelector("#graph-viewport svg g", { timeout: 15000 });
  await page.waitForTimeout(800);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "phase1_workspace_docked_real_paper.png") });
  console.log("Captured: phase1_workspace_docked_real_paper.png");

  await browser.close();
}

capture().catch(err => {
  console.error("Capture failed:", err);
  process.exit(1);
});
