"""
Tutor Agent - Main execution agent for tutoring tasks.

Responsibilities:
- Skill discovery and loading
- Context preparation
- LLM API calls (ONLY PLACE IN SYSTEM!)
- Memory updates
- Conversation management

This agent does the actual tutoring work. It receives skill names from
AgentCoordinator and executes them by calling LLM APIs with structured output.
"""

from typing import Any
from skills import SKILLS_REGISTRY
from memory.logic import MemoryManager


class TutorAgent:
    """
    Main tutoring agent that executes teaching tasks.

    This agent is responsible for:
    - Loading skills from registry (discovery)
    - Preparing execution context with state + conversation history
    - Making LLM API calls with structured output
    - Updating memory based on skill outputs
    - Managing conversation history buffer

    All LLM API calls in the system go through this agent's execute() method.
    This is the ONLY place where we call llm_client.chat.completions.create().
    """

    def __init__(self, llm_client: Any, memory_manager: MemoryManager):
        """
        Initialize agent with LLM client and memory manager.

        Args:
            llm_client: OpenAI client with Instructor patch for structured output
            memory_manager: MemoryManager instance for state updates
        """
        self.client = llm_client
        self.memory_manager = memory_manager

    def execute(self, skill_name: str, user_message: str, state: dict) -> dict:
        """
        Execute a tutoring skill.

        This is the main execution method. All skills go through here,
        whether it's Point A assessment, main tutoring, or any future skill.

        Flow:
        1. Load skill from registry (discovery)
        2. Prepare execution context (state, history, collected fields)
        3. Skill renders prompt template
        4. Build messages payload (system + history + current message)
        5. ★ CALL LLM API ★ (ONLY PLACE IN ENTIRE SYSTEM!)
        6. Update memory from skill output (via MemoryManager)
        7. Update conversation buffer
        8. Return result

        Args:
            skill_name: Name of skill to execute ("point_a", "tutoring", "point_b", etc.)
            user_message: Current user input
            state: Complete state dict

        Returns:
            Dict with:
            - ai_response: Agent's response to user
            - new_state: Updated state dict
            - skill_output: Raw skill output (for debugging)

        Raises:
            KeyError: If skill_name not found in SKILLS_REGISTRY
        """
        # 1. Skill discovery - load from registry
        skill = self._get_skill(skill_name)

        # 2. Prepare context - gather all info skill needs
        context = self._prepare_context(user_message, state, skill_name)

        # 3. Skill renders prompt (declarative - no execution!)
        prompt = skill.prepare_prompt(context)

        # 4. Build messages - system + optional history + current message
        messages = self._build_messages(prompt, user_message, state, skill_name)

        # 5. ★★★ CALL LLM API ★★★
        # This is the ONLY place in the entire system where we make LLM calls!
        # All retry logic, cost tracking, logging should be added here.
        from config import Config

        response = self.client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=messages,
            response_model=skill.output_model
        )

        # 6. Update memory from skill output
        # MemoryManager handles skill-specific mapping (e.g., PointAOutput -> profile)
        new_state = self.memory_manager.update_from_output(
            skill_name=skill_name,
            output=response,
            state=state
        )

        # 7. Update conversation buffer
        # Append both user message and AI response to history
        new_state = self._update_conversation_buffer(
            new_state,
            user_message,
            response.ai_response
        )

        return {
            "ai_response": response.ai_response,
            "new_state": new_state,
            "skill_output": response  # For debugging
        }

    def _get_skill(self, skill_name: str):
        """
        Load skill from registry (skill discovery).

        This is where we look up which skill to use based on name.
        The registry maps skill names to skill classes.

        Args:
            skill_name: Name of skill to load (e.g., "point_a", "tutoring")

        Returns:
            Skill instance

        Raises:
            KeyError: If skill not found in registry
        """
        if skill_name not in SKILLS_REGISTRY:
            raise KeyError(
                f"Skill '{skill_name}' not found in registry. "
                f"Available skills: {list(SKILLS_REGISTRY.keys())}"
            )

        # Instantiate skill (skills are stateless, safe to create new instance)
        return SKILLS_REGISTRY[skill_name]()

    def _prepare_context(self, user_message: str, state: dict, skill_name: str) -> dict:
        """
        Prepare execution context for skill.

        Context contains all information skill needs to render its prompt.
        Different skills may need different context elements.

        Args:
            user_message: Current user input
            state: Complete state dict
            skill_name: Name of skill being executed

        Returns:
            Context dictionary with relevant information
        """
        # Get recent conversation history
        conversation_buffer = state["working"]["conversation_buffer"]
        recent_messages = conversation_buffer[-10:]  # Last 10 messages

        # Base context - common for all skills
        context = {
            "user_message": user_message,
            "state": state,
            "core": state["core"],  # Agent identity (read-only)
            "recent_messages": recent_messages,
            "messages_count": len(conversation_buffer),
        }

        # Skill-specific context additions
        if skill_name == "point_a":
            # Point A needs to know which fields are already collected
            context["collected_fields"] = state["workflow"]["onboarding_progress"]["collected_fields"]
        elif skill_name == "point_b":
            # Point B needs to know which goal fields are already collected
            context["collected_fields"] = state["workflow"]["onboarding_progress"]["collected_fields_point_b"]
        # elif skill_name == "plan":
        #     context["student_profile"] = state["semantic"]["profile"]

        return context

    def _build_messages(self, prompt: str, user_message: str, state: dict, skill_name: str) -> list:
        """
        Build messages payload for LLM API call.

        Format depends on skill type:
        - Tutoring skill: system + conversation history + current message
        - Other skills: system + current message (no history)

        Args:
            prompt: Rendered system prompt
            user_message: Current user input
            state: Complete state dict
            skill_name: Name of skill being executed

        Returns:
            List of message dicts in OpenAI format
        """
        # Start with system prompt
        messages = [{"role": "system", "content": prompt}]

        # For tutoring skills, include conversation history
        if skill_name in ["tutoring", "enhanced_tutoring"]:
            conversation_buffer = state["working"]["conversation_buffer"]
            recent_messages = conversation_buffer[-10:]  # Last 10 for context window
            messages.extend(recent_messages)

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    def _update_conversation_buffer(
        self,
        state: dict,
        user_message: str,
        ai_response: str
    ) -> dict:
        """
        Append user and assistant messages to conversation buffer.

        The conversation buffer maintains the dialogue history and is used
        for context in future interactions (especially for tutoring skill).

        Args:
            state: State dict to update
            user_message: User's message
            ai_response: Agent's response

        Returns:
            Updated state dict (mutates in place and returns)
        """
        buffer = state["working"]["conversation_buffer"]

        # Append user message
        buffer.append({
            "role": "user",
            "content": user_message
        })

        # Append assistant message
        buffer.append({
            "role": "assistant",
            "content": ai_response
        })

        return state
