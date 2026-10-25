# Piek Image and PDF Rendering Quality Assurance & Architectural Repair
**Project:** Piek Universal Viewer (`/home/tk/projects/piek`)  
**Scope:** Diagnosis, Architectural Repair, and Verification of High-DPI and Vector PDF Rendering  
**Date:** October 25, 2026  
**Auditor:** Core Systems & Desktop Engineering  

---

## 1. Issue Overview & Technical Diagnosis

Prior to this engineering cycle, documents and images viewed inside Piek exhibited visual softness, pixelation during zooming, and blurriness on modern high-DPI displays (e.g. 1440p and 4K monitors, or 1.25x–2.0x display scaling).

An exhaustive investigation of the Piek C++/Qt6 codebase (`src/pdf_engine.h`, `src/canvas_widget.h`, `src/main_window.h`) revealed five fundamental architectural bottlenecks:

### 1.1 Fixed-DPI Rasterization (No Vector Re-rendering on Zoom)
- **Root Cause:** In `MainWindow::goToPage`, PDF pages were always rasterized via `m_pdfEngine.renderPage(m_currentPdfPage, 150.0)` at a hardcoded 150.0 DPI.
- **Degradation Mechanism:** When users zoomed into the page (e.g. 200%, 300%, or 500% magnification to inspect equations, dense tables, or small-font annotations), `CanvasWidget` simply stretched the 150 DPI bitmap bilinearly using `painter.drawPixmap()`. Because Poppler was never re-queried for a higher-resolution vector rasterization, text and mathematical formulas degraded into blurry, pixelated bitmaps.

### 1.2 Complete Lack of Qt Device Pixel Ratio (DPR) Awareness
- **Root Cause:** Neither `PdfEngine` nor `CanvasWidget` accounted for `devicePixelRatioF()`.
- **Degradation Mechanism:** On displays configured with 1.25x, 1.5x, or 2.0x display scaling (or HiDPI monitors), Qt stretched a 1.0 DPR raster pixmap across physical display pixels without 1:1 hardware pixel alignment. A 150 DPI render displayed on a 2.0x HiDPI screen yielded an effective physical resolution of only 75 DPI.

### 1.3 Redundant Per-Frame Resampling in `paintEvent`
- **Root Cause:** In `CanvasWidget::paintEvent`:
  ```cpp
  QTransform t;
  t.rotate(m_rotationAngle);
  QPixmap rotated = m_originalPixmap.transformed(t, Qt::SmoothTransformation);
  ```
- **Degradation Mechanism:** On **every single repaint** (including mouse cursor hover, laser pointer movements, and window activation), Piek re-filtered and transformed the entire multi-megapixel pixmap, even when `m_rotationAngle == 0`. This caused lossy repeated bilinear filtering passes and unnecessary CPU overhead.

### 1.4 Missing Poppler Font Hinting
- **Root Cause:** `PdfEngine::renderPage` enabled only `antialiasing` and `text_antialiasing`, omitting `text_hinting`.
- **Degradation Mechanism:** Glyphs rendered at smaller base sizes suffered from irregular stem weights, subpixel blurriness, and fuzzy serifs.

### 1.5 Wholesale Cache Eviction
- **Root Cause:** `PdfEngine` cleared its entire cache whenever `m_cache.size() > 12`.
- **Degradation Mechanism:** Navigating past page 12 purged all previously loaded pages from RAM, forcing redundant disk I/O and Poppler re-rasterization on backward navigation.

---

## 2. Engineering Solution & Implementation

### 2.1 Dynamic Multi-Resolution Vector Rasterization (`src/main_window.h` & `src/canvas_widget.h`)
- **Debounced Zoom Listener:** Added `m_zoomDebounceTimer` (120ms single-shot) to `CanvasWidget`, firing `m_onZoomSettled(double scale)`.
- **Target DPI Calculation:** In `MainWindow::handleDynamicPdfRerender`:
  $$\text{Target DPI} = \mathrm{clamp}\left(150.0 \times \text{scale} \times \text{dpr},\; 96.0,\; 600.0\right)$$
- **Non-Jumping Dynamic Pixmap Replacement:** When zoom settles and the target DPI exceeds the current DPI by $> 12$ DPI:
  1. Poppler renders the page natively at `targetDpi` (up to 600 DPI).
  2. The resulting `QPixmap` is assigned `pixmap.setDevicePixelRatio(targetDpi / 150.0)`.
  3. `CanvasWidget::updateRenderedPixmap` swaps the underlying buffer while preserving exact device-independent width, scale factor, and pan coordinates. The screen view remains perfectly stable while text visibly snaps from standard resolution to razor-sharp vector clarity.

### 2.2 Device-Independent Coordinate Alignment (`src/canvas_widget.h`)
- Upgraded `paintEvent`, `recalculateFit`, and `clampPanOffset` to query `rotated.deviceIndependentSize().width()` and `height()` rather than raw physical pixel counts.
- Selection rectangles, OCR bounding boxes, and PDF search highlights remain 100% mathematically synchronized regardless of whether the raster buffer is 150 DPI, 300 DPI, or 600 DPI.

### 2.3 Rotation Caching & Zero-Copy 0° Fast Path (`src/canvas_widget.h`)
- Introduced `m_displayPixmap` cached directly within `CanvasWidget`.
- When `m_rotationAngle == 0`, `m_displayPixmap = m_originalPixmap` (zero copy, zero resampling).
- When `m_rotationAngle != 0`, transformation is computed exactly once per rotation event rather than on every paint event.

### 2.4 Poppler Text Hinting Enabled (`src/pdf_engine.h`)
- Enabled `pr.set_render_hint(poppler::page_renderer::text_hinting, true)`. Poppler now applies full font hinting matrices, producing crisp stems and sharp typographic serifs.

### 2.5 Bounded FIFO/LRU Page Cache (`src/pdf_engine.h`)
- Implemented bounded eviction supporting up to 24 multi-resolution page pixmaps.
- Rather than wiping the entire cache, the oldest entries are evicted sequentially via `m_cacheOrder`, ensuring instant backward/forward page flips.

---

## 3. Verification & Test Suite Results

The Piek automated test suite (`tests/test_piek.cpp`) was expanded to test high-DPI rendering, vector rasterization, cache retention, and device pixel ratio normalization:

```
========================================================
               PIEK AUTOMATED TEST SUITE                
========================================================

[Suite 1: PDF Engine Tests]
  [PASS] Load valid real PDF document (main.pdf)
  [PASS] PdfEngine isLoaded() returns true
  [PASS] Page count matches expected (>= 30 pages)
  [PASS] Page 0 rect dimensions (A4 point dimensions)
  [PASS] Render page 0 at 100 DPI to QPixmap
  [PASS] Rendered pixmap has expected pixel dimensions
  [PASS] Render page 0 at 300 DPI (high-res vector rasterization)
  [PASS] 300 DPI pixmap matches high-res pixel dimensions (>2000x3000)
  [PASS] Bounded cache preserves and serves high-DPI page render
  [PASS] Extract native text from page 0
  [PASS] Extracted text contains title keywords
  [PASS] Extract word-level bounding boxes for text selection
  [PASS] Search for keyword 'Causal' across multi-page document
  [PASS] First search match is on page 0
  [PASS] Metadata contains page count key
  [PASS] Metadata pages count matches document page count
  [PASS] Gracefully fail on nonexistent PDF without crashing
  [PASS] isLoaded() is false after failed load

[Suite 2: CanvasWidget Zoom Modes & Fitting Tests]
  [PASS] Default zoom mode is FitPage
  [PASS] FitPage scale ensures whole page fits within viewport height margins
  [PASS] Explicit switch to ZoomMode::FitWidth
  [PASS] FitWidth scale > FitPage scale for portrait document
  [PASS] FitWidth scale exactly matches viewport width minus side padding
  [PASS] Explicit switch to ZoomMode::ActualSize
  [PASS] Actual size scale is exactly 1.0 (100%)
  [PASS] Zoom factor change automatically sets ZoomMode::Custom
  [PASS] Scale factor reflects magnification (125%)
  [PASS] Preserves FitPage mode across mixed-dimension page transition
  [PASS] Landscape page fits completely within both width and height without clipping
  [PASS] Canvas respects high-DPI device pixel ratio
  [PASS] Device-independent width normalized by DPR (1600/2=800)

[Suite 3: Fullscreen & Layout Stability Tests]
  [PASS] MainWindow initialized and visible
  [PASS] Executed 12 consecutive fullscreen entry/exit cycles without layout corruption
  [PASS] MainWindow restored to normal window mode
  [PASS] Window resize to 800x600 successful
  [PASS] Window resize to 1280x800 successful

[Suite 4: ZIP Archive & Yazi Tool Tests]
  [PASS] Sample test ZIP archive with unicode exists
  [PASS] piek-archive-tool inspect runs cleanly
  [PASS] Archive inspection accurately lists UTF-8 entry name with diacritics
  [PASS] piek-archive-tool extract-subfolder succeeds
  [PASS] Extracted unicode file exists with intact content in dedicated subfolder
  [PASS] Safe extraction handles existing folder without fatal crash
  [PASS] Corrupt archive returns non-zero error code gracefully

[Suite 5: State Manager & Display Tests]
  [PASS] Add recent file to recents list
  [PASS] Persist and retrieve reading position (Page 14)
  [PASS] Enumerate connected display screens

[Suite 6: Image Format Tests]
  [PASS] Load PNG image asset (piek-64.png)
  [PASS] PNG dimensions match 64x64

========================================================
TEST RESULTS: 48 / 48 tests passed (100% PASS)
========================================================
```

## 4. Deployment
The updated binary was built with `-O2 -std=c++17` and installed system-wide to `/home/tk/.local/bin/piek` (with backward-compatible symlink to `photos`).
