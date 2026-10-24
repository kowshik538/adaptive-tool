import enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import declarative_base, relationship
from pydantic import BaseModel, Field

Base = declarative_base()


class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    RESEARCHER = "Researcher"
    TESTER = "Tester"
    VIEWER = "Viewer"


class AccessStrategy(str, enum.Enum):
    FULL_ACCESS = "Full Access"
    MODERATE_ACCESS = "Moderate Access"
    LEAST_PRIVILEGE = "Least-Privilege"


class ModelScale(str, enum.Enum):
    SMALL_3B = "Small Model (3B)"
    LARGE_70B = "Large Model (70B)"
    CUSTOM_OLLAMA = "Custom / Ollama Local"


class PolicyDecision(str, enum.Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


class ToolSensitivity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class BenchmarkCategory(str, enum.Enum):
    INFORMATION_RETRIEVAL = "Information Retrieval"
    FILE_READING = "File Reading & Summarization"
    DATA_PROCESSING = "Data Processing & Calculation"
    MULTI_TOOL = "Multi-Tool Workflows"
    PERMISSION_LEVELS = "Role & Permission Verification"
    ADVERSARIAL = "Controlled Adversarial Tests"


# ------------------ SQLAlchemy ORM Models ------------------

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class ToolModel(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    parameters_schema = Column(JSON, nullable=False)
    permitted_operations = Column(JSON, nullable=False)  # List of permitted actions
    required_role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    sensitivity = Column(SQLEnum(ToolSensitivity), default=ToolSensitivity.LOW, nullable=False)
    risk_score = Column(Integer, default=1, nullable=False)  # 1 to 10
    is_enabled = Column(Boolean, default=True)
    requires_approval_by_default = Column(Boolean, default=False)


class SecurityPolicyModel(Base):
    __tablename__ = "security_policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    max_risk_threshold = Column(Integer, default=7)  # Block risk >= 7 unless explicit role
    enforce_relevance_check = Column(Boolean, default=True)
    block_destructive_ops_for_non_admin = Column(Boolean, default=True)
    block_exfiltration_tools = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TaskExecutionModel(Base):
    __tablename__ = "task_executions"

    id = Column(String(50), primary_key=True, index=True)
    task_prompt = Column(Text, nullable=False)
    access_strategy = Column(SQLEnum(AccessStrategy), nullable=False)
    model_scale = Column(SQLEnum(ModelScale), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_role = Column(SQLEnum(UserRole), nullable=False)
    benchmark_id = Column(String(50), nullable=True)
    
    # Scoping outputs
    candidate_tools = Column(JSON, default=list)
    scoped_allow_list = Column(JSON, default=list)
    blocked_tools = Column(JSON, default=list)
    
    # Agent execution outcome
    agent_final_response = Column(Text, nullable=True)
    status = Column(String(30), default="COMPLETED")  # COMPLETED, FAILED, BLOCKED, PENDING_APPROVAL
    is_adversarial_attempt = Column(Boolean, default=False)
    attack_succeeded = Column(Boolean, default=False)
    task_succeeded = Column(Boolean, default=True)
    
    # Metrics
    tool_selection_accuracy = Column(Float, default=1.0)
    unnecessary_tool_calls = Column(Integer, default=0)
    security_exposure_score = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    audit_logs = relationship("AuditLogModel", back_populates="task_execution", cascade="all, delete-orphan")


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), ForeignKey("task_executions.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    tool_name = Column(String(50), nullable=False)
    sanitized_arguments = Column(JSON, nullable=True)
    policy_decision = Column(SQLEnum(PolicyDecision), nullable=False)
    reason_code = Column(String(50), nullable=False)
    reason_description = Column(Text, nullable=False)
    was_executed = Column(Boolean, default=False)
    execution_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Float, default=0.0)
    user_role = Column(String(30), nullable=False)
    access_strategy = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)

    task_execution = relationship("TaskExecutionModel", back_populates="audit_logs")


class BenchmarkTaskModel(Base):
    __tablename__ = "benchmark_tasks"

    id = Column(String(50), primary_key=True)
    title = Column(String(100), nullable=False)
    category = Column(SQLEnum(BenchmarkCategory), nullable=False)
    task_prompt = Column(Text, nullable=False)
    expected_tools = Column(JSON, default=list)  # Ground-truth required tools
    forbidden_tools = Column(JSON, default=list)  # Ground-truth unauthorized tools
    is_adversarial = Column(Boolean, default=False)
    adversarial_payload_type = Column(String(50), nullable=True)
    required_user_role = Column(SQLEnum(UserRole), default=UserRole.VIEWER)
    evaluation_criteria = Column(Text, nullable=False)


# ------------------ Pydantic DTO Schemas ------------------

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole = UserRole.RESEARCHER


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ToolDefinition(BaseModel):
    name: str
    display_name: str
    description: str
    category: str
    parameters_schema: Dict[str, Any]
    permitted_operations: List[str]
    required_role: UserRole
    sensitivity: ToolSensitivity
    risk_score: int
    is_enabled: bool = True
    requires_approval_by_default: bool = False

    class Config:
        from_attributes = True


class TaskSubmission(BaseModel):
    task_prompt: str
    access_strategy: AccessStrategy = AccessStrategy.LEAST_PRIVILEGE
    model_scale: ModelScale = ModelScale.LARGE_70B
    benchmark_id: Optional[str] = None
    override_role: Optional[UserRole] = None  # To test role impersonation in playground


class TaskAnalysisResult(BaseModel):
    task_prompt: str
    detected_intent: str
    required_capabilities: List[str]
    candidate_tools: List[str]
    risk_flags: List[str]
    adversarial_detected: bool
    confidence_score: float


class TaskExecutionResult(BaseModel):
    task_id: str
    task_prompt: str
    access_strategy: AccessStrategy
    model_scale: ModelScale
    user_role: UserRole
    status: str
    agent_final_response: str
    candidate_tools: List[str]
    scoped_allow_list: List[str]
    blocked_tools: List[str]
    tool_calls_attempted: int
    tool_calls_allowed: int
    tool_calls_denied: int
    tool_selection_accuracy: float
    unnecessary_tool_calls: int
    security_exposure_score: float
    attack_succeeded: bool
    task_succeeded: bool
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float
    audit_events: List[Dict[str, Any]]
    approval_required_for: Optional[str] = None


class ExperimentRequest(BaseModel):
    benchmark_ids: Optional[List[str]] = None
    strategies: List[AccessStrategy] = [
        AccessStrategy.FULL_ACCESS,
        AccessStrategy.MODERATE_ACCESS,
        AccessStrategy.LEAST_PRIVILEGE
    ]
    models: List[ModelScale] = [
        ModelScale.SMALL_3B,
        ModelScale.LARGE_70B
    ]
    repetitions: int = 1


class ApprovalAction(BaseModel):
    task_id: str
    tool_name: str
    approved: bool
    decision_reason: Optional[str] = "Admin manual override"
