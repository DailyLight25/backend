import google.generativeai as genai
from django.conf import settings

# Configuration of Gemini with the API key
genai.configure(api_key=settings.GEMINI_API_KEY)

# Initializing the Gemini model
model = genai.GenerativeModel("gemini-pro")

def ai_moderate_content(content: str) -> dict:
    """
    Simulates content moderation using Gemini by prompting the model to evaluate safety.

    Args:
        content (str): The text content to be evaluated.

    Returns:
        dict: A dictionary containing moderation feedback.
    """
    try:
        prompt = (
            "You are a content moderation assistant. "
            "Analyze the following text and return whether it is flagged, "
            "and list any concerning categories (e.g., hate speech, violence, adult content). "
            "Respond in JSON format with keys: flagged (true/false), categories (list), and notes (string).\n\n"
            f"Content:\n{content}"
        )

        response = model.generate_content(prompt)
        moderation = response.text.strip()

        # Optional: parse the JSON if Gemini returns structured output
        import json
        try:
            return json.loads(moderation)
        except json.JSONDecodeError:
            return {
                "flagged": False,
                "categories": [],
                "notes": "Could not parse Gemini response.",
                "raw_response": moderation
            }

    except Exception as e:
        print(f"Gemini moderation error: {e}")
        return {
            "flagged": False,
            "categories": [],
            "notes": "Error during moderation.",
            "error": str(e)
        }