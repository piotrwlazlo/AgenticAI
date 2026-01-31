"""
Tutoring Skill - Regular conversation mode (post-onboarding).

This skill handles main tutoring sessions after onboarding is complete.
Previously this was hardcoded in TutorAgent.run_conversation().
"""

from pydantic import BaseModel
from jinja2 import Template
from ._base import Skill
from memory.schemas.working import TutorResponse


class TutoringSkill(Skill):
    """
    Main tutoring skill for conversation-based learning.

    This skill is used after onboarding (Point A, Point B, Plan) is complete.
    It handles regular tutoring conversations with the student, focusing on:
    - Communication practice
    - Error correction based on policy
    - Contextual learning
    - Fluency development

    This was previously the "conversation mode" hardcoded in TutorAgent.
    """

    @property
    def name(self) -> str:
        return "tutoring"

    @property
    def description(self) -> str:
        return "Main tutoring conversation for language practice"

    @property
    def output_model(self) -> type[BaseModel]:
        return TutorResponse

    def get_prompt_template(self) -> Template:
        """
        Return tutoring prompt template.

        Builds dynamic prompt from state using agent identity and student profile.
        """
        # Inline template for now (TODO: move to tutoring.j2 file)
        template_str = """
You are {{ core.name }}, a {{ core.role|lower }}.

{% if state.semantic.profile.name %}
STUDENT PROFILE:
- Name: {{ state.semantic.profile.name }}
- Native language: {{ state.semantic.profile.native_lang }}
- Learning: {{ state.semantic.profile.target_lang }}
- Current level: {{ state.semantic.profile.level }}
- Years learning: {{ state.semantic.profile.years_learning }}
- Previous experience: {{ state.semantic.profile.previous_experience }}
- Motivation: {{ state.semantic.profile.motivation }}
{% endif %}

PRIME DIRECTIVES:
{% for directive in core.prime_directives %}
- {{ directive }}
{% endfor %}

YOUR ROLE:
You are a language communication coach. Your primary goal is to help the student
improve their communication skills in {{ state.semantic.profile.target_lang if state.semantic.profile.target_lang else "the target language" }}.

Focus on:
1. Natural conversation practice
2. Encouraging fluency over perfection
3. Contextual learning (teach through examples)
4. Gentle corrections when appropriate
5. Building confidence

Continue the natural conversation with the student. Be warm, encouraging, and adapt
to their level and interests. Respond authentically as a language coach would.
"""
        return Template(template_str)

    def prepare_prompt(self, context: dict) -> str:
        """
        Build prompt from state.

        Uses context["state"] to access student profile and agent identity.

        Args:
            context: Execution context with state dict

        Returns:
            Rendered system prompt for tutoring
        """
        template = self.get_prompt_template()
        return template.render(**context)
