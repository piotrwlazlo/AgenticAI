"""
Skills Registry

Central registry for all skills (procedural memory).
Skills are looked up by name during execution.
"""

from ._base import Skill
from .point_a import PointASkill, PointAOutput
from .point_b import PointBSkill, PointBOutput
from .tutoring import TutoringSkill
from .enhanced_tutoring import EnhancedTutoringSkill, EnhancedTutorResponse
from .plan import PlanSkill, PlanOutput
from .preferences import PreferencesSkill, PreferencesOutput


# Skills registry - maps skill names to skill CLASSES (not instances!)
# TutorAgent instantiates skills as needed
SKILLS_REGISTRY = {
    "point_a": PointASkill,
    "point_b": PointBSkill,  # Phase 1 implemented
    "tutoring": TutoringSkill,  # Legacy - kept for backward compatibility
    "enhanced_tutoring": EnhancedTutoringSkill,  # Phase 1 - new default
    "plan": PlanSkill,  # Phase 3 - NOW ACTIVE
    "preferences": PreferencesSkill,  # Phase 3 - NOW ACTIVE
}


def get_skill(name: str) -> Skill:
    """
    Get skill instance by name.

    Args:
        name: Skill name (e.g. "point_a")

    Returns:
        Skill instance

    Raises:
        KeyError: If skill not found
    """
    skill = SKILLS_REGISTRY.get(name)
    if skill is None:
        raise KeyError(f"Unknown skill: {name}. Available: {list(SKILLS_REGISTRY.keys())}")
    return skill


def list_skills() -> list[str]:
    """Get list of available skill names."""
    return list(SKILLS_REGISTRY.keys())


__all__ = [
    "Skill",
    "PointASkill",
    "PointAOutput",
    "PointBSkill",
    "PointBOutput",
    "TutoringSkill",
    "EnhancedTutoringSkill",
    "EnhancedTutorResponse",
    "SKILLS_REGISTRY",
    "get_skill",
    "list_skills",
]
