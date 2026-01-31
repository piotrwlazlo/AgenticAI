"""
Point B Skill - Goal Setting and Learning Path Definition

Gathers learning goals and preferences through natural conversation:
- Goal category (exam, travel, work, hobby, immigration, academic, family)
- Specific goal description
- Target CEFR level
- Timeline/deadline
- Success criteria (optional)
- Material preferences (optional)
- Preferred topics (optional)

This is a MULTI-TURN skill - it stays active across multiple messages
until core information (4 required fields) is collected.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from ._base import Skill


class PointBOutput(BaseModel):
    """
    Structured output for Point B goal setting.

    Fields can be None if not yet collected (multi-turn).
    LLM fills in fields as information becomes available through conversation.
    """

    # Core fields (4 required for completion)
    goal_category: Optional[str] = Field(
        default=None,
        description="Primary reason for learning. MUST be one of: exam, travel, work, hobby, immigration, academic, family. Extract from conversation even if not explicitly stated. Examples: 'I need it for my job' -> 'work', 'planning a trip' -> 'travel', 'want to pass IELTS' -> 'exam'. Leave null if not yet determined."
    )

    specific_goal: Optional[str] = Field(
        default=None,
        description="Concrete description of what student wants to achieve. 1-2 sentences maximum. Examples: 'Pass IELTS with 7.0 overall', 'Communicate confidently during 3-month trip to Spain', 'Present technical topics to international engineering teams'. Should be specific and actionable, not vague. Leave null if not yet discussed."
    )

    target_level: Optional[str] = Field(
        default=None,
        description="CEFR level student wants to reach. MUST be one of: A1, A2, B1, B2, C1, C2. Can be same as current level (consolidation) or higher (progression). Ask explicitly: 'What level do you want to reach?' If student unsure, suggest based on their goal. Leave null if not yet specified."
    )

    deadline: Optional[str] = Field(
        default=None,
        description="When student needs to achieve their goal. Accept natural language: '6 months', 'by June 2025', 'next year', 'no rush', 'as soon as possible'. Don't force rigid dates if student is flexible. Leave null if not yet mentioned."
    )

    # 5th CORE field (NOW REQUIRED for completion!)
    success_criteria: List[str] = Field(
        default_factory=list,
        description="Concrete outcomes that show goal is achieved. List of 1-3 specific criteria. Examples: ['Can give 30-minute technical presentation without notes', 'Can understand native speakers in movies'], ['Pass job interview', 'Write professional emails confidently']. Focus on observable behaviors, not feelings. REQUIRED for completion - must have at least 1 criterion."
    )

    # Optional fields (nice to have, but not required for completion)
    practice_focus: List[str] = Field(
        default_factory=list,
        description="Business/real-world situations student wants to practice. Options: 'meetings', 'presentations', 'emails', 'negotiations', 'small_talk', 'phone_calls', 'interviews'. Extract from context: 'I need to talk with clients' -> ['meetings', 'phone_calls'], 'present to teams' -> ['presentations']. These are REALISTIC scenarios we can simulate in text conversation. Empty list if not yet mentioned."
    )

    preferred_topics: List[str] = Field(
        default_factory=list,
        description="Content topics of interest. Examples: 'technology', 'business', 'finance', 'marketing', 'travel', 'culture', 'news', 'sports', 'science'. Extract from conversation: 'I work in tech' -> ['technology'], 'interested in finance' -> ['finance', 'business']. Empty list if not yet mentioned."
    )

    # Meta fields
    ai_response: str = Field(
        description="Your warm, conversational response to the student for THIS turn. Guide the conversation naturally toward collecting missing information. Ask about 1-2 fields at a time, don't overwhelm. Be encouraging and build on what they just said. Keep it 2-3 sentences maximum. ALWAYS fill this field even if no new data collected."
    )

    fields_collected: List[str] = Field(
        default_factory=list,
        description="List of SHORT field names you have collected SO FAR (including this turn). Use exact names: 'category', 'goal', 'target_level', 'deadline', 'success_criteria', 'practice_focus', 'topics'. Include fields from previous turns PLUS any new ones from current message. This accumulates across conversation turns."
    )

    is_complete: bool = Field(
        default=False,
        description="Set to true ONLY when ALL 5 CORE fields are collected: goal_category, specific_goal, target_level, deadline, success_criteria (must have at least 1 item). Other fields (practice_focus, preferred_topics) are optional. True means Point B is finished and ready to move to next skill."
    )


class PointBSkill(Skill):
    """
    Point B skill for goal setting and learning path definition.

    Multi-turn conversation to understand:
    - WHY student is learning (goal category)
    - WHAT exactly they want to achieve (specific goal)
    - HOW FAR they want to go (target level)
    - WHEN they need it (deadline)
    - HOW they'll know they succeeded (success criteria - NOW REQUIRED!)
    - WHAT situations to practice (practice_focus - optional)
    - WHAT interests them (preferred_topics - optional)

    Follows same multi-turn pattern as Point A.
    Collects 5 CORE fields (was 4, now success_criteria is required).
    """

    @property
    def name(self) -> str:
        return "point_b"

    @property
    def description(self) -> str:
        return "Point B - Goal setting and learning path definition (multi-turn)"

    @property
    def output_model(self) -> type[BaseModel]:
        return PointBOutput

    def get_prompt_template(self):
        """Load point_b.j2 template from same directory."""
        env = Environment(loader=FileSystemLoader(Path(__file__).parent))
        return env.get_template("point_b.j2")
