const { chromium } = require('playwright');
const path = require('path');
const artDir = '/home/tk/.gemini/antigravity-cli/brain/ef3fc705-911a-4157-bc28-1d5bdf2aa3f1';

async function capture() {
  const browser = await chromium.launch({ headless: true });
  
  // 1. Desktop Large (1440x900) - Empty State
  let page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://127.0.0.1:8000', { waitUntil: 'networkidle' });
  await page.screenshot({ path: path.join(artDir, 'phase3_4_before_1440x900_empty.png') });
  console.log('Captured before 1440x900 empty');

  // Submit via Enter with waitForResponse
  await page.focus('#query-input');
  await page.keyboard.type('Aspirin inhibits COX-2, which significantly reduces prostaglandin synthesis.');
  await Promise.all([
    page.waitForResponse(resp => resp.url().includes('/api/extract')),
    page.keyboard.press('Enter'),
  ]);
  await page.waitForTimeout(1000);
  
  const nodes = await page.$$('.graph-node');
  const edges = await page.$$('.graph-edge');
  console.log(`Active state rendered: ${nodes.length} nodes, ${edges.length} edges`);

  await page.screenshot({ path: path.join(artDir, 'phase3_4_before_1440x900_active.png') });
  console.log('Captured before 1440x900 active');

  // Click an edge or node to open inspector
  if (edges.length > 0) {
    await edges[0].click({ force: true });
    await page.waitForTimeout(600);
  } else if (nodes.length > 0) {
    await nodes[0].click({ force: true });
    await page.waitForTimeout(600);
  }
  await page.screenshot({ path: path.join(artDir, 'phase3_4_before_1440x900_inspector.png') });
  console.log('Captured before 1440x900 inspector');

  // Click EVALUATE
  await page.click('#view-tab-gold');
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(artDir, 'phase3_4_before_1440x900_evaluate.png') });
  console.log('Captured before 1440x900 evaluate');

  // Click RESEARCH
  await page.click('#nav-mode-research');
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(artDir, 'phase3_4_before_1440x900_research.png') });
  console.log('Captured before 1440x900 research');
  await page.close();

  // 2. Desktop Standard (1280x720)
  page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await page.goto('http://127.0.0.1:8000', { waitUntil: 'networkidle' });
  await page.focus('#query-input');
  await page.keyboard.type('Aspirin inhibits COX-2, which reduces prostaglandin synthesis.');
  await Promise.all([
    page.waitForResponse(resp => resp.url().includes('/api/extract')),
    page.keyboard.press('Enter'),
  ]);
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(artDir, 'phase3_4_before_1280x720_active.png') });
  console.log('Captured before 1280x720 active');
  await page.close();

  // 3. Tablet (768x1024)
  page = await browser.newPage({ viewport: { width: 768, height: 1024 } });
  await page.goto('http://127.0.0.1:8000', { waitUntil: 'networkidle' });
  await page.focus('#query-input');
  await page.keyboard.type('Aspirin inhibits COX-2, which reduces prostaglandin synthesis.');
  await Promise.all([
    page.waitForResponse(resp => resp.url().includes('/api/extract')),
    page.keyboard.press('Enter'),
  ]);
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(artDir, 'phase3_4_before_768px_active.png') });
  console.log('Captured before 768px active');
  await page.close();

  // 4. Mobile (390x844)
  page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await page.goto('http://127.0.0.1:8000', { waitUntil: 'networkidle' });
  await page.screenshot({ path: path.join(artDir, 'phase3_4_before_390px_empty.png') });
  console.log('Captured before 390px empty');
  await page.focus('#query-input');
  await page.keyboard.type('Aspirin inhibits COX-2, which reduces prostaglandin synthesis.');
  await Promise.all([
    page.waitForResponse(resp => resp.url().includes('/api/extract')),
    page.keyboard.press('Enter'),
  ]);
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(artDir, 'phase3_4_before_390px_active.png') });
  console.log('Captured before 390px active');
  await page.close();

  await browser.close();
  console.log('All before screenshots captured successfully!');
}

capture().catch((err) => {
  console.error(err);
  process.exit(1);
});
