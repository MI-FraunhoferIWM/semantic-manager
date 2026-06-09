"""
Produce a JSON-LD annotated dataset from a plain Python dict.

Scenario: An engineer wants to publish measurement records as linked data
so that other systems can consume them with a shared understanding of what
each field means.
"""

import json
from semantic_manager import SemanticManager, TermType

sm = SemanticManager(
    "https://api.example.com",
    token="eyJhbGciOiJSUzI1NiJ9...",
)

# ── Raw measurement record ─────────────────────────────────────────────────────

record = {
    "sensor_id": "S-4712",
    "temperature": 1452.3,
    "pressure": 1.014,
    "timestamp": "2024-01-01T08:01:00Z",
}

# ── Build JSON-LD @context from vocabulary terms ───────────────────────────────

context = {
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}

field_terms = {
    "temperature": sm.find_term("temperature", type=TermType.DATA_PROPERTY),
    "pressure":    sm.find_term("pressure",    type=TermType.DATA_PROPERTY),
}

for field, term in field_terms.items():
    if term:
        context[field] = {
            "@id":   term.iri,
            "@type": "xsd:double",
        }
        print(f"Mapped '{field}' → {term.iri}")

# ── Produce annotated JSON-LD output ──────────────────────────────────────────

jsonld = {"@context": context, **record}
print("\nJSON-LD output:")
print(json.dumps(jsonld, indent=2))