from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging

from backend.retrieval.search_memory import search_memory
from backend.agents.agent_router import route_agent
from backend.workflows.workflow_engine import execute_workflow
from backend.workflows.workflow_registry import validate_workflow_payload, list_workflows

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Operations System API",
    description="Central API for AI-powered operational intelligence",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Request/Response Models
# ============================================================================

class QueryRequest(BaseModel):
    query: str = Field(..., description="The semantic query to execute")
    match_count: int = Field(3, description="Number of context matches to retrieve")

class WorkflowRequest(BaseModel):
    workflow_name: str = Field(..., description="Name of the workflow to execute")
    payload: Dict[str, Any] = Field(..., description="Input payload for the workflow")

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str

class APIResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str

# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/", tags=["Health"])
def root():
    """Health check endpoint"""
    from datetime import datetime
    return {
        "status": "AI Operations API Running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health", tags=["Health"])
def health_check():
    """Detailed health check"""
    from datetime import datetime
    return {
        "status": "healthy",
        "version": "1.0.0",
        "api": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/workflows", tags=["Workflows"])
def list_available_workflows():
    """List all available workflows"""
    try:
        workflows = list_workflows(enabled_only=False)
        return {
            "success": True,
            "workflows": workflows,
            "count": len(workflows)
        }
    except Exception as e:
        logger.error(f"Error listing workflows: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow list"
        )

# ============================================================================
# Agent Query Endpoints
# ============================================================================

@app.post("/agent/query", tags=["Agents"])
def agent_query(request: QueryRequest):
    """
    Execute an agent query with semantic memory retrieval.
    
    The query is routed to the appropriate agent based on its content,
    and context is retrieved from operational memory for RAG.
    """
    try:
        logger.info(f"Processing agent query: {request.query[:100]}...")
        
        # Retrieve semantic context
        retrieved_context = search_memory(
            request.query,
            match_count=request.match_count
        )
        
        if not retrieved_context:
            logger.warning(f"No context retrieved for query: {request.query}")
            retrieved_context = []
        
        # Build context text
        context_text = "\n\n".join([
            result.get('content', '') for result in retrieved_context
        ])
        
        # Route to appropriate agent
        agent = route_agent(request.query)
        logger.info(f"Routed to agent: {agent.role}")
        
        # Execute agent with context
        response = agent.execute(
            request.query,
            context_text
        )
        
        return {
            "success": True,
            "query": request.query,
            "selected_agent": agent.role,
            "retrieved_context": retrieved_context,
            "response": response,
            "context_count": len(retrieved_context)
        }
        
    except Exception as e:
        logger.error(f"Agent query error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent query failed: {str(e)}"
        )

# ============================================================================
# Workflow Execution Endpoints
# ============================================================================

@app.post("/workflow/execute", tags=["Workflows"])
def workflow_execute(request: WorkflowRequest):
    """
    Execute a registered workflow.
    
    Validates the payload, executes the workflow with proper error handling,
    and returns structured execution results with logging.
    """
    try:
        logger.info(f"Executing workflow: {request.workflow_name}")
        
        # Validate payload
        is_valid, error_msg = validate_workflow_payload(
            request.workflow_name,
            request.payload
        )
        
        if not is_valid:
            logger.warning(f"Workflow validation failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Execute workflow
        result = execute_workflow(
            request.workflow_name,
            request.payload
        )
        
        # Determine HTTP status based on execution result
        http_status = status.HTTP_200_OK
        if result.get("status") == "error":
            http_status = status.HTTP_400_BAD_REQUEST
        elif result.get("status") == "failed":
            http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        logger.info(f"Workflow execution completed: {result.get('status')}")
        
        return {
            "success": result.get("status") == "completed",
            "execution": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow execution error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )