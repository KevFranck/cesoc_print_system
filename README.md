# CESOC Print System

Solution de borne d'impression PDF pour centre de services, composée d'un backend FastAPI/PostgreSQL, d'une console d'administration PySide6 et d'une borne client PySide6 plein écran.

## Objectif

Le projet couvre désormais un MVP démontrable orienté impression PDF :

- création et suivi des utilisateurs par email
- authentification borne par email
- quota journalier avec bonus pages et déblocage manuel
- import de PDF depuis clé USB
- récupération de PDF depuis une boîte mail IMAP dédiée
- aperçu PDF côté borne
- impression Windows via service encapsulé
- traçabilité des jobs et des refus

## Architecture finale

```text
cesoc_print_system/
  app/
    __init__.py
  backend/
    alembic/
      versions/
    app/
      api/
      core/
      db/
      models/
      repositories/
      schemas/
      services/
      main.py
    .env.example
    alembic.ini
    requirements.txt
  desktop/
    app/
      config/
      core/
      services/
      ui/
        admin/
        client/
        kiosk_client/
        shared/
    main_admin.py
    main_client.py
    requirements.txt
  docs/
  scripts/
```

## Blocs applicatifs

### Backend

Le backend centralise :

- utilisateurs
- bonus pages / overrides
- documents importés
- sessions de poste
- jobs d'impression
- dashboard et paramètres

### Desktop admin

La console admin permet :

- dashboard synthétique
- gestion des utilisateurs
- suivi du quota
- ajout de bonus pages
- suivi des postes et sessions
- historique des impressions

### Desktop borne client

La borne fournit un parcours guidé :

1. bienvenue
2. connexion par email
3. choix de source
4. liste des documents PDF
5. aperçu / quota
6. impression
7. résultat

## Prérequis

### Python

- Python 3.12+

### Base de données

- PostgreSQL 14+

### Windows

Pour une démonstration réaliste de la borne :

- Windows 10/11
- une imprimante PDF ou physique disponible
- option recommandée : `SumatraPDF` pour une impression CLI plus fiable

### IMAP

Pour la récupération email :

- une boîte mail dédiée au service
- accès IMAP activé
- identifiants IMAP de la borne

## Installation backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Renseigner ensuite [backend/.env](/Users/kfowo/Desktop/Cesoc/cesoc_print_system/backend/.env), notamment :

```env
DATABASE_URL=postgresql+psycopg2://postgres:motdepasse@localhost:5432/cesoc_print_system
IMPORTED_DOCUMENTS_PATH=storage/imported_documents
DEFAULT_DAILY_QUOTA=10
```

## Migrations Alembic

Depuis `backend/` :

```powershell
alembic upgrade head
```

Les migrations incluent :

- schéma initial
- extensions borne MVP : bonus pages, documents importés, enrichissement des jobs

## Lancement backend

Depuis la racine du projet :

```powershell
.\backend\venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload
```

Ou depuis `backend/` :

```powershell
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Healthcheck :

```text
GET http://127.0.0.1:8000/health
```

## Installation desktop

```powershell
cd desktop
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration borne

Créer [desktop/app/config/client_config.json](/Users/kfowo/Desktop/Cesoc/cesoc_print_system/desktop/app/config/client_config.json) à partir de [client_config.example.json](/Users/kfowo/Desktop/Cesoc/cesoc_print_system/desktop/app/config/client_config.example.json).

Champs importants :

- `api_base_url`
- `station_code`
- `printer_name`
- `pdf_print_tool_path`
- `local_document_root`
- `imap_host`
- `imap_port`
- `imap_username`
- `imap_password`
- `mailbox_name`

## Dépendances système Windows

### Impression PDF

Le service d'impression Windows fonctionne de deux façons :

1. recommandé : outil externe CLI comme `SumatraPDF`
2. fallback : `os.startfile(..., "print")`

Recommandation démonstration :

```text
C:\Tools\SumatraPDF\SumatraPDF.exe
```

Puis dans `client_config.json` :

```json
{
  "printer_name": "Nom de votre imprimante",
  "pdf_print_tool_path": "C:/Tools/SumatraPDF/SumatraPDF.exe"
}
```

### IMAP

La borne lit les PDF depuis la boîte mail configurée. Le code :

- télécharge les pièces jointes PDF
- les place dans un cache local contrôlé
- associe les documents à l'utilisateur connecté quand l'expéditeur correspond

## Routes API principales

### Utilisateurs

- `POST /api/v1/users`
- `GET /api/v1/users`
- `GET /api/v1/users/{id}`
- `GET /api/v1/users/by-email/{email}`
- `GET /api/v1/users/{id}/quota-status`
- `POST /api/v1/users/{id}/grant-bonus-pages`

### Documents

- `GET /api/v1/documents/email/{user_id}`
- `GET /api/v1/documents/user/{user_id}`
- `POST /api/v1/documents/import-usb`
- `POST /api/v1/documents/import-email`
- `POST /api/v1/documents/{document_id}/print`
- `POST /api/v1/documents/{document_id}/mark-status/{status}`
- `POST /api/v1/documents/jobs/{job_id}/status`

### Jobs

- `POST /api/v1/print-jobs`
- `GET /api/v1/print-jobs`
- `GET /api/v1/print-jobs/today`
- `GET /api/v1/print-jobs/user/{user_id}`

### Dashboard

- `GET /api/v1/dashboard/summary`

## Lancement admin

Depuis `desktop/` :

```powershell
python main_admin.py
```

## Lancement borne

Depuis `desktop/` :

```powershell
python main_client.py
```

La borne démarre en plein écran.

## Ce qui fonctionne réellement déjà

### Backend

- création d'utilisateurs avec email
- recherche d'utilisateur par email
- calcul de quota quotidien
- ajout de bonus pages tracé
- enregistrement de documents importés
- réservation d'un job d'impression pour un document
- suivi d'état du job imprimé / échoué
- historique par utilisateur

### Desktop borne

- connexion par email
- détection des PDF sur clé USB
- récupération IMAP des pièces jointes PDF
- enregistrement des documents auprès du backend
- aperçu PDF si `QtPdf` est disponible dans l'installation PySide6
- déclenchement d'impression Windows via service dédié

### Desktop admin

- dashboard
- liste utilisateurs
- recherche
- détails quota
- ajout de pages bonus
- gestion postes / sessions
- historique des jobs

## Points à tester manuellement sur Windows

1. création d'un poste `POSTE-01`
2. création d'un utilisateur avec email
3. démarrage d'une session active sur le poste
4. connexion borne avec cet email
5. import PDF via clé USB
6. import PDF via boîte mail IMAP
7. aperçu PDF
8. impression avec `SumatraPDF` ou fallback Windows
9. mise à jour du statut du job
10. ajout de bonus pages depuis l'admin puis nouvel essai d'impression

## Seed de démonstration

Le script [scripts/seed_demo_data.py](/Users/kfowo/Desktop/Cesoc/cesoc_print_system/scripts/seed_demo_data.py) peut servir de base, mais il est recommandé de créer ensuite les utilisateurs et postes utiles à la borne.

## Build Windows

Depuis `desktop/` :

```powershell
pyinstaller --noconfirm --windowed --name admin main_admin.py
pyinstaller --noconfirm --windowed --name client main_client.py
```

Si `SumatraPDF` ou d'autres outils externes sont utilisés, prévoir leur déploiement sur le poste cible.

## Limites actuelles

- le flux email IMAP est volontairement simple et ne marque pas encore les messages comme traités côté serveur
- le fallback d'impression Windows via `startfile` est moins fiable qu'un outil CLI dédié
- l'aperçu PDF dépend de la disponibilité de `QtPdf`
- le backend suppose un stockage local du chemin document communiqué par la borne

## Prochaines étapes recommandées

1. chiffrer davantage les secrets et mots de passe IMAP
2. ajouter une authentification admin complète
3. signer et verrouiller le mode borne au démarrage Windows
4. ajouter tests automatiques backend et tests ciblés desktop
5. industrialiser la gestion des fichiers temporaires et l'archivage
