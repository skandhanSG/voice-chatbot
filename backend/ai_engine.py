from openai import AzureOpenAI
from backend import config

client = AzureOpenAI(
    api_key=config.AZURE_OPENAI_API_KEY,
    api_version=config.AZURE_OPENAI_API_VERSION,
    azure_endpoint=config.AZURE_OPENAI_ENDPOINT
)

def get_response(user_text):

    system_prompt = """
You are an L1 IT Support Assistant.

Rules:
- Answer only IT support queries
- Be short and clear
- If user asks for a specific language, respond in that language
- If unknown, say: Contact IT support - support@domain.com
"""

    response = client.chat.completions.create(
        model=config.AZURE_OPENAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content