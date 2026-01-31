"""
Workflow Memory Schema

Tracks the state of learning journey, onboarding progress, and session management.
This memory layer is used by TutorAgent.decide_next_action() for state machine logic.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class OnboardingProgress(BaseModel):
    """
    Tracks completion of onboarding skills.

    For multi-turn skills (like point_a), we track both:
    - in_progress: skill is currently active, waiting for more info
    - done: skill completed successfully
    """

    # Point A Assessment
    point_a_done: bool = False
    point_a_in_progress: bool = False
    collected_fields: List[str] = Field(
        default_factory=list,
        description="Fields collected so far in Point A: ['name', 'native_lang', etc.]"
    )

    # Point B Goal Setting
    point_b_done: bool = False
    point_b_in_progress: bool = False
    collected_fields_point_b: List[str] = Field(
        default_factory=list,
        description="Fields collected in Point B: ['category', 'goal', 'target_level', 'deadline', etc.]"
    )

    # Plan Creation
    plan_created: bool = False

    # Preferences
    preferences_set: bool = False

    def is_onboarding_complete(self) -> bool:
        """Check if all onboarding steps are done."""
        return (
            self.point_a_done and
            self.point_b_done and
            self.plan_created and
            self.preferences_set
        )

    def mark_point_a_field_collected(self, field_name: str):
        """Add field to collected list if not already there."""
        if field_name not in self.collected_fields:
            self.collected_fields.append(field_name)

    def get_missing_point_a_fields(self) -> List[str]:
        """Return fields that still need to be collected."""
        required = ["name", "native_lang", "target_lang", "level", "years_learning", "previous_experience"]
        return [f for f in required if f not in self.collected_fields]

    def mark_point_b_field_collected(self, field_name: str):
        """Add field to Point B collected list if not already there."""
        if field_name not in self.collected_fields_point_b:
            self.collected_fields_point_b.append(field_name)

    def get_missing_point_b_fields(self) -> List[str]:
        """Return Point B fields that still need to be collected."""
        required = ["category", "goal", "target_level", "deadline"]  # 4 core fields
        optional = ["success_criteria", "materials", "topics"]  # 3 optional
        missing_required = [f for f in required if f not in self.collected_fields_point_b]
        missing_optional = [f for f in optional if f not in self.collected_fields_point_b]
        return missing_required + missing_optional  # Show required first


class SessionCounter(BaseModel):
    """Tracks session metadata and history."""

    total_sessions: int = 0
    last_session_date: Optional[str] = None  # ISO format: "2025-11-27"
    current_session_id: Optional[str] = None

    def increment_session(self, session_id: str):
        """Increment counter and update last session date."""
        self.total_sessions += 1
        self.last_session_date = datetime.now().date().isoformat()
        self.current_session_id = session_id


class WorkflowMemory(BaseModel):
    """
    Complete workflow memory state.

    This tracks:
    - Where in the onboarding journey the student is
    - How many sessions they've completed
    - What phase of learning they're in
    """

    onboarding_progress: OnboardingProgress = Field(default_factory=OnboardingProgress)
    session_counter: SessionCounter = Field(default_factory=SessionCounter)

    # Future: Add homework tracking, learning phase, etc.
    # current_learning_phase: Optional[str] = None  # "BEGINNER_PHASE", "INTERMEDIATE_PHASE", etc.
    # homework_tracking: Optional[dict] = None

    def is_new_user(self) -> bool:
        """Check if this is a brand new user (no sessions yet)."""
        return self.session_counter.total_sessions == 0

    def should_start_onboarding(self) -> bool:
        """Check if onboarding should be initiated."""
        return not self.onboarding_progress.is_onboarding_complete()
