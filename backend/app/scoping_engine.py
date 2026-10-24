from typing import List, Dict, Tuple
from .models import AccessStrategy, UserRole, ToolDefinition
from .tool_registry import TOOL_REGISTRY
from .task_analyzer import TaskAnalysisResult
from .policy_engine import PolicyEngine, PolicyDecision

# Strategy B (Moderate) Predefined allowed subset
MODERATE_STRATEGY_TOOLS = [
    "read_file",
    "search_knowledge_base",
    "summarize_document",
    "calculate_statistics",
    "query_database",
    "send_email"
]


class ScopingResult:
    def __init__(
        self,
        strategy: AccessStrategy,
        candidate_tools: List[str],
        scoped_allow_list: List[str],
        blocked_tools: List[str],
        exposed_tool_definitions: List[ToolDefinition],
        security_exposure_score: float
    ):
        self.strategy = strategy
        self.candidate_tools = candidate_tools
        self.scoped_allow_list = scoped_allow_list
        self.blocked_tools = blocked_tools
        self.exposed_tool_definitions = exposed_tool_definitions
        self.security_exposure_score = security_exposure_score

    def to_dict(self) -> Dict[str, any]:
        return {
            "strategy": self.strategy.value,
            "candidate_tools": self.candidate_tools,
            "scoped_allow_list": self.scoped_allow_list,
            "blocked_tools": self.blocked_tools,
            "security_exposure_score": self.security_exposure_score
        }


class ScopingEngine:
    """
    Computes the temporary tool allow-list granted to the agent
    under Full Access, Moderate Access, or Adaptive Least-Privilege.
    """

    @classmethod
    def compute_scope(
        cls,
        strategy: AccessStrategy,
        task_analysis: TaskAnalysisResult,
        user_role: UserRole,
        policy_threshold: int = 8
    ) -> ScopingResult:
        all_tool_names = list(TOOL_REGISTRY.keys())
        candidate_tools = task_analysis.candidate_tools
        scoped_allow_list: List[str] = []
        blocked_tools: List[str] = []

        if strategy == AccessStrategy.FULL_ACCESS:
            # Baseline: Expose all enabled tools in registry to agent
            for name, tool in TOOL_REGISTRY.items():
                if tool.is_enabled:
                    scoped_allow_list.append(name)
                else:
                    blocked_tools.append(name)

        elif strategy == AccessStrategy.MODERATE_ACCESS:
            # Predefined static filter: exclude high-risk admin and delete tools
            for name, tool in TOOL_REGISTRY.items():
                if tool.is_enabled and name in MODERATE_STRATEGY_TOOLS:
                    scoped_allow_list.append(name)
                else:
                    blocked_tools.append(name)

        elif strategy == AccessStrategy.LEAST_PRIVILEGE:
            # Dynamic task-specific scoping: Only tools that pass relevance and permission checks
            for tool_name in candidate_tools:
                eval_res = PolicyEngine.evaluate(
                    tool_name=tool_name,
                    user_role=user_role,
                    task_analysis=task_analysis,
                    enforce_relevance=True,
                    max_risk_threshold=policy_threshold
                )
                if eval_res.decision in [PolicyDecision.ALLOW, PolicyDecision.REQUIRE_APPROVAL]:
                    scoped_allow_list.append(tool_name)
                else:
                    blocked_tools.append(tool_name)

            # Record any remaining catalogue tools as blocked for this task
            for name in all_tool_names:
                if name not in scoped_allow_list and name not in blocked_tools:
                    blocked_tools.append(name)

        # Calculate quantitative Security Exposure metric
        # Sum of risk_scores of exposed tools
        total_exposure = sum(
            TOOL_REGISTRY[name].risk_score
            for name in scoped_allow_list
            if name in TOOL_REGISTRY
        )

        exposed_defs = [
            TOOL_REGISTRY[name]
            for name in scoped_allow_list
            if name in TOOL_REGISTRY
        ]

        return ScopingResult(
            strategy=strategy,
            candidate_tools=candidate_tools,
            scoped_allow_list=scoped_allow_list,
            blocked_tools=blocked_tools,
            exposed_tool_definitions=exposed_defs,
            security_exposure_score=float(total_exposure)
        )
