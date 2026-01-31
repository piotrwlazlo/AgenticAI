"""
Semantic Memory Schema - Long-term knowledge about the student.

Contains:
- Student profile (from Point A)
- Learning goals (from Point B)
- Learning preferences (AI-managed)
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date


# Legacy enums (kept for backward compatibility)
class LearningStyle(str, Enum):
    VISUAL = "VISUAL"
    ANALYTICAL = "ANALYTICAL"
    IMMERSIVE = "IMMERSIVE"


class CorrectionPolicyEnum(str, Enum):
    """Legacy enum - kept for backward compatibility."""
    GENTLE = "GENTLE"
    STRICT = "STRICT"


# Point A Profile
class StudentProfile(BaseModel):
    """Student profile collected in Point A (assessment)."""

    # Required fields (from Point A)
    name: str = Field(description="Student's full name")
    native_lang: str = Field(description="Native language")
    target_lang: str = Field(description="Target learning language")
    level: str = Field(description="Current CEFR level (A1-C2)")

    # Extended Point A fields
    years_learning: Optional[str] = Field(default=None, description="Years spent learning")
    previous_experience: Optional[str] = Field(default=None, description="Previous learning methods")
    learning_motivation: Optional[str] = Field(default=None, description="Primary motivation")
    preferred_study_time: Optional[str] = Field(default=None, description="Preferred time of day")

    # Legacy fields (for backward compatibility)
    goal: Optional["LearningGoal"] = Field(default=None, description="Legacy goal field (moved to StudentGoals)")
    style: Optional[LearningStyle] = Field(default=None, description="Legacy learning style")
    policy: Optional[CorrectionPolicyEnum] = Field(default=None, description="Legacy correction policy (now auto-managed)")


# Point B Goals
class StudentGoals(BaseModel):
    """Learning goals collected in Point B (goal setting)."""

    # Core fields (4 required)
    goal_category: Optional[str] = Field(
        default=None,
        description="Goal type: exam, travel, work, hobby, immigration, academic, family"
    )
    specific_goal: Optional[str] = Field(
        default=None,
        description="Specific description (1-2 sentences)"
    )
    target_level: Optional[str] = Field(
        default=None,
        description="Desired CEFR level (can be same as current)"
    )
    deadline: Optional[str] = Field(
        default=None,
        description="When to achieve (natural language)"
    )

    # Optional fields
    success_criteria: List[str] = Field(
        default_factory=list,
        description="How student will know they succeeded (1-3 criteria)"
    )
    material_preferences: List[str] = Field(
        default_factory=list,
        description="Preferred learning materials: video, podcast, book, app, conversation"
    )
    preferred_topics: List[str] = Field(
        default_factory=list,
        description="Topics of interest for materials"
    )


# Legacy LearningGoal (for backward compatibility)
class LearningGoal(BaseModel):
    """Legacy goal model - kept for backward compatibility."""
    statement: str
    target_level: str
    deadline: Optional[date] = None
    success_criteria: List[str] = Field(default_factory=list)


class SemanticMemory(BaseModel):
    """
    Complete semantic memory layer.

    Contains all long-term knowledge about the student.
    """

    profile: StudentProfile = Field(
        description="Student profile from Point A"
    )
    goals: StudentGoals = Field(
        default_factory=StudentGoals,
        description="Learning goals from Point B"
    )

    learning_plan: Optional[dict] = Field(
        default=None,
        description="Generated learning plan from Plan Skill (Onboarding Phase 3). Contains: weekly_hours, weekly_schedule, focus_areas, milestones"
    )

    # Preferences are imported from preferences.py schema
    # Will be added in memory manager initialization
