# EVRYN Multi-Page Causal Discovery: Methodology and Mathematical Formulation

### 1. Document Modeling and Coordinate Representation

Let a multi-page document $D$ be defined as an ordered sequence of physical pages $P = (p_1, p_2, \dots, p_K)$ where $K$ denotes total page count. Each page $p_k$ spans a continuous character interval $[c_{start}^{(k)}, c_{end}^{(k)}]$ within the continuous full text $T \in \Sigma^*$.

A document is partitioned hierarchically:
$$D = (S, \Phi, \Psi)$$
where:
- $S = (s_1, s_2, \dots, s_M)$ is the set of recognized sections with semantic type $\tau(s) \in \{\text{TITLE}, \text{ABSTRACT}, \text{INTRO}, \text{METHODS}, \text{RESULTS}, \text{DISCUSSION}, \text{CONCLUSION}, \text{REFS}\}$.
- $\Phi = (\phi_1, \dots, \phi_P)$ represents paragraphs.
- $\Psi = (\psi_1, \dots, \psi_N)$ represents sentences.

Each sentence $\psi_i$ is mapped to a tuple:
$$\psi_i = (\text{id}_i, \text{page}(\psi_i), \text{section}(\psi_i), [c_{start}^{(i)}, c_{end}^{(i)}], \text{text}_i)$$
such that for any character offset $c \in [c_{start}^{(i)}, c_{end}^{(i)}]$, the physical page number is uniquely resolved by:
$$\text{page}(\psi_i) = k \iff c_{start}^{(k)} \le c_{start}^{(i)} \le c_{end}^{(k)}$$

### 2. Sentence-Level Causal Extraction & Epistemic Status

For each sentence $\psi$, entity mentions $E_\psi = \{e_1, e_2, \dots, e_m\}$ are extracted and mapped to canonical concepts via document-local abbreviation learning:
$$\kappa: e \mapsto e_{\text{canonical}}$$

A candidate pair $(e_u, e_v)$ with intervening text $w_{uv}$ is evaluated against causal operators:
1. **Directionality & Inversion**:
   $$\text{dir}(e_u, e_v) = \begin{cases} \text{FORWARD} & \text{if active voice and } \text{pos}(e_u) < \text{pos}(e_v) \\ \text{BACKWARD} & \text{if passive voice (e.g. 'is induced by')} \end{cases}$$
2. **Negation Flag**:
   $$\text{neg}(\psi) = \mathbb{I}(\exists p \in \mathcal{P}_{\text{neg}} : p \text{ matches } \text{text}_\psi)$$
3. **Epistemic Uncertainty Metric**:
   $$u(\psi) = u_0 + \Delta_{\text{section}}(\tau(\psi)) + \sum_{p \in \mathcal{P}_{\text{hedging}}} \Delta_{\text{hedge}}(p)$$
   where $u_0 = 0.1$, $\Delta_{\text{section}} \in \{0.0, 0.15, 0.20\}$, and $\Delta_{\text{hedge}} = 0.35$.
   Assertions with $\text{neg}(\psi) = 1$ are classified as `REFUTED_NEGATION`. Assertions with $u(\psi) \ge 0.5$ are classified as `HYPOTHESIS_CLAIM`. Assertions with $u(\psi) < 0.5$ and $\text{neg}(\psi) = 0$ are classified as `MEASURED_FACT`.

### 3. Cross-Page Evidence Linking & Transitive Chaining

Let $G_A = (V_A, E_A)$ be the directed assertion multigraph where vertices $V_A$ are canonical entities and directed edges $E_A$ represent unnegated causal assertions.

For any pair $(u, v) \in V_A \times V_A$ with $u \neq v$, EVRYN discovers all simple directed paths $\pi = (u = v_0, v_1, \dots, v_L = v)$ of length $2 \le L \le L_{\max}$ (default $L_{\max} = 4$).

For each path $\pi$:
- **Source page**: $p_{\text{src}} = \text{page}(e(v_0, v_1))$
- **Target page**: $p_{\text{tgt}} = \text{page}(e(v_{L-1}, v_L))$
- **Page distance**: $\Delta p = |p_{\text{src}} - p_{\text{tgt}}|$
- **Path Confidence**:
  $$C(\pi) = \left( \prod_{k=0}^{L-1} \text{conf}(e(v_k, v_{k+1})) \right) \cdot \gamma^{\max(0, \Delta p - 1)}$$
  where $\gamma = 0.96$ is the inter-page spatial decay parameter.

When $p_{\text{src}} \neq p_{\text{tgt}}$ and $\tau(s_{\text{src}}) = \text{RESULTS}$ while $\tau(s_{\text{tgt}}) = \text{DISCUSSION}$, EVRYN classifies the link as `claim_to_evidence_grounding`. In other multi-hop configurations, it is registered as `transitive_chain`.

### 4. Graph Synthesis & Complete Provenance

The unified paper causal graph $G_D = (V, E)$ combines direct sentence edges $E_{\text{direct}}$ and synthesized cross-page links $E_{\text{inferred}}$.

Each edge $e \in E$ maintains a traceable provenance vector:
$$\text{prov}(e) = \left( \{p_k\}, \{\text{sent\_id}\}, \{\text{quote}\}, \text{status}, C(e) \right)$$
ensuring that every edge in the final causal network can be inspected back to its origin page numbers and primary verbatim evidence sentences.
