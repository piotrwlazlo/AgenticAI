"""
Skill Base Class

Abstract base class for all skills (procedural memory).
Skills are DECLARATIVE - they define WHAT to do, not HOW to execute.
"""

from abc import ABC, abstractmethod
from pydantic import BaseModel
from jinja2 import Template


class Skill(ABC):
    """
    Base class for all skills.

    A skill is a DECLARATIVE definition of a task:
    1. Has a prompt template (Jinja2)
    2. Defines a structured output (Pydantic model)
    3. Does NOT execute - TutorAgent handles execution

    Skills are purely declarative. They provide:
    - Prompt template (WHAT to say to LLM)
    - Output schema (WHAT structure to expect back)
    - Prompt rendering (HOW to fill in template variables)

    Skills do NOT:
    - Make LLM API calls (TutorAgent does this)
    - Update memory (MemoryManager does this)
    - Manage conversation flow (AgentCoordinator does this)

    Subclasses must implement:
    - name: Unique identifier
    - description: What the skill does
    - output_model: Pydantic model for structured output
    - get_prompt_template(): Load Jinja2 template

    Usage:
        skill = PointASkill()
        context = {"user_message": "Hi", "state": {...}}
        prompt = skill.prepare_prompt(context)
        # TutorAgent uses this prompt to call LLM
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique skill identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this skill does."""
        pass

    @property
    @abstractmethod
    def output_model(self) -> type[BaseModel]:
        """Pydantic model for structured output."""
        pass

    @abstractmethod
    def get_prompt_template(self) -> Template:
        """Load and return Jinja2 template for this skill."""
        pass

    def prepare_prompt(self, context: dict) -> str:
        """
        Render prompt template with context variables.

        This is a DECLARATIVE operation - it produces a string (the prompt)
        but does NOT execute any LLM calls.

        Args:
            context: Dictionary with variables for template rendering

        Returns:
            Rendered prompt string
        """
        template = self.get_prompt_template()
        return template.render(context=context, **context)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
