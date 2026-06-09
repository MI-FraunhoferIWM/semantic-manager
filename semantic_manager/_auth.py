from __future__ import annotations

import requests

from ._exceptions import AuthenticationError


class _TokenAuth:
    """Pre-supplied bearer token (API key or externally obtained JWT)."""

    def __init__(self, token: str) -> None:
        self.token = token if token.startswith("Bearer ") else f"Bearer {token}"

    def headers(self) -> dict:
        return {"Authorization": self.token}


class _KeycloakAuth:
    """Exchange username + password for a Keycloak JWT, then use it as bearer."""

    def __init__(
        self,
        username: str,
        password: str,
        keycloak_url: str,
        realm: str,
        client_id: str,
        verify_ssl: bool,
    ) -> None:
        self._token = self._login(
            username, password, keycloak_url, realm, client_id, verify_ssl
        )

    @staticmethod
    def _login(
        username: str,
        password: str,
        keycloak_url: str,
        realm: str,
        client_id: str,
        verify_ssl: bool,
    ) -> str:
        url = (
            f"{keycloak_url.rstrip('/')}/realms/{realm}"
            "/protocol/openid-connect/token"
        )
        try:
            resp = requests.post(
                url,
                data={
                    "client_id": client_id,
                    "grant_type": "password",
                    "username": username,
                    "password": password,
                },
                verify=verify_ssl,
                timeout=15,
            )
        except requests.ConnectionError as exc:
            raise AuthenticationError(
                f"Could not reach Keycloak at {url}"
            ) from exc

        if resp.status_code == 401:
            raise AuthenticationError("Invalid username or password.")
        if not resp.ok:
            raise AuthenticationError(
                f"Keycloak returned {resp.status_code}: {resp.text}"
            )

        return resp.json()["access_token"]

    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}