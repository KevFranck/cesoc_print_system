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

    def authenticate(self, email: str, password: str) -> AuthenticatedUser:
        payload = self.api_client.post("/users/login", {"email": email, "password": password})
        if not isinstance(payload, dict):
            raise ApiError("Reponse inattendue du serveur.")
        return AuthenticatedUser(
            id=int(payload["id"]),
            email=payload.get("email"),
            full_name=f"{payload.get('first_name', '')} {payload.get('last_name', '')}".strip(),
        )

    def register(self, payload: dict) -> AuthenticatedUser:
        created = self.api_client.post("/users/register", payload)
        if not isinstance(created, dict):
            raise ApiError("Reponse inattendue du serveur.")
        return AuthenticatedUser(
            id=int(created["id"]),
            email=created.get("email"),
            full_name=f"{created.get('first_name', '')} {created.get('last_name', '')}".strip(),
        )

    def change_password(self, user_id: int, current_password: str, new_password: str) -> None:
        self.api_client.post(
            f"/users/{user_id}/change-password",
            {"current_password": current_password, "new_password": new_password},
        )
