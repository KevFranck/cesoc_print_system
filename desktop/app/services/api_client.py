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
        self.timeout = httpx.Timeout(connect=3.0, read=5.0, write=5.0, pool=3.0)
        self.client = httpx.Client(timeout=self.timeout)

    def get(self, path: str) -> dict | list | None:
        response = self._request("GET", path)
        self._raise_for_status(response)
        return response.json()

    def post(self, path: str, payload: dict) -> dict:
        response = self._request("POST", path, payload)
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
            message = "Une erreur est survenue."
            try:
                payload = response.json()
                message = payload.get("detail", message)
                if isinstance(message, list):
                    message = "; ".join(str(item.get("msg", item)) if isinstance(item, dict) else str(item) for item in message)
                elif not isinstance(message, str):
                    message = str(message)
            except ValueError:
                pass
            raise ApiError(message, response.status_code) from exc

    def _request(self, method: str, path: str, payload: dict | None = None) -> httpx.Response:
        """Centralise les appels HTTP avec un petit retry sur erreur transitoire."""

        last_error: Exception | None = None
        for _ in range(2):
            try:
                return self.client.request(method, f"{self.base_url}{path}", json=payload)
            except httpx.TimeoutException as exc:
                last_error = ApiError("Le serveur met trop de temps à répondre.")
            except httpx.NetworkError as exc:
                last_error = ApiError("Connexion au serveur impossible.")
        if last_error:
            raise last_error
        raise ApiError("Une erreur réseau inconnue est survenue.")
