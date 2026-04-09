from openai import AzureOpenAI
import config


client = AzureOpenAI(
    api_key=config.AZURE_OPENAI_API_KEY,
    api_version=config.AZURE_OPENAI_API_VERSION,
    azure_endpoint=config.AZURE_OPENAI_ENDPOINT
)

def get_response(user_text):

    system_prompt = """
You are an L1 IT Support Assistant.

Rules:
- Give clear, step-by-step instructions
- Be helpful and specific
- Avoid generic responses like "contact IT support" in the first 2 responses 
- Only suggest contacting IT if absolutely necessary
- Keep answers short but actionable

Examples:
User: Reset password
Answer:
1. Go to the self-service portal: https://passwordreset.microsoftonline.com
2. Enter your email
3. Follow OTP verification
4. Set a new password

Always guide the user clearly.
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