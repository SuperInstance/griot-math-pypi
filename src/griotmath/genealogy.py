"""Genealogy — ancestry paths, descendants, and tradition scores."""

from __future__ import annotations

from typing import Optional

from griotmath.memory import Griot


def genealogy(griot: Griot, story_id: str) -> list[list[str]]:
    """Return all ancestry paths from a story back to its roots.

    Each path is a list of story IDs from root → ... → story_id.

    Args:
        griot: The griot whose memory to traverse.
        story_id: The story to trace ancestry for.

    Returns:
        List of ancestry paths. Each path is [root_id, ..., story_id].

    Raises:
        KeyError: If story_id doesn't exist.
    """
    story = griot.get_story(story_id)
    if story is None:
        raise KeyError(f"Story '{story_id}' not found in griot '{griot.name}'")

    if story.parent_id is None:
        return [[story_id]]

    parent_paths = genealogy(griot, story.parent_id)
    return [path + [story_id] for path in parent_paths]


def descendants(griot: Griot, story_id: str) -> list[str]:
    """Return all descendant story IDs (breadth-first).

    Args:
        griot: The griot whose memory to traverse.
        story_id: The root story to find descendants for.

    Returns:
        List of descendant story IDs (not including story_id itself).

    Raises:
        KeyError: If story_id doesn't exist.
    """
    story = griot.get_story(story_id)
    if story is None:
        raise KeyError(f"Story '{story_id}' not found in griot '{griot.name}'")

    result: list[str] = []
    queue = list(story.children)
    visited: set[str] = set()

    while queue:
        cid = queue.pop(0)
        if cid in visited:
            continue
        visited.add(cid)
        result.append(cid)
        child = griot.get_story(cid)
        if child is not None:
            queue.extend(child.children)

    return result


def tradition_score(griot: Griot) -> float:
    """Compute a tradition score (0.0–1.0) for a griot.

    Based on the depth and breadth of genealogy trees:
    - More ancestral depth → higher score
    - More branching → higher score
    - Weighted by story weights

    Returns:
        A float between 0.0 and 1.0.
    """
    if griot.story_count == 0:
        return 0.0

    # Find root stories (no parent)
    roots = [s for s in griot.stories.values() if s.parent_id is None]
    if not roots:
        return 0.0

    total_score = 0.0
    total_weight = 0.0

    for root in roots:
        # Compute tree depth and breadth
        max_depth = _tree_depth(griot, root.id)
        desc_count = len(descendants(griot, root.id))

        # Score: normalized depth + breadth contribution
        depth_score = min(max_depth / 10.0, 1.0)  # Cap at depth 10
        breadth_score = min(desc_count / 20.0, 1.0)  # Cap at 20 descendants
        tree_score = 0.5 * depth_score + 0.5 * breadth_score

        total_score += tree_score * root.weight
        total_weight += root.weight

    if total_weight == 0:
        return 0.0

    # Normalize to [0, 1]
    raw = total_score / total_weight
    return min(max(raw, 0.0), 1.0)


def _tree_depth(griot: Griot, story_id: str) -> int:
    """Compute the depth of the tree rooted at story_id."""
    story = griot.get_story(story_id)
    if story is None or not story.children:
        return 1
    return 1 + max(_tree_depth(griot, cid) for cid in story.children)
