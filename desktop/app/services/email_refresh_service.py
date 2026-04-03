from __future__ import annotations

import email
import imaplib
import shutil
import socket
from email.message import Message
from pathlib import Path

from app.services.config_service import ClientStationConfig
from app.services.pdf_preview_service import PdfPreviewService
from app.services.usb_monitor_service import LocalPdfDocument


class EmailRefreshService:
    """Lit une boîte IMAP et extrait les pièces jointes PDF dans un cache local.

    La logique est volontairement simple pour le MVP : on télécharge les PDF
    pertinents, on les range dans un dossier local contrôlé et on les retourne à
    l'interface borne.
    """

    def __init__(self, config: ClientStationConfig) -> None:
        self.config = config
        self.preview_service = PdfPreviewService()
        self._page_count_cache: dict[Path, int] = {}

    def fetch_pdf_attachments(self, expected_sender_email: str | None = None) -> list[LocalPdfDocument]:
        """Télécharge les pièces jointes PDF depuis la boîte IMAP configurée.

        Cette méthode remonte des erreurs explicites quand la configuration IMAP
        est invalide, que le DNS ne résout pas l'hôte ou que l'authentification
        échoue. L'UI peut ainsi afficher un message compréhensible à l'usager ou
        au technicien au lieu d'une exception système opaque.
        """

        if not self.config.imap_host or not self.config.imap_username or not self.config.imap_password:
            raise RuntimeError("La configuration IMAP de la borne est incomplete.")

        destination = self._ensure_session_cache()
        documents = self._load_cached_documents(destination)

        try:
            with imaplib.IMAP4_SSL(self.config.imap_host, self.config.imap_port) as client:
                client.login(self.config.imap_username, self.config.imap_password)
                client.select(self.config.mailbox_name)
                for msg_id in self._search_candidate_messages(client):
                    status, msg_data = client.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue
                    raw_bytes = self._extract_raw_email_bytes(msg_data)
                    if not raw_bytes:
                        continue
                    message = email.message_from_bytes(raw_bytes)
                    sender = self._extract_sender_email(message)
                    if not self._sender_matches(expected_sender_email, sender):
                        continue
                    extracted = self._extract_pdf_documents(message, sender, destination, documents)
                    if not extracted:
                        continue
                    documents.extend(extracted)
                    client.store(msg_id, "+FLAGS", "\\Seen")
        except socket.gaierror as exc:
            raise RuntimeError(
                f"Hote IMAP introuvable: '{self.config.imap_host}'. Verifie le nom du serveur IMAP dans client_config.json."
            ) from exc
        except imaplib.IMAP4.error as exc:
            raise RuntimeError("Connexion IMAP refusee. Verifie l'identifiant, le mot de passe et l'acces IMAP.") from exc
        except OSError as exc:
            raise RuntimeError(f"Connexion IMAP impossible: {exc}") from exc
        return documents

    def clear_session_cache(self) -> None:
        """Supprime les fichiers mail temporaires à la déconnexion.

        Les documents mail ne doivent vivre que pendant la session active de
        l'usager. S'il revient plus tard, il doit donc renvoyer ses fichiers.
        """

        destination = Path(self.config.local_document_root).resolve() / "email_cache"
        if destination.exists():
            shutil.rmtree(destination, ignore_errors=True)
        self._page_count_cache.clear()

    def _ensure_session_cache(self) -> Path:
        """Crée le cache de session sans supprimer les documents déjà visibles."""

        destination = Path(self.config.local_document_root).resolve() / "email_cache"
        destination.mkdir(parents=True, exist_ok=True)
        return destination

    def _load_cached_documents(self, destination: Path) -> list[LocalPdfDocument]:
        """Recharge les PDF déjà récupérés pendant la session active."""

        documents: list[LocalPdfDocument] = []
        for pdf_file in sorted(destination.glob("*.pdf")):
            try:
                documents.append(
                    LocalPdfDocument(
                        source_type="email",
                        source_label="Boite mail de service",
                        original_filename=pdf_file.name,
                        local_path=str(pdf_file),
                        page_count=self._get_page_count(pdf_file),
                        sender_email=None,
                    )
                )
            except Exception:
                continue
        return documents

    def _extract_pdf_documents(
        self,
        message: Message,
        sender_email: str | None,
        destination: Path,
        existing_documents: list[LocalPdfDocument],
    ) -> list[LocalPdfDocument]:
        documents: list[LocalPdfDocument] = []
        known_paths = {Path(document.local_path).resolve() for document in existing_documents}
        for part in message.walk():
            filename = part.get_filename()
            if not filename or not filename.lower().endswith(".pdf"):
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            target = destination / filename
            resolved_target = target.resolve()
            if resolved_target in known_paths:
                continue
            target.write_bytes(payload)
            documents.append(
                LocalPdfDocument(
                    source_type="email",
                    source_label="Boite mail de service",
                    original_filename=filename,
                    local_path=str(target),
                    page_count=self._get_page_count(target),
                    sender_email=sender_email,
                )
            )
            known_paths.add(resolved_target)
        return documents

    def _search_candidate_messages(self, client: imaplib.IMAP4_SSL) -> list[bytes]:
        """Retourne les IDs des messages récents encore exploitables pour la session.

        On priorise `UNSEEN`, puis `RECENT` en secours selon le serveur IMAP.
        """

        for criteria in ("UNSEEN", "RECENT"):
            status, data = client.search(None, criteria)
            if status == "OK" and data and data[0]:
                return data[0].split()[-20:]
        return []

    def _extract_raw_email_bytes(self, msg_data: list[object]) -> bytes | None:
        """Normalise la réponse IMAP pour récupérer le contenu brut du message."""

        for item in msg_data:
            if isinstance(item, tuple) and len(item) > 1 and isinstance(item[1], bytes):
                return item[1]
        return None

    def _extract_sender_email(self, message: Message) -> str | None:
        """Extrait l'adresse expéditeur utile pour filtrer les documents."""

        for header_name in ("From", "Reply-To", "Sender"):
            value = message.get(header_name, "")
            sender = email.utils.parseaddr(value)[1]
            if sender:
                return sender.lower()
        return None

    def _sender_matches(self, expected_sender_email: str | None, sender_email: str | None) -> bool:
        """Vérifie si le mail peut être associé à l'usager connecté."""

        if not expected_sender_email:
            return True
        if not sender_email:
            return False
        return sender_email.strip().lower() == expected_sender_email.strip().lower()

    def _get_page_count(self, pdf_path: Path) -> int:
        """Met en cache le nombre de pages pour éviter les relectures répétées."""

        resolved_path = pdf_path.resolve()
        if resolved_path not in self._page_count_cache:
            self._page_count_cache[resolved_path] = self.preview_service.get_page_count(str(resolved_path))
        return self._page_count_cache[resolved_path]
