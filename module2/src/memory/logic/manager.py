"""
Memory Manager

Central component for managing user state updates.
Handles mapping between skill outputs and memory layer updates.
"""

from typing import Any
from pydantic import BaseModel
import copy
from memory.schemas.core import TutorCoreMemory


class MemoryManager:
    """
    Manages state creation, updates, and validation.

    Responsibilities:
    - Create empty state for new users
    - Update state based on skill outputs
    - Validate state consistency
    - Clean up old data
    """

    def create_empty_state(self) -> dict:
        """
        Create initial state for a new user.

        Uses TutorCoreMemory as single source of truth for agent identity.

        Returns:
            Complete state dict with all memory layers initialized to empty/default values.
        """
        # Use TutorCoreMemory schema as single source of truth
        # This eliminates duplication and ensures consistency
        core_memory = TutorCoreMemory()

        return {
            "core": core_memory.model_dump(),
            "semantic": {
                "profile": {
                    "name": None,
                    "native_lang": None,
                    "target_lang": None,
                    "level": None,
                    "years_learning": None,
                    "previous_experience": None,
                    "motivation": None,  # Why they're learning (7th field from Point A)
                    "style": None,  # LearningStyle enum
                    "correction_policy": None,  # CorrectionPolicy enum
                },
                "goal": None,  # Will be populated by point_b skill
                "plan": None,  # Will be populated by plan skill
            },
            "workflow": {
                "onboarding_progress": {
                    "point_a_done": False,
                    "point_a_in_progress": False,
                    "collected_fields": [],
                    "point_b_done": False,
                    "point_b_in_progress": False,
                    "collected_fields_point_b": [],  # Point B tracking
                    "plan_created": False,
                    "preferences_set": False,
                },
                "session_counter": {
                    "total_sessions": 0,
                    "last_session_date": None,
                    "current_session_id": None,
                }
            },
            "working": {
                "conversation_buffer": [],
                "session_state": {
                    "topic": None,
                    "phase": "ONBOARDING",  # SessionPhase enum
                    "conversation_language": None,  # Language for agent responses (set by coordinator)
                },
                "temp_vars": {}
            },
            # Episodic memory will be added in phase 2
            # "episodic": {
            #     "episodes": [],
            #     "mistake_log": [],
            #     "breakthrough_moments": [],
            #     "progress_snapshots": []
            # }
        }

    def update_from_output(
        self,
        skill_name: str,
        output: BaseModel,
        state: dict
    ) -> dict:
        """
        Update state based on skill output.

        This is the KEY method that maps skill outputs to memory layer updates.

        Args:
            skill_name: Name of the skill that produced the output ("point_a", "point_b", etc.)
            output: Pydantic model instance (PointAOutput, PointBOutput, etc.)
            state: Current state dict

        Returns:
            Updated state dict (new copy, doesn't mutate original)
        """
        # Deep copy to avoid mutations
        new_state = copy.deepcopy(state)

        if skill_name == "point_a":
            self._update_from_point_a(output, new_state)
        elif skill_name == "point_b":
            self._update_from_point_b(output, new_state)
        elif skill_name == "enhanced_tutoring":
            self._update_from_enhanced_tutoring(output, new_state)
        elif skill_name == "tutoring":
            # Legacy tutoring - minimal updates
            pass
        elif skill_name == "plan":
            self._update_from_plan(output, new_state)
        elif skill_name == "preferences":
            self._update_from_preferences(output, new_state)
        else:
            # Unknown skill - no updates (graceful degradation)
            pass

        return new_state

    def _update_from_point_a(self, output: Any, state: dict) -> None:
        """
        Update state from PointAOutput.

        Maps PointAOutput fields -> semantic.profile
        Updates workflow.onboarding_progress
        """
        profile = state["semantic"]["profile"]
        workflow = state["workflow"]["onboarding_progress"]

        # Update profile fields (only if not None)
        if output.student_name is not None:
            profile["name"] = output.student_name

        if output.native_language is not None:
            profile["native_lang"] = output.native_language

        if output.target_language is not None:
            profile["target_lang"] = output.target_language

        if output.current_level is not None:
            profile["level"] = output.current_level

        if output.years_learning is not None:
            profile["years_learning"] = output.years_learning

        if output.previous_experience is not None:
            profile["previous_experience"] = output.previous_experience

        if output.learning_motivation is not None:
            profile["motivation"] = output.learning_motivation

        # Update workflow progress
        workflow["collected_fields"] = output.fields_collected
        workflow["point_a_done"] = output.is_complete
        workflow["point_a_in_progress"] = not output.is_complete

    def _update_from_point_b(self, output: Any, state: dict) -> None:
        """
        Update state from PointBOutput.

        Maps PointBOutput fields -> semantic.goals
        Updates workflow.onboarding_progress (point_b flags)
        """
        # Initialize goals if not exists
        if "goals" not in state["semantic"]:
            state["semantic"]["goals"] = {}

        goals = state["semantic"]["goals"]
        workflow = state["workflow"]["onboarding_progress"]

        # Update goal fields (only if not None)
        if output.goal_category is not None:
            goals["goal_category"] = output.goal_category
            if "category" not in workflow["collected_fields_point_b"]:
                workflow["collected_fields_point_b"].append("category")

        if output.specific_goal is not None:
            goals["specific_goal"] = output.specific_goal
            if "goal" not in workflow["collected_fields_point_b"]:
                workflow["collected_fields_point_b"].append("goal")

        if output.target_level is not None:
            goals["target_level"] = output.target_level
            if "target_level" not in workflow["collected_fields_point_b"]:
                workflow["collected_fields_point_b"].append("target_level")

        if output.deadline is not None:
            goals["deadline"] = output.deadline
            if "deadline" not in workflow["collected_fields_point_b"]:
                workflow["collected_fields_point_b"].append("deadline")

        # 5th CORE field (NOW REQUIRED!)
        if output.success_criteria and len(output.success_criteria) > 0:
            goals["success_criteria"] = output.success_criteria
            if "success_criteria" not in workflow["collected_fields_point_b"]:
                workflow["collected_fields_point_b"].append("success_criteria")

        # Optional fields
        if output.practice_focus and len(output.practice_focus) > 0:
            goals["practice_focus"] = output.practice_focus
            if "practice_focus" not in workflow["collected_fields_point_b"]:
                workflow["collected_fields_point_b"].append("practice_focus")

        if output.preferred_topics and len(output.preferred_topics) > 0:
            goals["preferred_topics"] = output.preferred_topics
            if "topics" not in workflow["collected_fields_point_b"]:
                workflow["collected_fields_point_b"].append("topics")

        # Update workflow flags
        if output.is_complete:
            workflow["point_b_done"] = True
            workflow["point_b_in_progress"] = False
        else:
            workflow["point_b_in_progress"] = True

    def _update_from_enhanced_tutoring(self, output: Any, state: dict) -> None:
        """
        Update state from EnhancedTutorResponse.

        Tracks corrections made, updates episodic memory with mistake patterns.
        Manages homework assignment and checking.
        """
        # Initialize episodic memory if not exists
        if "episodic" not in state:
            state["episodic"] = {
                "episodes": [],
                "mistake_log": [],
                "breakthrough_moments": [],
                "progress_snapshots": [],
                "homework": {
                    "active_task": None,
                    "completed_tasks": []
                }
            }

        episodic = state["episodic"]

        # Ensure homework tracking exists
        if "homework" not in episodic:
            episodic["homework"] = {
                "active_task": None,
                "completed_tasks": []
            }

        # Process corrections made this turn
        if hasattr(output, 'corrections_made') and output.corrections_made:
            for correction in output.corrections_made:
                # Format: "error_type: wrong → correct"
                # Parse and update mistake log
                if " → " in correction and ":" in correction:
                    try:
                        parts = correction.split(":", 1)
                        grammar_category = parts[0].strip()
                        forms = parts[1].split("→")
                        if len(forms) == 2:
                            mistake_pattern = forms[0].strip()
                            correct_form = forms[1].strip()

                            # Update or create mistake log entry
                            self._update_mistake_log(
                                episodic["mistake_log"],
                                mistake_pattern,
                                correct_form,
                                grammar_category
                            )
                    except Exception:
                        # Graceful degradation if parsing fails
                        pass

        # Process homework assignment
        if hasattr(output, 'homework_assigned') and output.homework_assigned:
            from datetime import datetime
            import uuid

            # Generate task ID
            timestamp = datetime.now().strftime("%Y%m%d")
            task_id = f"hw_{timestamp}_{str(uuid.uuid4())[:8]}"

            # Create new homework task
            new_task = {
                "task_id": task_id,
                "description": output.homework_assigned,
                "focus_area": output.homework_focus_area or "general",
                "assigned_at": datetime.now().isoformat(),
                "status": "pending",
                "due_at": None,
                "completed_at": None,
                "student_response": None,
                "ai_feedback": None
            }

            # Assign (replaces any existing active task)
            episodic["homework"]["active_task"] = new_task

        # Process homework check/completion
        if hasattr(output, 'homework_checked') and output.homework_checked:
            active = episodic["homework"].get("active_task")
            if active:
                from datetime import datetime

                # Mark as completed
                active["status"] = "completed"
                active["completed_at"] = datetime.now().isoformat()
                active["ai_feedback"] = output.homework_feedback or "Good work!"

                # Move to history
                if "completed_tasks" not in episodic["homework"]:
                    episodic["homework"]["completed_tasks"] = []

                episodic["homework"]["completed_tasks"].append(active)

                # Keep last 50
                if len(episodic["homework"]["completed_tasks"]) > 50:
                    episodic["homework"]["completed_tasks"] = episodic["homework"]["completed_tasks"][-50:]

                # Clear active
                episodic["homework"]["active_task"] = None

    def _update_mistake_log(
        self,
        mistake_log: list,
        mistake_pattern: str,
        correct_form: str,
        grammar_category: str
    ):
        """Helper to update mistake log."""
        from datetime import date

        today = date.today().isoformat()

        # Find existing entry
        for mistake in mistake_log:
            if mistake.get("mistake_pattern", "").lower() == mistake_pattern.lower():
                mistake["count"] = mistake.get("count", 0) + 1
                mistake["last_seen"] = today
                return

        # Create new entry
        mistake_log.append({
            "mistake_pattern": mistake_pattern,
            "correct_form": correct_form,
            "grammar_category": grammar_category,
            "count": 1,
            "first_seen": today,
            "last_seen": today,
            "context_examples": [],
            "difficulty_level": "learning"
        })

    def _update_from_plan(self, output: Any, state: dict) -> None:
        """
        Update state from PlanOutput.

        Maps PlanOutput fields -> semantic.learning_plan
        Updates workflow.onboarding_progress (plan_created flag)
        """
        workflow = state["workflow"]["onboarding_progress"]

        # Initialize learning_plan if not exists
        if "learning_plan" not in state["semantic"]:
            state["semantic"]["learning_plan"] = {}

        plan = state["semantic"]["learning_plan"]

        # Update plan components (only if not None)
        if output.weekly_hours is not None:
            plan["weekly_hours"] = output.weekly_hours

        if output.weekly_schedule is not None:
            plan["weekly_schedule"] = output.weekly_schedule

        if output.focus_areas is not None:
            plan["focus_areas"] = output.focus_areas

        if output.milestones is not None:
            plan["milestones"] = output.milestones

        # Update workflow flags
        workflow["plan_created"] = output.is_complete

    def _update_from_preferences(self, output: Any, state: dict) -> None:
        """
        Update state from PreferencesOutput.

        Maps PreferencesOutput fields -> preferences (LearningPreferences)
        Updates workflow.onboarding_progress (preferences_set flag)
        """
        # Ensure preferences exists
        if "preferences" not in state:
            from memory.schemas.preferences import LearningPreferences
            state["preferences"] = LearningPreferences().dict()

        preferences = state["preferences"]
        workflow = state["workflow"]["onboarding_progress"]

        # Update correction intensity (maps to correction_policy.intensity)
        if output.correction_intensity:
            if "correction_policy" not in preferences:
                preferences["correction_policy"] = {}
            preferences["correction_policy"]["intensity"] = output.correction_intensity

        # Update homework frequency
        if output.homework_frequency:
            preferences["homework_frequency"] = output.homework_frequency

        # Update session length preference
        if output.session_length:
            preferences["session_length_preference"] = output.session_length

        # Update workflow flags
        workflow["preferences_set"] = output.is_complete

    def validate_state(self, state: dict) -> bool:
        """
        Validate state structure and required fields.

        Args:
            state: State dict to validate

        Returns:
            True if valid, False otherwise

        Note: For MVP, we do basic structure checking.
              Full Pydantic validation can be added later.
        """
        required_keys = ["core", "semantic", "workflow", "working"]

        for key in required_keys:
            if key not in state:
                return False

        # Check semantic.profile exists
        if "profile" not in state["semantic"]:
            return False

        # Check workflow.onboarding_progress exists
        if "onboarding_progress" not in state["workflow"]:
            return False

        return True

    def merge_states(self, old_state: dict, new_state: dict) -> dict:
        """
        Merge partial updates into existing state.

        Useful for incremental updates where only some fields change.

        Args:
            old_state: Existing state
            new_state: Partial updates

        Returns:
            Merged state (new copy)
        """
        merged = copy.deepcopy(old_state)

        # Deep merge dictionaries
        def deep_merge(base: dict, updates: dict) -> dict:
            for key, value in updates.items():
                if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                    base[key] = deep_merge(base[key], value)
                else:
                    base[key] = value
            return base

        return deep_merge(merged, new_state)
