import json
from typing import Dict, Any
from openai import OpenAI
from backend.security.secrets_manager import SecretsManager
from backend.copilot.context_manager import assemble_tenant_copilot_context
from backend.retrieval.search_memory import search_memory

def ask_copilot(query_text: str, tenant_id: str, username: str) -> Dict[str, Any]:
    """
    Execute a query using the AI Copilot.
    Combines DB status context and semantic memory.
    """
    context = assemble_tenant_copilot_context(tenant_id)
    
    # Retrieve memories
    memories = []
    try:
        memories = search_memory(query_text, match_count=2)
    except Exception:
        pass
        
    api_key = SecretsManager.get_openai_api_key()
    if not api_key:
        response_text = f"Hi {username}! Your active tenant is '{tenant_id}'. "
        query_lower = query_text.lower()
        if "sync" in query_lower or "integration" in query_lower:
            response_text += f"You have {len(context['active_integrations'])} active integrations. I can trigger a sync job on them."
        elif "kpi" in query_lower or "metric" in query_lower:
            response_text += f"I see you have {context['kpi_count']} KPI metrics configured: {', '.join(context['kpis_list'][:3]) or 'none'}."
        else:
            response_text += "How can I help you manage your AI Operations workspace today?"
            
        return {
            "response": response_text,
            "suggested_action": None,
            "context": context
        }

    try:
        client = OpenAI(api_key=api_key)
        system_prompt = (
            f"You are the AI Operations Copilot assisting {username}.\n"
            f"Active Tenant Context: {json.dumps(context)}\n"
            f"Relevant memories: {json.dumps(memories)}\n"
            "Provide helpful workspace guidance. If the user wants to sync files, suggest an action "
            "by returning JSON with: 'response' (text) and 'suggested_action' (dict with 'action' type like 'sync')."
        )
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query_text}
            ]
        )
        text = response.choices[0].message.content.strip()
        try:
            parsed = json.loads(text)
            if "response" in parsed:
                return parsed
        except Exception:
            pass
        return {"response": text, "suggested_action": None, "context": context}
        
    except Exception as e:
        return {"response": f"Error: {str(e)}", "suggested_action": None}
