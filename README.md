# Semantic Manager Python SDK

A Python client for the [Semantic Manager](https://github.com/your-org/semantic-manager) vocabulary service. Search controlled vocabulary terms, browse ontology namespaces, and annotate your datasets with standardised IRIs — all from Python.

```python
from semantic_manager import SemanticManager, TermType

sm = SemanticManager("https://api.example.com", token="eyJ...")

term = sm.find_term("thermal conductivity", type=TermType.DATA_PROPERTY)
print(term.iri)
# https://w3id.org/bwmd/ontologies/ThermalConductivity
```

---

## Table of Contents

1. [Installation](#installation)
2. [Authentication](#authentication)
   - [Bearer Token](#bearer-token)
   - [Username and Password (Keycloak)](#username-and-password-keycloak)
3. [Browsing Namespaces](#browsing-namespaces)
4. [Searching for Terms](#searching-for-terms)
   - [Type Filters](#type-filters)
   - [Namespace Filters](#namespace-filters)
   - [Pagination](#pagination)
   - [Facets and Counts](#facets-and-counts)
5. [Working with Terms](#working-with-terms)
   - [Term Fields](#term-fields)
   - [Annotation Helpers](#annotation-helpers)
6. [Real-World Examples](#real-world-examples)
   - [Annotating a Pandas DataFrame](#annotating-a-pandas-dataframe)
   - [Producing JSON-LD Output](#producing-json-ld-output)
   - [Building an Annotation Pipeline](#building-an-annotation-pipeline)
7. [Error Handling](#error-handling)
8. [API Reference](#api-reference)
9. [Contributing](#contributing)
10. [License](#license)

---

## Installation

```bash
pip install semantic-manager
```

Requires Python ≥ 3.9. The only runtime dependency is [`requests`](https://docs.python-requests.org/).

---

## Authentication

### Bearer Token

The simplest option. Obtain a token from your Semantic Manager instance (via the web UI or a Keycloak client credentials flow) and pass it directly:

```python
from semantic_manager import SemanticManager

sm = SemanticManager(
    "https://api.example.com",
    token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
)
```

The `"Bearer "` prefix is optional — the SDK adds it if absent.

### Username and Password (Keycloak)

If your organisation uses Keycloak for identity management you can authenticate directly with credentials. The SDK exchanges them for a JWT behind the scenes:

```python
sm = SemanticManager(
    "https://api.example.com",
    username="alice",
    password="s3cr3t",
    keycloak_url="https://auth.example.com",  # base URL of your Keycloak server
    realm="myrealm",                          # Keycloak realm name
    client_id="vocabulary-service",           # optional, default shown
)
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `base_url` | ✅ | — | Base URL of the Semantic Manager API |
| `token` | one of these | — | Pre-obtained bearer token |
| `username` + `password` + `keycloak_url` | one of these | — | Keycloak credentials |
| `realm` | only with credentials | `"master"` | Keycloak realm |
| `client_id` | only with credentials | `"vocabulary-service"` | Keycloak client ID |
| `verify_ssl` | ❌ | `True` | Set `False` for self-signed certs in dev environments |
| `timeout` | ❌ | `30` | Request timeout in seconds |

---

## Browsing Namespaces

### List all namespaces

```python
namespaces = sm.namespaces()
# Returns: list[Namespace]

for ns in namespaces:
    print(ns.id, ns.name, ns.version)
    for uc in ns.use_cases:
        print("  use-case:", uc.id, uc.name)
```

### Fetch a single namespace

```python
ns = sm.namespace("bwmd")

print(ns.name)        # "BWMD Ontology"
print(ns.base_iri)    # "https://w3id.org/bwmd/ontologies/"
print(ns.version)     # "1.2.0"
print(ns.mutable)     # False  (read-only)
print(ns.use_cases)   # [UseCase(id='base', name='Base')]
```

### Namespace fields

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Unique slug (e.g. `"dcat"`, `"bwmd"`) |
| `name` | `str` | Human-readable name |
| `description` | `str \| None` | Short description |
| `version` | `str \| None` | Ontology version string |
| `base_iri` | `str \| None` | Base IRI for terms |
| `reference_url` | `str \| None` | Link to ontology documentation |
| `mutable` | `bool` | Whether terms can be edited via the UI |
| `use_cases` | `list[UseCase]` | Scoped subsets of this namespace |

---

## Searching for Terms

```python
results = sm.search("temperature")
# Returns: list[Term], ordered by relevance
```

### Type Filters

Use `TermType` constants to restrict results to a specific RDF type:

```python
from semantic_manager import TermType

# Only OWL classes
classes = sm.search("material", type=TermType.CLASS)

# Only datatype properties (measurable quantities)
properties = sm.search("pressure", type=TermType.DATA_PROPERTY)

# Only object properties (relationships between entities)
relations = sm.search("has part", type=TermType.OBJECT_PROPERTY)
```

| Constant | RDF type | Typical use |
|---|---|---|
| `TermType.ALL` | — | No filter (default) |
| `TermType.CLASS` | `owl:Class` | Concepts, categories |
| `TermType.DATA_PROPERTY` | `owl:DatatypeProperty` | Measurable quantities, attributes |
| `TermType.OBJECT_PROPERTY` | `owl:ObjectProperty` | Relationships between entities |
| `TermType.ANNOTATION_PROPERTY` | `owl:AnnotationProperty` | Metadata properties |
| `TermType.PROPERTY` | `rdf:Property` | Generic properties |
| `TermType.MEASUREMENT_UNIT` | — | Units of measurement |
| `TermType.SKOS_CONCEPT` | `skos:Concept` | Thesaurus / taxonomy concepts |
| `TermType.NAMED_INDIVIDUAL` | `owl:NamedIndividual` | Specific instances |

### Namespace Filters

Search within one or more specific namespaces:

```python
# Single namespace
results = sm.search("heat", namespaces=["bwmd"])

# Multiple namespaces
results = sm.search("agent", namespaces=["dcat", "dcterms"])
```

### Pagination

```python
page_1 = sm.search("material", limit=20, offset=0)
page_2 = sm.search("material", limit=20, offset=20)
```

### Facets and Counts

Get a summary of what is available before fetching full results:

```python
# Total number of matches
total = sm.search_count("temperature")
print(f"{total} terms match 'temperature'")

# Counts grouped by type and namespace
facets = sm.search_facets("material")
print(facets["type_counts"])
# {'class': 24, 'data_property': 7, 'object_property': 3, ...}
print(facets["namespace_counts"])
# {'bwmd': 18, 'dcat': 5, 'dcterms': 2, ...}
```

---

## Working with Terms

### Term Fields

| Field | Type | Description |
|---|---|---|
| `iri` | `str` | Globally unique IRI |
| `label` | `str` | Human-readable label |
| `type` | `str` | RDF type IRI or short name |
| `namespace` | `str` | Namespace this term belongs to |
| `description` | `str \| None` | Definition or scope note |
| `language` | `str` | Language tag of the label (e.g. `"en"`) |

### Annotation Helpers

#### `term.as_annotation()` → `dict`

Returns a compact dict for embedding in dataset metadata:

```python
term = sm.find_term("temperature", type=TermType.DATA_PROPERTY)
ann = term.as_annotation()
# {
#   "iri":         "https://w3id.org/bwmd/ontologies/Temperature",
#   "label":       "temperature",
#   "type":        "data_property",
#   "namespace":   "bwmd",
#   "description": "Degree of hotness or coldness measured on a scale."
# }
```

#### `term.as_jsonld()` → `dict`

Returns a JSON-LD compatible representation:

```python
print(term.as_jsonld())
# {
#   "@context": {"rdfs": "...", "rdf": "...", "owl": "..."},
#   "@id":      "https://w3id.org/bwmd/ontologies/Temperature",
#   "@type":    "data_property",
#   "rdfs:label": "temperature"
# }
```

#### `sm.find_term(query)` → `Term | None`

Returns the single best match or `None` — safe for automation:

```python
term = sm.find_term("viscosity", type=TermType.DATA_PROPERTY)
if term:
    annotations["viscosity"] = term.iri
```

#### `sm.resolve(iris)` → `list[Term]`

Resolve known IRIs back to full Term objects:

```python
terms = sm.resolve([
    "https://w3id.org/bwmd/ontologies/Temperature",
    "https://w3id.org/bwmd/ontologies/Pressure",
])
```

---

## Real-World Examples

### Annotating a Pandas DataFrame

Attach standardised IRIs to DataFrame columns so downstream tools know exactly what each measurement represents:

```python
import pandas as pd
from semantic_manager import SemanticManager, TermType

sm = SemanticManager("https://api.example.com", token="eyJ...")

# Your measurement data
df = pd.DataFrame({
    "timestamp":   ["2024-01-01T08:00", "2024-01-01T08:01"],
    "temperature": [1450.2, 1452.1],   # furnace °C
    "pressure":    [1.013,  1.014],    # bar
    "flow_rate":   [12.5,   12.7],     # L/min
})

# Map each column to a vocabulary term
column_map = {
    "temperature": ("temperature",  TermType.DATA_PROPERTY),
    "pressure":    ("pressure",     TermType.DATA_PROPERTY),
    "flow_rate":   ("flow rate",    TermType.DATA_PROPERTY),
}

annotations = {}
for column, (query, term_type) in column_map.items():
    term = sm.find_term(query, type=term_type)
    if term:
        annotations[column] = term.as_annotation()

# Store annotations as DataFrame metadata
df.attrs["column_annotations"] = annotations

# Persist — pandas preserves .attrs in Parquet format
df.to_parquet("measurements_annotated.parquet")

# Recover annotations when loading
df2 = pd.read_parquet("measurements_annotated.parquet")
for col, ann in df2.attrs["column_annotations"].items():
    print(f"{col}: {ann['iri']}")
```

**Output:**
```
temperature: https://w3id.org/bwmd/ontologies/Temperature
pressure:    https://w3id.org/bwmd/ontologies/Pressure
flow_rate:   https://w3id.org/bwmd/ontologies/FlowRate
```

---

### Producing JSON-LD Output

Publish measurement records as linked data with a machine-readable `@context`:

```python
import json
from semantic_manager import SemanticManager, TermType

sm = SemanticManager("https://api.example.com", token="eyJ...")

record = {
    "sensor_id":   "S-4712",
    "temperature": 1452.3,
    "pressure":    1.014,
    "timestamp":   "2024-01-01T08:01:00Z",
}

# Build @context dynamically from vocabulary
context = {"xsd": "http://www.w3.org/2001/XMLSchema#"}

for field in ("temperature", "pressure"):
    term = sm.find_term(field, type=TermType.DATA_PROPERTY)
    if term:
        context[field] = {"@id": term.iri, "@type": "xsd:double"}

jsonld_record = {"@context": context, **record}
print(json.dumps(jsonld_record, indent=2))
```

**Output:**
```json
{
  "@context": {
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "temperature": {
      "@id": "https://w3id.org/bwmd/ontologies/Temperature",
      "@type": "xsd:double"
    },
    "pressure": {
      "@id": "https://w3id.org/bwmd/ontologies/Pressure",
      "@type": "xsd:double"
    }
  },
  "sensor_id": "S-4712",
  "temperature": 1452.3,
  "pressure": 1.014,
  "timestamp": "2024-01-01T08:01:00Z"
}
```

---

### Building an Annotation Pipeline

Annotate all columns in a data schema automatically, with a fallback for unknown terms:

```python
from dataclasses import dataclass
from typing import Optional
from semantic_manager import SemanticManager, TermType

sm = SemanticManager("https://api.example.com", token="eyJ...")

@dataclass
class ColumnSchema:
    name: str
    unit: str
    query_hint: str
    term_type: str = TermType.DATA_PROPERTY

SCHEMA = [
    ColumnSchema("melt_temperature",  "°C",    "melting temperature"),
    ColumnSchema("viscosity",          "Pa·s",  "dynamic viscosity"),
    ColumnSchema("grain_size",         "µm",    "grain size"),
    ColumnSchema("yield_strength",     "MPa",   "yield strength"),
    ColumnSchema("material_class",     "",      "material class",    TermType.CLASS),
]

print(f"{'Column':<25} {'Matched Term':<40} {'IRI'}")
print("-" * 110)

for col in SCHEMA:
    term = sm.find_term(col.query_hint, type=col.term_type)
    if term:
        print(f"{col.name:<25} {term.label:<40} {term.iri}")
    else:
        print(f"{col.name:<25} {'[no match — manual review needed]':<40}")
```

**Output:**
```
Column                    Matched Term                             IRI
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
melt_temperature          melting temperature                      https://w3id.org/bwmd/ontologies/MeltingTemperature
viscosity                 dynamic viscosity                        https://w3id.org/bwmd/ontologies/DynamicViscosity
grain_size                grain size                               https://w3id.org/bwmd/ontologies/GrainSize
yield_strength            yield strength                           https://w3id.org/bwmd/ontologies/YieldStrength
material_class            material class                           https://w3id.org/bwmd/ontologies/MaterialClass
```

---

## Error Handling

```python
from semantic_manager import (
    SemanticManager,
    AuthenticationError,
    NotFoundError,
    APIError,
    SemanticManagerError,
)

try:
    sm = SemanticManager("https://api.example.com", token="bad-token")
    ns = sm.namespace("does-not-exist")

except AuthenticationError:
    print("Token rejected — check credentials or expiry.")

except NotFoundError as e:
    print(f"Resource not found: {e}")

except APIError as e:
    print(f"Server error {e.status_code}: {e.detail}")

except SemanticManagerError as e:
    # Catch-all for any SDK error
    print(f"SDK error: {e}")
```

| Exception | HTTP status | When raised |
|---|---|---|
| `AuthenticationError` | 401 | Invalid or expired token / wrong credentials |
| `NotFoundError` | 404 | Namespace or resource does not exist |
| `APIError` | other 4xx / 5xx | Unexpected server error; check `.status_code` and `.detail` |
| `SemanticManagerError` | — | Base class for all SDK exceptions |

---

## API Reference

### `SemanticManager`

#### `__init__(base_url, *, token=None, username=None, password=None, keycloak_url=None, realm="master", client_id="vocabulary-service", verify_ssl=True, timeout=30)`

Create an authenticated client instance.

---

#### `namespaces() → list[Namespace]`

Return all registered namespaces including their use cases.

---

#### `namespace(namespace_id: str) → Namespace`

Return a single namespace by ID. Raises `NotFoundError` if not found.

---

#### `search(query, *, type=TermType.ALL, namespaces=None, limit=50, offset=0) → list[Term]`

Search vocabulary terms across all (or selected) namespaces.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | required | Free-text search string |
| `type` | `str` | `TermType.ALL` | RDF type filter (see `TermType`) |
| `namespaces` | `list[str] \| None` | `None` (all) | Restrict to these namespace IDs |
| `limit` | `int` | `50` | Maximum results |
| `offset` | `int` | `0` | Pagination offset |

---

#### `search_count(query, *, type=TermType.ALL, namespaces=None) → int`

Return the total number of matching terms without fetching them.

---

#### `search_facets(query, *, type=TermType.ALL, namespaces=None) → dict`

Return `{"type_counts": {...}, "namespace_counts": {...}}` for the query.

---

#### `find_term(query, *, type=TermType.ALL, namespaces=None) → Term | None`

Return the best single match, or `None` if no results.

---

#### `resolve(iris: list[str]) → list[Term]`

Look up full term details for a list of known IRIs.

---

### `Term`

| Attribute | Type | Description |
|---|---|---|
| `iri` | `str` | Globally unique IRI |
| `label` | `str` | Human-readable label |
| `type` | `str` | RDF type |
| `namespace` | `str` | Source namespace ID |
| `description` | `str \| None` | Definition |
| `language` | `str` | Language tag (e.g. `"en"`) |

**Methods:**
- `as_annotation() → dict` — compact dict for metadata storage
- `as_jsonld() → dict` — JSON-LD compatible representation

---

### `Namespace`

| Attribute | Type | Description |
|---|---|---|
| `id` | `str` | Unique slug |
| `name` | `str` | Display name |
| `description` | `str \| None` | Short description |
| `version` | `str \| None` | Version string |
| `base_iri` | `str \| None` | Base IRI prefix |
| `reference_url` | `str \| None` | Documentation URL |
| `mutable` | `bool` | Whether editable via UI |
| `use_cases` | `list[UseCase]` | Scoped subsets |

---

### `UseCase`

| Attribute | Type | Description |
|---|---|---|
| `id` | `str` | Unique slug within the namespace |
| `name` | `str` | Display name |
| `description` | `str \| None` | Short description |
| `mutable` | `bool` | Whether editable via UI |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Run tests: `pytest`
5. Submit a pull request

---

## License

MIT — see [LICENSE](LICENSE) for full text.

---

## Disclaimer

Copyright (c) 2014-2024, Fraunhofer-Gesellschaft zur Förderung der angewandten Forschung e.V. acting on behalf of its Fraunhofer IWM.

Contact: Kiran Kumaraswamy [kiran.kumaraswamy@iwm.fraunhofer.de]
