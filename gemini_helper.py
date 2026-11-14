import os
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

# Load GEMINI_API_KEY from your .env file
load_dotenv()

# Initialize the official Google Gen AI client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Try your preferred model first, then fall back to lighter models if servers are busy
MODELS_TO_TRY = [
    "gemini-3.8-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]

def get_game_commentary(score: int) -> str:
    """Generates a quick AI comment based on the player's Snake score."""
    prompt = f"Give a short, witty one-sentence reaction to someone scoring {score} points in Snake."

    for model_name in MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text
        except APIError as e:
            # 503 = High demand / overloaded, 429 = Rate limit, 404 = Not available
            if e.code in (503, 429, 404):
                print(f"[{model_name} busy ({e.code}), switching to backup model...]")
                continue
            raise

    # Ultimate fallback so your Snake game never crashes even if offline
    return f"{score} points! Not bad for a reptile with no legs."

# Quick test when running this file directly
if __name__ == "__main__":
    print(get_game_commentary(12))