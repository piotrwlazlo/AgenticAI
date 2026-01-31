import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MODEL_NAME = "gpt-4o-mini" #model as config

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
    MEMORY_DIR = os.path.join(BASE_DIR, "memory")

    # Persistence configuration
    PERSISTENCE_BACKEND = "in_memory"  # Options: "in_memory", "redis" (future)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")  # For future use
