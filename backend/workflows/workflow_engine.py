from backend.workflows.workflow_registry import WORKFLOW_REGISTRY
from backend.workflows.execution_logger import log_workflow_execution

def execute_workflow(
    workflow_name,
    payload
):

    if workflow_name not in WORKFLOW_REGISTRY:
        return {
            "status": "error",
            "message": "Workflow not found"
        }

    result = {
        "workflow": workflow_name,
        "payload": payload,
        "status": "completed"
    }

    log_workflow_execution(
        workflow_name,
        result
    )

    return result