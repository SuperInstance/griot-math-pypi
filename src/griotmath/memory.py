"""Core memory module — Griot and Story classes."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Story:
    """A single story held in a Griot's memory.

    Attributes:
        id: Unique identifier (auto-generated UUID-like).
        content: The story text.
        parent_id: ID of the parent story (for genealogy).
        children: IDs of child stories.
        weight: Current weight / importance (0.0–1.0+).
        tags: Set of semantic tags.
        tell_count: How many times this story has been told.
        created_at: Epoch timestamp when created.
        last_told_at: Epoch timestamp when last told.
    """

    id: str
    content: str
    parent_id: Optional[str] = None
    children: list[str] = field(default_factory=list)
    weight: float = 1.0
    tags: set[str] = field(default_factory=set)
    tell_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_told_at: Optional[float] = None

    def tell(self) -> str:
        """Tell the story: increment tell count, boost weight, update last_told_at."""
        self.tell_count += 1
        self.last_told_at = time.time()
        # Retelling strengthens memory (diminishing returns)
        self.weight += 0.1 / (1.0 + self.tell_count * 0.1)
        return self.content

    @property
    def age(self) -> float:
        """Seconds since creation."""
        return time.time() - self.created_at

    @property
    def time_since_told(self) -> float:
        """Seconds since last told (or creation if never told)."""
        if self.last_told_at is None:
            return self.age
        return time.time() - self.last_told_at


class Griot:
    """A living memory keeper.

    Stories are organized with genealogy (parent/child relationships),
    weighted by importance, tagged for retrieval, and subject to decay.

    Args:
        name: The griot's name.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._stories: dict[str, Story] = {}
        self._next_id: int = 0

    def _make_id(self) -> str:
        """Generate a simple unique story ID."""
        sid = f"{self.name}-{self._next_id}"
        self._next_id += 1
        return sid

    def add_story(
        self,
        content: str,
        parent_id: Optional[str] = None,
        weight: float = 1.0,
        tags: Optional[set[str] | list[str]] = None,
    ) -> str:
        """Add a story to memory.

        Args:
            content: The story text.
            parent_id: Optional parent story ID for genealogy.
            weight: Initial weight (default 1.0).
            tags: Optional tags for categorization.

        Returns:
            The new story's ID.

        Raises:
            ValueError: If parent_id is given but doesn't exist.
        """
        if parent_id is not None and parent_id not in self._stories:
            raise ValueError(f"Parent story '{parent_id}' not found")

        story_id = self._make_id()
        tag_set = set(tags) if tags else set()
        story = Story(
            id=story_id,
            content=content,
            parent_id=parent_id,
            weight=weight,
            tags=tag_set,
        )
        self._stories[story_id] = story

        if parent_id is not None:
            self._stories[parent_id].children.append(story_id)

        return story_id

    def get_story(self, story_id: str) -> Optional[Story]:
        """Retrieve a story by ID, or None if not found."""
        return self._stories.get(story_id)

    def tell_story(self, story_id: str) -> str:
        """Tell a story by ID.

        Returns:
            The story content.

        Raises:
            KeyError: If story_id doesn't exist.
        """
        if story_id not in self._stories:
            raise KeyError(f"Story '{story_id}' not found")
        return self._stories[story_id].tell()

    def apply_decay(self, rate: float = 0.1) -> None:
        """Apply exponential decay to all story weights.

        Each story's weight is reduced by: weight *= exp(-rate * time_since_told)

        Args:
            rate: Decay rate (higher = faster forgetting). Default 0.1.
        """
        for story in self._stories.values():
            decay_factor = math.exp(-rate * story.time_since_told)
            story.weight *= decay_factor

    def memory_strengths(self) -> dict[str, float]:
        """Return a mapping of story_id → current weight for all stories."""
        return {sid: s.weight for sid, s in self._stories.items()}

    def stories_by_tag(self, tag: str) -> list[Story]:
        """Return all stories matching a given tag."""
        return [s for s in self._stories.values() if tag in s.tags]

    def all_tags(self) -> set[str]:
        """Return the union of all tags across all stories."""
        tags: set[str] = set()
        for s in self._stories.values():
            tags |= s.tags
        return tags

    @property
    def story_count(self) -> int:
        """Number of stories in memory."""
        return len(self._stories)

    @property
    def stories(self) -> dict[str, Story]:
        """Read-only access to the internal story dict."""
        return dict(self._stories)

    def __repr__(self) -> str:
        return f"Griot(name={self.name!r}, stories={self.story_count})"
