import os
import uuid
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, status, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .models import (
    UserModel, ToolModel, SecurityPolicyModel, BenchmarkTaskModel,
    TaskExecutionModel, AuditLogModel, UserRole, AccessStrategy,
    ModelScale, PolicyDecision, UserCreate, UserResponse,
    TokenResponse, ToolDefinition, TaskSubmission, TaskAnalysisResult,
    TaskExecutionResult, ExperimentRequest, ApprovalAction
)
from .database import get_db, init_db
from .auth import (
    hash_password, verify_password, create_access_token,
    get_current_user_required, require_role
)
from .tool_registry import TOOL_REGISTRY, TOOL_HANDLERS
from .task_analyzer import TaskAnalyzer
from .agent_runner import AgentRunner
from .evaluation_engine import EvaluationEngine
from .benchmarks import BENCHMARK_TASKS

app = FastAPI(
    title="Adaptive Least-Privilege Tool Scoping API",
    description="Research framework for dynamic permission enforcement and model-scale evaluation of function-calling AI agents.",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()


# ==========================================
# 1. Authentication & Role Management
# ==========================================

@app.post("/api/auth/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(UserModel).filter(
        (UserModel.username == user_in.username) | (UserModel.email == user_in.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists.")
    user = UserModel(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=user_in.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: Dict[str, str], db: Session = Depends(get_db)):
    username = payload.get("username", "")
    password = payload.get("password", "")
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    token = create_access_token({"sub": user.username, "role": user.role.value, "email": user.email})
    return TokenResponse(
        access_token=token,
        user=UserResponse.from_orm(user)
    )


@app.get("/api/auth/me", response_model=UserResponse)
def get_me(user_claims: dict = Depends(get_current_user_required), db: Session = Depends(get_db)):
    username = user_claims.get("sub")
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


# ==========================================
# 2. Tool Registry & Policies
# ==========================================

@app.get("/api/tools", response_model=List[ToolDefinition])
def list_tools(db: Session = Depends(get_db)):
    db_tools = db.query(ToolModel).all()
    result = []
    for t in db_tools:
        result.append(ToolDefinition(
            name=t.name,
            display_name=t.display_name,
            description=t.description,
            category=t.category,
            parameters_schema=t.parameters_schema,
            permitted_operations=t.permitted_operations,
            required_role=t.required_role,
            sensitivity=t.sensitivity,
            risk_score=t.risk_score,
            is_enabled=t.is_enabled,
            requires_approval_by_default=t.requires_approval_by_default
        ))
    return result


@app.put("/api/tools/{name}", response_model=ToolDefinition)
def update_tool(
    name: str,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_role(UserRole.ADMIN))
):
    tool = db.query(ToolModel).filter(ToolModel.name == name).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found.")

    if "risk_score" in update_data:
        tool.risk_score = int(update_data["risk_score"])
    if "is_enabled" in update_data:
        tool.is_enabled = bool(update_data["is_enabled"])
    if "required_role" in update_data:
        tool.required_role = UserRole(update_data["required_role"])
    if "requires_approval_by_default" in update_data:
        tool.requires_approval_by_default = bool(update_data["requires_approval_by_default"])

    db.commit()
    db.refresh(tool)

    # Sync with memory registry
    if name in TOOL_REGISTRY:
        TOOL_REGISTRY[name].risk_score = tool.risk_score
        TOOL_REGISTRY[name].is_enabled = tool.is_enabled
        TOOL_REGISTRY[name].required_role = tool.required_role
        TOOL_REGISTRY[name].requires_approval_by_default = tool.requires_approval_by_default

    return ToolDefinition.from_orm(tool)


@app.post("/api/tools/{name}/test")
def test_tool_direct(
    name: str,
    payload: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_required)
):
    """Controlled direct invocation for tool testing."""
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        raise HTTPException(status_code=404, detail=f"No execution handler for tool '{name}'")
    args = payload.get("arguments", {}) if payload else {}
    return {
        "tool_name": name,
        "arguments": args,
        "result": handler(args)
    }


# ==========================================
# 3. Task Playground & Dynamic Scoping
# ==========================================

@app.post("/api/tasks/analyze", response_model=TaskAnalysisResult)
def analyze_task(payload: Dict[str, str]):
    prompt = payload.get("task_prompt", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="Task prompt cannot be empty.")
    return TaskAnalyzer.analyze(prompt)


@app.post("/api/tasks/execute", response_model=TaskExecutionResult)
def execute_task(
    submission: TaskSubmission,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user_required)
):
    task_id = f"TASK-{uuid.uuid4().hex[:10]}"
    user_role = submission.override_role or UserRole(user_claims.get("role", UserRole.RESEARCHER.value))
    
    # 1. Analyze Task
    analysis = TaskAnalyzer.analyze(submission.task_prompt)

    # 2. Check if benchmark item
    benchmark = None
    if submission.benchmark_id:
        benchmark = db.query(BenchmarkTaskModel).filter(BenchmarkTaskModel.id == submission.benchmark_id).first()

    expected_tools = benchmark.expected_tools if benchmark else None
    is_adv = benchmark.is_adversarial if benchmark else analysis.adversarial_detected

    # 3. Execute via Agent Runner
    result = AgentRunner.run_task(
        db=db,
        task_id=task_id,
        task_prompt=submission.task_prompt,
        access_strategy=submission.access_strategy,
        model_scale=submission.model_scale,
        user_role=user_role,
        task_analysis=analysis,
        benchmark_expected_tools=expected_tools,
        is_adversarial=is_adv
    )

    # 4. Save Task Execution Record
    record = TaskExecutionModel(
        id=result.task_id,
        task_prompt=result.task_prompt,
        access_strategy=result.access_strategy,
        model_scale=result.model_scale,
        user_role=result.user_role,
        benchmark_id=submission.benchmark_id,
        candidate_tools=result.candidate_tools,
        scoped_allow_list=result.scoped_allow_list,
        blocked_tools=result.blocked_tools,
        agent_final_response=result.agent_final_response,
        status=result.status,
        is_adversarial_attempt=is_adv,
        attack_succeeded=result.attack_succeeded,
        task_succeeded=result.task_succeeded,
        tool_selection_accuracy=result.tool_selection_accuracy,
        unnecessary_tool_calls=result.unnecessary_tool_calls,
        security_exposure_score=result.security_exposure_score,
        latency_ms=result.latency_ms,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        estimated_cost_usd=result.estimated_cost_usd
    )
    db.add(record)
    db.commit()

    return result


@app.post("/api/tasks/approve")
def approve_pending_tool(
    action: ApprovalAction,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_role(UserRole.ADMIN))
):
    task = db.query(TaskExecutionModel).filter(TaskExecutionModel.id == action.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    if action.approved:
        handler = TOOL_HANDLERS.get(action.tool_name)
        exec_res = handler({}) if handler else {"status": "EXECUTED_WITH_ADMIN_APPROVAL"}
        task.status = "COMPLETED"
        task.agent_final_response += f" [Admin manual approval granted for {action.tool_name}]."
        db.commit()
        return {"status": "APPROVED", "result": exec_res}
    else:
        task.status = "DENIED_BY_ADMIN"
        db.commit()
        return {"status": "DENIED", "reason": action.decision_reason}


# ==========================================
# 4. Experiment Lab (Reproducible Evaluations)
# ==========================================

@app.post("/api/experiments/run")
def run_experiment_batch(
    req: ExperimentRequest,
    db: Session = Depends(get_db),
    researcher: dict = Depends(require_role(UserRole.RESEARCHER))
):
    benchmarks_query = db.query(BenchmarkTaskModel)
    if req.benchmark_ids:
        benchmarks_query = benchmarks_query.filter(BenchmarkTaskModel.id.in_(req.benchmark_ids))
    benchmarks = benchmarks_query.all()

    if not benchmarks:
        raise HTTPException(status_code=400, detail="No benchmarks selected or found.")

    runs_created = []

    for b in benchmarks:
        task_analysis = TaskAnalyzer.analyze(b.task_prompt)
        for strat in req.strategies:
            for mod in req.models:
                for rep in range(req.repetitions):
                    task_id = f"EXP-{uuid.uuid4().hex[:8]}"
                    exec_res = AgentRunner.run_task(
                        db=db,
                        task_id=task_id,
                        task_prompt=b.task_prompt,
                        access_strategy=strat,
                        model_scale=mod,
                        user_role=b.required_user_role,
                        task_analysis=task_analysis,
                        benchmark_expected_tools=b.expected_tools,
                        is_adversarial=b.is_adversarial
                    )
                    record = TaskExecutionModel(
                        id=exec_res.task_id,
                        task_prompt=exec_res.task_prompt,
                        access_strategy=exec_res.access_strategy,
                        model_scale=exec_res.model_scale,
                        user_role=exec_res.user_role,
                        benchmark_id=b.id,
                        candidate_tools=exec_res.candidate_tools,
                        scoped_allow_list=exec_res.scoped_allow_list,
                        blocked_tools=exec_res.blocked_tools,
                        agent_final_response=exec_res.agent_final_response,
                        status=exec_res.status,
                        is_adversarial_attempt=b.is_adversarial,
                        attack_succeeded=exec_res.attack_succeeded,
                        task_succeeded=exec_res.task_succeeded,
                        tool_selection_accuracy=exec_res.tool_selection_accuracy,
                        unnecessary_tool_calls=exec_res.unnecessary_tool_calls,
                        security_exposure_score=exec_res.security_exposure_score,
                        latency_ms=exec_res.latency_ms,
                        prompt_tokens=exec_res.prompt_tokens,
                        completion_tokens=exec_res.completion_tokens,
                        estimated_cost_usd=exec_res.estimated_cost_usd
                    )
                    db.add(record)
                    runs_created.append(exec_res.task_id)

    db.commit()
    return {
        "success": True,
        "total_executions": len(runs_created),
        "execution_ids": runs_created[:10],
        "message": f"Successfully evaluated {len(runs_created)} benchmark configurations."
    }


# ==========================================
# 5. Security Testing (Adversarial Suite)
# ==========================================

@app.get("/api/security/scenarios")
def get_security_scenarios(db: Session = Depends(get_db)):
    scenarios = db.query(BenchmarkTaskModel).filter(BenchmarkTaskModel.is_adversarial == True).all()
    return scenarios


@app.post("/api/security/test")
def run_security_scenario(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    tester: dict = Depends(require_role(UserRole.TESTER))
):
    scenario_id = payload.get("scenario_id")
    scenario = db.query(BenchmarkTaskModel).filter(BenchmarkTaskModel.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Adversarial scenario not found.")

    # Run side-by-side comparison across Full Access, Moderate Access, and Least-Privilege
    task_analysis = TaskAnalyzer.analyze(scenario.task_prompt)
    comparative_results = {}

    for strat in [AccessStrategy.FULL_ACCESS, AccessStrategy.MODERATE_ACCESS, AccessStrategy.LEAST_PRIVILEGE]:
        task_id = f"SEC-TEST-{strat.name}-{uuid.uuid4().hex[:6]}"
        res = AgentRunner.run_task(
            db=db,
            task_id=task_id,
            task_prompt=scenario.task_prompt,
            access_strategy=strat,
            model_scale=ModelScale.LARGE_70B,
            user_role=UserRole.VIEWER,
            task_analysis=task_analysis,
            benchmark_expected_tools=scenario.expected_tools,
            is_adversarial=True
        )
        comparative_results[strat.value] = res.dict()

    return {
        "scenario_id": scenario.id,
        "scenario_title": scenario.title,
        "prompt": scenario.task_prompt,
        "comparison": comparative_results
    }


# ==========================================
# 6. Audit Logs & System Inspection
# ==========================================

@app.get("/api/audit/logs")
def get_audit_logs(
    limit: int = 50,
    decision: Optional[str] = None,
    tool_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(AuditLogModel).order_by(AuditLogModel.timestamp.desc())
    if decision:
        q = q.filter(AuditLogModel.policy_decision == PolicyDecision(decision))
    if tool_name:
        q = q.filter(AuditLogModel.tool_name == tool_name)
    logs = q.limit(limit).all()

    return [
        {
            "id": l.id,
            "task_id": l.task_id,
            "timestamp": l.timestamp.isoformat(),
            "tool_name": l.tool_name,
            "sanitized_arguments": l.sanitized_arguments,
            "policy_decision": l.policy_decision.value,
            "reason_code": l.reason_code,
            "reason_description": l.reason_description,
            "was_executed": l.was_executed,
            "execution_result": l.execution_result,
            "error_message": l.error_message,
            "latency_ms": l.latency_ms,
            "user_role": l.user_role,
            "access_strategy": l.access_strategy,
            "model": l.model
        }
        for l in logs
    ]


@app.get("/api/audit/stats")
def get_audit_stats(db: Session = Depends(get_db)):
    total = db.query(AuditLogModel).count()
    allowed = db.query(AuditLogModel).filter(AuditLogModel.policy_decision == PolicyDecision.ALLOW).count()
    denied = db.query(AuditLogModel).filter(AuditLogModel.policy_decision == PolicyDecision.DENY).count()
    approval = db.query(AuditLogModel).filter(AuditLogModel.policy_decision == PolicyDecision.REQUIRE_APPROVAL).count()
    return {
        "total_calls_logged": total,
        "allowed_calls": allowed,
        "denied_calls": denied,
        "approval_required_calls": approval,
        "block_ratio_percent": round((denied / total) * 100, 1) if total > 0 else 0
    }


# ==========================================
# 7. Evaluation Metrics & Reports
# ==========================================

@app.get("/api/metrics/summary")
def get_metrics_summary(db: Session = Depends(get_db)):
    return EvaluationEngine.calculate_summary(db)


@app.get("/api/reports/export")
def export_report(fmt: str = Query("json", enum=["json", "csv"]), db: Session = Depends(get_db)):
    summary = EvaluationEngine.calculate_summary(db)
    if fmt == "json":
        return summary
    else:
        # Generate CSV representation of comparison matrix
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        matrix = summary.get("comparison_matrix", [])
        if matrix:
            writer.writerow(matrix[0].keys())
            for row in matrix:
                writer.writerow(row.values())
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=adaptive_scoping_metrics.csv"}
        )


# ==========================================
# 8. Benchmarks & System Settings
# ==========================================

@app.get("/api/benchmarks")
def list_benchmarks(db: Session = Depends(get_db)):
    benchmarks = db.query(BenchmarkTaskModel).all()
    return [
        {
            "id": b.id,
            "title": b.title,
            "category": b.category.value,
            "task_prompt": b.task_prompt,
            "expected_tools": b.expected_tools,
            "forbidden_tools": b.forbidden_tools,
            "is_adversarial": b.is_adversarial,
            "adversarial_payload_type": b.adversarial_payload_type,
            "required_user_role": b.required_user_role.value,
            "evaluation_criteria": b.evaluation_criteria
        }
        for b in benchmarks
    ]


@app.get("/api/settings")
def get_settings(db: Session = Depends(get_db)):
    policy = db.query(SecurityPolicyModel).first()
    return {
        "policy_name": policy.name if policy else "Default Policy",
        "max_risk_threshold": policy.max_risk_threshold if policy else 7,
        "enforce_relevance_check": policy.enforce_relevance_check if policy else True,
        "block_destructive_ops": policy.block_destructive_ops_for_non_admin if policy else True,
        "block_exfiltration_tools": policy.block_exfiltration_tools if policy else True
    }


@app.post("/api/settings")
def update_settings(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    admin: dict = Depends(require_role(UserRole.ADMIN))
):
    policy = db.query(SecurityPolicyModel).first()
    if policy:
        if "max_risk_threshold" in payload:
            policy.max_risk_threshold = int(payload["max_risk_threshold"])
        if "enforce_relevance_check" in payload:
            policy.enforce_relevance_check = bool(payload["enforce_relevance_check"])
        if "block_destructive_ops" in payload:
            policy.block_destructive_ops_for_non_admin = bool(payload["block_destructive_ops"])
        if "block_exfiltration_tools" in payload:
            policy.block_exfiltration_tools = bool(payload["block_exfiltration_tools"])
        db.commit()
    return {"status": "SAVED", "settings": payload}


# ==========================================
# 9. Serve Frontend SPA in Production
# ==========================================

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))

if os.path.isdir(DIST_DIR):
    assets_dir = os.path.join(DIST_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API route not found.")
        file_path = os.path.join(DIST_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))

