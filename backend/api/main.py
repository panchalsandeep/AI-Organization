from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging

from backend.retrieval.search_memory import search_memory
from backend.agents.agent_router import route_agent
from backend.workflows.workflow_engine import execute_workflow
from backend.workflows.workflow_registry import validate_workflow_payload, list_workflows
from backend.multi_tenancy.tenant_router import TenantRouterMiddleware
from backend.multi_tenancy.tenant_service import create_tenant, get_tenant, list_tenants
from backend.multi_tenancy.tenant_context import get_tenant_id
from backend.auth.authentication import create_access_token, authenticate_credentials, require_permission, get_current_user
from backend.auth.role_service import create_role, assign_role_to_user, list_roles, get_permissions_for_user
from backend.audit.audit_queries import get_audit_events, get_compliance_events
from backend.audit.audit_logger import log_audit_event
from backend.audit.compliance_engine import record_compliance_event

from fastapi import WebSocket, WebSocketDisconnect
from backend.kpi.kpi_engine import create_kpi, list_kpis, log_kpi_metric, get_kpi_history
from backend.kpi.aggregation import aggregate_kpi_metrics
from backend.kpi.realtime_service import manager as kpi_manager
from backend.meeting_intelligence.transcription_service import transcribe_audio
from backend.meeting_intelligence.action_extractor import extract_action_items
from backend.meeting_intelligence.summary_generator import generate_meeting_summary
from backend.meeting_intelligence.models import create_meeting, get_meeting, list_meetings
from backend.collaboration.chat_service import chat_manager, save_chat_message, get_chat_history
from backend.collaboration.comment_service import create_comment, get_comments_for_resource

from backend.integrations.sync_manager import create_integration, list_integrations, test_integration_connection, trigger_sync, get_sync_logs
from backend.n8n_orchestrator.n8n_client import N8NClient
from backend.n8n_orchestrator.execution_monitor import get_execution_logs
from backend.copilot.copilot_engine import ask_copilot
from backend.decision_intelligence.decision_service import (
    create_decision,
    list_decisions,
    get_decision,
    update_decision,
    delete_decision
)
from backend.analytics.predictive_engine import (
    calculate_forecast,
    detect_anomalies
)
from backend.knowledge_base.wiki_service import (
    create_wiki_page,
    list_wiki_pages,
    get_wiki_page,
    update_wiki_page,
    delete_wiki_page,
    get_wiki_page_history,
    search_wiki_text
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Operations System API",
    description="Central API for AI-powered operational intelligence",
    version="1.0.0"
)

import os

allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://ai-organization.vercel.app",
]
env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    allowed_origins.extend([o.strip() for o in env_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex="https://ai-organization-.*\\.vercel\\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TenantRouterMiddleware)

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

class TenantCreateRequest(BaseModel):
    tenant_name: str = Field(..., description="Human-readable tenant name")
    organization_id: str = Field(..., description="Organization identifier for tenant grouping")

class RoleCreateRequest(BaseModel):
    role_name: str = Field(..., description="Name of the RBAC role")
    permissions: List[str] = Field(..., description="Permissions assigned to the role")

class RoleAssignmentRequest(BaseModel):
    role_id: str = Field(..., description="Role identifier to assign")
    user_id: str = Field(..., description="User identifier to assign the role")

class ComplianceEventCreateRequest(BaseModel):
    event_type: str = Field(..., description="Compliance event type")
    status: str = Field(..., description="Compliance event status")
    details: Dict[str, Any] = Field(..., description="Structured details for the compliance event")

class UserPermissionsResponse(BaseModel):
    user_id: str
    permissions: List[str]

class KPICreateRequest(BaseModel):
    name: str = Field(..., description="Name of the KPI")
    kpi_type: str = Field(..., description="Type of KPI ('number', 'percentage', 'currency')")
    formula: Optional[str] = Field(None, description="Optional calculation formula")
    target_value: Optional[float] = Field(None, description="Optional target value")

class KPIMetricLogRequest(BaseModel):
    kpi_id: str = Field(..., description="KPI identifier")
    value: float = Field(..., description="Value to log")

class MeetingCreateRequest(BaseModel):
    title: str = Field(..., description="Title of the meeting")
    audio_file_path: Optional[str] = Field(None, description="Path to the audio recording file")
    duration_seconds: int = Field(0, description="Meeting duration in seconds")

class CommentCreateRequest(BaseModel):
    resource_type: str = Field(..., description="Resource type comment belongs to")
    resource_id: str = Field(..., description="Resource ID")
    comment_text: str = Field(..., description="The comment content")
    parent_comment_id: Optional[str] = Field(None, description="Parent comment ID for threading")

class IntegrationCreateRequest(BaseModel):
    name: str = Field(..., description="Name of the integration")
    integration_type: str = Field(..., description="Integration type ('slack', 'notion', 'google_drive', 'github')")
    config: Dict[str, Any] = Field(..., description="JSON configuration payload")

class CopilotQueryRequest(BaseModel):
    query: str = Field(..., description="Query prompt text for the Copilot")

class WorkflowTriggerRequest(BaseModel):
    workflow_id: str = Field(..., description="N8N Workflow Identifier")
    payload: Dict[str, Any] = Field(..., description="Input variables payload")

class DecisionCreateRequest(BaseModel):
    title: str = Field(..., description="Title of the decision")
    description: str = Field(..., description="Detailed description of the decision")
    context: Optional[str] = Field(None, description="Background context or problem description")
    alternatives: List[str] = Field(default=[], description="List of alternatives considered")
    status: str = Field("proposed", description="Current status of the decision")
    estimated_impact: int = Field(..., description="Estimated impact rating (1-5)")

class DecisionUpdateRequest(BaseModel):
    title: str = Field(..., description="Title of the decision")
    description: str = Field(..., description="Detailed description of the decision")
    context: Optional[str] = Field(None, description="Background context or problem description")
    alternatives: List[str] = Field(default=[], description="List of alternatives considered")
    status: str = Field(..., description="Current status of the decision")
    estimated_impact: int = Field(..., description="Estimated impact rating (1-5)")
    actual_impact: Optional[int] = Field(None, description="Actual impact rating (1-5)")
    outcome: Optional[str] = Field(None, description="Final outcome details")

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

@app.post("/auth/token", tags=["Auth"])
def get_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Return a JWT access token for authenticated users."""
    credentials = authenticate_credentials(form_data.username, form_data.password)
    access_token = create_access_token(
        data={
            "sub": credentials["sub"],
            "permissions": credentials["permissions"]
        }
    )
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/admin/tenant", tags=["Admin"])
def create_tenant_endpoint(
    request: TenantCreateRequest,
    current_user: dict = Depends(require_permission("tenant:write"))
):
    """Create a new tenant for the AI Operations System."""
    tenant = create_tenant(
        name=request.tenant_name,
        organization_id=request.organization_id
    )
    log_audit_event(
        user_id=current_user["user_id"],
        action="tenant:create",
        resource_type="tenant",
        resource_id=tenant["id"],
        changes={"tenant_name": request.tenant_name, "organization_id": request.organization_id}
    )
    return {
        "success": True,
        "tenant": tenant
    }

@app.get("/admin/tenant/{tenant_id}", tags=["Admin"])
def get_tenant_endpoint(
    tenant_id: str,
    current_user: dict = Depends(require_permission("tenant:read"))
):
    """Retrieve tenant metadata."""
    tenant = get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    return {
        "success": True,
        "tenant": tenant
    }

@app.get("/admin/tenants", tags=["Admin"])
def list_tenants_endpoint(
    current_user: dict = Depends(require_permission("tenant:read"))
):
    """List all tenant records."""
    tenants = list_tenants()
    return {
        "success": True,
        "tenants": tenants,
        "count": len(tenants)
    }

@app.post("/admin/role", tags=["Admin"])
def create_role_endpoint(
    request: RoleCreateRequest,
    current_user: dict = Depends(require_permission("role:write"))
):
    """Create a new RBAC role."""
    tenant_id = get_tenant_id()
    role = create_role(
        tenant_id=tenant_id,
        name=request.role_name,
        permissions=request.permissions
    )
    log_audit_event(
        user_id=current_user["user_id"],
        action="role:create",
        resource_type="role",
        resource_id=role["id"],
        changes={"name": request.role_name, "permissions": request.permissions}
    )
    return {
        "success": True,
        "role": role
    }

@app.get("/admin/roles", tags=["Admin"])
def list_roles_endpoint(
    current_user: dict = Depends(require_permission("role:read"))
):
    """List roles for the current tenant."""
    tenant_id = get_tenant_id()
    roles = list_roles(tenant_id)
    return {
        "success": True,
        "roles": roles,
        "count": len(roles)
    }

@app.post("/admin/assign-role", tags=["Admin"])
def assign_role_endpoint(
    request: RoleAssignmentRequest,
    current_user: dict = Depends(require_permission("role:write"))
):
    """Assign a role to a user."""
    tenant_id = get_tenant_id()
    assignment = assign_role_to_user(
        user_id=request.user_id,
        role_id=request.role_id,
        tenant_id=tenant_id
    )
    log_audit_event(
        user_id=current_user["user_id"],
        action="role:assign",
        resource_type="user_role",
        resource_id=assignment["id"],
        changes={"user_id": request.user_id, "role_id": request.role_id}
    )
    return {
        "success": True,
        "assignment": assignment
    }

@app.get("/admin/user/{user_id}/permissions", tags=["Admin"])
def get_user_permissions_endpoint(
    user_id: str,
    current_user: dict = Depends(require_permission("role:read"))
):
    """Get effective permissions for a specific user."""
    tenant_id = get_tenant_id()
    permissions = get_permissions_for_user(user_id, tenant_id)
    return {
        "success": True,
        "user_id": user_id,
        "permissions": permissions
    }

@app.get("/admin/audit/events", tags=["Admin"])
def list_audit_events(
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(require_permission("audit:read"))
):
    """List recent audit events for the current tenant."""
    tenant_id = get_tenant_id()
    events = get_audit_events(tenant_id, limit=limit, offset=offset)
    return {
        "success": True,
        "events": [
            {
                "id": row[0],
                "user_id": row[1],
                "action": row[2],
                "resource_type": row[3],
                "resource_id": row[4],
                "changes": row[5],
                "ip_address": row[6],
                "metadata": row[7],
                "created_at": row[8].isoformat() if hasattr(row[8], "isoformat") else row[8]
            }
            for row in events
        ],
        "count": len(events)
    }

@app.get("/admin/compliance/events", tags=["Admin"])
def list_compliance_events(
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(require_permission("compliance:read"))
):
    """List recent compliance events for the current tenant."""
    tenant_id = get_tenant_id()
    events = get_compliance_events(tenant_id, limit=limit, offset=offset)
    return {
        "success": True,
        "events": [
            {
                "id": row[0],
                "event_type": row[1],
                "status": row[2],
                "details": row[3],
                "created_at": row[4].isoformat() if hasattr(row[4], "isoformat") else row[4]
            }
            for row in events
        ],
        "count": len(events)
    }

@app.post("/admin/compliance/event", tags=["Admin"])
def create_compliance_event(
    request: ComplianceEventCreateRequest,
    current_user: dict = Depends(require_permission("compliance:write"))
):
    """Record a compliance event for the current tenant."""
    record_compliance_event(
        event_type=request.event_type,
        status=request.status,
        details=request.details
    )
    log_audit_event(
        user_id=current_user["user_id"],
        action="compliance:event_recorded",
        resource_type="compliance_event",
        resource_id=request.event_type,
        changes={"status": request.status, "details": request.details}
    )
    return {
        "success": True,
        "message": "Compliance event recorded"
    }

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

# ============================================================================
# KPI Endpoints
# ============================================================================

@app.post("/kpi", tags=["KPIs"])
def create_kpi_endpoint(
    request: KPICreateRequest,
    current_user: dict = Depends(require_permission("kpi:write"))
):
    """Create a new KPI metric definition."""
    tenant_id = get_tenant_id()
    kpi = create_kpi(
        tenant_id=tenant_id,
        name=request.name,
        kpi_type=request.kpi_type,
        formula=request.formula,
        target_value=request.target_value
    )
    log_audit_event(
        user_id=current_user["user_id"],
        action="kpi:create",
        resource_type="kpi",
        resource_id=kpi["id"],
        changes={"name": request.name, "kpi_type": request.kpi_type, "target_value": request.target_value}
    )
    return {"success": True, "kpi": kpi}

@app.get("/kpis", tags=["KPIs"])
def list_kpis_endpoint(
    current_user: dict = Depends(require_permission("kpi:read"))
):
    """List all KPI metrics definitions for the tenant."""
    tenant_id = get_tenant_id()
    kpis = list_kpis(tenant_id)
    return {"success": True, "kpis": kpis, "count": len(kpis)}

@app.post("/kpi/metric", tags=["KPIs"])
async def log_kpi_metric_endpoint(
    request: KPIMetricLogRequest,
    current_user: dict = Depends(require_permission("kpi:write"))
):
    """Log a metric data point for a KPI and broadcast it to active dashboards."""
    tenant_id = get_tenant_id()
    result = log_kpi_metric(
        tenant_id=tenant_id,
        kpi_id=request.kpi_id,
        value=request.value
    )
    
    # Run anomaly check
    anomaly_flagged = False
    z_score = 0.0
    try:
        history = get_kpi_history(tenant_id, request.kpi_id, limit=50)
        anomalies = detect_anomalies(history, threshold=2.0)
        for anomaly in anomalies:
            if anomaly["id"] == result.get("id"):
                anomaly_flagged = True
                z_score = anomaly["z_score"]
                break
    except Exception as e:
        logger.error(f"Error checking anomalies on logging: {e}")
        
    if anomaly_flagged:
        log_audit_event(
            user_id=current_user["user_id"],
            action="kpi:anomaly",
            resource_type="kpi",
            resource_id=request.kpi_id,
            changes={"value": request.value, "z_score": z_score}
        )
    
    # Broadcast to real-time WebSockets
    await kpi_manager.broadcast_to_tenant(
        tenant_id=tenant_id,
        message={
            "event": "kpi_metric_logged",
            "kpi_id": request.kpi_id,
            "value": request.value,
            "alert_triggered": result["alert_triggered"],
            "anomaly_flagged": anomaly_flagged,
            "z_score": z_score
        }
    )
    
    return {"success": True, "metric": result}

@app.get("/kpi/{kpi_id}/history", tags=["KPIs"])
def get_kpi_history_endpoint(
    kpi_id: str,
    limit: int = 50,
    current_user: dict = Depends(require_permission("kpi:read"))
):
    """Retrieve historical values for a KPI."""
    tenant_id = get_tenant_id()
    history = get_kpi_history(tenant_id, kpi_id, limit=limit)
    return {"success": True, "history": history}

@app.get("/kpi/{kpi_id}/aggregation", tags=["KPIs"])
def get_kpi_aggregation(
    kpi_id: str,
    interval: str = "day",
    current_user: dict = Depends(require_permission("kpi:read"))
):
    """Retrieve time-series aggregated averages for a KPI."""
    tenant_id = get_tenant_id()
    aggregations = aggregate_kpi_metrics(tenant_id, kpi_id, interval=interval)
    return {"success": True, "aggregations": aggregations}

# ============================================================================
# Meeting Intelligence Endpoints
# ============================================================================

@app.post("/meeting", tags=["Meetings"])
def process_meeting_endpoint(
    request: MeetingCreateRequest,
    current_user: dict = Depends(require_permission("meeting:write"))
):
    """Transcribe an audio recording, extract actions, generate summaries, and save."""
    tenant_id = get_tenant_id()
    
    # Process transcription
    transcript_text = transcribe_audio(request.audio_file_path or "")
    
    # Generate reports
    summary = generate_meeting_summary(transcript_text)
    action_items = extract_action_items(transcript_text)
    
    meeting = create_meeting(
        tenant_id=tenant_id,
        title=request.title,
        duration_seconds=request.duration_seconds,
        transcript_text=transcript_text,
        summary=summary,
        action_items=action_items,
        audio_url=request.audio_file_path
    )
    
    log_audit_event(
        user_id=current_user["user_id"],
        action="meeting:process",
        resource_type="meeting",
        resource_id=meeting["id"],
        changes={"title": request.title}
    )
    
    return {"success": True, "meeting": meeting}

@app.get("/meeting/{meeting_id}", tags=["Meetings"])
def get_meeting_endpoint(
    meeting_id: str,
    current_user: dict = Depends(require_permission("meeting:read"))
):
    """Retrieve detailed meeting summary and transcript."""
    meeting = get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"success": True, "meeting": meeting}

@app.get("/meetings", tags=["Meetings"])
def list_meetings_endpoint(
    current_user: dict = Depends(require_permission("meeting:read"))
):
    """List all processed meetings."""
    tenant_id = get_tenant_id()
    meetings = list_meetings(tenant_id)
    return {"success": True, "meetings": meetings, "count": len(meetings)}

# ============================================================================
# Collaboration & Threaded Comments Endpoints
# ============================================================================

@app.post("/comment", tags=["Collaboration"])
def create_comment_endpoint(
    request: CommentCreateRequest,
    current_user: dict = Depends(require_permission("user:write"))
):
    """Post a new comment or reply to an existing one."""
    tenant_id = get_tenant_id()
    
    # Retrieve user details from context
    sender_id = current_user["user_id"]
    sender_name = current_user.get("username", "System User")
    
    comment = create_comment(
        tenant_id=tenant_id,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        sender_id=sender_id,
        sender_name=sender_name,
        comment_text=request.comment_text,
        parent_comment_id=request.parent_comment_id
    )
    
    return {"success": True, "comment": comment}

@app.get("/comments/{resource_type}/{resource_id}", tags=["Collaboration"])
def list_comments_endpoint(
    resource_type: str,
    resource_id: str,
    current_user: dict = Depends(require_permission("user:read"))
):
    """List comments and discussions on a specific card/KPI."""
    tenant_id = get_tenant_id()
    comments = get_comments_for_resource(tenant_id, resource_type, resource_id)
    return {"success": True, "comments": comments, "count": len(comments)}

# ============================================================================
# WebSockets Real-Time Handlers
# ============================================================================

@app.websocket("/ws/kpi/{tenant_id}")
async def ws_kpi_endpoint(websocket: WebSocket, tenant_id: str):
    """Real-time metrics updates WebSocket endpoint."""
    await kpi_manager.connect(websocket, tenant_id)
    try:
        while True:
            # Keep connection open and listen for client heartbeats/messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        kpi_manager.disconnect(websocket, tenant_id)

@app.websocket("/ws/chat/{tenant_id}/{room_id}")
async def ws_chat_endpoint(websocket: WebSocket, tenant_id: str, room_id: str, sender_id: str, sender_name: str):
    """Real-time chat messaging WebSocket room."""
    await chat_manager.connect(websocket, tenant_id, room_id)
    
    # Broadcast join message
    await chat_manager.broadcast_to_room(
        tenant_id=tenant_id,
        room_id=room_id,
        message={"event": "user_joined", "sender_name": sender_name, "sender_id": sender_id}
    )
    
    try:
        while True:
            text = await websocket.receive_text()
            # Save message history
            msg = save_chat_message(
                tenant_id=tenant_id,
                room_id=room_id,
                sender_id=sender_id,
                sender_name=sender_name,
                message_text=text
            )
            # Broadcast to room
            await chat_manager.broadcast_to_room(
                tenant_id=tenant_id,
                room_id=room_id,
                message={
                    "event": "new_message",
                    "id": msg["id"],
                    "sender_id": sender_id,
                    "sender_name": sender_name,
                    "message_text": text
                }
            )
    except WebSocketDisconnect:
        chat_manager.disconnect(websocket, tenant_id, room_id)
        await chat_manager.broadcast_to_room(
            tenant_id=tenant_id,
            room_id=room_id,
            message={"event": "user_left", "sender_name": sender_name, "sender_id": sender_id}
        )

@app.get("/chat/{room_id}/history", tags=["Collaboration"])
def get_chat_history_endpoint(
    room_id: str,
    limit: int = 50,
    current_user: dict = Depends(require_permission("user:read"))
):
    """Get scrollback history for a chat room."""
    tenant_id = get_tenant_id()
    history = get_chat_history(tenant_id, room_id, limit=limit)
    return {"success": True, "history": history}

# ============================================================================
# Integrations Endpoints (Sprint 3)
# ============================================================================

@app.post("/integration", tags=["Integrations"])
def create_integration_endpoint(
    request: IntegrationCreateRequest,
    current_user: dict = Depends(require_permission("integration:write"))
):
    """Add a new third-party connector integration."""
    tenant_id = get_tenant_id()
    integration = create_integration(
        tenant_id=tenant_id,
        name=request.name,
        integration_type=request.integration_type,
        config=request.config
    )
    log_audit_event(
        user_id=current_user["user_id"],
        action="integration:create",
        resource_type="integration",
        resource_id=integration["id"],
        changes={"name": request.name, "integration_type": request.integration_type}
    )
    return {"success": True, "integration": integration}

@app.get("/integrations", tags=["Integrations"])
def list_integrations_endpoint(
    current_user: dict = Depends(require_permission("integration:read"))
):
    """List all third-party integrations configured for the tenant."""
    tenant_id = get_tenant_id()
    integrations = list_integrations(tenant_id)
    return {"success": True, "integrations": integrations, "count": len(integrations)}

@app.post("/integration/{integration_id}/test", tags=["Integrations"])
def test_integration_connection_endpoint(
    integration_id: str,
    current_user: dict = Depends(require_permission("integration:write"))
):
    """Verify integration configuration connection status."""
    tenant_id = get_tenant_id()
    try:
        is_ok = test_integration_connection(tenant_id, integration_id)
        return {"success": True, "connected": is_ok}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/integration/{integration_id}/sync", tags=["Integrations"])
def trigger_integration_sync_endpoint(
    integration_id: str,
    current_user: dict = Depends(require_permission("integration:write"))
):
    """Trigger a manual sync of integration data."""
    tenant_id = get_tenant_id()
    try:
        result = trigger_sync(tenant_id, integration_id)
        log_audit_event(
            user_id=current_user["user_id"],
            action="integration:sync",
            resource_type="integration",
            resource_id=integration_id,
            changes={"result": result}
        )
        return {"success": True, "sync": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/integration/{integration_id}/sync-logs", tags=["Integrations"])
def get_integration_sync_logs_endpoint(
    integration_id: str,
    limit: int = 50,
    current_user: dict = Depends(require_permission("integration:read"))
):
    """Get history sync logs for a configured integration."""
    tenant_id = get_tenant_id()
    logs = get_sync_logs(tenant_id, integration_id, limit=limit)
    return {"success": True, "logs": logs, "count": len(logs)}

# ============================================================================
# n8n Orchestrator Endpoints (Sprint 3)
# ============================================================================

@app.get("/automation/n8n/workflows", tags=["Automation"])
def list_n8n_workflows_endpoint(
    current_user: dict = Depends(require_permission("workflow:manage"))
):
    """List active workflows inside the n8n orchestrator."""
    # Instantiates a client targeting configured N8N instance
    client = N8NClient()
    workflows = client.list_workflows()
    return {"success": True, "workflows": workflows, "count": len(workflows)}

@app.post("/automation/n8n/trigger", tags=["Automation"])
def trigger_n8n_workflow_endpoint(
    request: WorkflowTriggerRequest,
    current_user: dict = Depends(require_permission("workflow:execute"))
):
    """Trigger execution of an n8n webhook workflow."""
    client = N8NClient()
    result = client.trigger_workflow(request.workflow_id, request.payload)
    return {"success": True, "result": result}

@app.get("/automation/n8n/{workflow_id}/logs", tags=["Automation"])
def get_n8n_execution_logs_endpoint(
    workflow_id: str,
    current_user: dict = Depends(require_permission("workflow:manage"))
):
    """Get run execution logs for a specific n8n workflow."""
    logs = get_execution_logs(workflow_id)
    return {"success": True, "logs": logs, "count": len(logs)}

# ============================================================================
# AI Copilot Endpoints (Sprint 3)
# ============================================================================

@app.post("/copilot/ask", tags=["Copilot"])
def ask_copilot_endpoint(
    request: CopilotQueryRequest,
    current_user: dict = Depends(require_permission("user:read"))
):
    """Query the AI Copilot to get context answers or execute suggested actions."""
    tenant_id = get_tenant_id()
    username = current_user.get("username", "Team Member")
    result = ask_copilot(request.query, tenant_id, username)
    return {"success": True, "result": result}

# ============================================================================
# Decision Intelligence Endpoints (Sprint 3 Extension)
# ============================================================================

@app.post("/decision", tags=["Decision Intelligence"])
def create_decision_endpoint(
    request: DecisionCreateRequest,
    current_user: dict = Depends(require_permission("decision:write"))
):
    """Log a new operational decision."""
    tenant_id = get_tenant_id()
    username = current_user.get("username", "Team Member")
    decision = create_decision(
        tenant_id=tenant_id,
        title=request.title,
        description=request.description,
        context=request.context,
        alternatives=request.alternatives,
        status=request.status,
        estimated_impact=request.estimated_impact,
        created_by=username
    )
    log_audit_event(
        user_id=current_user["user_id"],
        action="decision:create",
        resource_type="decision",
        resource_id=decision["id"],
        changes={"title": request.title, "estimated_impact": request.estimated_impact}
    )
    return {"success": True, "decision": decision}

@app.get("/decisions", tags=["Decision Intelligence"])
def list_decisions_endpoint(
    current_user: dict = Depends(require_permission("decision:read"))
):
    """List all decisions logged for the active tenant."""
    tenant_id = get_tenant_id()
    decisions = list_decisions(tenant_id)
    return {"success": True, "decisions": decisions, "count": len(decisions)}

@app.get("/decision/{decision_id}", tags=["Decision Intelligence"])
def get_decision_endpoint(
    decision_id: str,
    current_user: dict = Depends(require_permission("decision:read"))
):
    """Get details of a specific logged decision."""
    tenant_id = get_tenant_id()
    decision = get_decision(tenant_id, decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return {"success": True, "decision": decision}

@app.put("/decision/{decision_id}", tags=["Decision Intelligence"])
def update_decision_endpoint(
    decision_id: str,
    request: DecisionUpdateRequest,
    current_user: dict = Depends(require_permission("decision:write"))
):
    """Update a decision status, details, or outcome evaluations."""
    tenant_id = get_tenant_id()
    decision = update_decision(
        tenant_id=tenant_id,
        decision_id=decision_id,
        title=request.title,
        description=request.description,
        context=request.context,
        alternatives=request.alternatives,
        status=request.status,
        estimated_impact=request.estimated_impact,
        actual_impact=request.actual_impact,
        outcome=request.outcome
    )
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    log_audit_event(
        user_id=current_user["user_id"],
        action="decision:update",
        resource_type="decision",
        resource_id=decision_id,
        changes={"status": request.status, "actual_impact": request.actual_impact}
    )
    return {"success": True, "decision": decision}

@app.delete("/decision/{decision_id}", tags=["Decision Intelligence"])
def delete_decision_endpoint(
    decision_id: str,
    current_user: dict = Depends(require_permission("decision:write"))
):
    """Delete a logged decision."""
    tenant_id = get_tenant_id()
    success = delete_decision(tenant_id, decision_id)
    if not success:
        raise HTTPException(status_code=404, detail="Decision not found")
    log_audit_event(
        user_id=current_user["user_id"],
        action="decision:delete",
        resource_type="decision",
        resource_id=decision_id,
        changes={}
    )
    return {"success": True}

# ============================================================================
# Knowledge Base & Wiki Endpoints
# ============================================================================

class WikiCreateRequest(BaseModel):
    title: str = Field(..., description="Title of the wiki page")
    slug: Optional[str] = Field(None, description="Custom URL slug for the wiki page")
    content: str = Field(..., description="Markdown or text content of the wiki page")
    tags: List[str] = Field(default=[], description="List of tags associated with the page")

class WikiUpdateRequest(BaseModel):
    title: str = Field(..., description="Title of the wiki page")
    slug: Optional[str] = Field(None, description="Custom URL slug for the wiki page")
    content: str = Field(..., description="Markdown or text content of the wiki page")
    tags: List[str] = Field(default=[], description="List of tags associated with the page")

@app.post("/wiki", tags=["Knowledge Base & Wiki"])
def create_wiki_endpoint(
    request: WikiCreateRequest,
    current_user: dict = Depends(require_permission("wiki:write"))
):
    """Create a new wiki page."""
    tenant_id = get_tenant_id()
    page = create_wiki_page(
        tenant_id=tenant_id,
        title=request.title,
        slug=request.slug,
        content=request.content,
        tags=request.tags,
        created_by=current_user.get("username", "system")
    )
    log_audit_event(
        user_id=current_user["user_id"],
        action="wiki:create",
        resource_type="wiki_page",
        resource_id=page["id"],
        changes={"title": page["title"], "slug": page["slug"]}
    )
    return {"success": True, "page": page}

@app.get("/wiki/pages", tags=["Knowledge Base & Wiki"])
def list_wiki_endpoint(
    current_user: dict = Depends(require_permission("wiki:read"))
):
    """List all wiki pages for the active tenant."""
    tenant_id = get_tenant_id()
    pages = list_wiki_pages(tenant_id)
    return {"success": True, "pages": pages, "count": len(pages)}

@app.get("/wiki/page/{page_id_or_slug}", tags=["Knowledge Base & Wiki"])
def get_wiki_endpoint(
    page_id_or_slug: str,
    current_user: dict = Depends(require_permission("wiki:read"))
):
    """Get a specific wiki page."""
    tenant_id = get_tenant_id()
    page = get_wiki_page(tenant_id, page_id_or_slug)
    if not page:
        raise HTTPException(status_code=404, detail="Wiki page not found")
    return {"success": True, "page": page}

@app.put("/wiki/page/{page_id}", tags=["Knowledge Base & Wiki"])
def update_wiki_endpoint(
    page_id: str,
    request: WikiUpdateRequest,
    current_user: dict = Depends(require_permission("wiki:write"))
):
    """Update a wiki page and increment its version."""
    tenant_id = get_tenant_id()
    page = update_wiki_page(
        tenant_id=tenant_id,
        page_id=page_id,
        title=request.title,
        slug=request.slug,
        content=request.content,
        tags=request.tags,
        updated_by=current_user.get("username", "system")
    )
    if not page:
        raise HTTPException(status_code=404, detail="Wiki page not found")
    log_audit_event(
        user_id=current_user["user_id"],
        action="wiki:update",
        resource_type="wiki_page",
        resource_id=page_id,
        changes={"version": page["version"]}
    )
    return {"success": True, "page": page}

@app.delete("/wiki/page/{page_id}", tags=["Knowledge Base & Wiki"])
def delete_wiki_endpoint(
    page_id: str,
    current_user: dict = Depends(require_permission("wiki:write"))
):
    """Delete a wiki page."""
    tenant_id = get_tenant_id()
    success = delete_wiki_page(tenant_id, page_id)
    if not success:
        raise HTTPException(status_code=404, detail="Wiki page not found")
    log_audit_event(
        user_id=current_user["user_id"],
        action="wiki:delete",
        resource_type="wiki_page",
        resource_id=page_id,
        changes={}
    )
    return {"success": True}

@app.get("/wiki/page/{page_id}/history", tags=["Knowledge Base & Wiki"])
def get_wiki_history_endpoint(
    page_id: str,
    current_user: dict = Depends(require_permission("wiki:read"))
):
    """Get edit history/snapshots of a wiki page."""
    tenant_id = get_tenant_id()
    history = get_wiki_page_history(tenant_id, page_id)
    return {"success": True, "history": history}

@app.get("/wiki/search", tags=["Knowledge Base & Wiki"])
def search_wiki_endpoint(
    q: str,
    current_user: dict = Depends(require_permission("wiki:read"))
):
    """Search wiki pages by text matching and query vector recommendations."""
    tenant_id = get_tenant_id()
    text_results = search_wiki_text(tenant_id, q)
    
    # Hooks to vector search similarity memory recommendations
    vector_recommendations = []
    try:
        raw_recommendations = search_memory(q, match_count=5)
        # Filter for wiki type pages belonging to this tenant context
        for item in raw_recommendations:
            metadata = item.get("metadata") or {}
            # Ensure it is a wiki page and has matching tenant id context
            if (item.get("content_type") == "wiki" or metadata.get("wiki_page_id")) and metadata.get("tenant_id") == tenant_id:
                # Add item
                vector_recommendations.append({
                    "title": item.get("title"),
                    "wiki_page_id": metadata.get("wiki_page_id"),
                    "similarity": item.get("similarity", 0.0)
                })
    except Exception as e:
        # Fail gracefully
        print(f"Error fetching vector memory similarities: {e}")
        
    return {
        "success": True,
        "results": text_results,
        "recommendations": vector_recommendations
    }

# ============================================================================
# Predictive Analytics Endpoints
# ============================================================================

@app.get("/kpi/{kpi_id}/forecast", tags=["Predictive Analytics"])
def get_kpi_forecast_endpoint(
    kpi_id: str,
    steps: int = 5,
    current_user: dict = Depends(require_permission("kpi:read"))
):
    """Generate time-series predictions and confidence bounds for a KPI."""
    tenant_id = get_tenant_id()
    history = get_kpi_history(tenant_id, kpi_id, limit=100)
    forecast = calculate_forecast(history, steps=steps)
    return {"success": True, "forecast": forecast}

@app.get("/kpi/{kpi_id}/anomalies", tags=["Predictive Analytics"])
def get_kpi_anomalies_endpoint(
    kpi_id: str,
    threshold: float = 2.0,
    current_user: dict = Depends(require_permission("kpi:read"))
):
    """Detect anomalous values in KPI historical data using Z-score thresholding."""
    tenant_id = get_tenant_id()
    history = get_kpi_history(tenant_id, kpi_id, limit=100)
    anomalies = detect_anomalies(history, threshold=threshold)
    return {"success": True, "anomalies": anomalies}