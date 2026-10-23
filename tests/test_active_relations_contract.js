/**
 * Regression Test Suite for CausalGraphRenderer activeRelations Contract & Safety
 * Tests initialization, boundary normalization, empty states, rapid view switching,
 * and malformed API data without throwing runtime exceptions.
 */
const fs = require("fs");
const path = require("path");
const assert = require("assert");

const graphJsPath = path.join(__dirname, "../evryn/web/static/js/graph.js");
const graphJsCode = fs.readFileSync(graphJsPath, "utf8");

// Mock DOM elements
class MockSVGElement {
  constructor(tag = "svg") {
    this.tagName = tag.toUpperCase();
    this.children = [];
    this.attributes = {};
    this.style = {};
    this.dataset = {};
  }
  setAttribute(k, v) { this.attributes[k] = String(v); }
  getAttribute(k) { return this.attributes[k]; }
  appendChild(c) { this.children.push(c); return c; }
  removeChild(c) {
    const idx = this.children.indexOf(c);
    if (idx >= 0) this.children.splice(idx, 1);
    return c;
  }
  get firstChild() { return this.children[0] || null; }
  querySelector(sel) { return null; }
  querySelectorAll(sel) { return []; }
  getBoundingClientRect() { return { width: 800, height: 600, top: 0, left: 0 }; }
  addEventListener() {}
  removeEventListener() {}
}

class MockContainer {
  constructor() {
    this.clientWidth = 800;
    this.clientHeight = 600;
    this.children = [];
    this.style = {};
  }
  appendChild(c) { this.children.push(c); return c; }
  querySelectorAll(sel) { return []; }
  querySelector(sel) { return null; }
  getBoundingClientRect() { return { width: 800, height: 600, top: 0, left: 0 }; }
  addEventListener() {}
}

const mockDoc = {
  getElementById(id) {
    if (id === "causal-graph-svg") return new MockSVGElement("svg");
    if (id === "graph-viewport") return new MockContainer();
    return new MockSVGElement("g");
  },
  createElementNS(ns, tag) {
    return new MockSVGElement(tag);
  },
  addEventListener() {},
};

// Evaluate graph.js in clean environment
const ctx = {
  document: mockDoc,
  window: { innerWidth: 1024, innerHeight: 768, addEventListener: () => {} },
  requestAnimationFrame: (cb) => setTimeout(cb, 16),
  cancelAnimationFrame: (id) => clearTimeout(id),
  setTimeout: setTimeout,
  clearTimeout: clearTimeout,
  console: console,
  Math: Math,
  module: { exports: {} },
  exports: {},
};

const vm = require("vm");
vm.createContext(ctx);
vm.runInContext(graphJsCode + "\n;this.CausalGraphRenderer = (typeof CausalGraphRenderer !== 'undefined' ? CausalGraphRenderer : module.exports.CausalGraphRenderer);", ctx);

const CausalGraphRenderer = ctx.CausalGraphRenderer || ctx.module.exports.CausalGraphRenderer;
assert(CausalGraphRenderer, "CausalGraphRenderer must be exported");

console.log("===============================================================");
console.log(" RUNNING activeRelations CONTRACT & SAFETY TEST SUITE");
console.log("===============================================================");

// 1. Initial State Contract: activeRelations must be an array immediately after construction
const renderer = new CausalGraphRenderer("graph-viewport", "causal-graph-svg");
assert(Array.isArray(renderer.activeRelations), "TEST 1 FAILED: activeRelations must be an Array on construction");
assert.strictEqual(renderer.activeRelations.length, 0, "TEST 1 FAILED: initial activeRelations should be empty");
console.log("  ✓ [TEST 1] Initial state contract: activeRelations is initialized to [] in constructor");

// 2. Safe execution of rendering methods before setData is called
assert.doesNotThrow(() => {
  renderer.renderElements();
}, "TEST 2 FAILED: renderElements before setData should not throw");
assert.doesNotThrow(() => {
  renderer.tick();
}, "TEST 2 FAILED: tick before setData should not throw");
assert.doesNotThrow(() => {
  renderer.setPhysicsPreset("rubber_band");
}, "TEST 2 FAILED: setPhysicsPreset before setData should not throw");
assert.doesNotThrow(() => {
  renderer.highlightSentenceElements([]);
}, "TEST 2 FAILED: highlightSentenceElements before setData should not throw");
console.log("  ✓ [TEST 2] Lifecycle safety: renderElements, tick, physics succeed before setData");

// 3. setData with empty nodes and relations
assert.doesNotThrow(() => {
  renderer.setData([], []);
}, "TEST 3 FAILED: setData([], []) should not throw");
assert(Array.isArray(renderer.activeRelations), "TEST 3 FAILED: activeRelations must be an array after empty setData");
assert.strictEqual(renderer.activeRelations.length, 0, "TEST 3 FAILED: activeRelations should be empty");
console.log("  ✓ [TEST 3] Empty state contract: setData([], []) sets activeRelations = [] safely");

// 4. setData with malformed inputs (null, undefined, malformed objects)
assert.doesNotThrow(() => {
  renderer.setData(null, null);
}, "TEST 4 FAILED: setData(null, null) should not crash");
assert(Array.isArray(renderer.activeRelations), "TEST 4 FAILED: activeRelations must remain array after null inputs");

assert.doesNotThrow(() => {
  renderer.setData(undefined, undefined);
}, "TEST 4 FAILED: setData(undefined, undefined) should not crash");
assert(Array.isArray(renderer.activeRelations), "TEST 4 FAILED: activeRelations must remain array after undefined inputs");
console.log("  ✓ [TEST 4] Boundary normalization: setData(null, null) and setData(undefined, undefined) normalized safely");

// 5. Successful data population
const testNodes = [
  { id: "n1", name: "Temperature", x: 100, y: 100 },
  { id: "n2", name: "Performance", x: 200, y: 200 },
];
const testRelations = [
  { id: "r1", cause_name: "Temperature", effect_name: "Performance", relation_type: "DIRECT_CAUSE", effect_polarity: "negative" },
];
assert.doesNotThrow(() => {
  renderer.setData(testNodes, testRelations);
}, "TEST 5 FAILED: setData with valid data threw");
assert.strictEqual(renderer.activeRelations.length, 1, "TEST 5 FAILED: should have 1 activeRelation");
console.log("  ✓ [TEST 5] Successful population: activeRelations correctly reflects valid graph edges");

// 6. Rapid reset, clearing and regeneration
assert.doesNotThrow(() => {
  renderer.clear();
  assert(Array.isArray(renderer.activeRelations), "activeRelations must be array after clear()");
  assert.strictEqual(renderer.activeRelations.length, 0);
  renderer.setData(testNodes, testRelations);
  renderer.clear();
  renderer.setData([], []);
}, "TEST 6 FAILED: rapid reset / clear threw");
console.log("  ✓ [TEST 6] Rapid reset and clearing: clear() maintains activeRelations = [] array contract");

// 7. Iteration safety if activeRelations property was deleted or corrupted
renderer.activeRelations = undefined;
assert.doesNotThrow(() => {
  renderer.renderElements();
  renderer.tick();
  renderer.highlightSentenceElements(["s1"]);
}, "TEST 7 FAILED: methods crashed when activeRelations was undefined");
console.log("  ✓ [TEST 7] Corruption defense: iteration loops gracefully guard against undefined activeRelations");

console.log("===============================================================");
console.log(" RESULTS: 7/7 activeRelations REGRESSION TESTS PASSED (100%)");
console.log("===============================================================");
