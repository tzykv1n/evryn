/**
 * EVRYN Hand-Drawn Minimalist Interactive SVG Causal Graph
 * Real force simulation, explicit collision avoidance, direct dragging, and evidence inspection.
 */
class CausalGraphRenderer {
  constructor(containerId, svgId, onSelectRelation, onSelectNode, onLayoutChanged, onHoverNode) {
    this.container = document.getElementById(containerId);
    this.svg = document.getElementById(svgId);
    this.transformGroup = this.svg
      ? (this.svg.querySelector(".graph-transform-group") ||
         this.svg.querySelector("#" + (this.svg.id === "gold-graph-svg" ? "gold-" : "") + "graph-transform-group") ||
         this.svg.querySelector("g"))
      : document.getElementById("graph-transform-group");
    this.edgesLayer = this.svg
      ? (this.svg.querySelector(".edges-layer") ||
         this.svg.querySelector("#" + (this.svg.id === "gold-graph-svg" ? "gold-" : "") + "edges-layer"))
      : document.getElementById("edges-layer");
    this.nodesLayer = this.svg
      ? (this.svg.querySelector(".nodes-layer") ||
         this.svg.querySelector("#" + (this.svg.id === "gold-graph-svg" ? "gold-" : "") + "nodes-layer"))
      : document.getElementById("nodes-layer");

    this.onSelectRelation = onSelectRelation || function () {};
    this.onSelectNode = onSelectNode || function () {};
    this.onLayoutChanged = onLayoutChanged || function () {};
    this.onHoverNode = onHoverNode || function () {};

    this.nodes = [];
    this.relations = [];
    this.activeRelations = [];
    this.nodeMap = new Map();

    // Viewport transform (Pan & Zoom)
    this.scale = 1.0;
    this.panX = 0;
    this.panY = 0;
    this.isPanning = false;
    this.startPan = { x: 0, y: 0 };

    // Physics parameters
    this.alpha = 1.0;
    this.alphaMin = 0.002;
    this.alphaDecay = 0.022;
    this.repulsionK = 180;
    this.springK = 0.04;
    this.springLength = 160;
    this.centerGravity = 0.008;

    // Physics & Tension Presets
    this.physicsPreset = "rubber_band";
    this.edgeTensions = new Map();
    this.showNegatedEdges = false;

    // Dragging state
    this.draggedNode = null;
    this.dragOffset = { x: 0, y: 0 };
    this.hasMovedDrag = false;

    // Selection state
    this.selectedRelationId = null;
    this.selectedNodeName = null;

    this.initEvents();
  }

  clear() {
    this.setData([], []);
  }

  setData(nodesData, relationsData, options = {}) {
    this.relations = Array.isArray(relationsData) ? relationsData : [];
    this.activeRelations = [];
    this.nodeMap.clear();

    if (options.physicsPreset) {
      this.physicsPreset = options.physicsPreset;
    }
    if (options.tensionSettings) {
      for (const [k, v] of Object.entries(options.tensionSettings)) {
        this.edgeTensions.set(k, v);
      }
    }

    const rect = this.container ? this.container.getBoundingClientRect() : { width: 900, height: 600 };
    const cX = rect.width > 100 ? rect.width / 2 : 450;
    const cY = rect.height > 100 ? rect.height / 2 : 300;

    const safeNodes = Array.isArray(nodesData) ? nodesData : [];

    // 1. Setup node objects with dimensions and layout
    this.nodes = safeNodes.map((nd, idx) => {
      const name = nd.canonical_name || nd.name || nd.display_name || `node_${idx}`;
      const label = nd.display_name || nd.name || name;
      const category = nd.category || "Unclassified";
      const state = nd.state || null;
      const stateDelta = typeof nd.state_delta === "number" ? nd.state_delta : (typeof nd.stateDelta === "number" ? nd.stateDelta : null);

      // Text width estimation: ~8px per character + 24px horizontal padding
      const maxCharCount = Math.max(label.length, state ? state.length + 4 : 0);
      const textWidth = Math.max(80, maxCharCount * 8.2 + 28);
      const textHeight = state ? 38 : 32;

      // Initial coordinates
      let x = nd.x;
      let y = nd.y;
      if (x == null || y == null || isNaN(x) || isNaN(y)) {
        const angle = (idx * 2 * Math.PI) / Math.max(1, safeNodes.length);
        const radius = Math.min(cX, cY) * 0.65;
        x = cX + radius * Math.cos(angle);
        y = cY + radius * Math.sin(angle);
      }

      const nodeObj = {
        id: nd.id || `node_${idx}`,
        name: name,
        canonical_name: name,
        label: label,
        category: category,
        colorFill: nd.color_fill || nd.colorFill,
        colorStroke: nd.color_stroke || nd.colorStroke,
        evidence_sentence_ids: Array.isArray(nd.evidence_sentence_ids) ? nd.evidence_sentence_ids : [],
        state: state,
        stateDelta: stateDelta,
        x: x,
        y: y,
        vx: 0,
        vy: 0,
        width: textWidth,
        height: textHeight,
        fixed: !!nd.fixed,
        in_degree: nd.in_degree || 0,
        out_degree: nd.out_degree || 0,
        isPinned: false,
      };

      this.nodeMap.set(name, nodeObj);
      return nodeObj;
    });

    // 2. Setup relation references
    this.activeRelations = [];
    for (const rel of this.relations) {
      const srcName = rel.cause_name || rel.source || rel.cause;
      const tgtName = rel.effect_name || rel.target || rel.effect;
      const src = this.nodeMap.get(srcName);
      const tgt = this.nodeMap.get(tgtName);
      if (src && tgt) {
        if (rel.tension_level && !this.edgeTensions.has(rel.id)) {
          this.edgeTensions.set(rel.id, rel.tension_level);
        }
        this.activeRelations.push({
          data: rel,
          source: src,
          target: tgt,
        });
      }
    }

    this.updateLegendCategories(safeNodes);
    this.renderElements();
    this.restartSimulation(1.0);
    this.fitToView();
  }

  updateLegendCategories(nodesData) {
    const listElem = document.getElementById("legend-categories-list");
    if (!listElem) return;

    const activeCats = new Set((nodesData || []).map((n) => n.category || "Concept"));
    const allChips = listElem.querySelectorAll(".category-chip");

    allChips.forEach((chip) => {
      const classes = chip.className;
      let matched = false;
      for (const cat of activeCats) {
        const slug = cat.toLowerCase().replace(/[^a-z]/g, "");
        if (classes.includes(`cat-${slug}`)) {
          matched = true;
          break;
        }
      }
      chip.style.display = (activeCats.size === 0 || matched) ? "inline-flex" : "none";
    });
  }

  initEvents() {
    if (!this.container) return;
    // Wheel Zoom
    this.container.addEventListener("wheel", (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
      const rect = this.container.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const newScale = Math.max(0.25, Math.min(3.0, this.scale * zoomFactor));
      this.panX = mouseX - (mouseX - this.panX) * (newScale / this.scale);
      this.panY = mouseY - (mouseY - this.panY) * (newScale / this.scale);
      this.scale = newScale;
      this.updateTransform();
    }, { passive: false });

    // Pan & Drag Start
    this.container.addEventListener("mousedown", (e) => {
      if (e.target.closest(".graph-node")) {
        return; // Handled by node drag
      }
      this.isPanning = true;
      this.startPan = { x: e.clientX - this.panX, y: e.clientY - this.panY };
    });

    window.addEventListener("mousemove", (e) => {
      if (this.isPanning) {
        this.panX = e.clientX - this.startPan.x;
        this.panY = e.clientY - this.startPan.y;
        this.updateTransform();
      } else if (this.draggedNode) {
        this.hasMovedDrag = true;
        const rect = this.container.getBoundingClientRect();
        const svgX = (e.clientX - rect.left - this.panX) / this.scale;
        const svgY = (e.clientY - rect.top - this.panY) / this.scale;

        this.draggedNode.x = svgX - this.dragOffset.x;
        this.draggedNode.y = svgY - this.dragOffset.y;
        this.restartSimulation(0.2);
        this.tick();
      }
    });

    window.addEventListener("mouseup", () => {
      if (this.isPanning) {
        this.isPanning = false;
      }
      if (this.draggedNode) {
        this.draggedNode.isPinned = false;
        if (this.hasMovedDrag) {
          // Persist coordinates
          const posMap = {};
          for (const n of this.nodes) {
            posMap[n.name] = { x: Math.round(n.x), y: Math.round(n.y) };
          }
          this.onLayoutChanged(posMap);
        }
        this.draggedNode = null;
        this.restartSimulation(0.15);
      }
    });

    window.addEventListener("resize", () => {
      this.handleResize();
    });
  }

  handleResize() {
    if (this.nodes && this.nodes.length > 0) {
      this.fitToView();
    }
  }

  updateTransform() {
    if (this.transformGroup && this.transformGroup.setAttribute) {
      this.transformGroup.setAttribute(
        "transform",
        `translate(${this.panX}, ${this.panY}) scale(${this.scale})`
      );
    }
  }

  zoomIn() {
    this.scale = Math.min(3.0, this.scale * 1.2);
    this.updateTransform();
  }

  zoomOut() {
    this.scale = Math.max(0.25, this.scale * 0.8);
    this.updateTransform();
  }

  fitToView() {
    if (this.nodes.length === 0) return;
    const rect = this.container.getBoundingClientRect();
    if (rect.width < 50 || rect.height < 50) return;

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const n of this.nodes) {
      minX = Math.min(minX, n.x - n.width / 2);
      maxX = Math.max(maxX, n.x + n.width / 2);
      minY = Math.min(minY, n.y - n.height / 2);
      maxY = Math.max(maxY, n.y + n.height / 2);
    }

    const padding = 80;
    const graphW = Math.max(100, maxX - minX + padding * 2);
    const graphH = Math.max(100, maxY - minY + padding * 2);

    const scaleX = rect.width / graphW;
    const scaleY = rect.height / graphH;
    this.scale = Math.max(0.35, Math.min(1.4, Math.min(scaleX, scaleY)));

    const midX = (minX + maxX) / 2;
    const midY = (minY + maxY) / 2;
    this.panX = rect.width / 2 - midX * this.scale;
    this.panY = rect.height / 2 - midY * this.scale;
    this.updateTransform();
  }

  resetLayout() {
    if (!this.nodes || this.nodes.length === 0) return;
    const rect = this.container ? this.container.getBoundingClientRect() : { width: 600, height: 400 };
    const cX = rect.width > 50 ? rect.width / 2 : 300;
    const cY = rect.height > 50 ? rect.height / 2 : 200;
    const count = this.nodes.length;
    this.nodes.forEach((n, idx) => {
      const angle = (idx * 2 * Math.PI) / Math.max(1, count);
      const radius = Math.min(cX, cY) * 0.65;
      n.x = cX + radius * Math.cos(angle);
      n.y = cY + radius * Math.sin(angle);
      n.vx = 0;
      n.vy = 0;
      n.isPinned = false;
    });
    this.restartSimulation(1.0);
    this.fitToView();
  }

  highlightNode(nodeName) {
    if (!nodeName || !this.nodesLayer) return;
    const norm = nodeName.toLowerCase().replace(/[^a-z0-9]/g, "");
    for (const n of this.nodes) {
      const nNorm = (n.canonical_name || n.name).toLowerCase().replace(/[^a-z0-9]/g, "");
      if (n.groupElem) {
        if (nNorm === norm || nNorm.includes(norm) || norm.includes(nNorm)) {
          n.groupElem.classList.add("synced-highlight");
        } else {
          n.groupElem.classList.remove("synced-highlight");
        }
      }
    }
  }

  clearNodeHighlight() {
    if (!this.nodesLayer) return;
    this.nodesLayer.querySelectorAll(".synced-highlight").forEach(el => el.classList.remove("synced-highlight"));
  }

  alignLayoutWith(otherRenderer, shouldRestart = false) {
    if (!otherRenderer || !otherRenderer.nodeMap) return;
    let anyMatched = false;
    for (const node of this.nodes) {
      const norm = (node.canonical_name || node.name).toLowerCase().replace(/[^a-z0-9]/g, "");
      for (const [otherName, otherNode] of otherRenderer.nodeMap.entries()) {
        const otherNorm = otherName.toLowerCase().replace(/[^a-z0-9]/g, "");
        if (norm === otherNorm || norm.includes(otherNorm) || otherNorm.includes(norm)) {
          node.x = otherNode.x;
          node.y = otherNode.y;
          node.vx = 0;
          node.vy = 0;
          anyMatched = true;
          break;
        }
      }
    }
    if (anyMatched) {
      this.tick();
      if (shouldRestart) {
        this.restartSimulation(0.3);
      }
      this.fitToView();
    }
  }

  restartSimulation(alphaValue) {
    this.alpha = Math.max(this.alpha, alphaValue || 0.6);
    if (!this.animating) {
      this.animating = true;
      this.simulate();
    }
  }

  simulate() {
    if (this.alpha < this.alphaMin) {
      this.animating = false;
      return;
    }

    this.stepPhysics();
    this.tick();

    this.alpha *= 1 - this.alphaDecay;
    requestAnimationFrame(() => this.simulate());
  }

  stepPhysics() {
    const rect = this.container.getBoundingClientRect();
    const cX = rect.width > 100 ? rect.width / 2 : 450;
    const cY = rect.height > 100 ? rect.height / 2 : 300;

    // 1. Repulsion between all node pairs (Coulomb force)
    for (let i = 0; i < this.nodes.length; i++) {
      const n1 = this.nodes[i];
      for (let j = i + 1; j < this.nodes.length; j++) {
        const n2 = this.nodes[j];
        const dx = n2.x - n1.x;
        const dy = n2.y - n1.y;
        const distSq = dx * dx + dy * dy || 1;
        const dist = Math.sqrt(distSq);

        const force = (this.repulsionK * this.repulsionK) / distSq;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        if (!n1.isPinned) {
          n1.vx -= fx * this.alpha;
          n1.vy -= fy * this.alpha;
        }
        if (!n2.isPinned) {
          n2.vx += fx * this.alpha;
          n2.vy += fy * this.alpha;
        }
      }
    }

    // 2. Spring attraction along edges (Hooke's law with physics preset & tension)
    for (const rel of (this.activeRelations || [])) {
      const src = rel.source;
      const tgt = rel.target;
      const dx = tgt.x - src.x;
      const dy = tgt.y - src.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;

      const tension = this.edgeTensions.get(rel.data.id) || rel.data.tension_level || 1;
      const targetLength = this.springLength / (1 + (tension - 1) * 0.28);
      let k = this.springK * (1 + (tension - 1) * 0.45);

      if (this.physicsPreset === "rigid") {
        k *= 2.8;
      } else if (this.physicsPreset === "inelastic") {
        if (dist > targetLength) k *= 2.2;
        else k *= 0.35;
      } else if (this.physicsPreset === "rubber_band") {
        if (dist > targetLength) k *= 1.5;
      }

      const displacement = dist - targetLength;
      const force = displacement * k;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;

      if (!src.isPinned) {
        src.vx += fx * this.alpha;
        src.vy += fy * this.alpha;
      }
      if (!tgt.isPinned) {
        tgt.vx -= fx * this.alpha;
        tgt.vy -= fy * this.alpha;
      }
    }

    // 3. Viewport centering gravity
    for (const n of this.nodes) {
      if (!n.isPinned) {
        n.vx += (cX - n.x) * this.centerGravity * this.alpha;
        n.vy += (cY - n.y) * this.centerGravity * this.alpha;
      }
    }

    // 4. Update positions with damping
    for (const n of this.nodes) {
      if (!n.isPinned) {
        n.vx *= 0.65;
        n.vy *= 0.65;
        n.x += n.vx;
        n.y += n.vy;
      }
    }

    // 5. Explicit Collision Detection & Resolution (AABB bounding box separation)
    const padding = 20;
    for (let i = 0; i < this.nodes.length; i++) {
      const a = this.nodes[i];
      for (let j = i + 1; j < this.nodes.length; j++) {
        const b = this.nodes[j];

        const aHalfW = a.width / 2 + padding;
        const aHalfH = a.height / 2 + padding;
        const bHalfW = b.width / 2 + padding;
        const bHalfH = b.height / 2 + padding;

        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const overlapX = aHalfW + bHalfW - Math.abs(dx);
        const overlapY = aHalfH + bHalfH - Math.abs(dy);

        if (overlapX > 0 && overlapY > 0) {
          if (overlapX < overlapY) {
            const push = (overlapX / 2) * (dx < 0 ? -1 : 1);
            if (!a.isPinned) a.x -= push;
            if (!b.isPinned) b.x += push;
          } else {
            const push = (overlapY / 2) * (dy < 0 ? -1 : 1);
            if (!a.isPinned) a.y -= push;
            if (!b.isPinned) b.y += push;
          }
        }
      }
    }
  }

  renderElements() {
    if (this.edgesLayer) this.edgesLayer.innerHTML = "";
    if (this.nodesLayer) this.nodesLayer.innerHTML = "";

    if (!this.nodes || this.nodes.length === 0) {
      const emptyText = document.createElementNS("http://www.w3.org/2000/svg", "text");
      emptyText.setAttribute("x", "50%");
      emptyText.setAttribute("y", "50%");
      emptyText.setAttribute("text-anchor", "middle");
      emptyText.setAttribute("dominant-baseline", "central");
      emptyText.setAttribute("fill", "#94a3b8");
      emptyText.setAttribute("font-family", "var(--font-mono, monospace)");
      emptyText.setAttribute("font-size", "12");
      emptyText.textContent = "No causal relationships extracted.";
      if (this.nodesLayer) this.nodesLayer.appendChild(emptyText);
      return;
    }

    // Render Edges
    for (const rel of (this.activeRelations || [])) {
      const edgeId = `edge-${rel.data.id}`;
      const isTransitive = !!rel.data.is_transitive;
      const isSuppressed = !!rel.data.is_suppressed;
      const polarity = rel.data.effect_polarity || (rel.data.is_negated ? "unknown" : "positive");
      const edgeColor = rel.data.edge_color || (polarity === "negative" ? "#dc2626" : (polarity === "association" ? "#64748b" : "#0f172a"));
      const edgeStyle = rel.data.edge_style || (polarity === "association" ? "dotted" : (isTransitive ? "dashed" : "solid"));

      let markerId = rel.data.marker_id || "arrowhead-positive";
      if (!rel.data.marker_id) {
        if (isSuppressed) {
          markerId = "arrowhead-negated";
        } else if (polarity === "negative") {
          markerId = "arrowhead-negative";
        } else if (polarity === "association") {
          markerId = "arrowhead-association";
        }
      }

      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("id", edgeId);
      path.setAttribute("class", `graph-edge ${polarity} ${edgeStyle} ${isTransitive ? "transitive" : ""} ${isSuppressed ? "negated-claim" : ""}`);
      path.setAttribute("stroke", edgeColor);
      path.setAttribute("marker-end", `url(#${markerId})`);
      path.dataset.relationId = rel.data.id;
      path.dataset.defaultMarker = markerId;
      path.dataset.edgeColor = edgeColor;
      path.dataset.sentenceIds = (rel.data.evidence_sentence_ids || []).join(",");

      if (isSuppressed && !this.showNegatedEdges) {
        path.style.display = "none";
      } else {
        path.style.display = "block";
      }

      path.addEventListener("click", (e) => {
        e.stopPropagation();
        this.selectRelation(rel.data.id);
      });

      if (this.edgesLayer) this.edgesLayer.appendChild(path);
      rel.pathElem = path;
    }

    // Render Nodes
    for (const n of this.nodes) {
      const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const catSlug = (n.category || "Unclassified").toLowerCase().replace(/[^a-z]/g, "");
      g.setAttribute("class", `graph-node cat-${catSlug}`);
      g.dataset.nodeName = n.name;
      g.dataset.category = n.category || "Unclassified";
      g.dataset.sentenceIds = (n.evidence_sentence_ids || []).join(",");
      n.groupElem = g;

      // Rectangle
      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rect.setAttribute("width", n.width);
      rect.setAttribute("height", n.height);
      rect.setAttribute("x", -n.width / 2);
      rect.setAttribute("y", -n.height / 2);
      rect.setAttribute("rx", "5");
      rect.setAttribute("ry", "5");

      if (n.colorFill) {
        rect.style.fill = n.colorFill;
      }
      if (n.colorStroke) {
        rect.style.stroke = n.colorStroke;
      }
      g.appendChild(rect);

      // Sentence Provenance Indicator Pips (top-right corner)
      if (n.evidence_sentence_ids && n.evidence_sentence_ids.length > 0) {
        const pipsGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
        pipsGroup.setAttribute("class", "node-pips");
        n.evidence_sentence_ids.slice(0, 3).forEach((sId, pIdx) => {
          const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
          circle.setAttribute("cx", n.width / 2 - 8 - pIdx * 8);
          circle.setAttribute("cy", -n.height / 2 + 7);
          circle.setAttribute("r", 3.2);
          circle.setAttribute("fill", this.getSentenceColor(sId));
          circle.setAttribute("stroke", "#ffffff");
          circle.setAttribute("stroke-width", "0.8");
          circle.setAttribute("title", `Evidence from ${sId}`);
          pipsGroup.appendChild(circle);
        });
        g.appendChild(pipsGroup);
      }

      // Text label
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("class", "node-label");
      text.textContent = n.label;

      if (n.state) {
        text.setAttribute("x", 0);
        text.setAttribute("y", -5);
        g.appendChild(text);

        // State sub-badge
        const stateText = document.createElementNS("http://www.w3.org/2000/svg", "text");
        const isNeg = n.stateDelta < 0 || n.state.toLowerCase().includes("decrease") || n.state.toLowerCase().includes("loss");
        stateText.setAttribute("class", `node-state-badge ${isNeg ? "state-negative" : "state-positive"}`);
        stateText.textContent = `${isNeg ? "▼" : "▲"} ${n.state}`;
        stateText.setAttribute("x", 0);
        stateText.setAttribute("y", 9);
        g.appendChild(stateText);
      } else {
        text.setAttribute("x", 0);
        text.setAttribute("y", 1);
        g.appendChild(text);
      }

      // Drag events
      g.addEventListener("mousedown", (e) => {
        e.stopPropagation();
        this.draggedNode = n;
        n.isPinned = true;
        this.hasMovedDrag = false;

        const bRect = this.container.getBoundingClientRect();
        const svgX = (e.clientX - bRect.left - this.panX) / this.scale;
        const svgY = (e.clientY - bRect.top - this.panY) / this.scale;
        this.dragOffset = { x: svgX - n.x, y: svgY - n.y };
      });

      g.addEventListener("click", (e) => {
        e.stopPropagation();
        if (!this.hasMovedDrag) {
          this.selectNode(n.name);
        }
      });

      g.addEventListener("mouseenter", () => {
        if (this.onHoverNode) {
          this.onHoverNode(n, true);
        }
      });

      g.addEventListener("mouseleave", () => {
        if (this.onHoverNode) {
          this.onHoverNode(n, false);
        }
      });

      if (this.nodesLayer) this.nodesLayer.appendChild(g);
      n.groupElem = g;
    }

    this.tick();
  }

  tick() {
    // 1. Update node positions
    for (const n of this.nodes) {
      if (n.groupElem) {
        n.groupElem.setAttribute("transform", `translate(${n.x}, ${n.y})`);
      }
    }

    // 2. Update edge paths connecting node perimeters exactly
    for (const rel of (this.activeRelations || [])) {
      if (rel.pathElem) {
        const src = rel.source;
        const tgt = rel.target;

        const startPt = this.getNodePerimeterPoint(src, tgt.x, tgt.y);
        const endPt = this.getNodePerimeterPoint(tgt, src.x, src.y);

        const dx = endPt.x - startPt.x;
        const dy = endPt.y - startPt.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist > 10) {
          if (this.physicsPreset === "string") {
            const tension = this.edgeTensions.get(rel.data.id) || rel.data.tension_level || 1;
            const sag = Math.max(8, 38 / tension);
            const midX = (startPt.x + endPt.x) / 2;
            const midY = (startPt.y + endPt.y) / 2 + sag;
            rel.pathElem.setAttribute("d", `M ${startPt.x} ${startPt.y} Q ${midX} ${midY} ${endPt.x} ${endPt.y}`);
          } else {
            const midX = (startPt.x + endPt.x) / 2 - (dy / dist) * 10;
            const midY = (startPt.y + endPt.y) / 2 + (dx / dist) * 10;
            rel.pathElem.setAttribute("d", `M ${startPt.x} ${startPt.y} Q ${midX} ${midY} ${endPt.x} ${endPt.y}`);
          }
        } else {
          rel.pathElem.setAttribute("d", `M ${startPt.x} ${startPt.y} L ${endPt.x} ${endPt.y}`);
        }
      }
    }
  }

  getNodePerimeterPoint(node, targetX, targetY) {
    const dx = targetX - node.x;
    const dy = targetY - node.y;
    if (Math.abs(dx) < 1e-4 && Math.abs(dy) < 1e-4) {
      return { x: node.x, y: node.y };
    }

    const halfW = node.width / 2;
    const halfH = node.height / 2;

    const tanTheta = Math.abs(dy / dx);
    const tanBox = halfH / halfW;

    let xInt, yInt;
    if (tanTheta <= tanBox) {
      xInt = halfW * (dx > 0 ? 1 : -1);
      yInt = halfW * tanTheta * (dy > 0 ? 1 : -1);
    } else {
      yInt = halfH * (dy > 0 ? 1 : -1);
      xInt = (halfH / tanTheta) * (dx > 0 ? 1 : -1);
    }

    return { x: node.x + xInt, y: node.y + yInt };
  }

  selectRelation(relId) {
    this.selectedRelationId = relId;
    this.selectedNodeName = null;

    // Reset styles preserving explicit edge marker colors
    const allEdges = this.edgesLayer.querySelectorAll(".graph-edge");
    allEdges.forEach((e) => {
      e.classList.remove("selected");
      const defaultMarker = e.dataset.defaultMarker || "arrowhead-positive";
      e.setAttribute("marker-end", `url(#${defaultMarker})`);
      if (e.dataset.edgeColor) {
        e.setAttribute("stroke", e.dataset.edgeColor);
      }
    });
    const allNodes = this.nodesLayer.querySelectorAll(".graph-node");
    allNodes.forEach((n) => n.classList.remove("selected"));

    // Highlight selected edge
    const edgeElem = document.getElementById(`edge-${relId}`);
    if (edgeElem) {
      edgeElem.classList.add("selected");
      edgeElem.setAttribute("marker-end", "url(#arrowhead-selected)");
      edgeElem.setAttribute("stroke", "#2563eb");
    }

    const relObj = this.relations.find((r) => r.id === relId);
    if (relObj) {
      this.onSelectRelation(relObj);
    }
  }

  selectNode(nodeName) {
    this.selectedNodeName = nodeName;
    this.selectedRelationId = null;

    const allNodes = this.nodesLayer.querySelectorAll(".graph-node");
    allNodes.forEach((n) => {
      if (n.dataset.nodeName === nodeName) {
        n.classList.add("selected");
      } else {
        n.classList.remove("selected");
      }
    });

    const allEdges = this.edgesLayer.querySelectorAll(".graph-edge");
    allEdges.forEach((e) => {
      e.classList.remove("selected");
      const defaultMarker = e.dataset.defaultMarker || "arrowhead-positive";
      e.setAttribute("marker-end", `url(#${defaultMarker})`);
      if (e.dataset.edgeColor) {
        e.setAttribute("stroke", e.dataset.edgeColor);
      }
    });

    const nodeObj = this.nodeMap.get(nodeName);
    if (nodeObj) {
      this.onSelectNode(nodeObj);
    }
  }

  getSentenceColor(sId) {
    const idx = parseInt((sId || "").replace(/\D/g, "")) || 1;
    const palette = ["#2563eb", "#d97706", "#059669", "#c026d3", "#e11d48", "#16a34a", "#7c3aed", "#ca8a04"];
    return palette[(idx - 1) % palette.length];
  }

  tightenEdge(relId) {
    const cur = this.edgeTensions.get(relId) || 1;
    const next = Math.min(5, cur + 1);
    this.edgeTensions.set(relId, next);
    this.restartSimulation(0.35);
    return next;
  }

  loosenEdge(relId) {
    this.edgeTensions.set(relId, 1);
    this.restartSimulation(0.3);
    return 1;
  }

  getEdgeTension(relId) {
    return this.edgeTensions.get(relId) || 1;
  }

  setPhysicsPreset(preset) {
    this.physicsPreset = preset;
    this.restartSimulation(0.35);
  }

  pause() {
    this.animating = false;
  }

  resume() {
    if (this.nodes && this.nodes.length > 0) {
      this.restartSimulation(0.25);
    }
  }

  setShowNegatedEdges(show) {
    this.showNegatedEdges = !!show;
    this.renderElements();
  }

  highlightSentenceElements(sentenceId) {
    this.clearSentenceHighlights();
    this.nodes.forEach((n) => {
      if ((n.evidence_sentence_ids || []).includes(sentenceId)) {
        if (n.groupElem) n.groupElem.classList.add("sentence-highlighted");
      }
    });
    (this.activeRelations || []).forEach((r) => {
      if ((r.data.evidence_sentence_ids || []).includes(sentenceId)) {
        if (r.pathElem) r.pathElem.classList.add("sentence-highlighted");
      }
    });
  }

  clearSentenceHighlights() {
    if (this.nodesLayer && this.nodesLayer.querySelectorAll) {
      this.nodesLayer.querySelectorAll(".sentence-highlighted").forEach((el) => el.classList.remove("sentence-highlighted"));
    }
    if (this.edgesLayer && this.edgesLayer.querySelectorAll) {
      this.edgesLayer.querySelectorAll(".sentence-highlighted").forEach((el) => el.classList.remove("sentence-highlighted"));
    }
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { CausalGraphRenderer };
}
