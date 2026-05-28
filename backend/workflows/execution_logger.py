import json
from datetime import datetime
from typing import Dict, Any, Optional
from backend.ingestion.ingest_memory import ingest_memory

class WorkflowExecutionLogger:
    """Structured logger for workflow executions"""
    
    @staticmethod
    def log_workflow_execution(
        workflow_name: str,
        execution_result: Dict[str, Any],
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a workflow execution with structured metadata.
        
        Args:
            workflow_name: Name of the workflow executed
            execution_result: Result dictionary from workflow execution
            additional_metadata: Additional metadata to attach to the log
        """
        # Extract key information from execution result
        status = execution_result.get("status", "unknown")
        execution_id = execution_result.get("execution_id", "unknown")
        execution_time = execution_result.get("execution_time_seconds", 0)
        timestamp = execution_result.get("timestamp", datetime.utcnow().isoformat())
        
        # Build comprehensive metadata
        metadata = {
            "workflow_name": workflow_name,
            "execution_id": execution_id,
            "status": status,
            "execution_time_seconds": execution_time,
            "timestamp": timestamp,
            "environment": "production"
        }
        
        # Add error information if present
        if status in ["error", "failed"]:
            metadata["error"] = execution_result.get("error", "Unknown error")
            metadata["error_type"] = execution_result.get("error_type")
        
        # Add workflow-specific metadata
        if "metadata" in execution_result:
            metadata.update(execution_result["metadata"])
        
        # Merge additional metadata if provided
        if additional_metadata:
            metadata.update(additional_metadata)
        
        # Build content for memory storage
        content = _format_execution_log(execution_result)
        
        # Log to operational memory
        try:
            ingest_memory(
                title=f"Workflow Execution: {workflow_name} [{status.upper()}]",
                content=content,
                content_type="workflow_execution",
                source="workflow_engine",
                tags=[
                    "workflow",
                    "automation",
                    "execution",
                    f"status:{status}",
                    f"workflow:{workflow_name}"
                ],
                metadata=metadata
            )
        except Exception as e:
            # Fallback logging if memory ingestion fails
            print(f"Failed to log workflow execution: {str(e)}")
            print(f"Execution result: {json.dumps(execution_result, indent=2)}")

def log_workflow_execution(
    workflow_name: str,
    execution_result: Dict[str, Any],
    additional_metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a workflow execution. Wrapper for the static method.
    
    Args:
        workflow_name: Name of the workflow executed
        execution_result: Result dictionary from workflow execution
        additional_metadata: Additional metadata to attach to the log
    """
    WorkflowExecutionLogger.log_workflow_execution(
        workflow_name,
        execution_result,
        additional_metadata
    )

def _format_execution_log(execution_result: Dict[str, Any]) -> str:
    """
    Format execution result into readable log content.
    
    Args:
        execution_result: The execution result dictionary
        
    Returns:
        Formatted string representation of the execution log
    """
    lines = []
    
    # Header
    workflow_name = execution_result.get("workflow_name", "Unknown")
    status = execution_result.get("status", "unknown").upper()
    execution_id = execution_result.get("execution_id", "N/A")
    timestamp = execution_result.get("timestamp", "N/A")
    
    lines.append(f"Workflow Execution Log")
    lines.append(f"{'=' * 50}")
    lines.append(f"Workflow: {workflow_name}")
    lines.append(f"Status: {status}")
    lines.append(f"Execution ID: {execution_id}")
    lines.append(f"Timestamp: {timestamp}")
    
    # Execution time
    exec_time = execution_result.get("execution_time_seconds")
    if exec_time is not None:
        lines.append(f"Execution Time: {exec_time}s")
    
    # Error information if applicable
    if status in ["ERROR", "FAILED"]:
        error = execution_result.get("error")
        if error:
            lines.append(f"\nError Details:")
            lines.append(f"{error}")
    
    # Payload information
    payload = execution_result.get("payload")
    if payload:
        lines.append(f"\nPayload:")
        lines.append(json.dumps(payload, indent=2))
    
    # Result information
    result = execution_result.get("result")
    if result and isinstance(result, dict):
        lines.append(f"\nResult:")
        lines.append(json.dumps(result, indent=2))
    
    return "\n".join(lines)