"""
Point A Skill - Starting Point Assessment

Gathers essential information about the student through natural conversation:
- Name
- Native language
- Target language
- Current proficiency level (CEFR)
- Years spent learning
- Previous learning experience

This is a MULTI-TURN skill - it stays active across multiple messages
until all required information is collected.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from jinja2 import Environment, FileSystemLoader, Template
from pathlib import Path
from ._base import Skill


class PointAOutput(BaseModel):
    """
    Structured output for Point A assessment.

    Fields can be None if not yet collected (multi-turn).
    LLM fills in fields as information becomes available through conversation.
    """

    # Student information fields
    student_name: Optional[str] = Field(
        default=None,
        description="The student's first name or preferred name. Extract from conversation even if informally given (e.g., 'I'm John' or 'call me Alice'). Leave null if not yet mentioned. Do not ask repeatedly if already collected."
    )

    native_language: Optional[str] = Field(
        default=None,
        description="The language the student grew up speaking or is most fluent in. Use standard language names in English (e.g., 'Polish', 'Spanish', 'Mandarin Chinese'). Infer from context clues like 'I'm from Poland' -> 'Polish'. Leave null if not yet determined."
    )

    target_language: Optional[str] = Field(
        default=None,
        description="The language the student wants to improve or learn. Use standard language names in English (e.g., 'English', 'French', 'Japanese'). This should be clearly stated by the student. Leave null if not yet specified."
    )

    current_level: Optional[str] = Field(
        default=None,
        description="The student's self-assessed proficiency level in the target language using CEFR scale. MUST be one of: A1, A2, B1, B2, C1, or C2. If student says 'beginner', map to A1-A2 range and ask for clarification. If 'intermediate', map to B1-B2. If 'advanced', map to C1-C2. Accept self-assessment without challenging. Leave null if not yet discussed."
    )

    years_learning: Optional[int] = Field(
        default=None,
        description="Approximate number of years the student has been learning the target language. Round to nearest year (e.g., '6 months' -> 1, '2.5 years' -> 2). Accept rough estimates like 'a few years' -> 3. Leave null if not yet mentioned. This helps gauge learning trajectory."
    )

    previous_experience: Optional[str] = Field(
        default=None,
        description="Concise summary of HOW the student has been learning so far. Include methods mentioned: apps (Duolingo, Babbel), formal classes (school, university, private), immersion (lived abroad, native speakers), self-study (books, YouTube, podcasts), tutors, etc. Capture 1-3 key methods in a brief phrase (e.g., '2 years Duolingo + school classes' or 'self-study with YouTube and books'). Leave null if not yet discussed."
    )

    learning_motivation: Optional[str] = Field(
        default=None,
        description="The student's primary reason or motivation for learning the target language. Common motivations include: career/work requirements, travel/tourism, academic studies, communication with family/friends, personal interest/hobby, relocation to a new country, or cultural exploration. Capture the main driver in a brief phrase (e.g., 'career - needs English for job', 'travel to Japan next year', 'communicate with Spanish-speaking family'). This helps tailor the learning approach. Leave null if not yet discussed."
    )

    # Meta fields for conversation flow
    ai_response: str = Field(
        description="Your warm, conversational response to the student for THIS turn. Acknowledge what they just said, then ask about the next missing field(s) naturally. Keep it short (2-3 sentences max). Ask 1-2 questions at a time, never all at once. Be encouraging and friendly. ALWAYS fill this field - it's what the student will see."
    )

    fields_collected: List[str] = Field(
        default_factory=list,
        description="List of short field names you have collected SO FAR across all conversation turns (cumulative, not just this turn). Use exact names: 'name', 'native_lang', 'target_lang', 'level', 'years_learning', 'previous_experience', 'motivation'. Include previously collected fields from context PLUS any new ones from this message. Example: if you already had ['name', 'native_lang'] and now got target language, return ['name', 'native_lang', 'target_lang']."
    )

    is_complete: bool = Field(
        default=False,
        description="Set to true ONLY when ALL 7 fields are collected: name, native_lang, target_lang, level, years_learning, previous_experience, motivation. If even one field is still null, this MUST be false. This signals that Point A assessment is finished and the system can move to the next phase."
    )

    def get_collected_field_names(self) -> List[str]:
        """
        Return names of fields that have been collected (not None).

        Returns:
            List of field names like ['name', 'native_language', 'level']
        """
        collected = []
        field_map = {
            'student_name': 'name',
            'native_language': 'native_lang',
            'target_language': 'target_lang',
            'current_level': 'level',
            'years_learning': 'years_learning',
            'previous_experience': 'previous_experience',
            'learning_motivation': 'motivation'
        }

        for field_name, short_name in field_map.items():
            value = getattr(self, field_name, None)
            if value is not None:
                collected.append(short_name)

        return collected

    def get_missing_fields(self) -> List[str]:
        """
        Return names of fields that still need to be collected.

        Returns:
            List of field names that are None
        """
        all_fields = ['name', 'native_lang', 'target_lang', 'level', 'years_learning', 'previous_experience', 'motivation']
        collected = self.get_collected_field_names()
        return [f for f in all_fields if f not in collected]


class PointASkill(Skill):
    """
    Point A skill implementation.

    Conducts natural conversation to gather student's starting point information.
    Handles multi-turn interaction gracefully.
    """

    @property
    def name(self) -> str:
        return "point_a"

    @property
    def description(self) -> str:
        return "Assess student's starting point: name, languages, level, and learning experience"

    @property
    def output_model(self) -> type[BaseModel]:
        return PointAOutput

    def get_prompt_template(self) -> Template:
        """Load point_a.j2 template from same directory."""
        env = Environment(loader=FileSystemLoader(Path(__file__).parent))
        return env.get_template("point_a.j2")
