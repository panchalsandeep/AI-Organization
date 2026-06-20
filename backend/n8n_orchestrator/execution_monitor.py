from typing import List, Dict, Any

def get_execution_logs(workflow_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve run/execution logs for a specific n8n workflow.
    Uses mock log outputs suitable for dashboard displays.
    """
    return [
        {
            "execution_id": f"exec-run-10",
            "workflow_id": workflow_id,
            "status": "success",
            "started_at": "2026-06-20T18:00:00Z",
            "finished_at": "2026-06-20T18:00:05Z",
            "duration_seconds": 5
        },
        {
            "execution_id": f"exec-run-09",
            "workflow_id": workflow_id,
            "status": "failed",
            "started_at": "2026-06-20T17:00:00Z",
            "finished_at": "2026-06-20T17:00:02Z",
            "duration_seconds": 2,
            "error": "Slack API returned 401 Unauthorized"
        }
    ]
