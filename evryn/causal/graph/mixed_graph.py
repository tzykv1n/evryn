# meflux --help

"""Mixed Causal Graph and Higher-Order Hypergraph Representation.

Represents causal relationships among multivariate variables:
1. Pairwise Relations:
   - Directed edges: u -> v (Cause-Effect relation)
   - Reverse directed edges: u <- v (Reverse Cause-Effect relation)
   - Bidirected edges: u <-> v (Unobserved Confounder / Latent Common Cause)
   - No edge: u ~ v (No direct relation / Independent)
2. Higher-Order / Hypergraph Relations:
   - Multi-source causal mechanisms: {u1, u2, ...} -> v
   - Latent confounding hyperedges: {u1, u2, ...} <-> v
   - Fully compatible with pairwise relations as special case (|sources|=1, |targets|=1).

Provides graph-level metrics (SHD, directed edge precision/recall, bidirected precision/recall,
macro-F1, balanced accuracy) for FLUX continual causal discovery.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Set, Optional, Any, Iterable, Union
import numpy as np
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support


class RelationType:
    NONE = 0
    FORWARD = 1
    BACKWARD = 2
    BIDIRECTED = 3
    JOINT_CAUSAL = 4

    NAMES = ["NO_RELATION", "FORWARD (->)", "BACKWARD (<-)", "CONFOUNDED (<->)", "JOINT_CAUSAL ({..}->v)"]

    @classmethod
    def to_str(cls, code: int) -> str:
        if 0 <= code < len(cls.NAMES):
            return cls.NAMES[code]
        return f"UNKNOWN({code})"


@dataclass(frozen=True)
class HyperCausalRelation:
    """Represents a higher-order causal hyperedge from a source set to a target set.

    Examples:
    - Pairwise: sources={'A'}, targets={'B'}, relation_type=RelationType.FORWARD (A -> B)
    - Synergistic: sources={'A', 'B'}, targets={'C'}, relation_type=RelationType.JOINT_CAUSAL ({A, B} -> C)
    - Higher-order: sources={'A', 'B', 'C'}, targets={'D'}, relation_type=RelationType.JOINT_CAUSAL
    - Latent confounding: sources={'A', 'B'}, targets={'C'}, relation_type=RelationType.BIDIRECTED
    """
    sources: frozenset = field(default_factory=frozenset)
    targets: frozenset = field(default_factory=frozenset)
    relation_type: Union[int, str] = RelationType.FORWARD
    mechanism: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not isinstance(self.sources, frozenset):
            if isinstance(self.sources, str):
                object.__setattr__(self, "sources", frozenset([self.sources]))
            else:
                object.__setattr__(self, "sources", frozenset(self.sources))
        if not isinstance(self.targets, frozenset):
            if isinstance(self.targets, str):
                object.__setattr__(self, "targets", frozenset([self.targets]))
            else:
                object.__setattr__(self, "targets", frozenset(self.targets))

    @property
    def target(self) -> str:
        """Convenience property returning the single target variable name."""
        if len(self.targets) == 1:
            return next(iter(self.targets))
        return "{" + ", ".join(sorted(self.targets)) + "}"

    @property
    def order(self) -> int:
        return len(self.sources)

    @property
    def is_higher_order(self) -> bool:
        return len(self.sources) > 1

    def __str__(self) -> str:
        src_str = "{" + ", ".join(sorted(self.sources)) + "}" if len(self.sources) > 1 else (next(iter(self.sources)) if self.sources else "∅")
        tgt_str = "{" + ", ".join(sorted(self.targets)) + "}" if len(self.targets) > 1 else (next(iter(self.targets)) if self.targets else "∅")
        rel = self.relation_type
        if rel in (RelationType.FORWARD, "FORWARD"):
            rel_symbol = "->"
        elif rel in (RelationType.BACKWARD, "BACKWARD"):
            rel_symbol = "<-"
        elif rel in (RelationType.BIDIRECTED, "BIDIRECTED"):
            rel_symbol = "<->"
        elif rel in (RelationType.JOINT_CAUSAL, "JOINT_CAUSAL"):
            rel_symbol = "=>"
        else:
            rel_symbol = "?"
        return f"{src_str} {rel_symbol} {tgt_str}"


def CausalRelation(
    sources: Union[Iterable[str], str],
    target: Union[Iterable[str], str],
    relation_type: Union[int, str] = RelationType.FORWARD,
    mechanism: Optional[str] = None,
    meta_info: Optional[Dict[str, Any]] = None,
) -> HyperCausalRelation:
    """Helper factory for constructing both pairwise and higher-order relations."""
    src = frozenset([sources] if isinstance(sources, str) else sources)
    tgt = frozenset([target] if isinstance(target, str) else target)
    return HyperCausalRelation(
        sources=src,
        targets=tgt,
        relation_type=relation_type,
        mechanism=mechanism,
        meta_info=meta_info,
    )


class MixedCausalGraph:
    """Represents a mixed causal graph with directed, bidirected, and higher-order relations."""

    def __init__(self, variable_names: List[str]):
        self.nodes = list(variable_names)
        self.node_to_idx = {name: idx for idx, name in enumerate(self.nodes)}
        self.directed_edges: Set[Tuple[str, str]] = set()
        self.bidirected_edges: Set[frozenset] = set()
        self.hyper_relations: List[HyperCausalRelation] = []

    def add_directed_edge(self, u: str, v: str) -> None:
        """Add directed edge u -> v."""
        if u not in self.node_to_idx or v not in self.node_to_idx:
            raise ValueError(f"Nodes {u} or {v} not in graph nodes.")
        self.directed_edges.add((u, v))
        self.hyper_relations.append(
            HyperCausalRelation(
                sources=frozenset([u]),
                targets=frozenset([v]),
                relation_type=RelationType.FORWARD,
            )
        )

    def add_bidirected_edge(self, u: str, v: str) -> None:
        """Add bidirected edge u <-> v (latent confounding)."""
        if u not in self.node_to_idx or v not in self.node_to_idx:
            raise ValueError(f"Nodes {u} or {v} not in graph nodes.")
        self.bidirected_edges.add(frozenset([u, v]))
        self.hyper_relations.append(
            HyperCausalRelation(
                sources=frozenset([u]),
                targets=frozenset([v]),
                relation_type=RelationType.BIDIRECTED,
            )
        )

    def add_hyper_relation(
        self,
        sources: Iterable[str],
        targets: Iterable[str],
        relation_type: int = RelationType.FORWARD,
        mechanism: Optional[str] = None,
        meta_info: Optional[Dict[str, Any]] = None,
    ) -> HyperCausalRelation:
        """Add a general higher-order hyper-relation: sources -> targets."""
        src_set = frozenset(sources)
        tgt_set = frozenset(targets)
        for node in src_set | tgt_set:
            if node not in self.node_to_idx:
                raise ValueError(f"Node {node} not in graph nodes.")

        rel = HyperCausalRelation(
            sources=src_set,
            targets=tgt_set,
            relation_type=relation_type,
            mechanism=mechanism,
            meta_info=meta_info,
        )
        self.hyper_relations.append(rel)

        if len(src_set) == 1 and len(tgt_set) == 1:
            u, v = next(iter(src_set)), next(iter(tgt_set))
            if relation_type == RelationType.FORWARD:
                self.directed_edges.add((u, v))
            elif relation_type == RelationType.BACKWARD:
                self.directed_edges.add((v, u))
            elif relation_type == RelationType.BIDIRECTED:
                self.bidirected_edges.add(frozenset([u, v]))

        return rel

    def add_hyperedge(
        self,
        sources: Union[Iterable[str], str],
        target: str,
        relation_type: Union[int, str] = RelationType.JOINT_CAUSAL,
        mechanism: Optional[str] = None,
        meta_info: Optional[Dict[str, Any]] = None,
    ) -> HyperCausalRelation:
        """Add a higher-order causal hyperedge {sources} -> target."""
        src_set = frozenset([sources] if isinstance(sources, str) else sources)
        for s in src_set:
            if s not in self.node_to_idx:
                raise ValueError(f"Node {s} not in graph nodes.")
        if target not in self.node_to_idx:
            raise ValueError(f"Node {target} not in graph nodes.")

        rel = HyperCausalRelation(
            sources=src_set,
            targets=frozenset([target]),
            relation_type=relation_type,
            mechanism=mechanism,
            meta_info=meta_info,
        )
        self.hyper_relations.append(rel)
        return rel

    def get_hyperedges(self, order: Optional[int] = None) -> List[HyperCausalRelation]:
        """Query higher-order relations, optionally filtering by order (|sources|)."""
        if order is None:
            return list(self.hyper_relations)
        return [r for r in self.hyper_relations if len(r.sources) == order]

    def pairwise_projection(self) -> "MixedCausalGraph":
        """Compute the pairwise projection of the mixed graph and all hyperedges."""
        proj = MixedCausalGraph(self.nodes)
        for u, v in self.directed_edges:
            proj.add_directed_edge(u, v)
        for pair in self.bidirected_edges:
            u, v = list(pair)
            proj.add_bidirected_edge(u, v)

        for rel in self.hyper_relations:
            if rel.relation_type in (RelationType.FORWARD, RelationType.JOINT_CAUSAL, "FORWARD", "JOINT_CAUSAL"):
                for s in rel.sources:
                    for t in rel.targets:
                        if (s, t) not in proj.directed_edges:
                            proj.add_directed_edge(s, t)
            elif rel.relation_type in (RelationType.BACKWARD, "BACKWARD"):
                for s in rel.sources:
                    for t in rel.targets:
                        if (t, s) not in proj.directed_edges:
                            proj.add_directed_edge(t, s)
            elif rel.relation_type in (RelationType.BIDIRECTED, "BIDIRECTED"):
                for s in rel.sources:
                    for t in rel.targets:
                        if frozenset([s, t]) not in proj.bidirected_edges:
                            proj.add_bidirected_edge(s, t)

        return proj

    def get_relation(self, u: str, v: str) -> int:
        """Get the pairwise relation type from u to v."""
        if (u, v) in self.directed_edges:
            return RelationType.FORWARD
        if (v, u) in self.directed_edges:
            return RelationType.BACKWARD
        if frozenset([u, v]) in self.bidirected_edges:
            return RelationType.BIDIRECTED
        return RelationType.NONE

    def get_hyper_relations(self, target: Optional[str] = None) -> List[HyperCausalRelation]:
        """Query higher-order relations, optionally filtering by target."""
        if target is None:
            return list(self.hyper_relations)
        return [r for r in self.hyper_relations if target in r.targets]

    @property
    def relation_matrix(self) -> np.ndarray:
        r"""Matrix M \in {0, 1, 2, 3}^{d x d} encoding pairwise relations."""
        d = len(self.nodes)
        M = np.zeros((d, d), dtype=int)
        for i, u in enumerate(self.nodes):
            for j, v in enumerate(self.nodes):
                if i != j:
                    M[i, j] = self.get_relation(u, v)
        return M

    @classmethod
    def from_relation_matrix(cls, matrix: np.ndarray, nodes: List[str]) -> "MixedCausalGraph":
        g = cls(nodes)
        d = len(nodes)
        for i in range(d):
            for j in range(i + 1, d):
                rel = matrix[i, j]
                u, v = nodes[i], nodes[j]
                if rel == RelationType.FORWARD:
                    g.add_directed_edge(u, v)
                elif rel == RelationType.BACKWARD:
                    g.add_directed_edge(v, u)
                elif rel == RelationType.BIDIRECTED:
                    g.add_bidirected_edge(u, v)
        return g

    def summary(self) -> Dict[str, Any]:
        """Summarize count of relation types and higher-order relations."""
        d = len(self.nodes)
        num_pairs = d * (d - 1) // 2
        directed = len(self.directed_edges)
        bidirected = len(self.bidirected_edges)
        no_rel = num_pairs - directed - bidirected
        hyper_count = len(self.hyper_relations)
        higher_order = sum(1 for r in self.hyper_relations if len(r.sources) > 1 or len(r.targets) > 1)
        return {
            "num_variables": d,
            "directed_edges (->)": directed,
            "bidirected_edges (<->)": bidirected,
            "no_relations (none)": no_rel,
            "total_pairs": num_pairs,
            "total_hyper_relations": hyper_count,
            "higher_order_relations": higher_order,
        }


def evaluate_mixed_graph(
    gt_graph: MixedCausalGraph,
    pred_graph: MixedCausalGraph,
    nodes: List[str],
) -> Dict[str, Any]:
    """Compute comprehensive pairwise and graph-level metrics between ground truth and predicted graphs.

    Returns:
    - pairwise accuracy (raw)
    - balanced accuracy
    - macro-F1
    - per-class precision, recall, F1
    - 4x4 confusion matrix
    - Structural Hamming Distance (SHD)
    - directed edge precision, recall, F1
    - bidirected edge precision, recall, F1
    - graph exact match (1.0 or 0.0)
    """
    d = len(nodes)
    true_rels, pred_rels = [], []
    pair_labels = []

    for i in range(d):
        for j in range(i + 1, d):
            u, v = nodes[i], nodes[j]
            t_rel = gt_graph.get_relation(u, v)
            p_rel = pred_graph.get_relation(u, v)
            true_rels.append(t_rel)
            pred_rels.append(p_rel)
            pair_labels.append(f"{u}-{v}")

    true_arr = np.array(true_rels, dtype=int)
    pred_arr = np.array(pred_rels, dtype=int)

    raw_acc = float(np.mean(true_arr == pred_arr))
    cm = confusion_matrix(true_arr, pred_arr, labels=[0, 1, 2, 3])
    prec, rec, f1, sup = precision_recall_fscore_support(
        true_arr, pred_arr, labels=[0, 1, 2, 3], zero_division=0
    )
    present_mask = (sup > 0)
    bal_acc = float(np.mean(rec[present_mask])) if np.any(present_mask) else raw_acc
    macro_f1 = float(f1_score(true_arr, pred_arr, average="macro", zero_division=0))

    shd = 0
    gt_dir = set(gt_graph.directed_edges)
    pr_dir = set(pred_graph.directed_edges)
    gt_bidir = set(gt_graph.bidirected_edges)
    pr_bidir = set(pred_graph.bidirected_edges)

    tp_dir = len(gt_dir & pr_dir)
    fp_dir = len(pr_dir - gt_dir)
    fn_dir = len(gt_dir - pr_dir)
    dir_prec = tp_dir / max(1, tp_dir + fp_dir) if (tp_dir + fp_dir) > 0 else 0.0
    dir_rec = tp_dir / max(1, tp_dir + fn_dir) if (tp_dir + fn_dir) > 0 else 0.0
    dir_f1 = 2 * dir_prec * dir_rec / max(1e-9, dir_prec + dir_rec) if (dir_prec + dir_rec) > 0 else 0.0

    tp_bidir = len(gt_bidir & pr_bidir)
    fp_bidir = len(pr_bidir - gt_bidir)
    fn_bidir = len(gt_bidir - pr_bidir)
    bidir_prec = tp_bidir / max(1, tp_bidir + fp_bidir) if (tp_bidir + fp_bidir) > 0 else 0.0
    bidir_rec = tp_bidir / max(1, tp_bidir + fn_bidir) if (tp_bidir + fn_bidir) > 0 else 0.0
    bidir_f1 = 2 * bidir_prec * bidir_rec / max(1e-9, bidir_prec + bidir_rec) if (bidir_prec + bidir_rec) > 0 else 0.0

    for i in range(d):
        for j in range(i + 1, d):
            u, v = nodes[i], nodes[j]
            t = gt_graph.get_relation(u, v)
            p = pred_graph.get_relation(u, v)
            if t != p:
                shd += 1

    graph_exact_match = 1.0 if shd == 0 else 0.0

    return {
        "accuracy": raw_acc,
        "balanced_accuracy": bal_acc,
        "macro_f1": macro_f1,
        "per_class_precision": prec,
        "per_class_recall": rec,
        "per_class_f1": f1,
        "per_class_support": sup,
        "confusion_matrix": cm,
        "shd": shd,
        "directed_precision": float(dir_prec),
        "directed_recall": float(dir_rec),
        "directed_f1": float(dir_f1),
        "bidirected_precision": float(bidir_prec),
        "bidirected_recall": float(bidir_rec),
        "bidirected_f1": float(bidir_f1),
        "graph_exact_match": float(graph_exact_match),
        "true_relations": true_arr,
        "pred_relations": pred_arr,
    }


def evaluate_hypergraph(
    gt_graph: MixedCausalGraph,
    pred_graph: MixedCausalGraph,
    nodes: List[str],
) -> Dict[str, Any]:
    """Compute comprehensive higher-order and hypergraph evaluation metrics.

    Calculates:
    - Hyperedge Precision, Recall, F1 (across all orders)
    - Order-specific F1:
      - Order 1 F1 (pairwise edges)
      - Order 2 F1 ({A, B} -> C)
      - Order 3 F1 ({A, B, C} -> D)
    - Exact Hypergraph Match (1.0 or 0.0)
    - Pairwise Projection F1
    - Pairwise Projection SHD
    - Pairwise Projection Balanced Accuracy
    """
    def _canon_key(rel: HyperCausalRelation):
        r_type = rel.relation_type
        if r_type in (RelationType.JOINT_CAUSAL, "JOINT_CAUSAL"):
            c_type = RelationType.JOINT_CAUSAL
        elif r_type in (RelationType.FORWARD, "FORWARD"):
            c_type = RelationType.FORWARD
        elif r_type in (RelationType.BACKWARD, "BACKWARD"):
            c_type = RelationType.BACKWARD
        elif r_type in (RelationType.BIDIRECTED, "BIDIRECTED"):
            c_type = RelationType.BIDIRECTED
        else:
            c_type = RelationType.NONE
        return (frozenset(rel.sources), frozenset(rel.targets), c_type)

    gt_keys = set(_canon_key(r) for r in gt_graph.hyper_relations)
    pred_keys = set(_canon_key(r) for r in pred_graph.hyper_relations)

    tp_all = len(gt_keys & pred_keys)
    fp_all = len(pred_keys - gt_keys)
    fn_all = len(gt_keys - pred_keys)
    prec_all = tp_all / max(1, tp_all + fp_all) if (tp_all + fp_all) > 0 else (1.0 if len(gt_keys) == 0 else 0.0)
    rec_all = tp_all / max(1, tp_all + fn_all) if (tp_all + fn_all) > 0 else (1.0 if len(pred_keys) == 0 else 0.0)
    f1_all = 2 * prec_all * rec_all / max(1e-9, prec_all + rec_all) if (prec_all + rec_all) > 0 else 0.0

    order_metrics = {}
    for ord_val in [1, 2, 3]:
        gt_ord = {k for k in gt_keys if len(k[0]) == ord_val}
        pred_ord = {k for k in pred_keys if len(k[0]) == ord_val}

        tp_o = len(gt_ord & pred_ord)
        fp_o = len(pred_ord - gt_ord)
        fn_o = len(gt_ord - pred_ord)
        p_o = tp_o / max(1, tp_o + fp_o) if (tp_o + fp_o) > 0 else (1.0 if len(gt_ord) == 0 else 0.0)
        r_o = tp_o / max(1, tp_o + fn_o) if (tp_o + fn_o) > 0 else (1.0 if len(pred_ord) == 0 else 0.0)
        f1_o = 2 * p_o * r_o / max(1e-9, p_o + r_o) if (p_o + r_o) > 0 else 0.0

        order_metrics[f"order_{ord_val}_precision"] = float(p_o)
        order_metrics[f"order_{ord_val}_recall"] = float(r_o)
        order_metrics[f"order_{ord_val}_f1"] = float(f1_o)
        order_metrics[f"order_{ord_val}_true_count"] = len(gt_ord)
        order_metrics[f"order_{ord_val}_pred_count"] = len(pred_ord)

    exact_match = 1.0 if gt_keys == pred_keys else 0.0

    gt_proj = gt_graph.pairwise_projection()
    pred_proj = pred_graph.pairwise_projection()
    proj_eval = evaluate_mixed_graph(gt_proj, pred_proj, nodes)

    res = {
        "hyperedge_precision": float(prec_all),
        "hyperedge_recall": float(rec_all),
        "hyperedge_f1": float(f1_all),
        "exact_hypergraph_match": float(exact_match),
        "pairwise_projection_f1": float(proj_eval["macro_f1"]),
        "pairwise_projection_shd": int(proj_eval["shd"]),
        "pairwise_projection_accuracy": float(proj_eval["accuracy"]),
        "pairwise_projection_balanced_acc": float(proj_eval["balanced_accuracy"]),
        "order_1_f1": order_metrics["order_1_f1"],
        "order_2_f1": order_metrics["order_2_f1"],
        "order_3_f1": order_metrics["order_3_f1"],
        "total_true_hyperedges": len(gt_keys),
        "total_pred_hyperedges": len(pred_keys),
    }
    res.update(order_metrics)
    return res

