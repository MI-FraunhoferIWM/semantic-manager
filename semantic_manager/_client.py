from __future__ import annotations

from typing import List, Optional, Union

import requests

from ._auth import _KeycloakAuth, _TokenAuth
from ._exceptions import APIError, AuthenticationError, NotFoundError
from ._models import Namespace, Term, TermType, UseCase


class SemanticManager:
    """Python client for the Semantic Manager vocabulary service.

    Authenticate with a pre-existing token **or** with username + password
    via Keycloak::

        # Token auth
        sm = SemanticManager("https://api.example.com", token="eyJ...")

        # Username / password auth
        sm = SemanticManager(
            "https://api.example.com",
            username="alice",
            password="secret",
            keycloak_url="https://auth.example.com",
            realm="myrealm",
        )
    """

    def __init__(
        self,
        base_url: str,
        *,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        keycloak_url: Optional[str] = None,
        realm: str = "master",
        client_id: str = "vocabulary-service",
        verify_ssl: bool = True,
        timeout: int = 30,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._verify = verify_ssl
        self._timeout = timeout

        if token:
            self._auth = _TokenAuth(token)
        elif username and password:
            if not keycloak_url:
                raise ValueError(
                    "keycloak_url is required when authenticating with username/password."
                )
            self._auth = _KeycloakAuth(
                username=username,
                password=password,
                keycloak_url=keycloak_url,
                realm=realm,
                client_id=client_id,
                verify_ssl=verify_ssl,
            )
        else:
            raise ValueError(
                "Provide either token= or (username= + password= + keycloak_url=)."
            )

    # ── Low-level HTTP ─────────────────────────────────────────────────

    def _get(self, path: str, params: Optional[dict] = None) -> Union[dict, list]:
        url = f"{self._base}/{path.lstrip('/')}"
        try:
            resp = requests.get(
                url,
                headers=self._auth.headers(),
                params=params,
                verify=self._verify,
                timeout=self._timeout,
            )
        except requests.ConnectionError as exc:
            raise APIError(0, f"Could not connect to {self._base}") from exc

        self._raise(resp)
        return resp.json()

    @staticmethod
    def _raise(resp: requests.Response) -> None:
        if resp.status_code == 401:
            raise AuthenticationError(
                "Request was rejected (401). Token may be expired."
            )
        if resp.status_code == 404:
            raise NotFoundError(f"Not found: {resp.url}")
        if not resp.ok:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise APIError(resp.status_code, detail)

    # ── Namespaces ─────────────────────────────────────────────────────

    def namespaces(self) -> List[Namespace]:
        """Return all available namespaces with their use cases.

        Returns:
            list[Namespace]: All registered namespaces.

        Example::

            for ns in sm.namespaces():
                print(ns.id, ns.name, len(ns.use_cases), "use case(s)")
        """
        data = self._get("/namespaces/")
        return [_parse_namespace(ns) for ns in data]

    def namespace(self, namespace_id: str) -> Namespace:
        """Return a single namespace by ID.

        Args:
            namespace_id: The unique slug identifier (e.g. ``"bwmd"``).

        Raises:
            NotFoundError: If no namespace with that ID exists.

        Example::

            ns = sm.namespace("dcat")
            print(ns.name, ns.base_iri)
        """
        all_ns = self.namespaces()
        for ns in all_ns:
            if ns.id == namespace_id:
                return ns
        raise NotFoundError(f"Namespace '{namespace_id}' not found.")

    # ── Search ─────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        *,
        type: str = TermType.ALL,
        namespaces: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Term]:
        """Search for vocabulary terms across all (or selected) namespaces.

        Args:
            query:      Free-text search string.
            type:       RDF type filter. Use constants from :class:`TermType`
                        (e.g. ``TermType.CLASS``, ``TermType.DATA_PROPERTY``).
                        Defaults to ``TermType.ALL``.
            namespaces: Restrict search to these namespace IDs. ``None`` means
                        all namespaces.
            limit:      Maximum number of results (default 50).
            offset:     Pagination offset (default 0).

        Returns:
            list[Term]: Matching terms, ordered by relevance.

        Example::

            results = sm.search("temperature", type=TermType.DATA_PROPERTY)
            for term in results:
                print(term.label, term.iri)
        """
        params: dict = {
            "query": query,
            "type": type,
            "limit": limit,
            "offset": offset,
        }
        if namespaces:
            # requests encodes repeated keys as ?namespace=a&namespace=b
            params["namespace"] = namespaces

        data = self._get("/search", params=params)
        return [_parse_search_term(t) for t in data]

    def search_count(
        self,
        query: str,
        *,
        type: str = TermType.ALL,
        namespaces: Optional[List[str]] = None,
    ) -> int:
        """Return the total number of terms matching a query (without fetching them).

        Useful for pagination or checking coverage before annotating.

        Example::

            n = sm.search_count("pressure", type=TermType.DATA_PROPERTY)
            print(f"{n} matching terms")
        """
        params: dict = {"query": query, "type": type}
        if namespaces:
            params["namespace"] = namespaces
        data = self._get("/search/count", params=params)
        return data["total"]

    def search_facets(
        self,
        query: str,
        *,
        type: str = TermType.ALL,
        namespaces: Optional[List[str]] = None,
    ) -> dict:
        """Return per-type and per-namespace counts for a query.

        Returns a dict with keys ``type_counts`` and ``namespace_counts``.

        Example::

            facets = sm.search_facets("material")
            print(facets["type_counts"])
            # {'class': 12, 'data_property': 3, ...}
            print(facets["namespace_counts"])
            # {'bwmd': 8, 'dcat': 4, ...}
        """
        params: dict = {"query": query, "type": type}
        if namespaces:
            params["namespace"] = namespaces
        return self._get("/search/facets", params=params)

    # ── Convenience ────────────────────────────────────────────────────

    def find_term(
        self,
        query: str,
        *,
        type: str = TermType.ALL,
        namespaces: Optional[List[str]] = None,
    ) -> Optional[Term]:
        """Return the single best match for *query*, or ``None`` if no results.

        Equivalent to ``search(..., limit=1)[0]`` with a safe fallback.

        Example::

            term = sm.find_term("thermal conductivity", type=TermType.DATA_PROPERTY)
            if term:
                df.attrs["annotations"] = {"value": term.as_annotation()}
        """
        results = self.search(query, type=type, namespaces=namespaces, limit=1)
        return results[0] if results else None

    def resolve(self, iris: List[str]) -> List[Term]:
        """Resolve a list of IRIs to full Term objects.

        Args:
            iris: List of IRI strings to look up.

        Returns:
            list[Term]: Resolved terms (unresolvable IRIs are silently skipped).

        Example::

            terms = sm.resolve([
                "https://w3id.org/bwmd/ontologies/ThermalConductivity",
                "https://w3id.org/bwmd/ontologies/Pressure",
            ])
        """
        data = requests.post(
            f"{self._base}/resolve",
            headers=self._auth.headers(),
            json={"iris": iris},
            verify=self._verify,
            timeout=self._timeout,
        )
        self._raise(data)
        return [_parse_search_term(t) for t in data.json()]


# ── Parsers (module-private) ───────────────────────────────────────────


def _parse_namespace(data: dict) -> Namespace:
    use_cases = [
        UseCase(
            id=uc["id"],
            name=uc["name"],
            description=uc.get("description"),
            mutable=uc.get("mutable", False),
        )
        for uc in (data.get("use_cases") or [])
    ]
    return Namespace(
        id=data["id"],
        name=data["name"],
        description=data.get("description"),
        version=data.get("version"),
        base_iri=data.get("base_iri"),
        reference_url=data.get("reference_url"),
        download_url=data.get("download_url"),
        mutable=data.get("mutable", False),
        use_cases=use_cases,
    )


def _parse_search_term(data: dict) -> Term:
    return Term(
        iri=data["iri"],
        label=data.get("label") or data["iri"].split("/")[-1].split("#")[-1],
        type=data.get("type", ""),
        namespace=data.get("namespace", ""),
        description=data.get("description"),
        language=data.get("language", "en"),
    )