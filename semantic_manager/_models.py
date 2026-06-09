from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class UseCase:
    id: str
    name: str
    description: Optional[str] = None
    mutable: bool = False

    def __repr__(self) -> str:
        return f"UseCase(id={self.id!r}, name={self.name!r})"


@dataclass
class Namespace:
    id: str
    name: str
    description: Optional[str] = None
    version: Optional[str] = None
    base_iri: Optional[str] = None
    reference_url: Optional[str] = None
    download_url: Optional[str] = None
    mutable: bool = False
    use_cases: List[UseCase] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"Namespace(id={self.id!r}, name={self.name!r}, use_cases={len(self.use_cases)})"


@dataclass
class Term:
    """A vocabulary term returned from search or namespace listing."""

    iri: str
    label: str
    type: str
    namespace: str
    description: Optional[str] = None
    language: str = "en"

    # ── Annotation helpers ────────────────────────────────────────────

    def as_annotation(self) -> dict:
        """Return a compact annotation dict suitable for embedding in metadata."""
        ann = {
            "iri": self.iri,
            "label": self.label,
            "type": self.type,
            "namespace": self.namespace,
        }
        if self.description:
            ann["description"] = self.description
        return ann

    def as_jsonld(self) -> dict:
        """Return a JSON-LD compatible representation of this term."""
        return {
            "@context": {
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "owl": "http://www.w3.org/2002/07/owl#",
            },
            "@id": self.iri,
            "@type": self.type,
            "rdfs:label": self.label,
        }

    def __repr__(self) -> str:
        return f"Term(label={self.label!r}, type={self.type!r}, iri={self.iri!r})"


class TermType:
    """Constants for the ``type`` filter parameter in :meth:`SemanticManager.search`."""

    ALL = "all"
    CLASS = "class"
    OBJECT_PROPERTY = "object_property"
    DATA_PROPERTY = "data_property"
    ANNOTATION_PROPERTY = "annotation_property"
    PROPERTY = "property"
    MEASUREMENT_UNIT = "measurement_unit"
    SKOS_CONCEPT = "skos_concept"
    NAMED_INDIVIDUAL = "named_individual"