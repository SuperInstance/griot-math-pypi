"""Call-and-response between griots — tag-based similarity matching."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from griotmath.memory import Griot


@dataclass
class CallResponse:
    """Result of a call-and-response exchange between two griots.

    Attributes:
        caller_name: Name of the calling griot.
        responder_name: Name of the responding griot.
        call_story_id: The story ID that initiated the call.
        response_story_id: The best-matching response story ID.
        response_content: The content of the response story.
        similarity: Tag-based Jaccard similarity score (0.0–1.0).
        shared_tags: Tags shared between call and response stories.
    """

    caller_name: str
    responder_name: str
    call_story_id: str
    response_story_id: Optional[str]
    response_content: Optional[str]
    similarity: float
    shared_tags: set[str]


def _jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity between two sets."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def call_and_response(
    caller: Griot,
    responder: Griot,
    story_id: str,
) -> CallResponse:
    """Perform a call-and-response between two griots.

    The caller tells a story (by ID), and the responder finds the
    best-matching story based on tag similarity (Jaccard index).

    Args:
        caller: The calling griot.
        responder: The responding griot.
        story_id: The story ID in the caller's memory to call with.

    Returns:
        A CallResponse with the match details.

    Raises:
        KeyError: If story_id doesn't exist in caller's memory.
    """
    call_story = caller.get_story(story_id)
    if call_story is None:
        raise KeyError(f"Story '{story_id}' not found in caller '{caller.name}'")

    # Tell the story (boosts its weight)
    caller.tell_story(story_id)

    # Find best matching story in responder
    best_match: Optional[str] = None
    best_similarity: float = 0.0
    best_shared: set[str] = set()

    for sid, story in responder.stories.items():
        sim = _jaccard(call_story.tags, story.tags)
        if sim > best_similarity:
            best_similarity = sim
            best_match = sid
            best_shared = call_story.tags & story.tags

    response_content: Optional[str] = None
    if best_match is not None:
        response_content = responder.tell_story(best_match)

    return CallResponse(
        caller_name=caller.name,
        responder_name=responder.name,
        call_story_id=story_id,
        response_story_id=best_match,
        response_content=response_content,
        similarity=best_similarity,
        shared_tags=best_shared,
    )
