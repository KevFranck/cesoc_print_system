# Architecture Notes

## Backend

- FastAPI expose les routes metier
- SQLAlchemy gere l'acces base
- Les services portent les regles metier
- Les repositories encapsulent les acces ORM

## Desktop

- `main_admin.py` et `main_client.py` utilisent le meme code source commun
- `services/` encapsule les appels API
- `ui/shared/` centralise les composants reutilisables
- la logique d'interface reste decouplee de la logique metier

## Evolution prevue

- authentification
- file d'impression reelle
- supervision temps reel
- packaging PyInstaller durci
