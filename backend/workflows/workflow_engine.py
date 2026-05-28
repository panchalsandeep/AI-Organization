import uuid
import time
from datetime import datetime
from typing import Dict, Any
from backend.workflows.workflow_registry import WORKFLOW_REGISTRY
from backend.workflows.execution_logger import log_workflow_execution

class WorkflowExecutionError(Exception):
    """Custom exception for workflow execution errors"""
    pass

def execute_workflow(
    workflow_name: str,
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute a registered workflow with error handling and structured logging.
    
    Args:
        workflow_name: Name of the workflow to execute
        payload: Input data for the workflow
        
    Returns:
        Dict containing execution status, results, and metadata
    """
    execution_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Validate workflow exists
        if workflow_name not in WORKFLOW_REGISTRY:
            raise WorkflowExecutionError(
                f"Workflow '{workflow_name}' not found in registry"
            )
        
        workflow_def = WORKFLOW_REGISTRY[workflow_name]
        
        # Execute workflow logic (placeholder for actual execution)
        # This will be expanded with actual workflow handlers
        execution_result = _execute_workflow_logic(
            workflow_name,
            workflow_def,
            payload
        )
        
        execution_time = time.time() - start_time
        
        result = {
            "execution_id": execution_id,
            "workflow_name": workflow_name,
            "status": "completed",
            "payload": payload,
            "result": execution_result,
            "execution_time_seconds": round(execution_time, 3),
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "workflow_description": workflow_def.get("description", ""),
                "handler": workflow_def.get("handler", "default")
            }
        }
        
    except WorkflowExecutionError as e:
        execution_time = time.time() - start_time
        result = {
            "execution_id": execution_id,
            "workflow_name": workflow_name,
            "status": "error",
            "error": str(e),
            "payload": payload,
            "execution_time_seconds": round(execution_time, 3),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        result = {
            "execution_id": execution_id,
            "workflow_name": workflow_name,
            "status": "failed",
            "error": f"Unexpected error: {str(e)}",
            "error_type": type(e).__name__,
            "payload": payload,
            "execution_time_seconds": round(execution_time, 3),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Log the execution
    log_workflow_execution(workflow_name, result)
    
    return result

def _execute_workflow_logic(
    workflow_name: str,
    workflow_def: Dict[str, Any],
    payload: Dict[str, Any]
) -> Any:
    """
    Execute the actual workflow logic based on the workflow definition.
    
    Args:
        workflow_name: Name of the workflow
        workflow_def: Workflow definition from registry
        payload: Input payload
        
    Returns:
        Result of workflow execution
    """
    handler_type = workflow_def.get("handler", "default")
    
    # Route to specific handlers based on workflow type
    handlers = {
        "send_report": _handle_send_report,
        "generate_kpi_summary": _handle_generate_kpi_summary,
        "log_decision": _handle_log_decision
    }
    
    handler = handlers.get(workflow_name)
    if handler:
        return handler(payload)
    
    # Default handler
    return {"message": f"Workflow {workflow_name} executed", "payload": payload}

def _handle_send_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for send_report workflow"""
    return {
        "type": "report_sent",
        "recipients": payload.get("recipients", []),
        "report_type": payload.get("report_type", "operational")
    }

def _handle_generate_kpi_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for generate_kpi_summary workflow"""
    return {
        "type": "kpi_summary",
        "period": payload.get("period", "weekly"),
        "kpi_count": payload.get("kpi_count", 0)
    }

def _handle_log_decision(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for log_decision workflow"""
    return {
        "type": "decision_logged",
        "decision_id": str(uuid.uuid4()),
        "category": payload.get("category", "operational"),
        "priority": payload.get("priority", "medium")
    }