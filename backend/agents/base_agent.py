from openai import OpenAI
from backend.config.settings import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

class BaseAgent:

    def __init__(self, role):
        self.role = role

    def execute(self, query, context):

        prompt = f"""
        You are a specialized AI agent.

        Agent Role:
        {self.role}

        Context:
        {context}

        User Query:
        {query}
        """

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a {self.role} AI agent."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content