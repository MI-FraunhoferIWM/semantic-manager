"""
Annotate a pandas DataFrame with controlled vocabulary terms from Semantic Manager.

Scenario: A materials engineer has sensor measurements from a manufacturing process.
Each column contains a physical quantity. They want to attach standardised IRIs to
each column so downstream systems know exactly what "temperature" means.
"""

import pandas as pd
from semantic_manager import SemanticManager, TermType

# ── 1. Connect ─────────────────────────────────────────────────────────────────

sm = SemanticManager(
    "https://api.example.com",
    token="eyJhbGciOiJSUzI1NiJ9...",  # replace with your token
)

# ── 2. Sample manufacturing dataset ───────────────────────────────────────────

df = pd.DataFrame({
    "timestamp":   ["2024-01-01T08:00", "2024-01-01T08:01", "2024-01-01T08:02"],
    "temperature": [1450.2, 1452.1, 1449.8],   # furnace temp in °C
    "pressure":    [1.013,  1.014,  1.012],     # bar
    "flow_rate":   [12.5,   12.7,   12.4],      # L/min
    "material_id": ["M-001", "M-001", "M-001"],
})

# ── 3. Look up terms for each measurement column ───────────────────────────────

column_annotations = {}

lookups = {
    "temperature": ("temperature",  TermType.DATA_PROPERTY),
    "pressure":    ("pressure",     TermType.DATA_PROPERTY),
    "flow_rate":   ("flow rate",    TermType.DATA_PROPERTY),
    "material_id": ("material",     TermType.CLASS),
}

for column, (query, term_type) in lookups.items():
    term = sm.find_term(query, type=term_type)
    if term:
        column_annotations[column] = term.as_annotation()
        print(f"  {column:15s}  →  {term.label} ({term.iri})")
    else:
        print(f"  {column:15s}  →  [no match found]")

# ── 4. Attach annotations to the DataFrame ────────────────────────────────────
#
# pandas .attrs is a dict for arbitrary metadata — it persists through most
# DataFrame operations and is the recommended place for column semantics.

df.attrs["column_annotations"] = column_annotations
df.attrs["annotation_source"] = "https://api.example.com"

print("\nAnnotated DataFrame attrs:")
for col, ann in df.attrs["column_annotations"].items():
    print(f"  {col}: {ann['iri']}")

# ── 5. Save to Parquet (annotations are preserved in the file metadata) ────────

df.to_parquet("sensor_data_annotated.parquet")
print("\nSaved to sensor_data_annotated.parquet")

# ── 6. Read back and verify ────────────────────────────────────────────────────

df2 = pd.read_parquet("sensor_data_annotated.parquet")
print("Annotations recovered from file:")
print(df2.attrs.get("column_annotations", {}))