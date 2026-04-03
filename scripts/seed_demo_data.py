from __future__ import annotations

"""Script de demonstration a executer une fois le backend configure.

Il cree quelques postes et utilisateurs borne pour faciliter les tests manuels.
"""

import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"


def main() -> None:
    stations = [
        {"code": "POSTE-01", "name": "Poste Accueil 1", "location": "Salle publique", "status": "available"},
        {"code": "POSTE-02", "name": "Poste Accueil 2", "location": "Salle publique", "status": "offline"},
    ]
    clients = [
        {"first_name": "Awa", "last_name": "Diallo", "email": "awa@example.com", "administrative_note": "CAF"},
        {"first_name": "Moussa", "last_name": "Traore", "email": "moussa@example.com", "administrative_note": "RSA"},
    ]

    for station in stations:
        try:
            httpx.post(f"{BASE_URL}/stations", json=station, timeout=5.0)
        except httpx.HTTPError:
            pass

    for client in clients:
        try:
            httpx.post(f"{BASE_URL}/users", json=client, timeout=5.0)
        except httpx.HTTPError:
            pass


if __name__ == "__main__":
    main()
