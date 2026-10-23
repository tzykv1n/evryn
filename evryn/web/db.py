import os
import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


DEFAULT_DB_PATH = os.path.expanduser("~/.evryn/evryn_sessions.db")


class SessionStore:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.environ.get("EVRYN_DB_PATH", DEFAULT_DB_PATH)
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    primary_prompt TEXT NOT NULL DEFAULT '',
                    physics_preset TEXT NOT NULL DEFAULT 'rubber_band',
                    tension_settings TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS session_inputs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    input_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    page_count INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'completed',
                    error_msg TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    canonical_name TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'Unclassified',
                    category_confidence REAL NOT NULL DEFAULT 0.85,
                    category_rationale TEXT,
                    user_override_category TEXT,
                    color_fill TEXT,
                    color_stroke TEXT,
                    state TEXT,
                    state_delta REAL,
                    x REAL,
                    y REAL,
                    fixed INTEGER NOT NULL DEFAULT 0,
                    evidence_sentence_ids TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
                    UNIQUE(session_id, canonical_name)
                );

                CREATE TABLE IF NOT EXISTS relations (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    doc_id TEXT,
                    cause_name TEXT NOT NULL,
                    effect_name TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    direction TEXT NOT NULL DEFAULT 'FORWARD',
                    source_state TEXT,
                    source_delta REAL,
                    target_state TEXT,
                    target_delta REAL,
                    assertion_status TEXT NOT NULL DEFAULT 'affirmed',
                    is_negated INTEGER NOT NULL DEFAULT 0,
                    is_suppressed INTEGER NOT NULL DEFAULT 0,
                    uncertainty_score REAL NOT NULL DEFAULT 0.05,
                    confidence REAL NOT NULL DEFAULT 0.90,
                    is_transitive INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'MEASURED_FACT',
                    has_contradiction INTEGER NOT NULL DEFAULT 0,
                    effect_polarity TEXT NOT NULL DEFAULT 'positive',
                    directional_trend TEXT,
                    edge_color TEXT NOT NULL DEFAULT '#0f172a',
                    edge_style TEXT NOT NULL DEFAULT 'solid',
                    tension_level INTEGER NOT NULL DEFAULT 1,
                    evidence_sentence_ids TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY,
                    relation_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    doc_id TEXT,
                    filename TEXT,
                    page_number INTEGER NOT NULL DEFAULT 1,
                    section_title TEXT,
                    sentence_text TEXT NOT NULL,
                    quote TEXT NOT NULL,
                    char_start INTEGER NOT NULL DEFAULT 0,
                    char_end INTEGER NOT NULL DEFAULT 0,
                    evidence_status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
                    FOREIGN KEY (relation_id) REFERENCES relations (id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_nodes_session ON nodes(session_id);
                CREATE INDEX IF NOT EXISTS idx_relations_session ON relations(session_id);
                CREATE INDEX IF NOT EXISTS idx_evidence_relation ON evidence(relation_id);
                """
            )
            # Schema migrations for existing databases
            sess_cols = {r["name"] for r in conn.execute("PRAGMA table_info(sessions)").fetchall()}
            if "primary_prompt" not in sess_cols:
                conn.execute("ALTER TABLE sessions ADD COLUMN primary_prompt TEXT NOT NULL DEFAULT ''")
            if "physics_preset" not in sess_cols:
                conn.execute("ALTER TABLE sessions ADD COLUMN physics_preset TEXT NOT NULL DEFAULT 'rubber_band'")
            if "tension_settings" not in sess_cols:
                conn.execute("ALTER TABLE sessions ADD COLUMN tension_settings TEXT NOT NULL DEFAULT '{}'")

            node_cols = {r["name"] for r in conn.execute("PRAGMA table_info(nodes)").fetchall()}
            if "category" not in node_cols:
                conn.execute("ALTER TABLE nodes ADD COLUMN category TEXT NOT NULL DEFAULT 'Unclassified'")
            if "category_confidence" not in node_cols:
                conn.execute("ALTER TABLE nodes ADD COLUMN category_confidence REAL NOT NULL DEFAULT 0.85")
            if "category_rationale" not in node_cols:
                conn.execute("ALTER TABLE nodes ADD COLUMN category_rationale TEXT")
            if "user_override_category" not in node_cols:
                conn.execute("ALTER TABLE nodes ADD COLUMN user_override_category TEXT")
            if "color_fill" not in node_cols:
                conn.execute("ALTER TABLE nodes ADD COLUMN color_fill TEXT")
            if "color_stroke" not in node_cols:
                conn.execute("ALTER TABLE nodes ADD COLUMN color_stroke TEXT")
            if "state" not in node_cols:
                conn.execute("ALTER TABLE nodes ADD COLUMN state TEXT")
            if "state_delta" not in node_cols:
                conn.execute("ALTER TABLE nodes ADD COLUMN state_delta REAL")
            else:
                # If state_delta was created with NOT NULL, relax it
                node_info = conn.execute("PRAGMA table_info(nodes)").fetchall()
                sd_info = next((r for r in node_info if r["name"] == "state_delta"), None)
                if sd_info and sd_info["notnull"] == 1:
                    conn.execute("""
                        CREATE TABLE nodes_migration (
                            id TEXT PRIMARY KEY,
                            session_id TEXT NOT NULL,
                            canonical_name TEXT NOT NULL,
                            display_name TEXT NOT NULL,
                            category TEXT NOT NULL DEFAULT 'Unclassified',
                            category_confidence REAL NOT NULL DEFAULT 0.85,
                            category_rationale TEXT,
                            user_override_category TEXT,
                            color_fill TEXT,
                            color_stroke TEXT,
                            state TEXT,
                            state_delta REAL,
                            x REAL,
                            y REAL,
                            fixed INTEGER NOT NULL DEFAULT 0,
                            evidence_sentence_ids TEXT NOT NULL DEFAULT '[]',
                            created_at TEXT NOT NULL,
                            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
                            UNIQUE(session_id, canonical_name)
                        );
                    """)
                    conn.execute("""
                        INSERT INTO nodes_migration (
                            id, session_id, canonical_name, display_name, category, category_confidence,
                            category_rationale, user_override_category, color_fill, color_stroke,
                            state, state_delta, x, y, fixed, evidence_sentence_ids, created_at
                        )
                        SELECT
                            id, session_id, canonical_name, display_name, category, category_confidence,
                            category_rationale, user_override_category, color_fill, color_stroke,
                            state, NULL, x, y, fixed, evidence_sentence_ids, created_at
                        FROM nodes;
                    """)
                    conn.execute("DROP TABLE nodes;")
                    conn.execute("ALTER TABLE nodes_migration RENAME TO nodes;")

            if "evidence_sentence_ids" not in node_cols:
                conn.execute("ALTER TABLE nodes ADD COLUMN evidence_sentence_ids TEXT NOT NULL DEFAULT '[]'")

            rel_cols = {r["name"] for r in conn.execute("PRAGMA table_info(relations)").fetchall()}
            if "source_state" not in rel_cols:
                conn.execute("ALTER TABLE relations ADD COLUMN source_state TEXT")
            if "source_delta" not in rel_cols:
                conn.execute("ALTER TABLE relations ADD COLUMN source_delta REAL")
            if "target_state" not in rel_cols:
                conn.execute("ALTER TABLE relations ADD COLUMN target_state TEXT")
            if "target_delta" not in rel_cols:
                conn.execute("ALTER TABLE relations ADD COLUMN target_delta REAL")

            rel_info = conn.execute("PRAGMA table_info(relations)").fetchall()
            src_delta_info = next((r for r in rel_info if r["name"] == "source_delta"), None)
            if src_delta_info and src_delta_info["notnull"] == 1:
                conn.execute("""
                    CREATE TABLE relations_migration (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        doc_id TEXT,
                        cause_name TEXT NOT NULL,
                        effect_name TEXT NOT NULL,
                        relation_type TEXT NOT NULL,
                        direction TEXT NOT NULL DEFAULT 'FORWARD',
                        source_state TEXT,
                        source_delta REAL,
                        target_state TEXT,
                        target_delta REAL,
                        assertion_status TEXT NOT NULL DEFAULT 'affirmed',
                        is_negated INTEGER NOT NULL DEFAULT 0,
                        is_suppressed INTEGER NOT NULL DEFAULT 0,
                        uncertainty_score REAL NOT NULL DEFAULT 0.05,
                        confidence REAL NOT NULL DEFAULT 0.90,
                        is_transitive INTEGER NOT NULL DEFAULT 0,
                        status TEXT NOT NULL DEFAULT 'MEASURED_FACT',
                        has_contradiction INTEGER NOT NULL DEFAULT 0,
                        effect_polarity TEXT NOT NULL DEFAULT 'positive',
                        directional_trend TEXT,
                        edge_color TEXT NOT NULL DEFAULT '#0f172a',
                        edge_style TEXT NOT NULL DEFAULT 'solid',
                        tension_level INTEGER NOT NULL DEFAULT 1,
                        evidence_sentence_ids TEXT NOT NULL DEFAULT '[]',
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                    );
                """)
                conn.execute("""
                    INSERT INTO relations_migration (
                        id, session_id, doc_id, cause_name, effect_name, relation_type, direction,
                        source_state, source_delta, target_state, target_delta, assertion_status,
                        is_negated, is_suppressed, uncertainty_score, confidence, is_transitive,
                        status, has_contradiction, effect_polarity, directional_trend, edge_color,
                        edge_style, tension_level, evidence_sentence_ids, created_at
                    )
                    SELECT
                        id, session_id, doc_id, cause_name, effect_name, relation_type, direction,
                        source_state, NULL, target_state, NULL, assertion_status,
                        is_negated, is_suppressed, uncertainty_score, confidence, is_transitive,
                        status, has_contradiction, effect_polarity, directional_trend, edge_color,
                        edge_style, tension_level, evidence_sentence_ids, created_at
                    FROM relations;
                """)
                conn.execute("DROP TABLE relations;")
                conn.execute("ALTER TABLE relations_migration RENAME TO relations;")
            if "assertion_status" not in rel_cols:
                conn.execute("ALTER TABLE relations ADD COLUMN assertion_status TEXT NOT NULL DEFAULT 'affirmed'")
            if "is_suppressed" not in rel_cols:
                conn.execute("ALTER TABLE relations ADD COLUMN is_suppressed INTEGER NOT NULL DEFAULT 0")
            if "effect_polarity" not in rel_cols:
                conn.execute("ALTER TABLE relations ADD COLUMN effect_polarity TEXT NOT NULL DEFAULT 'positive'")
            if "directional_trend" not in rel_cols:
                conn.execute("ALTER TABLE relations ADD COLUMN directional_trend TEXT")
            if "edge_color" not in rel_cols:
                conn.execute("ALTER TABLE relations ADD COLUMN edge_color TEXT NOT NULL DEFAULT '#0f172a'")
            if "edge_style" not in rel_cols:
                conn.execute("ALTER TABLE relations ADD COLUMN edge_style TEXT NOT NULL DEFAULT 'solid'")
            if "tension_level" not in rel_cols:
                conn.execute("ALTER TABLE relations ADD COLUMN tension_level INTEGER NOT NULL DEFAULT 1")
            if "evidence_sentence_ids" not in rel_cols:
                conn.execute("ALTER TABLE relations ADD COLUMN evidence_sentence_ids TEXT NOT NULL DEFAULT '[]'")

    def create_session(self, title: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        s_id = session_id or f"ses_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        s_title = title.strip() if title and title.strip() else f"Session {now[:10]}"
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO sessions (id, title, created_at, updated_at, status) VALUES (?, ?, ?, ?, 'active')",
                (s_id, s_title, now, now),
            )
        return {"id": s_id, "title": s_title, "created_at": now, "updated_at": now, "status": "active"}

    def list_sessions(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                SELECT s.id, s.title, s.created_at, s.updated_at, s.status,
                       COUNT(DISTINCT n.id) as node_count,
                       COUNT(DISTINCT r.id) as relation_count,
                       COUNT(DISTINCT d.id) as doc_count
                FROM sessions s
                LEFT JOIN nodes n ON s.id = n.session_id
                LEFT JOIN relations r ON s.id = r.session_id
                LEFT JOIN documents d ON s.id = d.session_id
                GROUP BY s.id
                ORDER BY s.updated_at DESC
                """
            )
            return [dict(row) for row in cur.fetchall()]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            s_cur = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            session_row = s_cur.fetchone()
            if not session_row:
                return None
            session = dict(session_row)
            session["primary_prompt"] = session.get("primary_prompt") or ""
            session["physics_preset"] = session.get("physics_preset") or "rubber_band"
            try:
                session["tension_settings"] = json.loads(session.get("tension_settings") or "{}")
            except Exception:
                session["tension_settings"] = {}

            # Inputs
            inp_cur = conn.execute("SELECT * FROM session_inputs WHERE session_id = ? ORDER BY id ASC", (session_id,))
            session["inputs"] = [dict(r) for r in inp_cur.fetchall()]

            # Documents
            doc_cur = conn.execute("SELECT * FROM documents WHERE session_id = ? ORDER BY created_at ASC", (session_id,))
            session["documents"] = [dict(r) for r in doc_cur.fetchall()]

            # Nodes
            node_cur = conn.execute("SELECT * FROM nodes WHERE session_id = ? ORDER BY canonical_name ASC", (session_id,))
            nodes = []
            for r in node_cur.fetchall():
                n_dict = dict(r)
                if n_dict.get("user_override_category"):
                    n_dict["category"] = n_dict["user_override_category"]
                try:
                    n_dict["evidence_sentence_ids"] = json.loads(n_dict.get("evidence_sentence_ids") or "[]")
                except Exception:
                    n_dict["evidence_sentence_ids"] = []
                nodes.append(n_dict)

            # Relations with evidence
            rel_cur = conn.execute("SELECT * FROM relations WHERE session_id = ? ORDER BY created_at ASC", (session_id,))
            relations = []
            for r in rel_cur.fetchall():
                rel_dict = dict(r)
                rel_dict["is_negated"] = bool(rel_dict.get("is_negated", 0))
                rel_dict["is_suppressed"] = bool(rel_dict.get("is_suppressed", 0))
                rel_dict["is_transitive"] = bool(rel_dict.get("is_transitive", 0))
                rel_dict["has_contradiction"] = bool(rel_dict.get("has_contradiction", 0))
                try:
                    rel_dict["evidence_sentence_ids"] = json.loads(rel_dict.get("evidence_sentence_ids") or "[]")
                except Exception:
                    rel_dict["evidence_sentence_ids"] = []
                ev_cur = conn.execute(
                    "SELECT * FROM evidence WHERE relation_id = ? ORDER BY page_number ASC", (rel_dict["id"],)
                )
                rel_dict["evidence"] = [dict(ev) for ev in ev_cur.fetchall()]
                relations.append(rel_dict)

            # Node degree calculation
            in_degree = {}
            out_degree = {}
            for rel in relations:
                c = rel["cause_name"]
                e = rel["effect_name"]
                out_degree[c] = out_degree.get(c, 0) + 1
                in_degree[e] = in_degree.get(e, 0) + 1

            for node in nodes:
                c_name = node["canonical_name"]
                node["in_degree"] = in_degree.get(c_name, 0)
                node["out_degree"] = out_degree.get(c_name, 0)

            session["nodes"] = nodes
            session["relations"] = relations
            return session

    def delete_session(self, session_id: str) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            return cur.rowcount > 0

    def override_node_category(self, session_id: str, canonical_name: str, new_category: str) -> bool:
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                UPDATE nodes
                SET user_override_category = ?, category = ?
                WHERE session_id = ? AND (canonical_name = ? OR display_name = ?)
                """,
                (new_category, new_category, session_id, canonical_name, canonical_name),
            )
            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
            return cur.rowcount > 0

    def update_physics_settings(
        self, session_id: str, preset: Optional[str] = None, tensions: Optional[Dict[str, int]] = None
    ) -> None:
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            if preset:
                conn.execute("UPDATE sessions SET physics_preset = ? WHERE id = ?", (preset, session_id))
            if tensions is not None:
                cur = conn.execute("SELECT tension_settings FROM sessions WHERE id = ?", (session_id,))
                row = cur.fetchone()
                existing = {}
                if row and row["tension_settings"]:
                    try:
                        existing = json.loads(row["tension_settings"])
                    except Exception:
                        existing = {}
                existing.update(tensions)
                conn.execute(
                    "UPDATE sessions SET tension_settings = ? WHERE id = ?",
                    (json.dumps(existing), session_id),
                )
                for r_id, t_lvl in tensions.items():
                    conn.execute("UPDATE relations SET tension_level = ? WHERE id = ?", (t_lvl, r_id))
            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))

    def add_input(self, session_id: str, input_type: str, content: str) -> None:
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO session_inputs (session_id, input_type, content, created_at) VALUES (?, ?, ?, ?)",
                (session_id, input_type, content, now),
            )
            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))

    def add_document(
        self,
        session_id: str,
        doc_id: str,
        filename: str,
        file_type: str,
        file_size: int,
        page_count: int = 1,
        status: str = "completed",
        error_msg: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO documents (id, session_id, filename, file_type, file_size, page_count, status, error_msg, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (doc_id, session_id, filename, file_type, file_size, page_count, status, error_msg, now),
            )
            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
        return {
            "id": doc_id,
            "session_id": session_id,
            "filename": filename,
            "file_type": file_type,
            "file_size": file_size,
            "page_count": page_count,
            "status": status,
            "error_msg": error_msg,
            "created_at": now,
        }

    def update_node_positions(self, session_id: str, positions: Dict[str, Dict[str, float]]) -> None:
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            for node_name, coords in positions.items():
                conn.execute(
                    """
                    UPDATE nodes
                    SET x = ?, y = ?, fixed = 1
                    WHERE session_id = ? AND (canonical_name = ? OR display_name = ?)
                    """,
                    (coords.get("x"), coords.get("y"), session_id, node_name, node_name),
                )
            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))

    def update_session_title(self, session_id: str, title: str) -> None:
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            conn.execute("UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?", (title, now, session_id))

    def accumulate_evidence(
        self,
        session_id: str,
        new_nodes: List[Dict[str, Any]],
        new_relations: List[Dict[str, Any]],
        new_evidence: List[Dict[str, Any]],
        title_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            # 1. Update session title if default
            if title_hint:
                conn.execute(
                    "UPDATE sessions SET title = ? WHERE id = ? AND title LIKE 'Session %'",
                    (title_hint[:60], session_id),
                )

            # 2. Add or update nodes (preserving existing layout positions x, y)
            for node in new_nodes:
                canon = node["canonical_name"].strip()
                disp = node.get("display_name", canon).strip()
                node_id = node.get("id") or f"node_{uuid.uuid4().hex[:10]}"
                ev_sent_ids = json.dumps(node.get("evidence_sentence_ids") or [])
                conn.execute(
                    """
                    INSERT INTO nodes (
                        id, session_id, canonical_name, display_name, category,
                        category_confidence, category_rationale, user_override_category,
                        color_fill, color_stroke, state, state_delta, x, y, fixed,
                        evidence_sentence_ids, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                    ON CONFLICT(session_id, canonical_name) DO UPDATE SET
                    display_name = excluded.display_name,
                    category = coalesce(nodes.user_override_category, excluded.category),
                    category_confidence = excluded.category_confidence,
                    category_rationale = coalesce(excluded.category_rationale, nodes.category_rationale),
                    color_fill = coalesce(excluded.color_fill, nodes.color_fill),
                    color_stroke = coalesce(excluded.color_stroke, nodes.color_stroke),
                    state = coalesce(excluded.state, nodes.state),
                    state_delta = excluded.state_delta,
                    evidence_sentence_ids = excluded.evidence_sentence_ids
                    """,
                    (
                        node_id,
                        session_id,
                        canon,
                        disp,
                        node.get("category", "Unclassified"),
                        node.get("category_confidence", 0.85),
                        node.get("category_rationale", ""),
                        node.get("user_override_category"),
                        node.get("color_fill"),
                        node.get("color_stroke"),
                        node.get("state"),
                        node.get("state_delta"),
                        node.get("x"),
                        node.get("y"),
                        ev_sent_ids,
                        now,
                    ),
                )

            # 3. Process relations and handle contradictions
            # Check existing relations for this session
            cur = conn.execute(
                "SELECT id, cause_name, effect_name, relation_type, is_negated, has_contradiction FROM relations WHERE session_id = ?",
                (session_id,),
            )
            existing_rels = {(r["cause_name"], r["effect_name"]): dict(r) for r in cur.fetchall()}

            rel_id_mapping = {}

            for rel in new_relations:
                cause = rel["cause_name"].strip()
                effect = rel["effect_name"].strip()
                rel_type = rel.get("relation_type", "UPREGULATES")
                is_neg = 1 if rel.get("is_negated") else 0
                key = (cause, effect)
                r_sent_ids = json.dumps(rel.get("evidence_sentence_ids") or [])

                if key in existing_rels:
                    existing = existing_rels[key]
                    existing_id = existing["id"]
                    rel_id_mapping[rel.get("id", "")] = existing_id

                    # Check for contradiction (e.g. existing was positive, new is negated, or vice-versa)
                    if existing["is_negated"] != is_neg or (existing["relation_type"] != rel_type and not is_neg):
                        conn.execute(
                            "UPDATE relations SET has_contradiction = 1, confidence = 0.50 WHERE id = ?",
                            (existing_id,),
                        )
                else:
                    rel_id = rel.get("id") or f"rel_{uuid.uuid4().hex[:10]}"
                    rel_id_mapping[rel.get("id", "")] = rel_id
                    conn.execute(
                        """
                        INSERT INTO relations (
                            id, session_id, doc_id, cause_name, effect_name, relation_type,
                            direction, is_negated, is_suppressed, uncertainty_score, confidence,
                            is_transitive, status, has_contradiction, effect_polarity,
                            directional_trend, edge_color, edge_style, tension_level,
                            source_state, source_delta, target_state, target_delta,
                            assertion_status, evidence_sentence_ids, created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            rel_id,
                            session_id,
                            rel.get("doc_id"),
                            cause,
                            effect,
                            rel_type,
                            rel.get("direction", "FORWARD"),
                            is_neg,
                            1 if rel.get("is_suppressed") else 0,
                            rel.get("uncertainty_score", 0.05),
                            rel.get("confidence", 0.90),
                            1 if rel.get("is_transitive") else 0,
                            rel.get("status", "MEASURED_FACT"),
                            rel.get("effect_polarity", "positive"),
                            rel.get("directional_trend"),
                            rel.get("edge_color", "#0f172a"),
                            rel.get("edge_style", "solid"),
                            rel.get("tension_level", 1),
                            rel.get("source_state"),
                            rel.get("source_delta"),
                            rel.get("target_state"),
                            rel.get("target_delta"),
                            rel.get("assertion_status", "affirmed"),
                            r_sent_ids,
                            now,
                        ),
                    )
                    existing_rels[key] = {
                        "id": rel_id,
                        "cause_name": cause,
                        "effect_name": effect,
                        "relation_type": rel_type,
                        "is_negated": is_neg,
                        "has_contradiction": 0,
                    }

            # 4. Insert evidence attached to the appropriate relation
            for ev in new_evidence:
                orig_rel_id = ev.get("relation_id", "")
                mapped_rel_id = rel_id_mapping.get(orig_rel_id, orig_rel_id)
                ev_id = ev.get("id") or f"ev_{uuid.uuid4().hex[:10]}"

                # Check if identical evidence quote already exists to avoid exact duplicate rows
                chk = conn.execute(
                    "SELECT id FROM evidence WHERE relation_id = ? AND sentence_text = ?",
                    (mapped_rel_id, ev.get("sentence_text", "")),
                ).fetchone()
                if not chk:
                    conn.execute(
                        """
                        INSERT INTO evidence (id, relation_id, session_id, doc_id, filename, page_number, section_title, sentence_text, quote, char_start, char_end, evidence_status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            ev_id,
                            mapped_rel_id,
                            session_id,
                            ev.get("doc_id"),
                            ev.get("filename", "User Input"),
                            ev.get("page_number", 1),
                            ev.get("section_title", "Evidence"),
                            ev.get("sentence_text", ""),
                            ev.get("quote", ev.get("sentence_text", "")),
                            ev.get("char_start", 0),
                            ev.get("char_end", 0),
                            ev.get("evidence_status", "MEASURED_FACT"),
                            now,
                        ),
                    )

            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))

        return self.get_session(session_id)

    def replace_session_graph(
        self,
        session_id: str,
        new_nodes: List[Dict[str, Any]],
        new_relations: List[Dict[str, Any]],
        new_evidence: List[Dict[str, Any]],
        primary_prompt: str,
        title_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            # 1. Fetch previous layout and overrides to preserve them across edits
            prev_nodes_cur = conn.execute(
                "SELECT canonical_name, display_name, x, y, fixed, user_override_category FROM nodes WHERE session_id = ?",
                (session_id,),
            )
            prev_nodes = {r["canonical_name"]: dict(r) for r in prev_nodes_cur.fetchall()}

            prev_rels_cur = conn.execute(
                "SELECT cause_name, effect_name, tension_level FROM relations WHERE session_id = ?",
                (session_id,),
            )
            prev_rels = {(r["cause_name"], r["effect_name"]): r["tension_level"] for r in prev_rels_cur.fetchall()}

            # 2. Clear old graph elements for this session (evidence cascades or deleted explicitly)
            conn.execute("DELETE FROM evidence WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM relations WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM nodes WHERE session_id = ?", (session_id,))

            # 3. Update session primary prompt and title
            if title_hint:
                conn.execute(
                    "UPDATE sessions SET title = ?, primary_prompt = ?, updated_at = ? WHERE id = ? AND title LIKE 'Session %'",
                    (title_hint[:60], primary_prompt, now, session_id),
                )
            conn.execute(
                "UPDATE sessions SET primary_prompt = ?, updated_at = ? WHERE id = ?",
                (primary_prompt, now, session_id),
            )

            # 4. Insert new nodes, preserving user positions/overrides if previously existing
            for node in new_nodes:
                canon = node["canonical_name"].strip()
                disp = node.get("display_name", canon).strip()
                node_id = node.get("id") or f"node_{uuid.uuid4().hex[:10]}"
                ev_sent_ids = json.dumps(node.get("evidence_sentence_ids") or [])

                prev = prev_nodes.get(canon)
                x = prev["x"] if (prev and prev.get("x") is not None) else node.get("x")
                y = prev["y"] if (prev and prev.get("y") is not None) else node.get("y")
                fixed = prev["fixed"] if prev else 0
                override = prev["user_override_category"] if (prev and prev.get("user_override_category")) else node.get("user_override_category")
                category = override if override else node.get("category", "Unclassified")

                conn.execute(
                    """
                    INSERT INTO nodes (
                        id, session_id, canonical_name, display_name, category,
                        category_confidence, category_rationale, user_override_category,
                        color_fill, color_stroke, state, state_delta, x, y, fixed,
                        evidence_sentence_ids, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        node_id,
                        session_id,
                        canon,
                        disp,
                        category,
                        node.get("category_confidence", 0.85),
                        node.get("category_rationale", ""),
                        override,
                        node.get("color_fill"),
                        node.get("color_stroke"),
                        node.get("state"),
                        node.get("state_delta"),
                        x,
                        y,
                        fixed,
                        ev_sent_ids,
                        now,
                    ),
                )

            # 5. Insert new relations
            rel_id_mapping = {}
            for rel in new_relations:
                cause = rel["cause_name"].strip()
                effect = rel["effect_name"].strip()
                rel_type = rel.get("relation_type", "UPREGULATES")
                is_neg = 1 if rel.get("is_negated") else 0
                rel_id = rel.get("id") or f"rel_{uuid.uuid4().hex[:10]}"
                rel_id_mapping[rel.get("id", "")] = rel_id
                r_sent_ids = json.dumps(rel.get("evidence_sentence_ids") or [])

                tension = prev_rels.get((cause, effect), rel.get("tension_level", 1))

                conn.execute(
                    """
                    INSERT INTO relations (
                        id, session_id, doc_id, cause_name, effect_name, relation_type,
                        direction, is_negated, is_suppressed, uncertainty_score, confidence,
                        is_transitive, status, has_contradiction, effect_polarity,
                        directional_trend, edge_color, edge_style, tension_level,
                        source_state, source_delta, target_state, target_delta,
                        assertion_status, evidence_sentence_ids, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rel_id,
                        session_id,
                        rel.get("doc_id"),
                        cause,
                        effect,
                        rel_type,
                        rel.get("direction", "FORWARD"),
                        is_neg,
                        1 if rel.get("is_suppressed") else 0,
                        rel.get("uncertainty_score", 0.05),
                        rel.get("confidence", 0.90),
                        1 if rel.get("is_transitive") else 0,
                        rel.get("status", "MEASURED_FACT"),
                        rel.get("effect_polarity", "positive"),
                        rel.get("directional_trend"),
                        rel.get("edge_color", "#0f172a"),
                        rel.get("edge_style", "solid"),
                        tension,
                        rel.get("source_state"),
                        rel.get("source_delta"),
                        rel.get("target_state"),
                        rel.get("target_delta"),
                        rel.get("assertion_status", "affirmed"),
                        r_sent_ids,
                        now,
                    ),
                )

            # 6. Insert new evidence
            for ev in new_evidence:
                orig_rel_id = ev.get("relation_id", "")
                mapped_rel_id = rel_id_mapping.get(orig_rel_id, orig_rel_id)
                ev_id = ev.get("id") or f"ev_{uuid.uuid4().hex[:10]}"
                conn.execute(
                    """
                    INSERT INTO evidence (
                        id, relation_id, session_id, doc_id, filename, page_number,
                        section_title, sentence_text, quote, char_start, char_end,
                        evidence_status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ev_id,
                        mapped_rel_id,
                        session_id,
                        ev.get("doc_id"),
                        ev.get("filename", "Primary Prompt"),
                        ev.get("page_number", 1),
                        ev.get("section_title", "User Specification"),
                        ev.get("sentence_text", ""),
                        ev.get("quote", ev.get("sentence_text", "")),
                        ev.get("char_start", 0),
                        ev.get("char_end", 0),
                        ev.get("evidence_status", "MEASURED_FACT"),
                        now,
                    ),
                )

        return self.get_session(session_id)
