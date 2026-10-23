const { chromium } = require("playwright");
const path = require("path");

const ARTIFACTS_DIR = "/home/tk/.gemini/antigravity-cli/brain/ef3fc705-911a-4157-bc28-1d5bdf2aa3f1";

async function captureArtifacts() {
  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });

  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });

  console.log("Navigating to http://127.0.0.1:8000/ ...");
  await page.goto("http://127.0.0.1:8000/", { waitUntil: "networkidle" });

  // 1. Open Examples View
  await page.click("#plus-btn");
  await page.waitForTimeout(300);
  await page.click("#menu-examples-btn");
  await page.waitForSelector(".pdf-card", { timeout: 8000 });
  await page.waitForTimeout(1000);

  // Capture PDF benchmark view
  const pdfViewPath = path.join(ARTIFACTS_DIR, "phase2_live_pdf_benchmark_view.png");
  await page.screenshot({ path: pdfViewPath, fullPage: false });
  console.log("Saved screenshot:", pdfViewPath);

  // 2. Open PMC1804205 modal and switch to Causal tab
  await page.click('.pdf-card [data-action="inspect"][data-pmcid="PMC1804205"]');
  await page.waitForSelector("#paper-modal:not(.hidden)", { timeout: 5000 });
  await page.click("#paper-tab-causal");
  await page.waitForTimeout(1000);

  const modalPath = path.join(ARTIFACTS_DIR, "phase2_live_paper_modal_causal_inspection.png");
  await page.screenshot({ path: modalPath, fullPage: false });
  console.log("Saved screenshot:", modalPath);

  // Close modal
  await page.click("#close-paper-modal-btn");
  await page.waitForTimeout(500);

  // 3. Switch to Text subview
  await page.click("#subnav-text");
  await page.waitForSelector(".text-card", { timeout: 5000 });
  await page.waitForTimeout(1000);

  const textViewPath = path.join(ARTIFACTS_DIR, "phase2_live_text_passages_view.png");
  await page.screenshot({ path: textViewPath, fullPage: false });
  console.log("Saved screenshot:", textViewPath);

  // 4. Switch to Multipage subview
  await page.click("#subnav-multipage");
  await page.waitForSelector(".multipage-card", { timeout: 5000 });
  await page.waitForTimeout(1000);

  const multiViewPath = path.join(ARTIFACTS_DIR, "phase2_live_multipage_chains_view.png");
  await page.screenshot({ path: multiViewPath, fullPage: false });
  console.log("Saved screenshot:", multiViewPath);

  // 5. Test Passage in Workspace and capture live Graph
  await page.click("#subnav-text");
  await page.waitForSelector(".text-card", { timeout: 5000 });
  await page.click('.text-card [data-action="load-text"]');
  await page.waitForTimeout(2500);

  const graphPath = path.join(ARTIFACTS_DIR, "phase2_live_workspace_graph_rendered.png");
  await page.screenshot({ path: graphPath, fullPage: false });
  console.log("Saved screenshot:", graphPath);

  await browser.close();
  console.log("All live verification artifacts captured successfully.");
}

captureArtifacts().catch((err) => {
  console.error("Capture failed:", err);
  process.exit(1);
});
