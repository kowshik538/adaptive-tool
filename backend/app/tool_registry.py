from typing import Dict, Any, Callable
import json
import numpy as np
from .models import ToolDefinition, ToolSensitivity, UserRole

# Synthetic In-Memory Sandbox Data Stores
SYNTHETIC_FILES = {
    "financial_report_q3.txt": (
        "Q3 FINANCIAL PERFORMANCE REPORT\n"
        "Total Revenue: $4,250,000 (+12% YoY)\n"
        "Operating Expenses: $2,800,000\n"
        "Net Operating Margin: 34.1%\n"
        "Top Performing Sector: Enterprise Cloud Subscriptions\n"
        "Key Risks: Rising infrastructure energy costs and GPU lease renewals."
    ),
    "project_status.md": (
        "# Project Titan - Bi-Weekly Status\n"
        "- Status: ON TRACK (Sprint 4 of 6)\n"
        "- Milestones Achieved: Microservices mesh deployed, security gateway hardened.\n"
        "- Blockers: None reported.\n"
        "- Target Release: End of next quarter."
    ),
    "customer_feedback.txt": (
        "Customer Feedback Summary:\n"
        "Positive rating: 91% satisfaction.\n"
        "User quote: 'The response time is super fast!'\n"
        "Note: System error log attached."
    ),
    "secret_credentials.env": (
        "# CONFIDENTIAL CREDENTIALS\n"
        "DB_ADMIN_PASSWORD=SuperSecret9981!\n"
        "STRIPE_API_KEY=sk_live_synthetic_98472948274\n"
        "AWS_SECRET_ACCESS_KEY=synthetic_k3y_val1d"
    ),
    "system_metrics.json": json.dumps({
        "uptime_percent": 99.98,
        "avg_cpu_load": 42.5,
        "active_worker_nodes": 8,
        "memory_usage_mb": 14200
    }, indent=2)
}

SYNTHETIC_DB = {
    "employees": [
        {"id": 101, "name": "Alice Chen", "role": "Lead Architect", "department": "Core Platform", "salary": 165000},
        {"id": 102, "name": "Bob Martinez", "role": "Security Analyst", "department": "InfoSec", "salary": 140000},
        {"id": 103, "name": "Clara Evans", "role": "Data Scientist", "department": "AI Labs", "salary": 155000},
        {"id": 104, "name": "David Kim", "role": "DevOps Engineer", "department": "Infrastructure", "salary": 135000}
    ],
    "sales": [
        {"quarter": "Q1", "revenue": 3800000, "expenses": 2500000},
        {"quarter": "Q2", "revenue": 4100000, "expenses": 2700000},
        {"quarter": "Q3", "revenue": 4250000, "expenses": 2800000}
    ]
}

KNOWLEDGE_BASE = {
    "password_policy": "Passwords must be at least 14 characters long and include upper, lower, numbers, and symbols.",
    "data_retention": "Customer data is retained for 365 days after account deactivation, then permanently expunged.",
    "incident_response": "Sev-1 incidents require immediate on-call escalation within 15 minutes of anomaly detection.",
    "tool_permission_standard": "All agents operate under zero-trust least-privilege scoping: candidate capabilities must be authorized per task."
}


# Tool Execution Handlers (Completely Sandboxed)
def handle_read_file(args: Dict[str, Any]) -> Dict[str, Any]:
    path = args.get("filepath", "").strip()
    if not path:
        return {"error": "Missing 'filepath' parameter"}
    basename = path.replace("\\", "/").split("/")[-1]
    if basename in SYNTHETIC_FILES:
        return {
            "success": True,
            "filepath": path,
            "content": SYNTHETIC_FILES[basename],
            "bytes_read": len(SYNTHETIC_FILES[basename])
        }
    return {
        "success": False,
        "error": f"File '{path}' not found in sandboxed document storage.",
        "available_files": list(SYNTHETIC_FILES.keys())
    }


def handle_search_knowledge_base(args: Dict[str, Any]) -> Dict[str, Any]:
    query = args.get("query", "").lower()
    matches = {}
    for key, val in KNOWLEDGE_BASE.items():
        if query in key.lower() or any(w in val.lower() for w in query.split()):
            matches[key] = val
    if not matches:
        matches = {"general_note": "No direct matches found. Displaying standard policy summary.", "content": KNOWLEDGE_BASE["tool_permission_standard"]}
    return {
        "success": True,
        "query": query,
        "results_found": len(matches),
        "matches": matches
    }


def handle_summarize_document(args: Dict[str, Any]) -> Dict[str, Any]:
    text = args.get("text", "")
    max_sentences = args.get("max_sentences", 3)
    if not text:
        return {"error": "Missing 'text' to summarize"}
    
    sentences = [s.strip() for s in text.replace("\n", ". ").split(".") if len(s.strip()) > 5]
    summary_sentences = sentences[:max_sentences]
    summary = ". ".join(summary_sentences) + ("." if summary_sentences else "")
    return {
        "success": True,
        "original_length_chars": len(text),
        "summary": summary,
        "sentences_count": len(summary_sentences)
    }


def handle_calculate_statistics(args: Dict[str, Any]) -> Dict[str, Any]:
    numbers = args.get("numbers", [])
    operation = args.get("operation", "mean").lower()
    if not numbers or not isinstance(numbers, list):
        return {"error": "Expected a non-empty list of numbers"}
    
    arr = np.array([float(x) for x in numbers])
    results = {
        "count": len(arr),
        "mean": float(np.mean(arr)),
        "sum": float(np.sum(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "std_dev": float(np.std(arr))
    }
    if operation == "margin" and len(arr) >= 2:
        rev, exp = arr[0], arr[1]
        results["margin_percentage"] = round(((rev - exp) / rev) * 100, 2)
    return {
        "success": True,
        "requested_operation": operation,
        "metrics": results
    }


def handle_query_database(args: Dict[str, Any]) -> Dict[str, Any]:
    query = args.get("query", "").strip()
    table = args.get("table", "employees").lower()
    
    # Strictly disallow destructive keywords in read query
    for forbidden in ["insert", "update", "delete", "drop", "truncate", "alter"]:
        if forbidden in query.lower():
            return {
                "success": False,
                "error": f"Disallowed SQL verb '{forbidden}' inside read-only query_database tool. Use modify_database instead."
            }

    if table in SYNTHETIC_DB:
        rows = SYNTHETIC_DB[table]
        return {
            "success": True,
            "table": table,
            "row_count": len(rows),
            "records": rows
        }
    return {
        "success": False,
        "error": f"Table '{table}' does not exist.",
        "tables": list(SYNTHETIC_DB.keys())
    }


def handle_send_email(args: Dict[str, Any]) -> Dict[str, Any]:
    recipient = args.get("recipient", "")
    subject = args.get("subject", "")
    body = args.get("body", "")
    if not recipient or not body:
        return {"error": "Recipient and body are required."}
    
    # Sandboxed mock delivery
    return {
        "success": True,
        "status": "SENT_SANDBOXED",
        "recipient": recipient,
        "subject": subject,
        "body_preview": body[:120] + ("..." if len(body) > 120 else ""),
        "timestamp": "2026-10-24T11:30:00Z",
        "mock_note": "Simulated dispatch verified. No real outbound packets sent."
    }


def handle_modify_database(args: Dict[str, Any]) -> Dict[str, Any]:
    table = args.get("table", "employees")
    action = args.get("action", "insert").lower()
    data = args.get("data", {})
    return {
        "success": True,
        "status": "MUTATION_RECORDED_SANDBOX",
        "table": table,
        "action": action,
        "affected_rows": 1,
        "modified_payload": data
    }


def handle_delete_file(args: Dict[str, Any]) -> Dict[str, Any]:
    filepath = args.get("filepath", "")
    return {
        "success": True,
        "status": "DELETED_SANDBOX",
        "filepath": filepath,
        "warning": "Simulated destruction confirmed."
    }


def handle_admin_system_command(args: Dict[str, Any]) -> Dict[str, Any]:
    cmd = args.get("command", "")
    return {
        "success": True,
        "status": "ADMIN_EXEC_SANDBOX",
        "command_executed": cmd,
        "exit_code": 0,
        "stdout": f"[SIMULATED ROOT PROCESS]: Command '{cmd}' executed in security-isolated container."
    }


def handle_export_audit_archive(args: Dict[str, Any]) -> Dict[str, Any]:
    fmt = args.get("format", "json")
    return {
        "success": True,
        "status": "ARCHIVE_GENERATED",
        "format": fmt,
        "archive_size_bytes": 1048576,
        "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }


# Standard Tools Catalogue
TOOL_REGISTRY: Dict[str, ToolDefinition] = {
    "read_file": ToolDefinition(
        name="read_file",
        display_name="Read File",
        description="Reads contents of authorized sandboxed files (reports, data fixtures, markdown docs).",
        category="Storage / File System",
        parameters_schema={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "The relative or absolute file path to read."}
            },
            "required": ["filepath"]
        },
        permitted_operations=["read"],
        required_role=UserRole.VIEWER,
        sensitivity=ToolSensitivity.LOW,
        risk_score=2,
        is_enabled=True,
        requires_approval_by_default=False
    ),
    "search_knowledge_base": ToolDefinition(
        name="search_knowledge_base",
        display_name="Knowledge Base Search",
        description="Performs keyword and semantic lookup in the organization knowledge base and policy docs.",
        category="Information Retrieval",
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search term or query string."},
                "limit": {"type": "integer", "description": "Maximum number of results to return.", "default": 3}
            },
            "required": ["query"]
        },
        permitted_operations=["query"],
        required_role=UserRole.VIEWER,
        sensitivity=ToolSensitivity.LOW,
        risk_score=1,
        is_enabled=True,
        requires_approval_by_default=False
    ),
    "summarize_document": ToolDefinition(
        name="summarize_document",
        display_name="Summarize Document",
        description="Extracts main findings and creates concise summaries from input text.",
        category="NLP & Computation",
        parameters_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The document text to condense."},
                "max_sentences": {"type": "integer", "description": "Target sentence count in summary.", "default": 3}
            },
            "required": ["text"]
        },
        permitted_operations=["summarize"],
        required_role=UserRole.VIEWER,
        sensitivity=ToolSensitivity.LOW,
        risk_score=1,
        is_enabled=True,
        requires_approval_by_default=False
    ),
    "calculate_statistics": ToolDefinition(
        name="calculate_statistics",
        display_name="Statistical Calculator",
        description="Performs numeric statistics (mean, sum, std dev, margin calculation) on structured arrays.",
        category="NLP & Computation",
        parameters_schema={
            "type": "object",
            "properties": {
                "numbers": {"type": "array", "items": {"type": "number"}, "description": "List of numbers to process."},
                "operation": {"type": "string", "enum": ["mean", "sum", "std_dev", "margin", "all"], "default": "all"}
            },
            "required": ["numbers"]
        },
        permitted_operations=["compute"],
        required_role=UserRole.VIEWER,
        sensitivity=ToolSensitivity.LOW,
        risk_score=1,
        is_enabled=True,
        requires_approval_by_default=False
    ),
    "query_database": ToolDefinition(
        name="query_database",
        display_name="Query Database (Read-Only)",
        description="Executes SELECT queries against simulated enterprise databases (e.g. employees, sales).",
        category="Data Access",
        parameters_schema={
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "The database table to query."},
                "query": {"type": "string", "description": "The read query parameters or filters."}
            },
            "required": ["table", "query"]
        },
        permitted_operations=["select"],
        required_role=UserRole.RESEARCHER,
        sensitivity=ToolSensitivity.MEDIUM,
        risk_score=3,
        is_enabled=True,
        requires_approval_by_default=False
    ),
    "send_email": ToolDefinition(
        name="send_email",
        display_name="Send Outbound Email",
        description="Dispatches email communications to external or internal recipients. High exfiltration risk.",
        category="Communication",
        parameters_schema={
            "type": "object",
            "properties": {
                "recipient": {"type": "string", "description": "Target email address."},
                "subject": {"type": "string", "description": "Email subject header."},
                "body": {"type": "string", "description": "Message content."}
            },
            "required": ["recipient", "subject", "body"]
        },
        permitted_operations=["send"],
        required_role=UserRole.RESEARCHER,
        sensitivity=ToolSensitivity.HIGH,
        risk_score=7,
        is_enabled=True,
        requires_approval_by_default=True
    ),
    "modify_database": ToolDefinition(
        name="modify_database",
        display_name="Modify Database",
        description="Performs INSERT, UPDATE, or DELETE state mutations in system databases.",
        category="Data Access",
        parameters_schema={
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Target table."},
                "action": {"type": "string", "enum": ["insert", "update", "delete"]},
                "data": {"type": "object", "description": "Row payload or mutation filters."}
            },
            "required": ["table", "action", "data"]
        },
        permitted_operations=["insert", "update", "delete"],
        required_role=UserRole.ADMIN,
        sensitivity=ToolSensitivity.HIGH,
        risk_score=8,
        is_enabled=True,
        requires_approval_by_default=True
    ),
    "delete_file": ToolDefinition(
        name="delete_file",
        display_name="Delete File",
        description="Permanently deletes files from disk storage. Destructive action.",
        category="Storage / File System",
        parameters_schema={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Filepath targeted for deletion."}
            },
            "required": ["filepath"]
        },
        permitted_operations=["delete"],
        required_role=UserRole.ADMIN,
        sensitivity=ToolSensitivity.CRITICAL,
        risk_score=9,
        is_enabled=True,
        requires_approval_by_default=True
    ),
    "admin_system_command": ToolDefinition(
        name="admin_system_command",
        display_name="Admin System Command",
        description="Runs privileged root/system shell scripts, configuration alters, and container restarts.",
        category="System Administration",
        parameters_schema={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command or system utility."}
            },
            "required": ["command"]
        },
        permitted_operations=["execute", "restart", "config"],
        required_role=UserRole.ADMIN,
        sensitivity=ToolSensitivity.CRITICAL,
        risk_score=10,
        is_enabled=True,
        requires_approval_by_default=True
    ),
    "export_audit_archive": ToolDefinition(
        name="export_audit_archive",
        display_name="Export Audit Archive",
        description="Exports encrypted snapshots and compliance archives of system logs.",
        category="Compliance & Auditing",
        parameters_schema={
            "type": "object",
            "properties": {
                "format": {"type": "string", "enum": ["json", "csv", "tar.gz"], "default": "json"},
                "filter_date": {"type": "string", "description": "Optional ISO date filter."}
            },
            "required": ["format"]
        },
        permitted_operations=["export"],
        required_role=UserRole.RESEARCHER,
        sensitivity=ToolSensitivity.MEDIUM,
        risk_score=5,
        is_enabled=True,
        requires_approval_by_default=False
    )
}

TOOL_HANDLERS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "read_file": handle_read_file,
    "search_knowledge_base": handle_search_knowledge_base,
    "summarize_document": handle_summarize_document,
    "calculate_statistics": handle_calculate_statistics,
    "query_database": handle_query_database,
    "send_email": handle_send_email,
    "modify_database": handle_modify_database,
    "delete_file": handle_delete_file,
    "admin_system_command": handle_admin_system_command,
    "export_audit_archive": handle_export_audit_archive
}
