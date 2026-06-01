"""Comprehensive tests for griot-math."""

import math
import time

import pytest

from griotmath import Griot, Story
from griotmath.call_response import call_and_response
from griotmath.federation import Federation, MergeResult, SyncResult
from griotmath.genealogy import descendants, genealogy, tradition_score
from griotmath.praise import PraiseName, generate_praise_name


# ─── Story Tests ───────────────────────────────────────────────


class TestStory:
    def test_tell_increments_count(self):
        s = Story(id="s0", content="hello")
        assert s.tell_count == 0
        s.tell()
        assert s.tell_count == 1
        s.tell()
        assert s.tell_count == 2

    def test_tell_returns_content(self):
        s = Story(id="s1", content="a tale")
        assert s.tell() == "a tale"

    def test_tell_updates_last_told_at(self):
        s = Story(id="s2", content="test")
        assert s.last_told_at is None
        s.tell()
        assert s.last_told_at is not None
        assert s.last_told_at > 0

    def test_tell_boosts_weight(self):
        s = Story(id="s3", content="test", weight=1.0)
        old_weight = s.weight
        s.tell()
        assert s.weight > old_weight

    def test_age_property(self):
        s = Story(id="s4", content="test", created_at=time.time() - 10)
        assert s.age >= 10

    def test_time_since_told_never_told(self):
        s = Story(id="s5", content="test", created_at=time.time() - 5)
        assert s.time_since_told >= 5

    def test_time_since_told_after_tell(self):
        s = Story(id="s6", content="test")
        s.tell()
        assert s.time_since_told < 1.0

    def test_default_tags_empty(self):
        s = Story(id="s7", content="test")
        assert s.tags == set()

    def test_default_children_empty(self):
        s = Story(id="s8", content="test")
        assert s.children == []


# ─── Griot Tests ───────────────────────────────────────────────


class TestGriot:
    def test_create_griot(self):
        g = Griot(name="Anansi")
        assert g.name == "Anansi"
        assert g.story_count == 0

    def test_add_story_returns_id(self):
        g = Griot(name="G1")
        sid = g.add_story("A tale of wonder")
        assert isinstance(sid, str)
        assert len(sid) > 0

    def test_add_story_with_parent(self):
        g = Griot(name="G2")
        s1 = g.add_story("Parent tale")
        s2 = g.add_story("Child tale", parent_id=s1)
        parent = g.get_story(s1)
        assert s2 in parent.children

    def test_add_story_invalid_parent(self):
        g = Griot(name="G3")
        with pytest.raises(ValueError, match="Parent story"):
            g.add_story("Orphan", parent_id="nonexistent")

    def test_get_story(self):
        g = Griot(name="G4")
        sid = g.add_story("Find me", tags={"searchable"})
        story = g.get_story(sid)
        assert story is not None
        assert story.content == "Find me"

    def test_get_story_nonexistent(self):
        g = Griot(name="G5")
        assert g.get_story("nope") is None

    def test_tell_story(self):
        g = Griot(name="G6")
        sid = g.add_story("Tell this")
        result = g.tell_story(sid)
        assert result == "Tell this"
        assert g.get_story(sid).tell_count == 1

    def test_tell_story_nonexistent(self):
        g = Griot(name="G7")
        with pytest.raises(KeyError):
            g.tell_story("ghost")

    def test_apply_decay(self):
        g = Griot(name="G8")
        s1 = g.add_story("Old story", weight=1.0)
        # Make it age a bit
        g._stories[s1].created_at = time.time() - 100
        g.apply_decay(rate=0.01)
        assert g.get_story(s1).weight < 1.0

    def test_apply_decay_recent_story_less_decay(self):
        g = Griot(name="G9")
        old_id = g.add_story("Old")
        new_id = g.add_story("New")
        g._stories[old_id].created_at = time.time() - 1000
        g._stories[new_id].created_at = time.time()
        g.apply_decay(rate=0.01)
        old_w = g.get_story(old_id).weight
        new_w = g.get_story(new_id).weight
        assert new_w > old_w

    def test_memory_strengths(self):
        g = Griot(name="G10")
        g.add_story("A", weight=0.5)
        g.add_story("B", weight=0.8)
        strengths = g.memory_strengths()
        assert len(strengths) == 2
        values = list(strengths.values())
        assert 0.5 in values
        assert 0.8 in values

    def test_stories_by_tag(self):
        g = Griot(name="G11")
        g.add_story("Cosmic", tags={"origin", "cosmic"})
        g.add_story("Earthly", tags={"earth"})
        g.add_story("Also cosmic", tags={"cosmic"})
        cosmic = g.stories_by_tag("cosmic")
        assert len(cosmic) == 2

    def test_all_tags(self):
        g = Griot(name="G12")
        g.add_story("A", tags={"x", "y"})
        g.add_story("B", tags={"y", "z"})
        assert g.all_tags() == {"x", "y", "z"}

    def test_repr(self):
        g = Griot(name="TestRepr")
        g.add_story("Story")
        r = repr(g)
        assert "TestRepr" in r
        assert "1" in r


# ─── Praise Name Tests ────────────────────────────────────────


class TestPraiseName:
    def test_generate_all_stories(self):
        g = Griot(name="Singer")
        g.add_story("Tale one", tags={"fire", "water"})
        g.add_story("Tale two", tags={"earth"})
        pn = generate_praise_name(g)
        assert pn.griot_name == "Singer"
        assert len(pn.story_ids) == 2
        assert pn.compression_ratio > 0

    def test_generate_specific_stories(self):
        g = Griot(name="Chanter")
        s1 = g.add_story("A", tags={"alpha"})
        s2 = g.add_story("B", tags={"beta"})
        pn = generate_praise_name(g, story_ids=[s1])
        assert len(pn.story_ids) == 1
        assert s1 in pn.story_ids

    def test_explicit_name(self):
        g = Griot(name="Namer")
        g.add_story("Content here", tags={"x"})
        pn = generate_praise_name(g, name="Thread-Spinner")
        assert pn.name == "Thread-Spinner"

    def test_auto_name_from_tags(self):
        g = Griot(name="AutoNamer")
        g.add_story("Content", tags={"fire", "water"})
        pn = generate_praise_name(g)
        assert "Fire" in pn.name or "Water" in pn.name

    def test_compression_ratio(self):
        g = Griot(name="Compressor")
        g.add_story("A" * 100, tags={"tag"})
        pn = generate_praise_name(g, name="X")
        assert pn.compression_ratio >= 100  # 100 chars / 1 char

    def test_density(self):
        g = Griot(name="Dense")
        g.add_story("X", tags={"a", "b", "c"})
        pn = generate_praise_name(g, name="XX")
        assert pn.density == 3 / 2  # 3 tags / 2 chars

    def test_total_weight(self):
        g = Griot(name="Weigher")
        g.add_story("A", weight=0.3)
        g.add_story("B", weight=0.7)
        pn = generate_praise_name(g)
        assert abs(pn.total_weight - 1.0) < 1e-9

    def test_invalid_story_id(self):
        g = Griot(name="Bad")
        with pytest.raises(KeyError):
            generate_praise_name(g, story_ids=["ghost"])

    def test_empty_griot_auto_name(self):
        g = Griot(name="Empty")
        pn = generate_praise_name(g)
        assert "Empty" in pn.name
        assert pn.compression_ratio == 0.0


# ─── Call-and-Response Tests ──────────────────────────────────


class TestCallResponse:
    def test_basic_call_response(self):
        caller = Griot(name="Caller")
        responder = Griot(name="Responder")
        c1 = caller.add_story("Fire story", tags={"fire", "element"})
        r1 = responder.add_story("Water story", tags={"water", "element"})
        cr = call_and_response(caller, responder, c1)
        assert cr.response_story_id == r1
        assert cr.similarity > 0  # share "element"

    def test_no_match(self):
        caller = Griot(name="C")
        responder = Griot(name="R")
        c1 = caller.add_story("Fire", tags={"fire"})
        responder.add_story("Water", tags={"water"})
        cr = call_and_response(caller, responder, c1)
        assert cr.similarity == 0.0
        assert cr.response_story_id is None  # no overlapping tags → no match
        assert cr.shared_tags == set()

    def test_call_boosts_tell_count(self):
        caller = Griot(name="C")
        responder = Griot(name="R")
        c1 = caller.add_story("Tale", tags={"t"})
        responder.add_story("Reply", tags={"t"})
        call_and_response(caller, responder, c1)
        assert caller.get_story(c1).tell_count == 1

    def test_response_tells_story(self):
        caller = Griot(name="C")
        responder = Griot(name="R")
        c1 = caller.add_story("Tale", tags={"shared"})
        r1 = responder.add_story("Reply", tags={"shared"})
        cr = call_and_response(caller, responder, c1)
        assert cr.response_content == "Reply"
        assert responder.get_story(r1).tell_count == 1

    def test_invalid_call_story(self):
        caller = Griot(name="C")
        responder = Griot(name="R")
        with pytest.raises(KeyError):
            call_and_response(caller, responder, "ghost")

    def test_shared_tags(self):
        caller = Griot(name="C")
        responder = Griot(name="R")
        c1 = caller.add_story("Tale", tags={"a", "b", "c"})
        r1 = responder.add_story("Reply", tags={"b", "c", "d"})
        cr = call_and_response(caller, responder, c1)
        assert cr.shared_tags == {"b", "c"}

    def test_empty_responder(self):
        caller = Griot(name="C")
        responder = Griot(name="R")
        c1 = caller.add_story("Tale", tags={"t"})
        cr = call_and_response(caller, responder, c1)
        assert cr.response_story_id is None
        assert cr.response_content is None


# ─── Genealogy Tests ──────────────────────────────────────────


class TestGenealogy:
    def test_root_genealogy(self):
        g = Griot(name="G")
        s1 = g.add_story("Root")
        paths = genealogy(g, s1)
        assert paths == [[s1]]

    def test_linear_chain(self):
        g = Griot(name="G")
        s1 = g.add_story("Root")
        s2 = g.add_story("Child", parent_id=s1)
        s3 = g.add_story("Grandchild", parent_id=s2)
        paths = genealogy(g, s3)
        assert len(paths) == 1
        assert paths[0] == [s1, s2, s3]

    def test_branching_genealogy(self):
        g = Griot(name="G")
        root = g.add_story("Root")
        c1 = g.add_story("Child1", parent_id=root)
        c2 = g.add_story("Child2", parent_id=root)
        gc1 = g.add_story("GC1", parent_id=c1)
        paths = genealogy(g, gc1)
        assert paths == [[root, c1, gc1]]

    def test_descendants(self):
        g = Griot(name="G")
        root = g.add_story("Root")
        c1 = g.add_story("C1", parent_id=root)
        c2 = g.add_story("C2", parent_id=root)
        gc1 = g.add_story("GC1", parent_id=c1)
        desc = descendants(g, root)
        assert c1 in desc
        assert c2 in desc
        assert gc1 in desc
        assert root not in desc

    def test_descendants_leaf(self):
        g = Griot(name="G")
        s1 = g.add_story("Leaf")
        assert descendants(g, s1) == []

    def test_tradition_score_empty(self):
        g = Griot(name="Empty")
        assert tradition_score(g) == 0.0

    def test_tradition_score_single_story(self):
        g = Griot(name="G")
        g.add_story("Just one")
        score = tradition_score(g)
        assert 0.0 <= score <= 1.0

    def test_tradition_score_deep_tree(self):
        g = Griot(name="Deep")
        s = g.add_story("Root")
        for i in range(15):
            s = g.add_story(f"Level {i}", parent_id=s)
        score = tradition_score(g)
        assert score > 0.5

    def test_invalid_story_id(self):
        g = Griot(name="G")
        with pytest.raises(KeyError):
            genealogy(g, "ghost")


# ─── Federation Tests ─────────────────────────────────────────


class TestFederation:
    def test_add_griot(self):
        fed = Federation()
        g = Griot(name="A")
        fed.add_griot(g)
        assert fed.size == 1
        assert "A" in fed.griot_names

    def test_remove_griot(self):
        fed = Federation()
        g = Griot(name="B")
        fed.add_griot(g)
        fed.remove_griot("B")
        assert fed.size == 0

    def test_remove_nonexistent(self):
        fed = Federation()
        with pytest.raises(KeyError):
            fed.remove_griot("Ghost")

    def test_get_griot(self):
        fed = Federation()
        g = Griot(name="C")
        fed.add_griot(g)
        assert fed.get_griot("C") is g
        assert fed.get_griot("X") is None

    def test_sync_story(self):
        fed = Federation()
        a = Griot(name="A")
        b = Griot(name="B")
        fed.add_griot(a)
        fed.add_griot(b)
        s1 = a.add_story("Shared tale", tags={"shared"})
        result = fed.sync_story("A", "B", s1)
        assert result.success
        assert b.story_count == 1

    def test_sync_nonexistent_source(self):
        fed = Federation()
        b = Griot(name="B")
        fed.add_griot(b)
        result = fed.sync_story("Ghost", "B", "x")
        assert not result.success

    def test_sync_nonexistent_target(self):
        fed = Federation()
        a = Griot(name="A")
        fed.add_griot(a)
        s1 = a.add_story("Tale")
        result = fed.sync_story("A", "Ghost", s1)
        assert not result.success

    def test_sync_duplicate(self):
        fed = Federation()
        a = Griot(name="A")
        b = Griot(name="B")
        fed.add_griot(a)
        fed.add_griot(b)
        s1 = a.add_story("Tale")
        first = fed.sync_story("A", "B", s1)
        assert first.success
        # The story gets a new ID in B, so syncing again also succeeds (new ID)
        second = fed.sync_story("A", "B", s1)
        assert second.success  # Different ID assigned each sync
        assert b.story_count == 2

    def test_merge_memories(self):
        fed = Federation()
        a = Griot(name="A")
        b = Griot(name="B")
        a.add_story("Tale 1", tags={"a"})
        a.add_story("Tale 2", tags={"b"})
        fed.add_griot(a)
        fed.add_griot(b)
        result = fed.merge_memories("A", "B")
        assert result.stories_merged == 2
        assert b.story_count == 2

    def test_merge_with_conflicts(self):
        fed = Federation()
        a = Griot(name="A")
        b = Griot(name="B")
        # Both have same story ID (simulate by adding same-id story)
        s1 = a.add_story("Original")
        # Manually inject into b with same id to create conflict
        b._stories[s1] = Story(id=s1, content="Different")
        fed.add_griot(a)
        fed.add_griot(b)
        result = fed.merge_memories("A", "B")
        assert result.stories_skipped == 1
        assert s1 in result.conflicts

    def test_merge_overwrite(self):
        fed = Federation()
        a = Griot(name="A")
        b = Griot(name="B")
        s1 = a.add_story("Original")
        b._stories[s1] = Story(id=s1, content="Old")
        fed.add_griot(a)
        fed.add_griot(b)
        result = fed.merge_memories("A", "B", overwrite=True)
        assert result.stories_merged == 1
        assert b.get_story(s1).content == "Original"

    def test_total_stories(self):
        fed = Federation()
        a = Griot(name="A")
        b = Griot(name="B")
        a.add_story("T1")
        a.add_story("T2")
        b.add_story("T3")
        fed.add_griot(a)
        fed.add_griot(b)
        assert fed.total_stories() == 3

    def test_repr(self):
        fed = Federation()
        g = Griot(name="X")
        g.add_story("Tale")
        fed.add_griot(g)
        r = repr(fed)
        assert "Federation" in r
