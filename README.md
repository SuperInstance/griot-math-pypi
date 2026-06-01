# griot-math

Living memory systems for data scientists and ML engineers.

Stories, genealogy, praise names, call-and-response, and federated memory — as a pip-installable package.

## Install

```bash
pip install griot-math
```

## Quick Start

```python
from griotmath import Griot

griot = Griot(name="Anansi")
s1 = griot.add_story("In the beginning, there was only darkness.", tags=["origin", "cosmic"])
s2 = griot.add_story("The spider spun a thread of light.", parent_id=s1, tags=["light", "spider"])

# Story decay and retrieval
griot.apply_decay(rate=0.1)
strengths = griot.memory_strengths()

# Genealogy
from griotmath.genealogy import genealogy, descendants, tradition_score
paths = genealogy(griot, s2)
score = tradition_score(griot)

# Praise names — dense semantic compression
from griotmath.praise import generate_praise_name
pn = generate_praise_name(griot, [s1, s2], name="Thread-Spinner")

# Call-and-response
from griotmath.call_response import call_and_response
caller = Griot(name="Caller")
responder = Griot(name="Responder")
# ...

# Federation
from griotmath.federation import Federation
fed = Federation()
fed.add_griot(griot)
```

## Concepts

- **Griot**: A living memory keeper. Stories have weight, tags, tell count, and genealogy.
- **Decay**: Memory follows exponential decay — stories weaken over time unless retold.
- **Praise Name**: Dense semantic compression of a griot's stories into a name with metadata.
- **Call-and-Response**: Tag-based similarity matching between griots.
- **Genealogy**: Ancestry paths, descendants, and tradition scores.
- **Federation**: Distributed memory across multiple griots with sync and merge.

## License

MIT
