"""Praise names — dense semantic compression of a griot's stories."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from griotmath.memory import Griot


@dataclass
class PraiseName:
    """A praise name: a dense compression of a griot's story memory.

    Attributes:
        name: The praise name string.
        griot_name: Name of the griot being praised.
        story_ids: IDs of stories compressed into this name.
        compression_ratio: Ratio of total story content length to name length.
        density: Semantic density score (tags per character of name).
        total_weight: Sum of story weights at time of generation.
        total_tags: Union of all tags from included stories.
    """

    name: str
    griot_name: str
    story_ids: list[str]
    compression_ratio: float
    density: float
    total_weight: float
    total_tags: set[str]


def generate_praise_name(
    griot: Griot,
    story_ids: Optional[list[str]] = None,
    name: Optional[str] = None,
) -> PraiseName:
    """Generate a praise name compressing a griot's stories.

    If no story_ids are given, all stories are included.
    If no name is given, one is derived from tags.

    Args:
        griot: The griot whose stories to compress.
        story_ids: Optional list of story IDs (default: all stories).
        name: Optional explicit praise name (default: auto-derived).

    Returns:
        A PraiseName with compression metadata.
    """
    if story_ids is None:
        story_ids = list(griot.stories.keys())

    stories = []
    for sid in story_ids:
        s = griot.get_story(sid)
        if s is None:
            raise KeyError(f"Story '{sid}' not found in griot '{griot.name}'")
        stories.append(s)

    # Gather metrics
    total_content_len = sum(len(s.content) for s in stories)
    total_weight = sum(s.weight for s in stories)
    all_tags: set[str] = set()
    for s in stories:
        all_tags |= s.tags

    # Auto-derive name from tags if not given
    if name is None:
        sorted_tags = sorted(all_tags)
        if sorted_tags:
            # CamelCase join of tags
            name = "".join(t.capitalize() for t in sorted_tags)
        else:
            name = f"PraiseOf{griot.name}"

    name_len = max(len(name), 1)
    compression_ratio = total_content_len / name_len if total_content_len > 0 else 0.0
    density = len(all_tags) / name_len

    return PraiseName(
        name=name,
        griot_name=griot.name,
        story_ids=list(story_ids),
        compression_ratio=compression_ratio,
        density=density,
        total_weight=total_weight,
        total_tags=all_tags,
    )
