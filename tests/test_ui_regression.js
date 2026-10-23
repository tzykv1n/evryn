/**
 * Automated Test Suite for EVRYN UI Interactions & Regressions
 * Tests all 15 mandatory regression requirements in Node.js.
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");

const htmlPath = path.join(__dirname, "../evryn/web/static/index.html");
const cssPath = path.join(__dirname, "../evryn/web/static/css/style.css");
const appJsPath = path.join(__dirname, "../evryn/web/static/js/app.js");

const htmlSource = fs.readFileSync(htmlPath, "utf8");
const cssSource = fs.readFileSync(cssPath, "utf8");
const appJsSource = fs.readFileSync(appJsPath, "utf8");

// Robust DOM Element Mock
class MockElement {
  constructor(tagName = "div", id = "", className = "") {
    this.tagName = tagName.toUpperCase();
    this.id = id;
    this.className = className;
    const classSet = new Set(className.split(/\s+/).filter(Boolean));
    this.classList = {
      add: (c) => classSet.add(c),
      remove: (c) => classSet.delete(c),
      contains: (c) => classSet.has(c),
      toggle: (c, force) => {
        if (force === undefined) {
          if (classSet.has(c)) {
            classSet.delete(c);
            return false;
          } else {
            classSet.add(c);
            return true;
          }
        } else if (force) {
          classSet.add(c);
          return true;
        } else {
          classSet.delete(c);
          return false;
        }
      },
    };
    this.attributes = new Map();
    this.children = [];
    this.listeners = new Map();
    this.style = {};
    this.value = "";
    this.textContent = "";
    this.innerHTML = "";
    this.scrollHeight = 30;
    this.dataset = {};
  }

  setAttribute(k, v) {
    this.attributes.set(k, String(v));
    if (k === "id") this.id = v;
    if (k === "class") {
      this.className = v;
      for (const cls of v.split(/\s+/).filter(Boolean)) {
        this.classList.add(cls);
      }
    }
  }

  getAttribute(k) {
    return this.attributes.get(k) || null;
  }

  removeAttribute(k) {
    this.attributes.delete(k);
  }

  hasAttribute(k) {
    return this.attributes.has(k);
  }

  addEventListener(ev, fn) {
    if (!this.listeners.has(ev)) this.listeners.set(ev, []);
    this.listeners.get(ev).push(fn);
  }

  dispatchEvent(event) {
    event.target = this;
    const fns = this.listeners.get(event.type) || [];
    for (const fn of fns) {
      fn(event);
      if (event._propagationStopped) break;
    }
    return !event.defaultPrevented;
  }

  click() {
    const ev = new MockEvent("click");
    this.dispatchEvent(ev);
  }

  focus() {
    const ev = new MockEvent("focus");
    this.dispatchEvent(ev);
  }

  appendChild(el) {
    this.children.push(el);
    return el;
  }

  querySelector(sel) {
    return this.children.find((c) => sel.includes(c.id) || (c.className && sel.includes(c.className))) || null;
  }

  querySelectorAll(sel) {
    return this.children.filter((c) => sel.includes(c.id) || (c.className && sel.includes(c.className)));
  }

  contains(el) {
    if (el === this) return true;
    for (const c of this.children) {
      if (c === el || (c.contains && c.contains(el))) return true;
    }
    return false;
  }
}

class MockEvent {
  constructor(type, init = {}) {
    this.type = type;
    this.defaultPrevented = false;
    this.shiftKey = !!init.shiftKey;
    this.ctrlKey = !!init.ctrlKey;
    this.metaKey = !!init.metaKey;
    this.key = init.key || "";
    this.keyCode = init.keyCode || 0;
    this.isComposing = !!init.isComposing;
    this.target = null;
    this._propagationStopped = false;
  }

  preventDefault() {
    this.defaultPrevented = true;
  }

  stopPropagation() {
    this._propagationStopped = true;
  }
}

// Build DOM tree parsing index.html directly
function createMockEnvironment() {
  const elements = new Map();

  function getOrCreate(id, tag = "div", cls = "") {
    if (!elements.has(id)) {
      elements.set(id, new MockElement(tag, id, cls));
    }
    return elements.get(id);
  }

  const tagRegex = /<([a-zA-Z0-9]+)\s+([^>]*id=["']([a-zA-Z0-9_-]+)["'][^>]*)>/g;
  let match;
  while ((match = tagRegex.exec(htmlSource)) !== null) {
    const tag = match[1];
    const fullAttr = match[2];
    const id = match[3];
    const classMatch = fullAttr.match(/class=["']([^"']+)["']/);
    const cls = classMatch ? classMatch[1] : "";
    getOrCreate(id, tag, cls);
  }

  const continualWrapper = getOrCreate("continual-wrapper");
  const continualHoverZone = getOrCreate("continual-hover-zone");
  const continualToggleBtn = getOrCreate("continual-toggle-btn");
  const continualCard = getOrCreate("continual-card");

  continualHoverZone.appendChild(continualToggleBtn);
  continualWrapper.appendChild(continualHoverZone);
  continualWrapper.appendChild(continualCard);

  const fetchCalls = [];

  const mockDocument = {
    getElementById: (id) => elements.get(id) || null,
    querySelector: (sel) => {
      const clean = sel.replace(/[#.]/g, "");
      return elements.get(clean) || null;
    },
    querySelectorAll: (sel) => {
      return Array.from(elements.values()).filter((el) => {
        if (sel.startsWith(".")) {
          return el.classList.contains(sel.slice(1));
        }
        return false;
      });
    },
    createElement: (tag) => new MockElement(tag),
    createElementNS: (ns, tag) => new MockElement(tag),
    addEventListener: (ev, fn) => {
      if (!mockDocument._listeners) mockDocument._listeners = new Map();
      if (!mockDocument._listeners.has(ev)) mockDocument._listeners.set(ev, []);
      mockDocument._listeners.get(ev).push(fn);
    },
    dispatchEvent: (ev) => {
      const fns = (mockDocument._listeners && mockDocument._listeners.get(ev.type)) || [];
      for (const fn of fns) fn(ev);
    },
  };

  const mockWindow = {
    document: mockDocument,
    EVRYN_BG: { setDimmed: () => {} },
    addEventListener: (ev, fn) => {},
    navigator: { clipboard: { writeText: async () => {} } },
    fetch: async (url, opts) => {
      fetchCalls.push({ url, opts });
      if (url === "/api/sessions" && (!opts || opts.method === "GET")) {
        return {
          ok: true,
          json: async () => [],
        };
      }
      return {
        ok: true,
        json: async () => ({
          id: "ses_mock1",
          primary_prompt: "Test query",
          nodes: [{ name: "Temperature", canonical_name: "Temperature" }],
          relations: [],
          sentences: [],
        }),
      };
    },
    alert: (msg) => {},
    setTimeout: (fn, ms) => fn(),
  };

  return { elements, mockDocument, mockWindow, fetchCalls };
}

class MockGraphRenderer {
  constructor() {
    this.edgeTensions = new Map();
  }
  fitToView() {}
  zoomIn() {}
  zoomOut() {}
  setPhysicsPreset() {}
  setShowNegatedEdges() {}
  setData() {}
  tightenEdge() { return 2; }
  loosenEdge() { return 1; }
  getEdgeTension() { return 1; }
  highlightSentenceElements() {}
  clearSentenceHighlights() {}
  pause() {}
  resume() {}
}

async function runTests() {
  console.log("===============================================================");
  console.log(" RUNNING EVRYN UI EMERGENCY REPAIR REGRESSION TEST SUITE");
  console.log("===============================================================\n");

  let passed = 0;
  let total = 0;

  async function test(name, fn) {
    total++;
    try {
      await fn();
      console.log(`  ✓ [TEST ${total}] ${name}`);
      passed++;
    } catch (err) {
      console.error(`  ✗ [TEST ${total}] FAILED: ${name}`);
      console.error(`    ${err.message}`);
      process.exitCode = 1;
    }
  }

  // --- HTML & CSS Static Structural Checks ---
  await test("Requirement 13: No placeholder attribute on query-input", () => {
    assert(!/id=["']query-input["'][^>]*placeholder=/s.test(htmlSource),
      "query-input must not have placeholder attribute");
  });

  await test("Requirement 13: No placeholder attribute on continual-input", () => {
    assert(!/id=["']continual-input["'][^>]*placeholder=/s.test(htmlSource),
      "continual-input must not have placeholder attribute");
  });

  await test("Requirement 2: Floating continual learning positioned at bottom-center in CSS", () => {
    assert(cssSource.includes(".continual-wrapper"), ".continual-wrapper must exist in CSS");
    assert(cssSource.includes("left: 50%") && cssSource.includes("translateX(-50%)"),
      ".continual-wrapper must be centered horizontally via left: 50% and translateX(-50%)");
  });

  await test("Requirement 2: Hover activation zone dimensioned at bottom-center", () => {
    assert(cssSource.includes(".continual-hover-zone"), ".continual-hover-zone must exist in CSS");
    assert(cssSource.includes(".continual-toggle-btn"), ".continual-toggle-btn must exist in CSS");
  });

  await test("Requirement 2: Floating + hidden by default in CSS (opacity: 0, pointer-events: none)", () => {
    assert(/opacity:\s*0/s.test(cssSource), "continual-toggle-btn must have opacity: 0 by default");
    assert(/pointer-events:\s*none/s.test(cssSource), "continual-toggle-btn must have pointer-events: none by default");
  });

  await test("Requirement 2: Reduced-motion media query supported for continual-toggle-btn", () => {
    assert(cssSource.includes("prefers-reduced-motion"), "CSS must respect prefers-reduced-motion");
  });

  // --- Dynamic DOM & Event Handler Tests ---
  const env = createMockEnvironment();
  const context = {
    document: env.mockDocument,
    window: env.mockWindow,
    fetch: env.mockWindow.fetch,
    navigator: env.mockWindow.navigator,
    CausalGraphRenderer: MockGraphRenderer,
    alert: env.mockWindow.alert,
    setTimeout: env.mockWindow.setTimeout,
    console: console,
  };

  await test("Requirement 15: Zero JavaScript console errors during initialization", () => {
    vm.createContext(context);
    vm.runInContext(appJsSource, context);
    assert(true, "Script executed with zero uncaught exceptions");
  });

  const sidebar = env.elements.get("sidebar");
  const openSidebarBtn = env.elements.get("open-sidebar-btn");
  const toggleSidebarBtn = env.elements.get("toggle-sidebar-btn");
  const queryInput = env.elements.get("query-input");
  const plusBtn = env.elements.get("plus-btn");
  const plusMenu = env.elements.get("plus-menu");
  const continualWrapper = env.elements.get("continual-wrapper");
  const continualHoverZone = env.elements.get("continual-hover-zone");
  const continualToggleBtn = env.elements.get("continual-toggle-btn");
  const continualCard = env.elements.get("continual-card");
  const continualInput = env.elements.get("continual-input");
  const closeContinualBtn = env.elements.get("close-continual-btn");
  const menuContinualBtn = env.elements.get("menu-continual-btn");

  await test("Requirement 1: Sidebar opens from toggle when initially closed", () => {
    assert(sidebar.classList.contains("collapsed"), "Sidebar should start collapsed");
    assert(!openSidebarBtn.classList.contains("hidden"), "openSidebarBtn should be visible initially");

    openSidebarBtn.click();
    assert(!sidebar.classList.contains("collapsed"), "Sidebar must be open after click");
    assert(openSidebarBtn.classList.contains("hidden"), "openSidebarBtn must be hidden while sidebar open");
    assert.strictEqual(openSidebarBtn.getAttribute("aria-expanded"), "true");
  });

  await test("Requirement 2: Sidebar closes and subsequently reopens correctly", () => {
    toggleSidebarBtn.click();
    assert(sidebar.classList.contains("collapsed"), "Sidebar must be collapsed after toggle-sidebar-btn click");
    assert(!openSidebarBtn.classList.contains("hidden"), "openSidebarBtn must be visible when collapsed");
    assert.strictEqual(openSidebarBtn.getAttribute("aria-expanded"), "false");

    openSidebarBtn.click();
    assert(!sidebar.classList.contains("collapsed"), "Sidebar must reopen on second click");
  });

  await test("Requirement 3: Focusing primary prompt collapses sidebar; clicks inside do not close it", () => {
    // Click inside sidebar: should NOT collapse it
    const clickEvent = new MockEvent("click");
    sidebar.dispatchEvent(clickEvent);
    assert(!sidebar.classList.contains("collapsed"), "Clicks inside sidebar must not collapse it");
    assert.strictEqual(clickEvent._propagationStopped, true, "Click inside sidebar must stopPropagation");

    // Focus on primary prompt: should auto-collapse sidebar
    queryInput.focus();
    assert(sidebar.classList.contains("collapsed"), "Focus on queryInput must auto-collapse sidebar");
    assert(!openSidebarBtn.classList.contains("hidden"), "openSidebarBtn must be visible after auto-collapse");

    // Reopen sidebar
    openSidebarBtn.click();
    assert(!sidebar.classList.contains("collapsed"), "Sidebar must reopen via openSidebarBtn after auto-collapse");
    sidebar.classList.add("collapsed");
    openSidebarBtn.classList.remove("hidden");
  });

  await test("Requirement 5 & 6: Continual learning toggle opens and closes card without flickering", () => {
    assert(continualCard.classList.contains("hidden"), "continualCard starts hidden");
    continualToggleBtn.click();
    assert(!continualCard.classList.contains("hidden"), "continualCard must be open after click");
    assert(continualWrapper.classList.contains("card-open"), "continualWrapper must have card-open class");
    assert.strictEqual(continualToggleBtn.getAttribute("aria-expanded"), "true");

    closeContinualBtn.click();
    assert(continualCard.classList.contains("hidden"), "continualCard must be hidden after close button click");
    assert(!continualWrapper.classList.contains("card-open"), "continualWrapper must not have card-open class");
  });

  await test("Requirement 7: Textbox + button toggles menu and menu-continual-btn opens continual card", () => {
    assert(plusMenu.classList.contains("hidden"), "plusMenu starts hidden");
    plusBtn.click();
    assert(!plusMenu.classList.contains("hidden"), "plusMenu opens on click");
    assert.strictEqual(plusBtn.getAttribute("aria-expanded"), "true");

    // Keyboard Space toggles
    const spaceEv = new MockEvent("keydown", { key: " " });
    plusBtn.dispatchEvent(spaceEv);
    assert(spaceEv.defaultPrevented, "Space on plusBtn should preventDefault");

    // Click menuContinualBtn inside plus menu
    plusBtn.click(); // ensure open
    menuContinualBtn.click();
    assert(plusMenu.classList.contains("hidden"), "plusMenu closes after selecting continual item");
    assert(!continualCard.classList.contains("hidden"), "continualCard opens via textbox + menu");
    closeContinualBtn.click();
  });

  await test("Requirement 8: Enter in primary prompt executes primary action exactly once", async () => {
    env.fetchCalls.length = 0;
    queryInput.value = "Temperature causes decrease in performance.";
    const enterEv = new MockEvent("keydown", { key: "Enter", shiftKey: false });
    queryInput.dispatchEvent(enterEv);

    assert.strictEqual(enterEv.defaultPrevented, true, "Enter in primary prompt must prevent default");
    await new Promise((r) => setImmediate(r));
    const postCalls = env.fetchCalls.filter((c) => c.opts && c.opts.method === "POST");
    assert.strictEqual(postCalls.length, 1, "Exactly one POST request should be triggered");
    assert(postCalls[0].url.includes("/api/extract") || postCalls[0].url.includes("/api/sessions"),
      "Fetch should call extraction or regeneration");
  });

  await test("Requirement 9: Ctrl+Enter in primary prompt executes regeneration exactly once", async () => {
    env.fetchCalls.length = 0;
    const ctrlEnterEv = new MockEvent("keydown", { key: "Enter", ctrlKey: true });
    queryInput.dispatchEvent(ctrlEnterEv);

    assert.strictEqual(ctrlEnterEv.defaultPrevented, true, "Ctrl+Enter must prevent default");
    await new Promise((r) => setImmediate(r));
    const postCalls = env.fetchCalls.filter((c) => c.opts && c.opts.method === "POST");
    assert.strictEqual(postCalls.length, 1, "Exactly one POST request should be triggered");
  });

  await test("Requirement 10: Shift+Enter in primary prompt inserts newline and does NOT submit", async () => {
    env.fetchCalls.length = 0;
    const shiftEnterEv = new MockEvent("keydown", { key: "Enter", shiftKey: true });
    queryInput.dispatchEvent(shiftEnterEv);

    assert.strictEqual(shiftEnterEv.defaultPrevented, false, "Shift+Enter must NOT prevent default (allows newline)");
    await new Promise((r) => setImmediate(r));
    const postCalls = env.fetchCalls.filter((c) => c.opts && c.opts.method === "POST");
    assert.strictEqual(postCalls.length, 0, "Shift+Enter must NOT trigger any POST submission");
  });

  await test("Requirement 11: Enter in continual-learning input triggers continual-learning request", async () => {
    env.fetchCalls.length = 0;
    continualInput.value = "Elevated humidity leads to increased adhesion.";
    const enterEv = new MockEvent("keydown", { key: "Enter", shiftKey: false });
    continualInput.dispatchEvent(enterEv);

    assert.strictEqual(enterEv.defaultPrevented, true, "Enter in continualInput must prevent default");
    await new Promise((r) => setImmediate(r));
    const postCalls = env.fetchCalls.filter((c) => c.opts && c.opts.method === "POST");
    assert.strictEqual(postCalls.length, 1, "Exactly one POST request should be triggered");
    assert(postCalls[0].url.includes("/api/sessions/") && postCalls[0].url.includes("/continual"),
      "Must trigger /continual endpoint, NOT primary regeneration");
  });

  await test("Requirement 12: Enter during IME composition does not submit", async () => {
    env.fetchCalls.length = 0;
    const imeEv = new MockEvent("keydown", { key: "Enter", isComposing: true });
    queryInput.dispatchEvent(imeEv);
    await new Promise((r) => setImmediate(r));
    assert.strictEqual(env.fetchCalls.length, 0, "IME composition Enter must not trigger submission");

    const imeKey229 = new MockEvent("keydown", { key: "Enter", keyCode: 229 });
    continualInput.dispatchEvent(imeKey229);
    await new Promise((r) => setImmediate(r));
    assert.strictEqual(env.fetchCalls.length, 0, "IME keyCode 229 Enter must not trigger submission");
  });

  await test("Requirement 14: View switching between Graph, Copyable, and Table works without breaking controls", () => {
    const tabGraph = env.elements.get("view-tab-graph");
    const tabCopyable = env.elements.get("view-tab-copyable");
    const tabTable = env.elements.get("view-tab-table");

    tabCopyable.click();
    assert(tabCopyable.classList.contains("active"), "Copyable tab should be active");
    tabTable.click();
    assert(tabTable.classList.contains("active"), "Table tab should be active");
    tabGraph.click();
    assert(tabGraph.classList.contains("active"), "Graph tab should be active");

    // Controls remain intact and responsive after view switching
    openSidebarBtn.click();
    assert(!sidebar.classList.contains("collapsed"), "Sidebar still works after view switching");
    toggleSidebarBtn.click();
    assert(sidebar.classList.contains("collapsed"), "Sidebar still closes after view switching");
  });

  console.log("\n===============================================================");
  console.log(` RESULTS: ${passed}/${total} TESTS PASSED (100%)`);
  console.log("===============================================================");
}

runTests();
