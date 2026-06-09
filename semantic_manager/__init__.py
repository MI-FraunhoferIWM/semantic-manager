"""Semantic Manager Python SDK.

Quickly connect to a Semantic Manager instance, browse vocabulary namespaces,
search for terms, and annotate your data with standardised IRIs.

Basic usage::

    from semantic_manager import SemanticManager, TermType

    sm = SemanticManager("https://api.example.com", token="eyJ...")

    results = sm.search("temperature", type=TermType.DATA_PROPERTY)
    print(results[0].iri)
"""

from ._client import SemanticManager
from ._exceptions import APIError, AuthenticationError, NotFoundError, SemanticManagerError
from ._models import Namespace, Term, TermType, UseCase

__version__ = "0.1.0"
__all__ = [
    "SemanticManager",
    "Namespace",
    "UseCase",
    "Term",
    "TermType",
    "SemanticManagerError",
    "AuthenticationError",
    "NotFoundError",
    "APIError",
]