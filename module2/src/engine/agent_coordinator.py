"""
Agent Coordinator - High-level orchestration layer.

Responsibilities:
- Multi-user state management (load/save)
- Routing logic (which skill to use)
- Flow validation
- Delegates execution to TutorAgent
"""

from persistence import create_backend
from memory.logic import MemoryManager
from .tutor_agent import TutorAgent
from engine.client import get_client
from config import Config


class AgentCoordinator:
    """
    High-level coordinator for the AI Tutor system.

    Manages state persistence, routing decisions, and delegates
    actual tutoring work to TutorAgent.

    This is the entry point for the multi-user tutoring system.
    """

    def __init__(self):
        """Initialize coordinator with dependencies."""
        self.persistence = create_backend(Config.PERSISTENCE_BACKEND)
        self.memory_manager = MemoryManager()

        # TutorAgent does the actual work
        llm_client = get_client()
        self.tutor_agent = TutorAgent(llm_client, self.memory_manager)

    def process_message(self, user_id: str, message: str) -> dict:
        """
        Main entry point for processing user messages.

        High-level flow:
        1. Load user state
        2. Decide which skill to use (routing)
        3. Delegate to TutorAgent for execution
        4. Save updated state
        5. Return response

        Args:
            user_id: Unique user identifier
            message: User's message

        Returns:
            Dict with:
            - ai_response: Agent's response to the user
            - state: Updated state dict
            - action: What action was taken (e.g., "skill:point_a")
        """
        # 1. Load state (or create new)
        state = self.persistence.load(user_id)
        if state is None:
            state = self.memory_manager.create_empty_state()

        # 2. Routing: decide which skill to use
        skill_name = self.decide_next_skill(state)

        # 3. Delegate to TutorAgent (actual execution)
        result = self.tutor_agent.execute(skill_name, message, state)

        # 4. Save state
        self.persistence.save(user_id, result["new_state"])

        # 5. Return with action info
        return {
            "ai_response": result["ai_response"],
            "state": result["new_state"],
            "action": f"skill:{skill_name}"
        }

    def decide_next_skill(self, state: dict) -> str:
        """
        Routing logic: decide which skill to execute based on state.

        This is explicit state machine logic (not LLM-driven).
        Examines workflow flags and decides the next appropriate skill.

        Also sets conversation_language for each phase.

        Args:
            state: Current user state

        Returns:
            Skill name to execute (e.g., "point_a", "point_b", "enhanced_tutoring")
        """
        workflow = state["workflow"]["onboarding_progress"]
        profile = state["semantic"]["profile"]

        # Onboarding Phase 1: Point A (assessment)
        if workflow["point_a_in_progress"] or not workflow["point_a_done"]:
            # Point A: Use native language if known, otherwise start with English
            state["working"]["session_state"]["conversation_language"] = (
                profile.get("native_lang") or "English"
            )
            return "point_a"

        # Onboarding Phase 2: Point B (goal setting) - NOW ACTIVE
        # CRITICAL: Point B requires ALL 5 core fields: category, goal, target_level, deadline, success_criteria
        collected_point_b = workflow.get("collected_fields_point_b", [])
        goals = state["semantic"].get("goals", {})
        success_criteria = goals.get("success_criteria", [])

        # Point B not complete if:
        # 1. Still in progress flag OR not done flag
        # 2. Less than 5 field names collected
        # 3. success_criteria list is empty (REQUIRED field!)
        if (workflow["point_b_in_progress"] or
            not workflow["point_b_done"] or
            len(collected_point_b) < 5 or
            len(success_criteria) == 0):  # MUST have at least 1 success criterion
            # Point B: Use native language (onboarding comfort)
            state["working"]["session_state"]["conversation_language"] = (
                profile.get("native_lang") or "English"
            )
            return "point_b"

        # Onboarding Phase 3: Plan creation
        if not workflow["plan_created"]:
            state["working"]["session_state"]["conversation_language"] = profile.get("native_lang")
            return "plan"

        # Onboarding Phase 4: Preferences
        if not workflow["preferences_set"]:
            state["working"]["session_state"]["conversation_language"] = profile.get("native_lang")
            return "preferences"

        # Main tutoring mode (post-onboarding) - USING ENHANCED VERSION
        # Enhanced Tutoring: Switch to target language (AI-adaptive)
        state["working"]["session_state"]["conversation_language"] = (
            profile.get("target_lang") or "English"
        )
        return "enhanced_tutoring"

    def validate_state(self, state: dict) -> bool:
        """
        Validate state structure before processing.

        Optional: can add validation logic here to ensure state is well-formed.

        Args:
            state: State dict to validate

        Returns:
            True if valid, False otherwise
        """
        return self.memory_manager.validate_state(state)

    def export_conversation(self, user_id: str) -> dict:
        """
        Export full conversation with metadata as JSON.

        Provides complete session data for analysis, debugging, or archiving.

        Args:
            user_id: User identifier

        Returns:
            Dict with:
            - export_metadata: Timestamp, session info
            - student_profile: Name, languages, level, goal
            - conversation_history: Full dialogue
            - full_state: Complete state dump
        """
        from datetime import datetime, timezone

        # Get current state from persistence
        state = self.persistence.load(user_id)
        if not state:
            return {
                "error": "No conversation found for this user",
                "user_id": user_id
            }

        # Prepare export
        profile = state["semantic"]["profile"]
        goals = state["semantic"].get("goals", {})
        conversation = state["working"]["conversation_buffer"]
        workflow = state["workflow"]["onboarding_progress"]

        return {
            "export_metadata": {
                "user_id": user_id,
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": state["workflow"]["session_counter"].get("current_session_id"),
                "total_messages": len(conversation),
                "onboarding_complete": workflow["point_a_done"] and workflow["point_b_done"]
            },
            "student_profile": {
                "name": profile.get("name"),
                "native_language": profile.get("native_lang"),
                "target_language": profile.get("target_lang"),
                "current_level": profile.get("level"),
                "years_learning": profile.get("years_learning"),
                "previous_experience": profile.get("previous_experience"),
                "motivation": profile.get("motivation"),
                "goal": goals.get("specific_goal"),
                "target_level": goals.get("target_level"),
                "deadline": goals.get("deadline"),
                "success_criteria": goals.get("success_criteria", [])
            },
            "conversation_history": conversation,
            "full_state": state  # Complete state dump for reconstruction
        }
