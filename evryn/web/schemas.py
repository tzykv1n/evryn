from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ExtractionRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw text for causal extraction")
    session_id: Optional[str] = Field(None, description="Optional existing session ID to extend")
    system_mode: Optional[str] = Field("nlp_baseline", description="Extraction backend: 'nlp_baseline' (System A), 'llm_only' (System B), or 'hybrid' (System C)")
    model_name: Optional[str] = Field(None, description="Optional LLM model identifier")


class ContinuationRequest(BaseModel):
    text: Optional[str] = Field(None, description="Additional text to extend existing session")


class LayoutUpdateRequest(BaseModel):
    positions: Dict[str, Dict[str, float]] = Field(..., description="Mapping of node names to {x, y} coordinates")


class BulkDeleteRequest(BaseModel):
    session_ids: List[str] = Field(..., description="List of session IDs to delete in bulk")


class SentenceSpanModel(BaseModel):
    id: str
    text: str
    char_start: int = 0
    char_end: int = 0
    color_fill: str = "#eff6ff"
    color_border: str = "#bfdbfe"
    sentence_index: Optional[int] = None
    color_tint: Optional[str] = None
    border_color: Optional[str] = None


class EvidenceModel(BaseModel):
    id: str
    relation_id: str
    session_id: Optional[str] = None
    doc_id: Optional[str] = None
    filename: Optional[str] = "User Input"
    page_number: int = 1
    section_title: Optional[str] = "Evidence"
    sentence_text: str
    quote: str
    char_start: int = 0
    char_end: int = 0
    evidence_status: str = "MEASURED_FACT"
    created_at: Optional[str] = None


class RelationModel(BaseModel):
    id: str
    session_id: Optional[str] = None
    doc_id: Optional[str] = None
    cause_name: str
    effect_name: str
    relation_type: str = "UPREGULATES"
    direction: str = "FORWARD"
    source_state: Optional[str] = None
    source_delta: Optional[float] = None
    target_state: Optional[str] = None
    target_delta: Optional[float] = None
    assertion_status: str = "affirmed"
    is_negated: bool = False
    is_suppressed: bool = False
    effect_polarity: str = "positive"
    directional_trend: Optional[str] = None
    uncertainty_score: float = 0.05
    confidence: float = 0.90
    is_transitive: bool = False
    status: str = "MEASURED_FACT"
    has_contradiction: bool = False
    edge_color: str = "#0f172a"
    edge_style: str = "solid"
    tension_level: int = 1
    evidence_sentence_ids: List[str] = []
    evidence: List[EvidenceModel] = []
    extraction_method: Optional[str] = "nlp_baseline"
    validation_status: Optional[str] = "ACCEPTED"
    rejection_reasons: List[str] = []
    created_at: Optional[str] = None


class NodeModel(BaseModel):
    id: str
    session_id: Optional[str] = None
    canonical_name: str
    display_name: str
    category: str = "Unclassified"
    category_confidence: float = 0.85
    category_rationale: Optional[str] = None
    user_override_category: Optional[str] = None
    color_fill: Optional[str] = None
    color_stroke: Optional[str] = None
    state: Optional[str] = None
    state_delta: Optional[float] = None
    x: Optional[float] = None
    y: Optional[float] = None
    fixed: bool = False
    in_degree: int = 0
    out_degree: int = 0
    evidence_sentence_ids: List[str] = []
    created_at: Optional[str] = None


class DocumentModel(BaseModel):
    id: str
    session_id: str
    filename: str
    file_type: str
    file_size: int
    page_count: int = 1
    status: str = "completed"
    error_msg: Optional[str] = None
    created_at: str


class SessionSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    status: str = "active"
    node_count: int = 0
    relation_count: int = 0
    doc_count: int = 0


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    status: str = "active"
    primary_prompt: str = ""
    sentences: List[SentenceSpanModel] = []
    inputs: List[Dict[str, Any]] = []
    documents: List[DocumentModel] = []
    nodes: List[NodeModel] = []
    relations: List[RelationModel] = []
    physics_preset: str = "rubber_band"
    tension_settings: Dict[str, int] = {}


class RegenerateRequest(BaseModel):
    text: Optional[str] = Field(None, description="Complete authoritative primary prompt")
    primary_prompt: Optional[str] = Field(None, description="Alias for text")

    def get_text(self) -> str:
        return (self.text or self.primary_prompt or "").strip()


class ContinualRequest(BaseModel):
    incremental_text: str = Field(..., min_length=1, description="Incremental evidence text to append to primary prompt")


class PhysicsUpdateRequest(BaseModel):
    preset: Optional[str] = Field(None, description="Physics mode: string, rubber_band, inelastic, or rigid")
    tensions: Optional[Dict[str, int]] = Field(None, description="Relation ID to tension level (1-5)")


class CategoryOverrideRequest(BaseModel):
    category: str = Field(..., min_length=1, description="New user-specified category")


class DocumentCardResult(BaseModel):
    doc_id: str
    filename: str
    file_type: str
    file_size: int
    page_count: int
    status: str
    error_msg: Optional[str] = None
    nodes: List[NodeModel] = []
    relations: List[RelationModel] = []
    relation_count: int = 0


class BatchUploadResponse(BaseModel):
    session_id: str
    documents: List[DocumentCardResult] = []
    combined_graph: SessionResponse
    warnings: List[str] = []


class ClearSessionsRequest(BaseModel):
    confirm: bool = Field(False, description="Must be true to confirm clearing all sessions")
    backup: bool = Field(True, description="Whether to create a full backup before clearing")

