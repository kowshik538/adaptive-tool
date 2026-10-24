import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import (
    Base, UserModel, ToolModel, SecurityPolicyModel, BenchmarkTaskModel,
    TaskExecutionModel, UserRole, AccessStrategy, ModelScale
)
from .auth import hash_password
from .tool_registry import TOOL_REGISTRY
from .benchmarks import BENCHMARK_TASKS
from .task_analyzer import TaskAnalyzer
from .agent_runner import AgentRunner

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "app.db")
DATABASE_URL = f"sqlite:///{DB_PATH}?check_same_thread=False"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Seed Users
        existing_users = db.query(UserModel).count()
        if existing_users == 0:
            demo_users = [
                UserModel(
                    username="admin",
                    email="admin@security.lab",
                    hashed_password=hash_password("AdminPass123!"),
                    role=UserRole.ADMIN
                ),
                UserModel(
                    username="researcher",
                    email="researcher@security.lab",
                    hashed_password=hash_password("ResearchPass123!"),
                    role=UserRole.RESEARCHER
                ),
                UserModel(
                    username="tester",
                    email="tester@security.lab",
                    hashed_password=hash_password("TesterPass123!"),
                    role=UserRole.TESTER
                ),
                UserModel(
                    username="viewer",
                    email="viewer@security.lab",
                    hashed_password=hash_password("ViewerPass123!"),
                    role=UserRole.VIEWER
                ),
            ]
            db.add_all(demo_users)
            db.commit()

        # 2. Seed Tools
        existing_tools = db.query(ToolModel).count()
        if existing_tools == 0:
            for name, tool_def in TOOL_REGISTRY.items():
                tool_orm = ToolModel(
                    name=tool_def.name,
                    display_name=tool_def.display_name,
                    description=tool_def.description,
                    category=tool_def.category,
                    parameters_schema=tool_def.parameters_schema,
                    permitted_operations=tool_def.permitted_operations,
                    required_role=tool_def.required_role,
                    sensitivity=tool_def.sensitivity,
                    risk_score=tool_def.risk_score,
                    is_enabled=tool_def.is_enabled,
                    requires_approval_by_default=tool_def.requires_approval_by_default
                )
                db.add(tool_orm)
            db.commit()

        # 3. Seed Default Security Policy
        existing_policy = db.query(SecurityPolicyModel).first()
        if not existing_policy:
            policy = SecurityPolicyModel(
                name="Default Least-Privilege Adaptive Policy",
                max_risk_threshold=7,
                enforce_relevance_check=True,
                block_destructive_ops_for_non_admin=True,
                block_exfiltration_tools=True,
                is_active=True
            )
            db.add(policy)
            db.commit()

        # 4. Seed Benchmark Tasks
        existing_benchmarks = db.query(BenchmarkTaskModel).count()
        if existing_benchmarks == 0:
            for bench in BENCHMARK_TASKS:
                bench_orm = BenchmarkTaskModel(
                    id=bench["id"],
                    title=bench["title"],
                    category=bench["category"],
                    task_prompt=bench["task_prompt"],
                    expected_tools=bench["expected_tools"],
                    forbidden_tools=bench["forbidden_tools"],
                    is_adversarial=bench["is_adversarial"],
                    adversarial_payload_type=bench["adversarial_payload_type"],
                    required_user_role=bench["required_user_role"],
                    evaluation_criteria=bench["evaluation_criteria"]
                )
                db.add(bench_orm)
            db.commit()

        # 5. Pre-run Baseline Benchmark Matrix if empty (Produces genuine measurable evidence)
        existing_runs = db.query(TaskExecutionModel).count()
        if existing_runs == 0:
            print("[INFO] Seeding initial baseline experimental evaluations across benchmark suite...")
            # We run the 12 benchmarks across Full Access, Moderate Access, Least-Privilege
            # for Small Model (3B) and Large Model (70B)
            # To ensure quick startup, run key representative benchmarks (1 from each category)
            seed_benchmarks = [b for b in BENCHMARK_TASKS if b["id"] in [
                "BENCH-IR-01", "BENCH-FS-01", "BENCH-DC-01", "BENCH-MT-01", "BENCH-PL-01", "BENCH-ADV-01", "BENCH-ADV-02"
            ]]
            
            strategies = [AccessStrategy.FULL_ACCESS, AccessStrategy.MODERATE_ACCESS, AccessStrategy.LEAST_PRIVILEGE]
            models = [ModelScale.SMALL_3B, ModelScale.LARGE_70B]

            for b in seed_benchmarks:
                task_analysis = TaskAnalyzer.analyze(b["task_prompt"])
                for strat in strategies:
                    for mod in models:
                        task_id = f"EXP-INIT-{uuid.uuid4().hex[:8]}"
                        exec_res = AgentRunner.run_task(
                            db=db,
                            task_id=task_id,
                            task_prompt=b["task_prompt"],
                            access_strategy=strat,
                            model_scale=mod,
                            user_role=b["required_user_role"],
                            task_analysis=task_analysis,
                            benchmark_expected_tools=b["expected_tools"],
                            is_adversarial=b["is_adversarial"]
                        )
                        task_record = TaskExecutionModel(
                            id=exec_res.task_id,
                            task_prompt=exec_res.task_prompt,
                            access_strategy=exec_res.access_strategy,
                            model_scale=exec_res.model_scale,
                            user_role=exec_res.user_role,
                            benchmark_id=b["id"],
                            candidate_tools=exec_res.candidate_tools,
                            scoped_allow_list=exec_res.scoped_allow_list,
                            blocked_tools=exec_res.blocked_tools,
                            agent_final_response=exec_res.agent_final_response,
                            status=exec_res.status,
                            is_adversarial_attempt=b["is_adversarial"],
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
                        db.add(task_record)
            db.commit()
            print("[INFO] Baseline benchmarks successfully executed and recorded.")

    finally:
        db.close()
