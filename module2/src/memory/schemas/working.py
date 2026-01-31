from enum import Enum
from pydantic import BaseModel, Field

# --- STAN SESJI ---
class SessionPhase(str, Enum):
    HOMEWORK_CHECK = "HOMEWORK_CHECK"
    TOPIC_INTRODUCTION = "TOPIC_INTRODUCTION"
    PRACTICE_MODE = "PRACTICE_MODE"
    FEEDBACK_WRAPUP = "FEEDBACK_WRAPUP"

class SessionState(BaseModel):
    """
    Working Memory - tracks what we're doing right now in the current session.
    """
    topic: str
    phase: SessionPhase = SessionPhase.PRACTICE_MODE

# --- STRUKTURA ODPOWIEDZI LLM (Structured Output) ---
class TutorResponse(BaseModel):
    thinking: str = Field(
        ...,
        description="Internal reasoning process before responding. Explain your thought process: what you noticed in the student's message, what learning opportunity you see, and why you chose this particular response approach. Be specific and analytical."
    )
    ai_answer: str = Field(
        ...,
        description="Your complete response message to the student. This is what the student will see and read. Write naturally, warmly, and conversationally as a language coach. Include any questions, explanations, corrections, or encouragement appropriate for this moment in the conversation."
    )
