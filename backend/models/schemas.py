"""Pydantic models = the wire contract. Mirrors CONTRACTS.md. snake_case everywhere."""
from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

NETWORKS = ["visual", "auditory", "language", "motion", "default_mode"]
METRICS = ["peak", "sustained", "retention", "overall"]
SAMPLE_RATE_HZ = 1
DB_NAME = "reeled_in"
API_BASE = "/api"

class TestType(str, Enum):
    upload = "upload"
    voice = "voice"

class TestStatus(str, Enum):
    pending = "pending"
    scoring = "scoring"
    complete = "complete"
    failed = "failed"

class Metrics(BaseModel):
    peak: float
    sustained: float
    retention: float
    overall: float

class RegionTick(BaseModel):
    t: int
    top_network: str
    top_region: str
    activation: float

class ScoreObject(BaseModel):
    variant_id: str
    networks: dict[str, list[float]]            # keys = NETWORKS
    engagement: list[float]                     # composite curve
    metrics: Metrics
    brain_frames: list[str] = Field(default_factory=list)      # media_keys, one/sec
    region_timeline: list[RegionTick] = Field(default_factory=list)
    duration_sec: float
    sample_rate_hz: int = SAMPLE_RATE_HZ

class Variant(BaseModel):
    id: str                    # var_...  (Mongo _id)
    test_id: str
    label: str
    media_key: str
    params: dict = Field(default_factory=dict)
    created_at: str

class Test(BaseModel):
    id: str                    # test_...
    user_id: str
    type: TestType
    objective: str = "retention"
    status: TestStatus = TestStatus.pending
    variant_ids: list[str] = Field(default_factory=list)
    winner_variant_id: Optional[str] = None
    created_at: str
    updated_at: str

class User(BaseModel):
    id: str                    # usr_...
    email: str
    display_name: str
    created_at: str

class TestDetail(BaseModel):
    test: Test
    variants: list[Variant]
    scores: list[ScoreObject]

class WinnerRef(BaseModel):
    variant_id: str
    label: str

class TestSummary(BaseModel):
    """Lightweight per-test shape for /history (CONTRACTS §5) — no N+1 fetches."""
    test_id: str
    type: TestType
    objective: str
    status: TestStatus
    created_at: str
    variant_count: int
    winner: Optional[WinnerRef] = None

class HistoryResp(BaseModel):
    tests: list[TestSummary]

# --- request bodies (CONTRACTS §5) ---

class CreateTestReq(BaseModel):
    type: TestType
    objective: str = "retention"

class VoiceSpec(BaseModel):
    """One requested voice variant (CONTRACTS §5). `script` required; rest optional."""
    script: str = Field(min_length=1)
    label: Optional[str] = None
    voice_id: Optional[str] = None
    voice_settings: dict = Field(default_factory=dict)  # speed [0.7,1.2], stability/style [0,1]

class VoiceVariantsReq(BaseModel):
    base_media_key: str
    variants: list[VoiceSpec] = Field(min_length=1)

class SuggestReq(BaseModel):
    base_media_key: str
    context: str = ""
