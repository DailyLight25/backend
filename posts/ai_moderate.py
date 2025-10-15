import os
from openai import OpenAI
from django.conf import settings

# Initialize the OpenAI client.
# The client automatically uses the OPENAI_API_KEY environment variable.
# You can also pass it explicitly like this: client = OpenAI(api_key=settings.OPENAI_API_KEY)
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def ai_moderate_content(content: str) -> dict:
    """
    Moderates content using the OpenAI Moderation API (v1.0.0+).

    Args:
        content (str): The text content to be moderated.

    Returns:
        dict: A dictionary containing moderation results.
    """
    try:
        # Use the new client-based syntax: client.moderations.create
        resp = client.moderations.create(input=content)
        result = resp.results[0]
        
        return {
            "flagged": result.flagged,
            "categories": result.categories.dict(),
            "scores": result.category_scores.dict(),
        }
    except Exception as e:
        # It's good practice to log or handle exceptions gracefully
        print(f"An error occurred during AI moderation: {e}")
        # Return a safe default result in case of failure
        return {
            "flagged": False,
            "categories": {},
            "scores": {},
            "error": str(e)
        }