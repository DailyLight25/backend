import os
import openai
from django.conf import settings

openai.api_key = os.getenv("OPENAI_API_KEY", settings.OPENAI_API_KEY)

def ai_moderate_content(content: str) -> dict:
    resp = openai.Moderation.create(input=content)
    result = resp["results"][0]
    return {
        "flagged": result["flagged"],
        "categories": result["categories"],
        "scores": result["category_scores"],
    }
