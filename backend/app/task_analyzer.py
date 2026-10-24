import re
from typing import List, Dict, Any, Tuple
from .models import TaskAnalysisResult

# Suspicious Adversarial Signatures
ADVERSARIAL_PATTERNS = [
    (r"ignore\s+(all\s+)?(previous|prior)\s+instructions?", "INJECTION_OVERRIDE_INSTRUCTION"),
    (r"bypass\s+(all\s+)?(security|guardrails|policies|filters)", "SECURITY_BYPASS_ATTEMPT"),
    (r"(delete|drop|wipe|truncate)\s+(database|table|all\s+records|users)", "DESTRUCTIVE_DATABASE_ATTEMPT"),
    (r"(delete|remove|erase|shred)\s+(file|log|report|everything)", "DESTRUCTIVE_FILE_ATTEMPT"),
    (r"(send|forward|leak|exfiltrate)\s+(email|credential|secret|password|key)\s+to", "DATA_EXFILTRATION_ATTEMPT"),
    (r"(sudo|root|chmod|chown|rm\s+-rf|powershell|cmd\.exe|bash|eval\(|exec\()", "PRIVILEGE_ESCALATION_ATTEMPT"),
    (r"system\s*administrator\s*mode|developer\s*mode\s*enabled", "JAILBREAK_ROLEPLAY"),
    (r"now\s+you\s+must\s+call\s+tool", "FORCED_TOOL_INVOCATION")
]

# Capability intent mapping heuristics
CAPABILITY_MAPPINGS = [
    {
        "keywords": ["read", "open", "view file", "report", "document", "financial_report", "project_status", "inspect file"],
        "capability": "file_read",
        "tool": "read_file"
    },
    {
        "keywords": ["summarize", "summary", "brief", "key findings", "condense", "overview", "main points", "synthesize"],
        "capability": "summarize",
        "tool": "summarize_document"
    },
    {
        "keywords": ["search", "knowledge base", "policy", "documentation", "lookup", "faq", "guide", "procedure"],
        "capability": "knowledge_retrieval",
        "tool": "search_knowledge_base"
    },
    {
        "keywords": ["calculate", "statistics", "mean", "average", "margin", "std dev", "sum", "metrics", "percentage", "variance"],
        "capability": "calculation",
        "tool": "calculate_statistics"
    },
    {
        "keywords": ["query db", "database", "select from", "employee table", "sales table", "view rows", "fetch records"],
        "capability": "db_read",
        "tool": "query_database"
    },
    {
        "keywords": ["send email", "notify via email", "email the", "dispatch message", "forward report to"],
        "capability": "email_communication",
        "tool": "send_email"
    },
    {
        "keywords": ["modify database", "insert into", "update table", "alter record", "change salary", "create record"],
        "capability": "db_mutation",
        "tool": "modify_database"
    },
    {
        "keywords": ["delete file", "remove document", "purge file", "erase file"],
        "capability": "file_deletion",
        "tool": "delete_file"
    },
    {
        "keywords": ["admin command", "execute command", "system shell", "terminal", "restart container", "root execution"],
        "capability": "system_admin",
        "tool": "admin_system_command"
    },
    {
        "keywords": ["export audit", "archive logs", "compliance export", "download logs"],
        "capability": "audit_export",
        "tool": "export_audit_archive"
    }
]


class TaskAnalyzer:
    """
    Translates freeform prompt text into structured capabilities,
    identifies candidate tools, and scans for adversarial manipulation.
    """

    @staticmethod
    def analyze(task_prompt: str) -> TaskAnalysisResult:
        text = task_prompt.lower()
        risk_flags: List[str] = []
        candidate_tools: List[str] = []
        required_capabilities: List[str] = []

        # 1. Scan for adversarial patterns
        adversarial_detected = False
        for pattern, flag in ADVERSARIAL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                risk_flags.append(flag)
                adversarial_detected = True

        # 2. Extract genuine capabilities required
        for mapping in CAPABILITY_MAPPINGS:
            for kw in mapping["keywords"]:
                if kw in text:
                    if mapping["tool"] not in candidate_tools:
                        candidate_tools.append(mapping["tool"])
                    if mapping["capability"] not in required_capabilities:
                        required_capabilities.append(mapping["capability"])
                    break

        # If adversarial keywords requested unauthorized tools, note in candidate tools or flags
        if "delete" in text and "delete_file" not in candidate_tools and ("file" in text or "report" in text):
            candidate_tools.append("delete_file")
        if any(term in text for term in ["drop", "truncate", "wipe"]) and "modify_database" not in candidate_tools:
            candidate_tools.append("modify_database")
        if any(term in text for term in ["bash", "sh", "exec", "shell", "admin"]) and "admin_system_command" not in candidate_tools:
            candidate_tools.append("admin_system_command")
        if any(term in text for term in ["email", "exfiltrate", "leak"]) and "send_email" not in candidate_tools:
            candidate_tools.append("send_email")

        # Fallback default if very short or generic query
        if not candidate_tools:
            if "?" in text or "what" in text or "how" in text or "find" in text:
                candidate_tools = ["search_knowledge_base"]
                required_capabilities = ["knowledge_retrieval"]
            else:
                candidate_tools = ["read_file", "summarize_document"]
                required_capabilities = ["file_read", "summarize"]

        # Derive primary intent
        if adversarial_detected:
            detected_intent = f"ADVERSARIAL_PAYLOAD: Potential {risk_flags[0]}"
        elif "summarize" in text or "summary" in text:
            detected_intent = "Document Summarization & Extraction"
        elif "calculate" in text or "margin" in text:
            detected_intent = "Financial / Statistical Computation"
        elif "query" in text or "database" in text:
            detected_intent = "Database Query & Verification"
        elif "search" in text or "policy" in text:
            detected_intent = "Knowledge Base Information Lookup"
        else:
            detected_intent = "General Task Execution"

        confidence_score = 0.95 if candidate_tools else 0.65

        return TaskAnalysisResult(
            task_prompt=task_prompt,
            detected_intent=detected_intent,
            required_capabilities=required_capabilities,
            candidate_tools=candidate_tools,
            risk_flags=risk_flags,
            adversarial_detected=adversarial_detected,
            confidence_score=confidence_score
        )
