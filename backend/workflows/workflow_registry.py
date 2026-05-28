"""
Workflow Registry

Central registry for all available workflows in the AI Operations System.
Each workflow includes metadata, handlers, and execution configuration.
"""

WORKFLOW_REGISTRY = {
    "send_report": {
        "description": "Send operational KPI reports to stakeholders",
        "handler": "default",
        "required_fields": ["recipients", "report_type"],
        "optional_fields": ["format", "filters", "delivery_method"],
        "category": "reporting",
        "priority": "high",
        "enabled": True,
        "retry_count": 3,
        "timeout_seconds": 300
    },

    "generate_kpi_summary": {
        "description": "Generate KPI intelligence summary for specified period",
        "handler": "default",
        "required_fields": ["period"],
        "optional_fields": ["metrics", "departments", "depth"],
        "category": "analytics",
        "priority": "medium",
        "enabled": True,
        "retry_count": 3,
        "timeout_seconds": 600
    },

    "log_decision": {
        "description": "Store operational decisions with context and metadata",
        "handler": "default",
        "required_fields": ["category", "decision"],
        "optional_fields": ["priority", "owner", "tags", "related_decisions"],
        "category": "governance",
        "priority": "high",
        "enabled": True,
        "retry_count": 2,
        "timeout_seconds": 120
    },

    "sync_knowledge_base": {
        "description": "Synchronize external knowledge sources (Google Drive, Notion)",
        "handler": "default",
        "required_fields": ["source"],
        "optional_fields": ["scope", "incremental", "filters"],
        "category": "integration",
        "priority": "medium",
        "enabled": False,  # Pending real integration
        "retry_count": 5,
        "timeout_seconds": 1800
    },

    "execute_ai_analysis": {
        "description": "Execute AI agent analysis on specified data",
        "handler": "default",
        "required_fields": ["agent_type", "query"],
        "optional_fields": ["context", "max_iterations"],
        "category": "ai",
        "priority": "high",
        "enabled": True,
        "retry_count": 2,
        "timeout_seconds": 900
    },

    "trigger_automation": {
        "description": "Trigger n8n automation workflow",
        "handler": "default",
        "required_fields": ["automation_id", "trigger_data"],
        "optional_fields": ["wait_for_response", "timeout"],
        "category": "automation",
        "priority": "medium",
        "enabled": False,  # Pending n8n integration
        "retry_count": 3,
        "timeout_seconds": 600
    },

    "archive_memory": {
        "description": "Archive old operational memory entries",
        "handler": "default",
        "required_fields": ["retention_days"],
        "optional_fields": ["categories", "archive_location"],
        "category": "maintenance",
        "priority": "low",
        "enabled": True,
        "retry_count": 3,
        "timeout_seconds": 1200
    },

    "generate_audit_report": {
        "description": "Generate audit trail and compliance report",
        "handler": "default",
        "required_fields": ["period"],
        "optional_fields": ["scope", "include_decisions", "include_errors"],
        "category": "governance",
        "priority": "high",
        "enabled": True,
        "retry_count": 2,
        "timeout_seconds": 1200
    }
}

def get_workflow(workflow_name: str) -> dict:
    """
    Retrieve a workflow definition from the registry.
    
    Args:
        workflow_name: Name of the workflow
        
    Returns:
        Workflow definition dictionary or None if not found
    """
    return WORKFLOW_REGISTRY.get(workflow_name)

def list_workflows(enabled_only: bool = False) -> list:
    """
    List all available workflows.
    
    Args:
        enabled_only: If True, only return enabled workflows
        
    Returns:
        List of workflow names
    """
    if enabled_only:
        return [
            name for name, config in WORKFLOW_REGISTRY.items()
            if config.get("enabled", True)
        ]
    return list(WORKFLOW_REGISTRY.keys())

def validate_workflow_payload(workflow_name: str, payload: dict) -> tuple:
    """
    Validate if a payload meets the requirements for a workflow.
    
    Args:
        workflow_name: Name of the workflow
        payload: The payload to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    workflow = get_workflow(workflow_name)
    if not workflow:
        return False, f"Workflow '{workflow_name}' not found"
    
    # Check if workflow is enabled
    if not workflow.get("enabled", True):
        return False, f"Workflow '{workflow_name}' is disabled"
    
    # Check required fields
    required_fields = workflow.get("required_fields", [])
    for field in required_fields:
        if field not in payload:
            return False, f"Missing required field: '{field}'"
    
    return True, "Payload is valid"