from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

Severity = Literal["Low", "Medium", "High"]

class GPU(BaseModel):
    id: str
    temperature_c: float
    utilization_pct: float
    memory_used_gb: float
    memory_total_gb: float = 24.0
    threshold_c: float
    health: Literal["Normal", "Elevated"]

class TelemetryRecord(BaseModel):
    record_id: str
    timestamp: datetime
    gpu_id: str
    temperature_c: float
    utilization_pct: float
    memory_used_gb: float
    memory_total_gb: float
    error_count: int = Field(ge=0)

class Anomaly(BaseModel):
    id: str
    gpu_id: str
    timestamp: datetime
    observed_value: float
    threshold: float
    severity: Severity
    description: str
    rule: str
    source_record_id: str
    source_record: TelemetryRecord

class LogEntry(BaseModel):
    id: str
    timestamp: datetime
    gpu_id: str
    event_type: str
    severity: Severity
    message: str
    anomaly_id: str | None = None

class Summary(BaseModel):
    gpus: list[GPU]
    anomaly_count: int
    error_count: int
    generated_at: datetime

class Config(BaseModel):
    temperature_thresholds: dict[str, float]
    sustained_readings: int
    severity_rules: dict[str, str]
