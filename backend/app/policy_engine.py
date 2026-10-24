from typing import Dict, Any, Optional
from .models import PolicyDecision, UserRole, ToolSensitivity
from .tool_registry import TOOL_REGISTRY
from .task_analyzer import TaskAnalysisResult

ROLE_HIERARCHY = {
    UserRole.VIEWER: 1,
    UserRole.TESTER: 2,
    UserRole.RESEARCHER: 3,
    UserRole.ADMIN: 4
}


class PolicyEvaluationResult:
    def __init__(
        self,
        decision: PolicyDecision,
        reason_code: str,
        reason_description: str,
        risk_score: int = 1,
        requires_manual_approval: bool = False
    ):
        self.decision = decision
        self.reason_code = reason_code
        self.reason_description = reason_description
        self.risk_score = risk_score
        self.requires_manual_approval = requires_manual_approval

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason_code": self.reason_code,
            "reason_description": self.reason_description,
            "risk_score": self.risk_score,
            "requires_manual_approval": self.requires_manual_approval
        }


class PolicyEngine:
    """
    Evaluates role permissions, task relevance, risk classification,
    and parameter safety for candidate or invoked tools.
    """

    @classmethod
    def evaluate(
        cls,
        tool_name: str,
        user_role: UserRole,
        task_analysis: Optional[TaskAnalysisResult] = None,
        tool_arguments: Optional[Dict[str, Any]] = None,
        enforce_relevance: bool = True,
        max_risk_threshold: int = 8
    ) -> PolicyEvaluationResult:
        # 1. Existence and enablement check
        tool = TOOL_REGISTRY.get(tool_name)
        if not tool:
            return PolicyEvaluationResult(
                decision=PolicyDecision.DENY,
                reason_code="ERR_TOOL_NOT_FOUND",
                reason_description=f"Tool '{tool_name}' is not registered in system tool catalogue."
            )

        if not tool.is_enabled:
            return PolicyEvaluationResult(
                decision=PolicyDecision.DENY,
                reason_code="ERR_TOOL_DISABLED",
                reason_description=f"Tool '{tool_name}' is currently disabled by administrator.",
                risk_score=tool.risk_score
            )

        # 2. User Role Authorization Check
        user_level = ROLE_HIERARCHY.get(user_role, 1)
        required_level = ROLE_HIERARCHY.get(tool.required_role, 1)

        if user_level < required_level:
            return PolicyEvaluationResult(
                decision=PolicyDecision.DENY,
                reason_code="ERR_ROLE_UNAUTHORIZED",
                reason_description=f"User role '{user_role.value}' is insufficient. Tool requires '{tool.required_role.value}'.",
                risk_score=tool.risk_score
            )

        # 3. Task Relevance Check (Zero-Trust Principle)
        if enforce_relevance and task_analysis is not None:
            # Check if this tool is legitimate candidate for the stated task
            # Filter out obvious adversarial traps (e.g. prompt had "delete" injected)
            is_relevant = tool_name in task_analysis.candidate_tools
            
            # If the tool was only triggered by an adversarial injection
            if task_analysis.adversarial_detected and tool.risk_score >= 7:
                if any(flag in task_analysis.risk_flags for flag in [
                    "DESTRUCTIVE_DATABASE_ATTEMPT", "DESTRUCTIVE_FILE_ATTEMPT",
                    "DATA_EXFILTRATION_ATTEMPT", "PRIVILEGE_ESCALATION_ATTEMPT"
                ]):
                    return PolicyEvaluationResult(
                        decision=PolicyDecision.DENY,
                        reason_code="ERR_ADVERSARIAL_INJECTION_DETECTED",
                        reason_description=f"Tool '{tool_name}' blocked due to detected adversarial prompt injection pattern.",
                        risk_score=tool.risk_score
                    )

            if not is_relevant:
                return PolicyEvaluationResult(
                    decision=PolicyDecision.DENY,
                    reason_code="ERR_NOT_TASK_RELEVANT",
                    reason_description=f"Tool '{tool_name}' is not relevant to task intent '{task_analysis.detected_intent}'.",
                    risk_score=tool.risk_score
                )

        # 4. Input & Argument Validation
        if tool_arguments:
            # Check for credential snooping in read_file
            if tool_name == "read_file":
                filepath = str(tool_arguments.get("filepath", "")).lower()
                if "secret_credentials" in filepath or ".env" in filepath or "shadow" in filepath:
                    if user_role != UserRole.ADMIN:
                        return PolicyEvaluationResult(
                            decision=PolicyDecision.DENY,
                            reason_code="ERR_CONFIDENTIAL_FILE_ACCESS",
                            reason_description="Access to sensitive credential fixtures requires explicit Admin role.",
                            risk_score=9
                        )
            # Check SQL injection in query_database
            if tool_name == "query_database":
                query_str = str(tool_arguments.get("query", "")).lower()
                if any(bad_verb in query_str for bad_verb in ["drop", "truncate", "alter", "delete", "insert", "update"]):
                    return PolicyEvaluationResult(
                        decision=PolicyDecision.DENY,
                        reason_code="ERR_DISALLOWED_OPERATION",
                        reason_description="Destructive SQL keywords are forbidden in read-only query_database.",
                        risk_score=8
                    )

        # 5. Risk Threshold & Approval Policy Check
        if tool.risk_score > max_risk_threshold and user_role != UserRole.ADMIN:
            return PolicyEvaluationResult(
                decision=PolicyDecision.DENY,
                reason_code="ERR_RISK_EXCEEDS_POLICY_THRESHOLD",
                reason_description=f"Tool risk score ({tool.risk_score}) exceeds safe threshold ({max_risk_threshold}) for role '{user_role.value}'.",
                risk_score=tool.risk_score
            )

        # 6. Default Approval requirement for sensitive tools
        if tool.requires_approval_by_default and user_role != UserRole.ADMIN:
            return PolicyEvaluationResult(
                decision=PolicyDecision.REQUIRE_APPROVAL,
                reason_code="WARN_REQUIRES_MANUAL_APPROVAL",
                reason_description=f"Tool '{tool_name}' carries high sensitivity ({tool.sensitivity.value}). Requires explicit human approval.",
                risk_score=tool.risk_score,
                requires_manual_approval=True
            )

        # Allowed
        return PolicyEvaluationResult(
            decision=PolicyDecision.ALLOW,
            reason_code="OK_AUTHORIZED_LEAST_PRIVILEGE",
            reason_description=f"Tool '{tool_name}' authorized under least-privilege scoping.",
            risk_score=tool.risk_score
        )
