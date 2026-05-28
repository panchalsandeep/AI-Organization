from backend.ingestion.ingest_memory import ingest_memory

def log_workflow_execution(
    workflow_name,
    execution_result
):

    ingest_memory(
        title=f"Workflow Execution: {workflow_name}",
        content=str(execution_result),
        content_type="workflow_execution",
        source="workflow_engine",
        tags=["workflow", "automation"],
        metadata={
            "workflow_name": workflow_name
        }
    )