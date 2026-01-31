from functools import lru_cache
import instructor
from openai import OpenAI
from config import Config

@lru_cache()
def get_client():
    """
    Returns a configured OpenAI client with the Instructor patch.
    Thanks to @lru_cache, the client is created only once (singleton).
    """
    if not Config.OPENAI_API_KEY:
        raise ValueError("❌ Brak klucza API w konfiguracji!")

    client = OpenAI(
        base_url = "https://llm-api.dataworkshop.eu",
        api_key=Config.OPENAI_API_KEY
    )
    

    return instructor.patch(client, mode=instructor.Mode.MD_JSON)
