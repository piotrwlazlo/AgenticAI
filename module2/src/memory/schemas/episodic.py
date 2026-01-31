"""
Episodic Memory Schema - Compressed session history and learning patterns.

Tracks:
- Session summaries (compressed, last 10)
- Recurring mistake patterns (for spaced repetition)
- Breakthrough moments (achievements)
- Progress snapshots (periodic assessments)
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime, timedelta


class MistakeLog(BaseModel):
    """
    Record of recurring error pattern.

    Used for:
    - Targeted corrections during tutoring
    - Spaced repetition scheduling
    - Progress tracking (error rate over time)
    """

    mistake_pattern: str = Field(
        description="The error pattern. E.g., 'he don't', 'I go yesterday', 'for learn' (preposition error)"
    )
    correct_form: str = Field(
        description="The correct form. E.g., 'he doesn't', 'I went yesterday', 'to learn'"
    )
    grammar_category: str = Field(
        description="Category of error. E.g., 'verb_conjugation', 'tense', 'articles', 'prepositions'"
    )

    count: int = Field(
        default=1,
        description="How many times this pattern was observed"
    )
    first_seen: date = Field(
        description="First occurrence date"
    )
    last_seen: date = Field(
        description="Most recent occurrence date"
    )

    context_examples: List[str] = Field(
        default_factory=list,
        description="Example sentences where mistake occurred (keep last 5)"
    )

    # Spaced repetition tracking
    last_practiced: Optional[date] = Field(
        default=None,
        description="When this pattern was last explicitly practiced"
    )
    next_review_date: Optional[date] = Field(
        default=None,
        description="When to review this pattern again (SRS scheduling)"
    )
    difficulty_level: str = Field(
        default="learning",
        description="SRS difficulty. One of: new, learning, known, mastered"
    )

    def update_srs_schedule(self, performance: str):
        """
        Update next review date based on performance.

        Args:
            performance: 'again', 'hard', 'good', 'easy'

        SM-2 inspired intervals:
        - again: 1 day
        - hard: 3 days
        - good: 7 days
        - easy: 14 days
        """
        today = date.today()
        self.last_practiced = today

        intervals = {
            "again": timedelta(days=1),
            "hard": timedelta(days=3),
            "good": timedelta(days=7),
            "easy": timedelta(days=14)
        }

        self.next_review_date = today + intervals.get(performance, timedelta(days=3))

        # Update difficulty level
        if performance == "easy" and self.difficulty_level == "learning":
            self.difficulty_level = "known"
        elif performance == "easy" and self.difficulty_level == "known":
            self.difficulty_level = "mastered"
        elif performance == "again":
            self.difficulty_level = "learning"


class BreakthroughMoment(BaseModel):
    """
    Record of notable learning success.

    Examples:
    - First correct use of subjunctive
    - First full conversation without major errors
    - Successfully used 5 new vocabulary words
    """

    date: date
    achievement: str = Field(
        description="What student achieved. E.g., 'First correct use of subjunctive'"
    )
    context: str = Field(
        description="In what context it happened. E.g., 'If I were you, I would...'"
    )


class ProgressSnapshot(BaseModel):
    """
    Point-in-time assessment of student level.

    Taken periodically (e.g., every 10 sessions) to track improvement.
    """

    date: date
    level: str = Field(
        description="CEFR level at this point (A1, A2, B1, B2, C1, C2)"
    )

    # Skill breakdown (1-10 scale, optional)
    speaking_score: Optional[int] = Field(default=None, ge=1, le=10)
    listening_score: Optional[int] = Field(default=None, ge=1, le=10)
    reading_score: Optional[int] = Field(default=None, ge=1, le=10)
    writing_score: Optional[int] = Field(default=None, ge=1, le=10)
    grammar_score: Optional[int] = Field(default=None, ge=1, le=10)
    vocabulary_score: Optional[int] = Field(default=None, ge=1, le=10)

    notes: Optional[str] = Field(
        default=None,
        description="Agent's observations about progress"
    )


class Episode(BaseModel):
    """
    Compressed record of a single session.

    Instead of storing full conversation (memory intensive),
    we store compressed summaries with key events.
    """

    session_id: str
    date: date
    duration_minutes: int

    summary: str = Field(
        description="2-3 sentence summary of session content"
    )
    key_topics: List[str] = Field(
        default_factory=list,
        description="Main topics discussed (3-5 max)"
    )

    # Learning events
    new_vocabulary: List[str] = Field(
        default_factory=list,
        description="New words/phrases introduced (5-10 max)"
    )
    mistakes_made: List[str] = Field(
        default_factory=list,
        description="Error patterns observed (reference to mistake_log)"
    )
    corrections_given: List[str] = Field(
        default_factory=list,
        description="What corrections were made (3-5 max)"
    )

    # Meta
    student_engagement: Optional[str] = Field(
        default=None,
        description="Engagement level: high, medium, low"
    )
    homework_completed: Optional[bool] = Field(
        default=None,
        description="Whether student completed previous homework"
    )


class HomeworkTask(BaseModel):
    """
    A single homework assignment.

    Homework is optional practice between sessions, assigned by Enhanced Tutoring.
    Storage in episodic (not working) because homework persists across sessions.
    """

    task_id: str = Field(
        description="Unique identifier. Format: 'hw_YYYYMMDD_NNN'"
    )
    description: str = Field(
        description="Task description. E.g., 'Practice describing your morning routine in past tense'"
    )
    focus_area: str = Field(
        description="Learning focus. One of: 'speaking', 'grammar', 'vocabulary', 'writing', 'listening'"
    )

    assigned_at: str = Field(
        description="ISO timestamp when assigned (e.g., '2025-11-27T15:30:00Z')"
    )
    due_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp when due (optional)"
    )
    status: str = Field(
        default="pending",
        description="Status: 'pending', 'completed', 'skipped'"
    )

    # Completion data (filled when status = 'completed')
    completed_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp when completed"
    )
    student_response: Optional[str] = Field(
        default=None,
        description="Student's submitted work/response"
    )
    ai_feedback: Optional[str] = Field(
        default=None,
        description="AI's feedback on the submission"
    )


class HomeworkTracking(BaseModel):
    """
    Complete homework tracking system.

    Stored in episodic memory because homework are events that happen over time.
    """

    active_task: Optional[HomeworkTask] = Field(
        default=None,
        description="Current active homework (if any)"
    )

    completed_tasks: List[HomeworkTask] = Field(
        default_factory=list,
        description="Homework history (keep last 50 for performance)"
    )

    def assign_homework(self, task: HomeworkTask):
        """Assign new homework (replaces active_task if exists)."""
        self.active_task = task

    def complete_homework(self, student_response: str, ai_feedback: str):
        """Mark active homework as completed and move to history."""
        if not self.active_task:
            return

        # Update completion info
        self.active_task.status = "completed"
        self.active_task.completed_at = datetime.now().isoformat()
        self.active_task.student_response = student_response
        self.active_task.ai_feedback = ai_feedback

        # Move to history
        self.completed_tasks.append(self.active_task)
        if len(self.completed_tasks) > 50:
            self.completed_tasks = self.completed_tasks[-50:]

        # Clear active
        self.active_task = None

    def skip_homework(self):
        """Mark active homework as skipped and move to history."""
        if not self.active_task:
            return

        self.active_task.status = "skipped"
        self.completed_tasks.append(self.active_task)
        if len(self.completed_tasks) > 50:
            self.completed_tasks = self.completed_tasks[-50:]

        self.active_task = None


class EpisodicMemory(BaseModel):
    """
    Complete episodic memory layer.

    Stores compressed history to maintain context without
    overwhelming token budget.
    """

    episodes: List[Episode] = Field(
        default_factory=list,
        description="Compressed sessions (keep last 10 for performance)"
    )

    mistake_log: List[MistakeLog] = Field(
        default_factory=list,
        description="Recurring error patterns (all time)"
    )

    breakthrough_moments: List[BreakthroughMoment] = Field(
        default_factory=list,
        description="Notable learning successes (all time)"
    )

    progress_snapshots: List[ProgressSnapshot] = Field(
        default_factory=list,
        description="Level assessments over time (all time)"
    )

    homework: HomeworkTracking = Field(
        default_factory=HomeworkTracking,
        description="Homework tracking (Phase 3)"
    )

    def add_episode(self, episode: Episode):
        """Add new episode, keep only last 10 for performance."""
        self.episodes.append(episode)
        if len(self.episodes) > 10:
            self.episodes = self.episodes[-10:]

    def update_mistake_log(
        self,
        mistake_pattern: str,
        correct_form: str,
        grammar_category: str,
        context: str
    ):
        """
        Add or update mistake in log.

        If mistake already exists, increment count and update context.
        Otherwise, create new entry.
        """
        today = date.today()

        # Find existing
        for mistake in self.mistake_log:
            if mistake.mistake_pattern.lower() == mistake_pattern.lower():
                mistake.count += 1
                mistake.last_seen = today

                # Add context example (keep last 5)
                if context not in mistake.context_examples:
                    mistake.context_examples.append(context)
                    if len(mistake.context_examples) > 5:
                        mistake.context_examples = mistake.context_examples[-5:]

                return

        # Create new
        self.mistake_log.append(MistakeLog(
            mistake_pattern=mistake_pattern,
            correct_form=correct_form,
            grammar_category=grammar_category,
            count=1,
            first_seen=today,
            last_seen=today,
            context_examples=[context],
            next_review_date=today + timedelta(days=1)  # Review tomorrow
        ))

    def get_high_priority_mistakes(self, top_n: int = 5) -> List[MistakeLog]:
        """
        Get most frequent mistakes for targeted corrections.

        Sorted by frequency (count), returns top N.
        """
        return sorted(
            self.mistake_log,
            key=lambda m: m.count,
            reverse=True
        )[:top_n]

    def get_due_for_review(self) -> List[MistakeLog]:
        """
        Get mistakes that are due for spaced repetition review.

        Returns mistakes where next_review_date <= today.
        """
        today = date.today()
        return [
            m for m in self.mistake_log
            if m.next_review_date and m.next_review_date <= today
        ]

    def get_recent_summary(self, last_n: int = 2) -> str:
        """
        Get summary of recent sessions for context.

        Args:
            last_n: Number of recent episodes to summarize

        Returns:
            Human-readable summary string
        """
        if not self.episodes:
            return "No previous sessions."

        recent = self.episodes[-last_n:]
        summaries = [
            f"- {ep.date.isoformat()}: {ep.summary}"
            for ep in recent
        ]
        return "\n".join(summaries)
