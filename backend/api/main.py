from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.retrieval.search_memory import search_memory
from backend.agents.agent_router import route_agent
from backend.workflows.workflow_engine import execute_workflow

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class WorkflowRequest(BaseModel):
    workflow_name: str
    payload: dict

@app.get("/")
def root():
    return {"status": "AI Operations API Running"}

@app.post("/agent/query")
def agent_query(request: QueryRequest):

    retrieved_context = search_memory(
        request.query,
        match_count=3
    )

    context_text = "\n\n".join([
        result.get('content', '') for result in retrieved_context
    ])

    agent = route_agent(request.query)

    response = agent.execute(
        request.query,
        context_text
    )

    return {
        "query": request.query,
        "selected_agent": agent.role,
        "retrieved_context": retrieved_context,
        "response": response
    }

@app.post("/workflow/execute")
def workflow_execute(request: WorkflowRequest):

    result = execute_workflow(
        request.workflow_name,
        request.payload
    )

    return result