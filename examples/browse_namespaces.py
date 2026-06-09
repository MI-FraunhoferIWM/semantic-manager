"""
Browse available namespaces and their terms.
"""

from semantic_manager import SemanticManager, TermType

sm = SemanticManager(
    "https://api.example.com",
    username="alice",
    password="secret",
    keycloak_url="https://auth.example.com",
    realm="myrealm",
)

# ── List all namespaces ────────────────────────────────────────────────────────

namespaces = sm.namespaces()
print(f"Found {len(namespaces)} namespace(s):\n")

for ns in namespaces:
    mutable = "editable" if ns.mutable else "read-only"
    print(f"  [{ns.id}]  {ns.name}  ({mutable})")
    if ns.description:
        print(f"           {ns.description}")
    for uc in ns.use_cases:
        print(f"           use-case: {uc.id} — {uc.name}")
    print()

# ── Inspect one namespace ──────────────────────────────────────────────────────

ns = sm.namespace("bwmd")
print(f"\nNamespace: {ns.name}")
print(f"  Base IRI:  {ns.base_iri}")
print(f"  Version:   {ns.version}")
print(f"  Use cases: {[uc.name for uc in ns.use_cases]}")

# ── Search within a specific namespace ────────────────────────────────────────

results = sm.search("heat", namespaces=["bwmd"], type=TermType.DATA_PROPERTY)
print(f"\nData properties matching 'heat' in bwmd ({len(results)} results):")
for term in results:
    print(f"  {term.label:40s}  {term.iri}")