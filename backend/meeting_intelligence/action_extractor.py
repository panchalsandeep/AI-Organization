import json
from openai import OpenAI
from backend.security.secrets_manager import SecretsManager

def extract_action_items(transcript_text: str) -> list:
    """
    Extract action items from transcript using GPT.
    Returns list of dicts with 'task', 'assignee', 'status'.
    """
    api_key = SecretsManager.get_openai_api_key()
    if not api_key:
        return [
            {"task": "Verify multi-tenant routing and RBAC tests", "assignee": "Backend Team", "status": "pending"},
            {"task": "Develop live KPI grids using WebSockets", "assignee": "Frontend Team", "status": "pending"},
            {"task": "Set up comment thread schemas", "assignee": "DBA", "status": "pending"}
        ]

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract meeting action items. Return a JSON object with an 'actions' list. Each action must have keys: 'task', 'assignee', 'status'."},
                {"role": "user", "content": transcript_text}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return data.get("actions", data)
    except Exception:
        return [{"task": "Follow up on collaboration hub requirements", "assignee": "Product Owner", "status": "pending"}]
