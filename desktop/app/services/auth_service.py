from __future__ import annotations

from dataclasses import dataclass

from app.services.api_client import ApiClient, ApiError


@dataclass(slots=True)
class AuthenticatedUser:
    """Représente l'usager actuellement connecté sur la borne."""

    id: int
    email: str | None
    full_name: str


class AuthService:
    """Gère l'authentification simple par email sur la borne."""

    def __init__(self, api_client: ApiClient) -> None:
        self.api_client = api_client

    def authenticate_by_email(self, email: str) -> AuthenticatedUser:
        payload = self.api_client.get(f"/users/by-email/{email}")
        if not isinstance(payload, dict):
            raise ApiError("Reponse inattendue du serveur.")
        return AuthenticatedUser(
            id=int(payload["id"]),
            email=payload.get("email"),
            full_name=f"{payload.get('first_name', '')} {payload.get('last_name', '')}".strip(),
        )
