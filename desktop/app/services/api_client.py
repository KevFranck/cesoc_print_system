from __future__ import annotations

import httpx


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ApiClient:
    """Client HTTP léger partagé par les applications desktop.

    Il centralise les appels REST et transforme les erreurs backend en messages
    exploitables par l'UI sans répéter la même logique partout.
    """

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = 8.0

    def get(self, path: str) -> dict | list | None:
        response = httpx.get(f"{self.base_url}{path}", timeout=self.timeout)
        self._raise_for_status(response)
        return response.json()

    def post(self, path: str, payload: dict) -> dict:
        response = httpx.post(f"{self.base_url}{path}", json=payload, timeout=self.timeout)
        self._raise_for_status(response)
        return response.json()

    def safe_get(self, path: str, fallback: dict | list | None) -> dict | list | None:
        try:
            return self.get(path)
        except (httpx.HTTPError, ApiError, ValueError):
            return fallback

    def safe_post(self, path: str, payload: dict, fallback: dict | None = None) -> dict | None:
        try:
            return self.post(path, payload)
        except (httpx.HTTPError, ApiError, ValueError):
            return fallback

    def _raise_for_status(self, response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            message = "Erreur API."
            try:
                payload = response.json()
                message = payload.get("detail", message)
            except ValueError:
                pass
            raise ApiError(message, response.status_code) from exc
