from backend.agents.strategy_agent import strategy_agent
from backend.agents.operations_agent import operations_agent
from backend.agents.analytics_agent import analytics_agent

def route_agent(query):

    query_lower = query.lower()

    if "strategy" in query_lower:
        return strategy_agent

    elif "operations" in query_lower:
        return operations_agent

    elif "analytics" in query_lower:
        return analytics_agent

    return operations_agent