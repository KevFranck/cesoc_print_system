from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

try:
    from PySide6.QtPdfWidgets import QPdfView
except Exception:  # pragma: no cover - depends on Qt PDF runtime
    QPdfView = None  # type: ignore[assignment]

from app.services.api_client import ApiClient, ApiError
from app.services.config_service import ClientStationConfig
from app.services.kiosk_workflow_service import KioskWorkflowService, RegisteredDocument
from app.services.usb_monitor_service import LocalPdfDocument
from app.ui.shared.widgets import HeroBanner, SectionCard


@dataclass(slots=True)
class KioskSelection:
    """Transient state for the current kiosk user session."""

    user_id: int | None = None
    user_name: str | None = None
    user_email: str | None = None
    selected_method: str | None = None
    selected_local_document: LocalPdfDocument | None = None
    registered_document: RegisteredDocument | None = None


class KioskMainWindow(QMainWindow):
    """Main kiosk window with a guided print flow."""

    def __init__(self, api_client: ApiClient, config: ClientStationConfig) -> None:
        super().__init__()
        self.workflow = KioskWorkflowService(api_client, config)
        self.config = config
        self.state = KioskSelection()
        self.is_busy = False
        self.current_pdf_document = None
        self.busy_widgets: list[QWidget] = []

        self.auto_logout_timer = QTimer(self)
        self.auto_logout_timer.setSingleShot(True)
        self.auto_logout_timer.timeout.connect(self._logout_user)

        self.setWindowTitle(f"CESOC Borne Impression - {config.station_code}")
        self.resize(1365, 900)
        logo_path = Path(__file__).resolve().parents[2] / "assets" / "cesoc-logo.svg"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        self.hero = HeroBanner(
            "Borne d'impression CESOC",
            "Connectez-vous avec votre email, choisissez votre document PDF puis lancez l'impression.",
        )
        layout.addWidget(self.hero)

        self.top_actions = QHBoxLayout()
        self.top_actions.addStretch(1)
        self.logout_button = QPushButton("Se deconnecter")
        self.logout_button.setObjectName("SecondaryButton")
        self.logout_button.clicked.connect(self._logout_user)
        self.top_actions.addWidget(self.logout_button)
        self.busy_widgets.append(self.logout_button)
        layout.addLayout(self.top_actions)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        self.welcome_page = self._build_welcome_page()
        self.login_page = self._build_login_page()
        self.method_page = self._build_method_page()
        self.documents_page = self._build_documents_page()
        self.preview_page = self._build_preview_page()
        self.result_page = self._build_result_page()
        for page in (
            self.welcome_page,
            self.login_page,
            self.method_page,
            self.documents_page,
            self.preview_page,
            self.result_page,
        ):
            self.stack.addWidget(page)

        self._goto(self.welcome_page)
        self._update_session_actions()

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self.showFullScreen()

    def _build_welcome_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_path = Path(__file__).resolve().parents[2] / "assets" / "cesoc-logo.svg"
        if logo_path.exists():
            logo = QLabel()
            logo.setObjectName("LogoMark")
            logo.setPixmap(QIcon(str(logo_path)).pixmap(148, 148))
            layout.addWidget(logo, 0, Qt.AlignmentFlag.AlignHCenter)

        title = QLabel("Bienvenue")
        title.setObjectName("KioskTitle")
        subtitle = QLabel("Appuyez pour commencer votre impression PDF.")
        subtitle.setObjectName("KioskText")

        start_button = QPushButton("Commencer")
        start_button.setObjectName("KioskPrimaryButton")
        start_button.clicked.connect(lambda: self._goto(self.login_page))
        self.busy_widgets.append(start_button)

        layout.addWidget(title, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(subtitle, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(18)
        layout.addWidget(start_button, 0, Qt.AlignmentFlag.AlignHCenter)
        return page

    def _build_login_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = SectionCard("Connexion")
        card_layout = QVBoxLayout(card.content)

        title = QLabel("Entrez votre email")
        title.setObjectName("KioskTitle")
        text = QLabel("Votre adresse email permet de retrouver votre quota du jour.")
        text.setObjectName("KioskText")
        text.setWordWrap(True)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("exemple@domaine.com")

        login_button = QPushButton("Se connecter")
        login_button.setObjectName("KioskPrimaryButton")
        login_button.clicked.connect(self._authenticate)
        self.busy_widgets.append(login_button)

        back_button = QPushButton("Retour")
        back_button.setObjectName("SecondaryButton")
        back_button.clicked.connect(lambda: self._goto(self.welcome_page))
        self.busy_widgets.append(back_button)

        card_layout.addWidget(title)
        card_layout.addWidget(text)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(login_button)
        card_layout.addWidget(back_button)
        layout.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)
        return page

    def _build_method_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Choisissez votre methode")
        title.setObjectName("KioskTitle")
        subtitle = QLabel("Vous pouvez imprimer depuis une cle USB ou depuis un email envoye pendant cette session.")
        subtitle.setObjectName("KioskText")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)

        buttons = [
            ("Cle USB", "usb", "Parcourir les PDF detectes sur le support amovible"),
            ("Telephone par email", "email_phone", "Recuperer les PDF envoyes depuis votre telephone"),
            ("Poste reseau par email", "email_network", "Recuperer les PDF envoyes depuis un poste du centre"),
        ]
        for label, method, description in buttons:
            button = QPushButton(f"{label}\n{description}")
            button.setObjectName("KioskChoiceButton")
            button.clicked.connect(lambda checked=False, m=method, l=label: self._load_documents(m, l))
            layout.addWidget(button)
            self.busy_widgets.append(button)
        layout.addStretch(1)
        return page

    def _build_documents_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(18)

        action_bar = QHBoxLayout()
        self.documents_context = QLabel("Choisissez un document a imprimer.")
        self.documents_context.setObjectName("KioskText")
        action_bar.addWidget(self.documents_context)
        action_bar.addStretch(1)

        change_method_button = QPushButton("Changer de methode")
        change_method_button.setObjectName("KioskGhostButton")
        change_method_button.clicked.connect(self._back_to_methods)
        self.busy_widgets.append(change_method_button)
        action_bar.addWidget(change_method_button)
        layout.addLayout(action_bar)

        body = QHBoxLayout()
        body.setSpacing(18)

        left = SectionCard("Documents disponibles")
        left_layout = QVBoxLayout(left.content)
        self.documents_title = QLabel("Aucun chargement")
        self.documents_title.setObjectName("SectionTitle")
        self.documents_list = QListWidget()
        self.documents_list.setUniformItemSizes(True)
        self.documents_list.setSpacing(6)
        self.documents_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.documents_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.documents_list.itemSelectionChanged.connect(self._select_document)

        refresh_button = QPushButton("Rafraichir")
        refresh_button.setObjectName("SecondaryButton")
        refresh_button.clicked.connect(self._refresh_current_method)
        self.busy_widgets.append(refresh_button)

        left_layout.addWidget(self.documents_title)
        left_layout.addWidget(self.documents_list)
        left_layout.addWidget(refresh_button)
        body.addWidget(left, 1)

        right = SectionCard("Resume")
        right_layout = QVBoxLayout(right.content)
        self.document_summary = QLabel("Selectionnez un document PDF.")
        self.document_summary.setObjectName("KioskText")
        self.document_summary.setWordWrap(True)

        self.documents_help = QLabel(
            "Les documents recuperes par email restent disponibles uniquement pendant cette session."
        )
        self.documents_help.setObjectName("KioskText")
        self.documents_help.setWordWrap(True)

        next_button = QPushButton("Continuer")
        next_button.setObjectName("KioskPrimaryButton")
        next_button.clicked.connect(self._prepare_preview)
        self.busy_widgets.append(next_button)

        right_layout.addWidget(self.document_summary)
        right_layout.addWidget(self.documents_help)
        right_layout.addStretch(1)
        right_layout.addWidget(next_button)
        body.addWidget(right, 1)

        layout.addLayout(body)
        return page

    def _build_preview_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        header = QLabel("Apercu et impression")
        header.setObjectName("KioskTitle")
        layout.addWidget(header)

        body = QHBoxLayout()

        info_card = SectionCard("Resume du document")
        info_layout = QVBoxLayout(info_card.content)

        self.preview_summary = QLabel("Aucun document.")
        self.preview_summary.setObjectName("KioskText")
        self.preview_summary.setWordWrap(True)

        self.quota_summary = QLabel("")
        self.quota_summary.setObjectName("KioskText")

        self.page_selection_input = QLineEdit()
        self.page_selection_input.setPlaceholderText("Pages a imprimer: toutes ou ex: 1-3,5")

        self.context_input = QLineEdit()
        self.context_input.setPlaceholderText("Exemple: CAF, titre de sejour, CV")

        back_button = QPushButton("Choisir un autre document")
        back_button.setObjectName("SecondaryButton")
        back_button.clicked.connect(self._back_to_documents)
        self.busy_widgets.append(back_button)

        self.print_button = QPushButton("Imprimer maintenant")
        self.print_button.setObjectName("KioskPrimaryButton")
        self.print_button.clicked.connect(self._print_current_document)
        self.busy_widgets.append(self.print_button)

        info_layout.addWidget(self.preview_summary)
        info_layout.addWidget(self.quota_summary)
        info_layout.addWidget(self.page_selection_input)
        info_layout.addWidget(self.context_input)
        info_layout.addStretch(1)
        info_layout.addWidget(back_button)
        info_layout.addWidget(self.print_button)
        body.addWidget(info_card, 1)

        preview_card = SectionCard("Apercu PDF")
        preview_layout = QVBoxLayout(preview_card.content)
        if QPdfView is not None:
            self.pdf_view = QPdfView()
            preview_layout.addWidget(self.pdf_view)
        else:
            self.pdf_view = None

        self.preview_status = QLabel("")
        self.preview_status.setObjectName("KioskText")
        self.preview_status.setWordWrap(True)
        preview_layout.addWidget(self.preview_status)
        body.addWidget(preview_card, 2)

        layout.addLayout(body)
        return page

    def _build_result_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(18)

        result_card = SectionCard("Resultat d'impression")
        result_card.setMaximumWidth(760)
        result_layout = QVBoxLayout(result_card.content)
        result_layout.setSpacing(14)

        self.result_badge = QLabel("EN ATTENTE")
        self.result_badge.setObjectName("ResultBadgeNeutral")
        self.result_badge.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.result_title = QLabel("Resultat")
        self.result_title.setObjectName("KioskTitle")
        self.result_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.result_message = QLabel("")
        self.result_message.setObjectName("KioskText")
        self.result_message.setWordWrap(True)
        self.result_message.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        done_button = QPushButton("Se deconnecter")
        done_button.setObjectName("KioskPrimaryButton")
        done_button.clicked.connect(self._logout_user)
        self.busy_widgets.append(done_button)

        result_layout.addWidget(self.result_badge, 0, Qt.AlignmentFlag.AlignHCenter)
        result_layout.addWidget(self.result_title, 0, Qt.AlignmentFlag.AlignHCenter)
        result_layout.addWidget(self.result_message, 0, Qt.AlignmentFlag.AlignHCenter)
        result_layout.addSpacing(6)
        result_layout.addWidget(done_button, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(result_card, 0, Qt.AlignmentFlag.AlignCenter)
        return page

    def _authenticate(self) -> None:
        if self.is_busy:
            return
        self._set_busy(True)
        try:
            user = self.workflow.authenticate_user(self.email_input.text().strip())
        except ApiError as exc:
            QMessageBox.warning(self, "Connexion impossible", exc.message)
            self._set_busy(False)
            return

        self.state.user_id = user.id
        self.state.user_name = user.full_name
        self.state.user_email = user.email
        self.hero.set_metrics("Connecte", user.full_name)
        self._update_session_actions()
        self._goto(self.method_page)
        self._set_busy(False)

    def _load_documents(self, method: str, label: str) -> None:
        """Loads USB or email documents for the selected method."""

        if self.is_busy:
            return
        self._set_busy(True)

        self.state.selected_method = method
        self.state.selected_local_document = None
        self.state.registered_document = None
        self.current_pdf_document = None
        self.documents_title.setText(f"Documents via {label}")
        self.documents_context.setText(f"Source active: {label}. Selectionnez un fichier pour continuer.")
        self._reset_document_selection()

        try:
            documents = (
                self.workflow.load_usb_documents()
                if method == "usb"
                else self.workflow.load_email_documents(self.state.user_email)
            )
        except Exception as exc:
            QMessageBox.warning(self, "Chargement impossible", str(exc))
            self._set_busy(False)
            return

        self.documents_list.setUpdatesEnabled(False)
        try:
            for document in documents:
                item = QListWidgetItem(f"{document.original_filename} - {document.page_count} pages")
                item.setData(Qt.ItemDataRole.UserRole, document)
                self.documents_list.addItem(item)
        finally:
            self.documents_list.setUpdatesEnabled(True)

        self._goto(self.documents_page)
        self._set_busy(False)

    def _refresh_current_method(self) -> None:
        labels = {
            "usb": "Cle USB",
            "email_phone": "Telephone par email",
            "email_network": "Poste reseau par email",
        }
        if self.state.selected_method:
            self._load_documents(self.state.selected_method, labels.get(self.state.selected_method, "Documents"))

    def _select_document(self) -> None:
        current_item = self.documents_list.currentItem()
        if not current_item:
            self.state.selected_local_document = None
            self.document_summary.setText("Selectionnez un document PDF.")
            return

        document = current_item.data(Qt.ItemDataRole.UserRole)
        self.state.selected_local_document = document
        self.document_summary.setText(
            f"Document: {document.original_filename}\n"
            f"Source: {document.source_label}\n"
            f"Pages: {document.page_count}\n"
            f"Chemin local: {document.local_path}"
        )

    def _reset_document_selection(self) -> None:
        """Resets the document selection panel."""

        self.documents_list.clear()
        self.documents_context.setText("Choisissez un document a imprimer.")
        self.document_summary.setText("Selectionnez un document PDF.")
        self.preview_status.setText("")

    def _prepare_preview(self) -> None:
        """Registers the selected local document and prepares the preview page."""

        if self.is_busy:
            return
        if not self.state.user_id or not self.state.selected_local_document:
            QMessageBox.warning(self, "Document requis", "Choisissez d'abord un document.")
            return

        self._set_busy(True)
        try:
            registered = self.workflow.register_local_document(self.state.user_id, self.state.selected_local_document)
            quota = self.workflow.get_user_quota(self.state.user_id)
        except ApiError as exc:
            QMessageBox.warning(self, "Preparation impossible", exc.message)
            self._set_busy(False)
            return

        self.state.registered_document = registered
        self.preview_summary.setText(
            f"Document: {registered.original_filename}\n"
            f"Pages: {registered.page_count}\n"
            f"Source: {registered.source_type} ({registered.source_label})"
        )
        self.quota_summary.setText(
            f"Quota restant: {quota.get('remaining_pages', 0)} / {quota.get('effective_quota', 0)} pages"
        )
        self.page_selection_input.clear()

        self.current_pdf_document = self.workflow.preview_service.create_pdf_document(registered.local_path)
        if self.pdf_view is not None:
            self.pdf_view.setDocument(self.current_pdf_document)
            if self.current_pdf_document is not None and hasattr(QPdfView, "PageMode"):
                self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
            if hasattr(QPdfView, "ZoomMode"):
                self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)
        if self.pdf_view is None:
            self.preview_status.setText("L'apercu integre n'est pas disponible sur cette installation Qt.")
        elif self.current_pdf_document is None:
            self.preview_status.setText("Le PDF a bien ete charge pour impression, mais l'apercu n'a pas pu etre affiche.")
        else:
            self.preview_status.setText("Apercu charge. Verifiez le document avant impression.")

        self._goto(self.preview_page)
        self._set_busy(False)

    def _print_current_document(self) -> None:
        if self.is_busy:
            return
        if not self.state.registered_document:
            QMessageBox.warning(self, "Impression impossible", "Aucun document pret a imprimer.")
            return

        self._set_busy(True)
        context_label = self.context_input.text().strip() or "Demarche administrative"
        try:
            normalized_selection, selected_page_count = self.workflow.resolve_page_selection(
                self.state.registered_document.page_count,
                self.page_selection_input.text().strip() or None,
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Pages invalides", str(exc))
            self._set_busy(False)
            return
        try:
            job, result = self.workflow.print_registered_document(
                self.state.registered_document,
                context_label,
                normalized_selection,
            )
        except ApiError as exc:
            QMessageBox.warning(self, "Erreur API", exc.message)
            self._set_busy(False)
            return

        self.result_title.setText("Impression reussie" if result.success else "Impression echouee")
        self.result_badge.setText("TERMINE" if result.success else "ECHEC")
        self.result_badge.setObjectName("ResultBadgeSuccess" if result.success else "ResultBadgeError")
        self.result_badge.style().unpolish(self.result_badge)
        self.result_badge.style().polish(self.result_badge)
        self.result_message.setText(
            f"Document: {self.state.registered_document.original_filename}\n"
            f"Job #{job.get('id')}\n"
            f"Pages imprimees: {selected_page_count}\n"
            f"Selection: {normalized_selection or 'Toutes les pages'}\n"
            f"{result.message}\n\nLa session va maintenant se fermer pour proteger vos documents."
        )
        self._goto(self.result_page)
        self._set_busy(False)
        self.auto_logout_timer.start(12000)

    def _reset_workflow(self) -> None:
        """Resets kiosk state and clears temporary session artifacts."""

        self.workflow.cleanup_session_artifacts()
        self.state = KioskSelection()
        self.current_pdf_document = None
        self.auto_logout_timer.stop()
        self.email_input.clear()
        self.documents_list.clear()
        self.page_selection_input.clear()
        self.context_input.clear()
        self.documents_context.setText("Choisissez un document a imprimer.")
        self.document_summary.setText("Selectionnez un document PDF.")
        self.preview_summary.setText("Aucun document.")
        self.quota_summary.setText("")
        self.preview_status.setText("")
        self.result_badge.setText("EN ATTENTE")
        self.result_badge.setObjectName("ResultBadgeNeutral")
        self.result_badge.style().unpolish(self.result_badge)
        self.result_badge.style().polish(self.result_badge)
        self.hero.set_metrics("Pret", self.config.station_code)
        self._update_session_actions()
        self._goto(self.welcome_page)

    def _back_to_methods(self) -> None:
        """Returns to the source choice without disconnecting the current user."""

        self.state.selected_local_document = None
        self.state.registered_document = None
        self.current_pdf_document = None
        self._reset_document_selection()
        self.page_selection_input.clear()
        self.context_input.clear()
        self.auto_logout_timer.stop()
        self._goto(self.method_page)

    def _back_to_documents(self) -> None:
        """Lets the user return to the document list to change file."""

        self.state.registered_document = None
        self.current_pdf_document = None
        self.page_selection_input.clear()
        self.context_input.clear()
        self.preview_status.setText("")
        self.auto_logout_timer.stop()
        self._goto(self.documents_page)

    def _goto(self, page: QWidget) -> None:
        self.stack.setCurrentWidget(page)

    def _logout_user(self) -> None:
        self._reset_workflow()

    def _update_session_actions(self) -> None:
        self.logout_button.setVisible(self.state.user_id is not None)

    def _set_busy(self, busy: bool) -> None:
        self.is_busy = busy
        for widget in self.busy_widgets:
            widget.setEnabled(not busy)
        if busy:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
