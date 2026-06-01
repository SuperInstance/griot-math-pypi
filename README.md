# griot-math

> Living memory mathematics — West African griot oral tradition as exponential decay, genealogy trees, and federated memory.

## What This Does

`griot-math` implements the mathematics of oral memory systems inspired by West African griots (storytellers, historians, praise singers). It models stories with importance-weighted exponential decay, genealogy trees tracking story lineage, praise names as lossy compression of memory, call-and-response protocols for memory similarity, and federated memory networks where multiple griots sync and merge their memories. Use it for caching systems with cultural decay models, knowledge graph lineage tracking, or distributed consensus on shared narratives.

## The Cultural Root

Griots (jali in Mandinka) are West African oral historians who maintain genealogies, histories, and cultural knowledge across generations. Stories told more frequently are remembered better; stories that aren't told decay. The mathematical insight: **memory follows exponential decay weighted by retelling frequency** — identical to how reinforcement learning weights recent rewards. Praise names compress a griot's entire repertoire into a single dense identifier, like a hash of a merkle tree.

## Install

```bash
pip install griot-math
```

## Quick Start

```python
from griotmath.memory import Griot, Story
from griotmath.genealogy import genealogy, descendants, tradition_score
from griotmath.praise import generate_praise_name
from griotmath.call_response import call_and_response
from griotmath.federation import Federation

# Create a griot and add stories
griot = Griot()
s1 = griot.add_story("The founding of the village", weight=1.0, tags=["history", "origin"])
s2 = griot.add_story("The great flood", weight=0.8, parent_id=s1, tags=["disaster"])
s3 = griot.add_story("Rebuilding after the flood", weight=0.9, parent_id=s2, tags=["recovery"])

# Tell a story — boosts its weight
griot.tell_story(s1)
griot.tell_story(s1)  # telling again makes it stronger

# Apply time-based decay
griot.apply_decay(rate=0.01, elapsed=3600)  # 1 hour of decay

# Check memory strengths
strengths = griot.memory_strengths()

# Genealogy — trace story lineage
path = genealogy(griot, s3)
# [s1, s2, s3] — from root to the given story

kids = descendants(griot, s1)
# [s2, s3] — all descendants

score = tradition_score(griot)  # 0.0–1.0 depth/breadth score

# Praise name — compress stories into a dense identifier
praise = generate_praise_name(griot, story_ids=[s1, s2, s3], name="Keeper of Origins")
print(f"Compression ratio: {praise.compression_ratio:.2f}")
print(f"Density: {praise.density:.2f}")

# Call and response between griots
griot2 = Griot()
griot2.add_story("The great flood", weight=0.5)
griot2.add_story("A different flood story", weight=0.3)
result = call_and_response(griot, griot2, caller_story_id=s2)
print(f"Similarity: {result.similarity:.2f}")
print(f"Matched: {result.responder_name}")

# Federation — distributed memory
fed = Federation()
fed.add_griot(griot)
fed.add_griot(griot2)
sync = fed.sync_story(from_name="griot-0", to_name="griot-1", story_id=s2)
merge = fed.merge_memories(source_name="griot-0", target_name="griot-1")
print(f"Total stories: {fed.total_stories()}")
```

## API Reference

### `memory` module

#### `Story`
```python
@dataclass
class Story:
    id: str
    content: str
    weight: float         # Importance (0–∞)
    tags: list[str]
    parent_id: str | None
    tell_count: int       # Times told
    created_at: float     # Timestamp
    last_told_at: float

    def tell(self) -> None       # Increment tell count, boost weight
    def age(self) -> float       # Seconds since creation
    def time_since_told(self) -> float
```

#### `Griot`
```python
class Griot:
    def add_story(self, content, weight=1.0, parent_id=None, tags=None) -> str
    def get_story(self, story_id) -> Story | None
    def tell_story(self, story_id) -> str
    def apply_decay(self, rate=0.01, elapsed=None) → None
    def memory_strengths(self) → dict[str, float]
    def stories_by_tag(self, tag) → list[Story]
    def all_tags(self) → set[str]
    def story_count(self) → int
```

### `genealogy` module

#### `genealogy(griot, story_id) → list[str]`
All ancestry paths from root to the given story.

#### `descendants(griot, story_id) → list[str]`
All descendant story IDs (breadth-first).

#### `tradition_score(griot) → float`
0.0–1.0 score based on genealogy tree depth and breadth.

### `praise` module

#### `PraiseName`
```python
@dataclass
class PraiseName:
    name: str
    story_ids: list[str]
    compression_ratio: float
    density: float
```

#### `generate_praise_name(griot, story_ids=None, name=None) → PraiseName`
Compress selected stories into a praise name. Compression ratio = total weight / count. Density = weight concentration.

### `call_response` module

#### `CallResponse`
```python
@dataclass
class CallResponse:
    caller_name: str
    responder_name: str
    caller_story: str
    responder_story: str
    similarity: float  # Jaccard similarity
```

#### `call_and_response(caller, responder, caller_story_id) → CallResponse`
The caller tells a story; the responder finds the closest match by tag overlap (Jaccard similarity).

### `federation` module

#### `Federation`
```python
class Federation:
    def add_griot(self, griot) → None
    def remove_griot(self, name) → None
    def get_griot(self, name) → Griot | None
    def griot_names(self) → list[str]
    def size(self) → int
    def sync_story(self, from_name, to_name, story_id) → SyncResult
    def merge_memories(self, source_name, target_name) → MergeResult
    def total_stories(self) → int
```

#### `SyncResult`
Result of syncing one story between griots.

#### `MergeResult`
Result of merging all stories: `added`, `updated`, `skipped`, `conflicts`.

## How It Works

**Memory Decay:** Each story has a weight that decays exponentially: w(t) = w₀ · e^(−λ·Δt), where λ is the decay rate and Δt is time since last telling. Telling a story boosts its weight by a fixed increment, counteracting decay.

**Genealogy:** Stories form a tree via `parent_id`. Genealogy traces ancestry paths; descendants uses BFS. Tradition score normalizes depth × breadth to [0, 1].

**Praise Names:** A lossy compression of multiple stories into a single identifier. Compression ratio = Σ weights / n. Density = max weight / total weight. A good praise name has high density (concentrated meaning).

**Call-and-Response:** Uses Jaccard similarity on tag sets: J(A, B) = |A ∩ B| / |A ∪ B|. The responder returns the story with highest tag overlap.

**Federation:** Distributed memory with sync (copy one story) and merge (copy all with conflict resolution — keep higher weight on conflict).

## The Math

**Exponential Decay:** w(t + Δt) = w(t) · e^(−λΔt). This is the same model as radioactive decay, capacitor discharge, and discount factors in reinforcement learning.

**Jaccard Similarity:** J(A, B) = |A ∩ B| / |A ∪ B| ∈ [0, 1].

**Tradition Score:** Based on tree depth and breadth, normalized: score = f(max_depth, max_breadth, n_stories) ∈ [0, 1].

## License

MIT
