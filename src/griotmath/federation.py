"""Federation — distributed memory across multiple griots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from griotmath.memory import Griot, Story


@dataclass
class SyncResult:
    """Result of syncing a story between griots.

    Attributes:
        story_id: The story ID that was synced.
        source: Name of the source griot.
        target: Name of the target griot.
        success: Whether the sync succeeded.
        message: Human-readable status.
    """

    story_id: str
    source: str
    target: str
    success: bool
    message: str


@dataclass
class MergeResult:
    """Result of merging memories between griots.

    Attributes:
        source: Name of the source griot.
        target: Name of the target griot.
        stories_merged: Number of stories merged.
        stories_skipped: Number of stories skipped (already present).
        conflicts: List of story IDs that had conflicts.
    """

    source: str
    target: str
    stories_merged: int
    stories_skipped: int
    conflicts: list[str] = field(default_factory=list)


class Federation:
    """A federation of griots — distributed memory with sync and merge.

    Manages a collection of Griots and provides operations for
    synchronizing and merging stories across them.
    """

    def __init__(self) -> None:
        self._griots: dict[str, Griot] = {}

    def add_griot(self, griot: Griot) -> None:
        """Add a griot to the federation.

        Args:
            griot: The Griot instance to add.
        """
        self._griots[griot.name] = griot

    def remove_griot(self, name: str) -> None:
        """Remove a griot by name.

        Args:
            name: Name of the griot to remove.

        Raises:
            KeyError: If griot not found.
        """
        if name not in self._griots:
            raise KeyError(f"Griot '{name}' not in federation")
        del self._griots[name]

    def get_griot(self, name: str) -> Optional[Griot]:
        """Get a griot by name, or None."""
        return self._griots.get(name)

    @property
    def griot_names(self) -> list[str]:
        """Names of all griots in the federation."""
        return list(self._griots.keys())

    @property
    def size(self) -> int:
        """Number of griots in the federation."""
        return len(self._griots)

    def sync_story(
        self,
        source_name: str,
        target_name: str,
        story_id: str,
    ) -> SyncResult:
        """Sync a single story from one griot to another.

        Copies the story (without genealogy links) from source to target.

        Args:
            source_name: Name of the source griot.
            target_name: Name of the target griot.
            story_id: Story ID to sync.

        Returns:
            A SyncResult with details.
        """
        source = self._griots.get(source_name)
        target = self._griots.get(target_name)

        if source is None:
            return SyncResult(story_id, source_name, target_name, False,
                              f"Source griot '{source_name}' not found")
        if target is None:
            return SyncResult(story_id, source_name, target_name, False,
                              f"Target griot '{target_name}' not found")

        story = source.get_story(story_id)
        if story is None:
            return SyncResult(story_id, source_name, target_name, False,
                              f"Story '{story_id}' not found in '{source_name}'")

        # Check if already present
        existing = target.get_story(story_id)
        if existing is not None:
            return SyncResult(story_id, source_name, target_name, False,
                              f"Story '{story_id}' already exists in '{target_name}'")

        # Create a copy without parent/children (genealogy doesn't transfer)
        new_id = target.add_story(
            content=story.content,
            weight=story.weight,
            tags=story.tags,
        )
        # Preserve tell count and timing
        new_story = target.get_story(new_id)
        if new_story is not None:
            new_story.tell_count = story.tell_count
            new_story.created_at = story.created_at
            new_story.last_told_at = story.last_told_at

        return SyncResult(story_id, source_name, target_name, True,
                          f"Synced '{story_id}' → '{target_name}' as '{new_id}'")

    def merge_memories(
        self,
        source_name: str,
        target_name: str,
        overwrite: bool = False,
    ) -> MergeResult:
        """Merge all stories from source griot into target griot.

        Args:
            source_name: Name of the source griot.
            target_name: Name of the target griot.
            overwrite: If True, overwrite existing stories. Default False.

        Returns:
            A MergeResult with merge statistics.

        Raises:
            KeyError: If either griot doesn't exist.
        """
        source = self._griots.get(source_name)
        target = self._griots.get(target_name)

        if source is None:
            raise KeyError(f"Source griot '{source_name}' not found")
        if target is None:
            raise KeyError(f"Target griot '{target_name}' not found")

        merged = 0
        skipped = 0
        conflicts: list[str] = []

        for sid, story in source.stories.items():
            existing = target.get_story(sid)
            if existing is not None:
                if overwrite:
                    # Update existing story
                    existing.content = story.content
                    existing.weight = story.weight
                    existing.tags = story.tags
                    merged += 1
                else:
                    conflicts.append(sid)
                    skipped += 1
            else:
                # Add new story (without genealogy)
                new_id = target.add_story(
                    content=story.content,
                    weight=story.weight,
                    tags=story.tags,
                )
                new_story = target.get_story(new_id)
                if new_story is not None:
                    new_story.tell_count = story.tell_count
                    new_story.created_at = story.created_at
                    new_story.last_told_at = story.last_told_at
                merged += 1

        return MergeResult(
            source=source_name,
            target=target_name,
            stories_merged=merged,
            stories_skipped=skipped,
            conflicts=conflicts,
        )

    def total_stories(self) -> int:
        """Total stories across all griots in the federation."""
        return sum(g.story_count for g in self._griots.values())

    def __repr__(self) -> str:
        return f"Federation(griots={self.size}, total_stories={self.total_stories()})"
