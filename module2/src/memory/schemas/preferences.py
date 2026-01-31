"""
Learning Preferences Schema - AI-managed learning settings.

This schema captures HOW the AI should teach, automatically adapted
based on student's level, reactions, and progress.

Key principle: AI decides, not the student. Preferences are auto-adjusted.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class CorrectionPolicy(BaseModel):
    """
    How aggressive should error corrections be.

    Auto-adjusted by AI based on:
    - Student's CEFR level (A1=gentle, B1=balanced, C1=strict)
    - Student's reactions to corrections
    - Error persistence (if errors repeat → adjust strategy)
    """

    intensity: str = Field(
        default="balanced",
        description="Correction intensity: 'gentle', 'balanced', 'strict'"
    )

    corrections_per_session: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Target number of corrections per session (0-10)"
    )

    preferred_method: str = Field(
        default="recast",
        description="Primary correction method: 'recast' (implicit), 'clarification' (ask), 'explicit' (direct)"
    )

    # Auto-adjustment tracking
    last_adjusted: Optional[date] = None
    adjustment_reason: Optional[str] = None

    @staticmethod
    def from_level(level: str) -> "CorrectionPolicy":
        """
        Auto-create policy from CEFR level.

        Defaults:
        - A1-A2: gentle (1-2 corrections, recast)
        - B1-B2: balanced (3-4 corrections, mix)
        - C1-C2: strict (5-6 corrections, explicit)
        """
        level_upper = level.upper()

        if level_upper in ["A1", "A2"]:
            return CorrectionPolicy(
                intensity="gentle",
                corrections_per_session=2,
                preferred_method="recast"
            )
        elif level_upper in ["B1", "B2"]:
            return CorrectionPolicy(
                intensity="balanced",
                corrections_per_session=3,
                preferred_method="recast"
            )
        else:  # C1, C2
            return CorrectionPolicy(
                intensity="strict",
                corrections_per_session=5,
                preferred_method="explicit"
            )

    def adjust_based_on_feedback(self, feedback_signal: str):
        """
        Adjust policy based on student reactions.

        Args:
            feedback_signal: One of:
                - 'frustrated' → reduce corrections
                - 'requesting_more' → increase corrections
                - 'not_improving' → change method
                - 'improving_well' → maintain
        """
        today = date.today()
        self.last_adjusted = today

        if feedback_signal == "frustrated":
            # Reduce corrections
            self.corrections_per_session = max(1, self.corrections_per_session - 1)
            if self.intensity == "strict":
                self.intensity = "balanced"
            elif self.intensity == "balanced":
                self.intensity = "gentle"
            self.adjustment_reason = "Student seemed frustrated with corrections"

        elif feedback_signal == "requesting_more":
            # Increase corrections
            self.corrections_per_session = min(10, self.corrections_per_session + 1)
            if self.intensity == "gentle":
                self.intensity = "balanced"
            elif self.intensity == "balanced":
                self.intensity = "strict"
            self.adjustment_reason = "Student requested more feedback"

        elif feedback_signal == "not_improving":
            # Change method
            methods = ["recast", "clarification", "explicit"]
            current_index = methods.index(self.preferred_method)
            self.preferred_method = methods[(current_index + 1) % len(methods)]
            self.adjustment_reason = "Errors persisting, trying different correction method"

        elif feedback_signal == "improving_well":
            # Maintain or slightly increase challenge
            self.adjustment_reason = "Progress is good, maintaining current approach"


class ContentDifficulty(BaseModel):
    """
    How challenging should conversation topics and language be.

    i+1 principle: Content should be slightly above current level.
    """

    current_level: str = Field(
        description="Current CEFR level (A1-C2)"
    )

    target_complexity: str = Field(
        default="i+1",
        description="Content complexity: 'i' (at level), 'i+1' (slightly above), 'i+2' (challenging)"
    )

    vocabulary_range: str = Field(
        default="intermediate",
        description="Vocabulary complexity: 'basic', 'intermediate', 'advanced', 'native'"
    )

    sentence_complexity: str = Field(
        default="moderate",
        description="Sentence structure: 'simple', 'moderate', 'complex'"
    )

    abstract_topics: bool = Field(
        default=False,
        description="Whether to introduce abstract/philosophical topics"
    )

    @staticmethod
    def from_level(level: str) -> "ContentDifficulty":
        """Auto-create difficulty settings from CEFR level."""
        level_upper = level.upper()

        if level_upper in ["A1", "A2"]:
            return ContentDifficulty(
                current_level=level_upper,
                target_complexity="i+1",
                vocabulary_range="basic",
                sentence_complexity="simple",
                abstract_topics=False
            )
        elif level_upper in ["B1", "B2"]:
            return ContentDifficulty(
                current_level=level_upper,
                target_complexity="i+1",
                vocabulary_range="intermediate",
                sentence_complexity="moderate",
                abstract_topics=False
            )
        else:  # C1, C2
            return ContentDifficulty(
                current_level=level_upper,
                target_complexity="i+1",
                vocabulary_range="advanced",
                sentence_complexity="complex",
                abstract_topics=True
            )


class InteractionStyle(BaseModel):
    """
    Conversational style and pacing.

    Auto-adjusted based on student's engagement and preferences.
    """

    formality: str = Field(
        default="friendly_professional",
        description="Tone: 'casual', 'friendly_professional', 'formal'"
    )

    pacing: str = Field(
        default="moderate",
        description="Conversation pace: 'slow' (more explanations), 'moderate', 'fast' (native-like)"
    )

    encouragement_level: str = Field(
        default="high",
        description="How much encouragement: 'low', 'moderate', 'high'"
    )

    humor_usage: bool = Field(
        default=True,
        description="Whether to use jokes/light humor when appropriate"
    )


class LearningPreferences(BaseModel):
    """
    Complete set of AI-managed learning preferences.

    These are NOT set by the student explicitly.
    AI decides based on level, progress, and observations.
    """

    correction_policy: CorrectionPolicy = Field(
        default_factory=lambda: CorrectionPolicy.from_level("B1")
    )

    content_difficulty: ContentDifficulty = Field(
        default_factory=lambda: ContentDifficulty.from_level("B1")
    )

    interaction_style: InteractionStyle = Field(
        default_factory=InteractionStyle
    )

    # Material recommendations (general, no URLs)
    recommended_resource_types: List[str] = Field(
        default_factory=lambda: ["video", "podcast", "conversation"],
        description="Types of resources to recommend: 'video', 'podcast', 'book', 'app', 'conversation'"
    )

    focus_areas: List[str] = Field(
        default_factory=list,
        description="Current focus areas (auto-detected): 'grammar', 'vocabulary', 'pronunciation', 'fluency'"
    )

    # Student-set preferences (from Preferences Skill - Phase 3)
    homework_frequency: str = Field(
        default="none",
        description="Homework frequency: 'none', 'light', 'moderate', 'intensive'"
    )

    session_length_preference: str = Field(
        default="medium",
        description="Preferred session length: 'short' (15min), 'medium' (30min), 'long' (45min+)"
    )

    @staticmethod
    def initialize_from_profile(level: str, goal_category: Optional[str] = None) -> "LearningPreferences":
        """
        Initialize preferences from student profile.

        Args:
            level: CEFR level (A1-C2)
            goal_category: Goal type (exam, travel, work, etc.)

        Returns:
            LearningPreferences with sensible defaults
        """
        prefs = LearningPreferences(
            correction_policy=CorrectionPolicy.from_level(level),
            content_difficulty=ContentDifficulty.from_level(level),
            interaction_style=InteractionStyle()
        )

        # Adjust based on goal
        if goal_category == "exam":
            prefs.correction_policy.intensity = "strict"
            prefs.correction_policy.corrections_per_session = 5
            prefs.focus_areas = ["grammar", "vocabulary", "accuracy"]

        elif goal_category == "travel":
            prefs.correction_policy.intensity = "gentle"
            prefs.interaction_style.pacing = "fast"
            prefs.focus_areas = ["fluency", "vocabulary", "pronunciation"]

        elif goal_category == "work":
            prefs.interaction_style.formality = "friendly_professional"
            prefs.focus_areas = ["vocabulary", "fluency", "confidence"]

        return prefs
