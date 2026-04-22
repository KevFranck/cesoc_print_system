from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Qt, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QComboBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.runtime import guarded_ui_action
from app.services.api_client import ApiClient, ApiError
from app.services.config_service import ClientStationConfig
from app.services.kiosk_workflow_service import KioskWorkflowService, RegisteredDocument
from app.services.usb_monitor_service import LocalPdfDocument
from app.ui.shared.widgets import FormField, HeroBanner, SectionCard


class DocumentLoadWorker(QObject):
    """Charge les documents USB ou e-mail hors du thread principal."""

    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, workflow: KioskWorkflowService, method: str, user_email: str | None) -> None:
        super().__init__()
        self.workflow = workflow
        self.method = method
        self.user_email = user_email

    def run(self) -> None:
        try:
            documents = (
                self.workflow.load_usb_documents()
                if self.method == "usb"
                else self.workflow.load_email_documents(self.user_email)
            )
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.finished.emit(documents)


class PreviewRenderWorker(QObject):
    """Prépare les pages d'aperçu en arrière-plan pour garder la borne fluide."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, workflow: KioskWorkflowService, pdf_path: str) -> None:
        super().__init__()
        self.workflow = workflow
        self.pdf_path = pdf_path

    def run(self) -> None:
        try:
            payload = self.workflow.preview_service.build_preview_payload(self.pdf_path)
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.finished.emit(payload)


@dataclass(slots=True)
class KioskSelection:
    """État transitoire de la session active sur la borne."""

    user_id: int | None = None
    user_name: str | None = None
    user_email: str | None = None
    active_session_id: int | None = None
    selected_method: str | None = None
    selected_local_document: LocalPdfDocument | None = None
    registered_document: RegisteredDocument | None = None


class KioskMainWindow(QMainWindow):
    """Fenêtre principale de la borne avec un parcours guidé et stable."""

    def __init__(self, api_client: ApiClient, config: ClientStationConfig) -> None:
        super().__init__()
        self.workflow = KioskWorkflowService(api_client, config)
        self.config = config
        self.state = KioskSelection()
        self.is_busy = False
        self.current_preview_pixmaps: list[QPixmap] = []
        self.busy_widgets: list[QWidget] = []
        self.load_thread: QThread | None = None
        self.load_worker: DocumentLoadWorker | None = None
        self.preview_thread: QThread | None = None
        self.preview_worker: PreviewRenderWorker | None = None
        self.navigation_history: list[QWidget] = []

        self.auto_logout_timer = QTimer(self)
        self.auto_logout_timer.setSingleShot(True)
        self.auto_logout_timer.timeout.connect(self._logout_user)

        self.setWindowTitle(f"CESOC Borne d'impression - {config.station_code}")
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
            "Connectez-vous avec votre e-mail, choisissez votre document PDF puis lancez l'impression.",
        )
        layout.addWidget(self.hero)

        self.top_actions = QHBoxLayout()
        self.back_button = QPushButton("Retour")
        self.back_button.setObjectName("SecondaryButton")
        self.back_button.clicked.connect(self._go_back)
        self.top_actions.addWidget(self.back_button)
        self.busy_widgets.append(self.back_button)
        self.top_actions.addStretch(1)
        self.logout_button = QPushButton("Se déconnecter")
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

        title = QLabel("Connectez-vous")
        title.setObjectName("KioskTitle")
        text = QLabel("Votre e-mail et votre mot de passe permettent de retrouver votre quota du jour.")
        text.setObjectName("KioskText")
        text.setWordWrap(True)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("exemple@domaine.com")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        login_button = QPushButton("Se connecter")
        login_button.setObjectName("KioskPrimaryButton")
        login_button.clicked.connect(self._authenticate)
        self.busy_widgets.append(login_button)

        register_button = QPushButton("Creer mon compte")
        register_button.setObjectName("SecondaryButton")
        register_button.clicked.connect(self._open_registration_dialog)
        self.busy_widgets.append(register_button)

        back_button = QPushButton("Retour")
        back_button.setObjectName("SecondaryButton")
        back_button.clicked.connect(self._go_back)
        self.busy_widgets.append(back_button)

        card_layout.addWidget(title)
        card_layout.addWidget(text)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(login_button)
        card_layout.addWidget(register_button)
        card_layout.addWidget(back_button)
        layout.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)
        return page

    def _build_method_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Choisissez votre méthode")
        title.setObjectName("KioskTitle")
        subtitle = QLabel("Vous pouvez imprimer depuis une clé USB ou depuis un e-mail envoyé pendant cette session.")
        subtitle.setObjectName("KioskText")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)

        change_password_button = QPushButton("Modifier mon mot de passe")
        change_password_button.setObjectName("SecondaryButton")
        change_password_button.clicked.connect(self._open_password_change_dialog)
        self.busy_widgets.append(change_password_button)
        layout.addWidget(change_password_button)

        buttons = [
            ("Clé USB", "usb", "Parcourir les PDF détectés sur le support amovible"),
            ("E-mail", "email", "Récupérer les PDF envoyés à la boîte mail de service"),
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
        self.documents_context = QLabel("Choisissez un document à imprimer.")
        self.documents_context.setObjectName("KioskText")
        action_bar.addWidget(self.documents_context)
        action_bar.addStretch(1)

        change_method_button = QPushButton("Changer de méthode")
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

        refresh_button = QPushButton("Rafraîchir")
        refresh_button.setObjectName("SecondaryButton")
        refresh_button.clicked.connect(self._refresh_current_method)
        self.busy_widgets.append(refresh_button)

        left_layout.addWidget(self.documents_title)
        left_layout.addWidget(self.documents_list)
        left_layout.addWidget(refresh_button)
        body.addWidget(left, 1)

        right = SectionCard("Resume")
        right_layout = QVBoxLayout(right.content)
        self.document_summary = QLabel("Sélectionnez un document PDF.")
        self.document_summary.setObjectName("KioskText")
        self.document_summary.setWordWrap(True)

        self.documents_help = QLabel(
            "Les documents récupérés par e-mail restent disponibles uniquement pendant cette session."
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

        header = QLabel("Aperçu et impression")
        header.setObjectName("KioskTitle")
        layout.addWidget(header)

        body = QHBoxLayout()

        info_card = SectionCard("Résumé du document")
        info_layout = QVBoxLayout(info_card.content)

        self.preview_summary = QLabel("Aucun document.")
        self.preview_summary.setObjectName("KioskText")
        self.preview_summary.setWordWrap(True)

        self.quota_summary = QLabel("")
        self.quota_summary.setObjectName("QuotaAlertText")
        self.quota_summary.setWordWrap(True)

        self.page_selection_input = QLineEdit()
        self.page_selection_input.setPlaceholderText("Pages à imprimer : toutes, ou par exemple 1-3,5")

        self.copy_count_input = QLineEdit()
        self.copy_count_input.setPlaceholderText("Nombre de copies : 1")
        self.duplex_mode_input = QComboBox()
        self.duplex_mode_input.addItem("Recto uniquement", "simplex")
        self.duplex_mode_input.addItem("Recto-verso", "duplex")
        self.duplex_mode_input.addItem("Recto-verso bord court", "duplexshort")
        self.context_input = QLineEdit()
        self.context_input.setPlaceholderText("Exemple : CAF, titre de séjour, CV")

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
        info_layout.addWidget(self.copy_count_input)
        info_layout.addWidget(self.duplex_mode_input)
        info_layout.addWidget(self.context_input)
        info_layout.addStretch(1)
        info_layout.addWidget(back_button)
        info_layout.addWidget(self.print_button)
        body.addWidget(info_card, 1)

        preview_card = SectionCard("Aperçu du document")
        preview_layout = QVBoxLayout(preview_card.content)

        self.preview_pages_container = QWidget()
        self.preview_pages_layout = QVBoxLayout(self.preview_pages_container)
        self.preview_pages_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_pages_layout.setSpacing(18)

        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setWidget(self.preview_pages_container)
        preview_layout.addWidget(self.preview_scroll)

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

        result_card = SectionCard("Résultat de l'impression")
        result_card.setMaximumWidth(760)
        result_layout = QVBoxLayout(result_card.content)
        result_layout.setSpacing(14)

        self.result_badge = QLabel("EN ATTENTE")
        self.result_badge.setObjectName("ResultBadgeNeutral")
        self.result_badge.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.result_title = QLabel("Résultat")
        self.result_title.setObjectName("KioskTitle")
        self.result_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.result_message = QLabel("")
        self.result_message.setObjectName("KioskText")
        self.result_message.setWordWrap(True)
        self.result_message.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.continue_after_print_button = QPushButton("Continuer")
        self.continue_after_print_button.setObjectName("KioskPrimaryButton")
        self.continue_after_print_button.clicked.connect(self._continue_after_print)
        self.busy_widgets.append(self.continue_after_print_button)

        self.done_after_print_button = QPushButton("Se déconnecter")
        self.done_after_print_button.setObjectName("KioskPrimaryButton")
        self.done_after_print_button.clicked.connect(self._logout_user)
        self.busy_widgets.append(self.done_after_print_button)

        result_layout.addWidget(self.result_badge, 0, Qt.AlignmentFlag.AlignHCenter)
        result_layout.addWidget(self.result_title, 0, Qt.AlignmentFlag.AlignHCenter)
        result_layout.addWidget(self.result_message, 0, Qt.AlignmentFlag.AlignHCenter)
        result_layout.addSpacing(6)
        result_layout.addWidget(self.continue_after_print_button, 0, Qt.AlignmentFlag.AlignHCenter)
        result_layout.addWidget(self.done_after_print_button, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(result_card, 0, Qt.AlignmentFlag.AlignCenter)
        return page

    @guarded_ui_action
    def _authenticate(self) -> None:
        if self.is_busy:
            return
        email = self.email_input.text().strip()
        password = self.password_input.text()
        if not email or not password:
            QMessageBox.warning(self, "Connexion impossible", "Renseigne ton e-mail et ton mot de passe.")
            return
        self._set_busy(True)
        try:
            user = self.workflow.authenticate_user(email, password)
            session = self.workflow.start_station_session(user)
        except ApiError as exc:
            QMessageBox.warning(self, "Connexion impossible", exc.message)
            self._set_busy(False)
            return

        self.state.user_id = user.id
        self.state.user_name = user.full_name
        self.state.user_email = user.email
        self.state.active_session_id = int(session.get("id") or 0) or None
        self.hero.set_metrics("Connecté", user.full_name)
        self.navigation_history.clear()
        self._update_session_actions()
        self._goto(self.method_page, remember=False)
        self._set_busy(False)

    @guarded_ui_action
    def _open_registration_dialog(self) -> None:
        if self.is_busy:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Creer mon compte")
        dialog.setMinimumWidth(680)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)

        title = QLabel("Un compte pour imprimer plus vite")
        title.setObjectName("KioskTitle")
        intro = QLabel(
            "Crée ton accès CESOC en une minute. Ton e-mail servira à retrouver tes documents envoyés et ton quota."
        )
        intro.setObjectName("KioskText")
        intro.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(intro)

        form_card = SectionCard("Tes informations")
        form = QGridLayout(form_card.content)
        form.setSpacing(12)

        first_name = QLineEdit()
        first_name.setPlaceholderText("Exemple : Amina")
        last_name = QLineEdit()
        last_name.setPlaceholderText("Exemple : Diallo")
        email = QLineEdit()
        email.setPlaceholderText("prenom.nom@email.com")
        phone = QLineEdit()
        phone.setPlaceholderText("Optionnel")
        password = QLineEdit()
        password.setPlaceholderText("Au moins 4 caracteres")
        password.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_password = QLineEdit()
        confirm_password.setPlaceholderText("Retape le mot de passe")
        confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

        form.addWidget(FormField("Prenom", first_name), 0, 0)
        form.addWidget(FormField("Nom", last_name), 0, 1)
        form.addWidget(FormField("Email", email), 1, 0)
        form.addWidget(FormField("Telephone", phone), 1, 1)
        form.addWidget(FormField("Mot de passe", password), 2, 0)
        form.addWidget(FormField("Confirmation", confirm_password), 2, 1)
        layout.addWidget(form_card)

        hint = QLabel("Garde ce mot de passe pour tes prochaines impressions sur la borne.")
        hint.setObjectName("QuotaAlertText")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        create_button = QPushButton("Creer le compte")
        create_button.setObjectName("KioskPrimaryButton")
        cancel_button = QPushButton("Annuler")
        cancel_button.setObjectName("SecondaryButton")
        create_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        actions = QHBoxLayout()
        actions.addWidget(cancel_button)
        actions.addStretch(1)
        actions.addWidget(create_button)
        layout.addLayout(actions)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if password.text() != confirm_password.text():
            QMessageBox.warning(self, "Erreur", "Les deux mots de passe ne correspondent pas.")
            return
        if len(password.text()) < 4:
            QMessageBox.warning(self, "Erreur", "Le mot de passe doit contenir au moins 4 caracteres.")
            return
        payload = {
            "first_name": first_name.text().strip(),
            "last_name": last_name.text().strip(),
            "email": email.text().strip(),
            "phone": phone.text().strip() or None,
            "password": password.text(),
        }
        if not payload["first_name"] or not payload["last_name"] or not payload["email"] or not payload["password"]:
            QMessageBox.warning(self, "Erreur", "Prenom, nom, email et mot de passe sont obligatoires.")
            return
        self._set_busy(True)
        try:
            user = self.workflow.register_user(payload)
        except ApiError as exc:
            QMessageBox.warning(self, "Creation impossible", exc.message)
            self._set_busy(False)
            return
        self.email_input.setText(user.email or payload["email"])
        self.password_input.setText(payload["password"])
        self._set_busy(False)
        QMessageBox.information(self, "Compte cree", "Ton compte est pret. Tu peux maintenant te connecter.")

    @guarded_ui_action
    def _open_password_change_dialog(self) -> None:
        if self.is_busy or not self.state.user_id:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Modifier mon mot de passe")
        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        current_password = QLineEdit()
        current_password.setEchoMode(QLineEdit.EchoMode.Password)
        new_password = QLineEdit()
        new_password.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_password = QLineEdit()
        confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("Mot de passe actuel", current_password)
        form.addRow("Nouveau mot de passe", new_password)
        form.addRow("Confirmer", confirm_password)
        layout.addLayout(form)

        save_button = QPushButton("Enregistrer")
        cancel_button = QPushButton("Annuler")
        save_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        layout.addWidget(save_button)
        layout.addWidget(cancel_button)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if new_password.text() != confirm_password.text():
            QMessageBox.warning(self, "Erreur", "Les deux nouveaux mots de passe ne correspondent pas.")
            return
        self._set_busy(True)
        try:
            self.workflow.change_user_password(self.state.user_id, current_password.text(), new_password.text())
        except ApiError as exc:
            QMessageBox.warning(self, "Modification impossible", exc.message)
            self._set_busy(False)
            return
        self._set_busy(False)
        QMessageBox.information(self, "Mot de passe modifie", "Ton mot de passe a ete mis a jour.")

    @guarded_ui_action
    def _load_documents(self, method: str, label: str) -> None:
        if self.is_busy:
            return
        self._set_busy(True)

        self.state.selected_method = method
        self.state.selected_local_document = None
        self.state.registered_document = None
        self.current_preview_pixmaps = []
        self.documents_title.setText(f"Documents via {label}")
        self.documents_context.setText(f"Source active : {label}. Chargement des documents en cours...")
        self._reset_document_selection()
        self._goto(self.documents_page)
        self._start_document_loading(method, self.state.user_email)

    @guarded_ui_action
    def _refresh_current_method(self) -> None:
        labels = {
            "usb": "Clé USB",
            "email": "E-mail",
        }
        if self.state.selected_method:
            self._load_documents(self.state.selected_method, labels.get(self.state.selected_method, "Documents"))

    def _select_document(self) -> None:
        current_item = self.documents_list.currentItem()
        if not current_item:
            self.state.selected_local_document = None
            self.document_summary.setText("Sélectionnez un document PDF.")
            return

        document = current_item.data(Qt.ItemDataRole.UserRole)
        self.state.selected_local_document = document
        self.document_summary.setText(
            f"Document: {document.original_filename}\n"
            f"Source : {document.source_label}\n"
            f"Pages : {document.page_count}\n"
            f"Chemin local : {document.local_path}"
        )

    def _clear_preview_pages(self) -> None:
        while self.preview_pages_layout.count():
            item = self.preview_pages_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _add_preview_placeholder(self, message: str) -> None:
        placeholder = QLabel(message)
        placeholder.setObjectName("KioskText")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setWordWrap(True)
        placeholder.setMinimumHeight(220)
        self.preview_pages_layout.addWidget(placeholder)
        self.preview_pages_layout.addStretch(1)

    def _reset_document_selection(self) -> None:
        self.documents_list.clear()
        self.document_summary.setText("Sélectionnez un document PDF.")
        self.preview_status.setText("")
        self._clear_preview_pages()
        self._add_preview_placeholder("Aperçu en attente.")

    def _start_document_loading(self, method: str, user_email: str | None) -> None:
        self._dispose_load_worker()
        self.load_thread = QThread(self)
        self.load_worker = DocumentLoadWorker(self.workflow, method, user_email)
        self.load_worker.moveToThread(self.load_thread)
        self.load_thread.started.connect(self.load_worker.run)
        self.load_worker.finished.connect(self._on_documents_loaded)
        self.load_worker.failed.connect(self._on_document_loading_failed)
        self.load_worker.finished.connect(self.load_thread.quit)
        self.load_worker.failed.connect(self.load_thread.quit)
        self.load_thread.finished.connect(self._dispose_load_worker)
        self.load_thread.start()

    def _dispose_load_worker(self) -> None:
        if self.load_thread is not None and self.load_thread.isRunning():
            self.load_thread.quit()
            self.load_thread.wait(2000)
        if self.load_worker is not None:
            self.load_worker.deleteLater()
            self.load_worker = None
        if self.load_thread is not None:
            self.load_thread.deleteLater()
            self.load_thread = None

    def _on_documents_loaded(self, documents: list[LocalPdfDocument]) -> None:
        self.documents_list.setUpdatesEnabled(False)
        try:
            for document in documents:
                item = QListWidgetItem(f"{document.original_filename} - {document.page_count} pages")
                item.setData(Qt.ItemDataRole.UserRole, document)
                self.documents_list.addItem(item)
        finally:
            self.documents_list.setUpdatesEnabled(True)
        active_label = self.documents_title.text().replace("Documents via ", "")
        count = len(documents)
        self.documents_context.setText(f"Source active : {active_label}. {count} document(s) disponible(s).")
        self._set_busy(False)

    def _on_document_loading_failed(self, message: str) -> None:
        QMessageBox.warning(self, "Chargement impossible", message)
        active_label = self.documents_title.text().replace("Documents via ", "")
        self.documents_context.setText(f"Source active : {active_label}. Aucun document chargé.")
        self._set_busy(False)

    @guarded_ui_action
    def _prepare_preview(self) -> None:
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
            QMessageBox.warning(self, "Préparation impossible", exc.message)
            self._set_busy(False)
            return

        self.state.registered_document = registered
        self.preview_summary.setText(
            f"Document : {registered.original_filename}\n"
            f"Pages : {registered.page_count}\n"
            f"Source : {registered.source_type} ({registered.source_label})"
        )
        self.quota_summary.setText(
            f"Quota restant : {quota.get('remaining_pages', 0)} / {quota.get('effective_quota', 0)} pages"
        )
        self.page_selection_input.clear()
        self.copy_count_input.setText("1")
        self.duplex_mode_input.setCurrentIndex(0)
        self._clear_preview_pages()
        self._add_preview_placeholder("Chargement du document en cours…")
        self.preview_status.setText("Le document est en cours de préparation pour l'aperçu.")
        self._goto(self.preview_page)
        self._set_busy(False)
        self._start_preview_render(registered.local_path)

    def _start_preview_render(self, pdf_path: str) -> None:
        self._dispose_preview_worker()
        self.preview_thread = QThread(self)
        self.preview_worker = PreviewRenderWorker(self.workflow, pdf_path)
        self.preview_worker.moveToThread(self.preview_thread)
        self.preview_thread.started.connect(self.preview_worker.run)
        self.preview_worker.finished.connect(self._on_preview_rendered)
        self.preview_worker.failed.connect(self._on_preview_failed)
        self.preview_worker.finished.connect(self.preview_thread.quit)
        self.preview_worker.failed.connect(self.preview_thread.quit)
        self.preview_thread.finished.connect(self._dispose_preview_worker)
        self.preview_thread.start()

    def _dispose_preview_worker(self) -> None:
        if self.preview_thread is not None and self.preview_thread.isRunning():
            self.preview_thread.quit()
            self.preview_thread.wait(1000)
        if self.preview_worker is not None:
            self.preview_worker.deleteLater()
            self.preview_worker = None
        if self.preview_thread is not None:
            self.preview_thread.deleteLater()
            self.preview_thread = None

    def _on_preview_rendered(self, payload: object) -> None:
        self._clear_preview_pages()

        if not isinstance(payload, dict):
            self.current_preview_pixmaps = []
            self._add_preview_placeholder("Aperçu indisponible pour ce document sur ce poste.")
            self.preview_status.setText("Le document n'a pas pu être préparé pour l'aperçu.")
            return

        images = payload.get("images")
        image_source = str(payload.get("image_source") or "").strip()
        page_count = int(payload.get("page_count") or 0)
        rendered_pages = int(payload.get("rendered_pages") or 0)
        valid_images = [image for image in images if isinstance(image, QImage) and not image.isNull()] if isinstance(images, list) else []

        if not valid_images:
            self.current_preview_pixmaps = []
            self._add_preview_placeholder("Aperçu indisponible sur ce poste.")
            self.preview_status.setText("Le document n'a pas pu être affiché visuellement.")
            return

        self.current_preview_pixmaps = []
        for index, image in enumerate(valid_images, start=1):
            pixmap = QPixmap.fromImage(image)
            self.current_preview_pixmaps.append(pixmap)

            page_frame = QFrame()
            page_frame.setObjectName("PreviewPageCard")
            page_layout = QVBoxLayout(page_frame)
            page_layout.setContentsMargins(12, 12, 12, 12)
            page_layout.setSpacing(10)

            page_title = QLabel(f"Page {index}")
            page_title.setObjectName("SectionTitle")
            page_layout.addWidget(page_title)

            page_label = QLabel()
            page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            page_label.setPixmap(pixmap)
            page_layout.addWidget(page_label)

            self.preview_pages_layout.addWidget(page_frame)

        self.preview_pages_layout.addStretch(1)

        if rendered_pages < page_count:
            self.preview_status.setText(
                f"Aperçu chargé. {rendered_pages} page(s) affichée(s) sur {page_count} pour garder la borne fluide."
            )
        else:
            self.preview_status.setText(
                f"Aperçu complet chargé. {page_count} page(s) affichée(s)."
            )

    def _on_preview_failed(self, message: str) -> None:
        self._clear_preview_pages()
        self.current_preview_pixmaps = []
        self._add_preview_placeholder("Aperçu indisponible pour ce document sur ce poste.")
        self.preview_status.setText(
            f"Échec de l'aperçu : {message or 'une erreur interne est survenue.'}"
        )

    @guarded_ui_action
    def _print_current_document(self) -> None:
        if self.is_busy:
            return
        if not self.state.registered_document:
            QMessageBox.warning(self, "Impression impossible", "Aucun document pret a imprimer.")
            return

        self._set_busy(True)
        context_label = self.context_input.text().strip() or "Démarche administrative"
        try:
            normalized_selection, selected_page_count = self.workflow.resolve_page_selection(
                self.state.registered_document.page_count,
                self.page_selection_input.text().strip() or None,
            )
            copy_count = self.workflow.resolve_copy_count(self.copy_count_input.text().strip() or None)
            duplex_mode = str(self.duplex_mode_input.currentData() or "simplex")
            duplex_label = self.duplex_mode_input.currentText()
            printer_ready = self.workflow.validate_printer_ready()
            if not printer_ready.success:
                QMessageBox.warning(self, "Imprimante indisponible", printer_ready.message)
                self._set_busy(False)
                return
        except ValueError as exc:
            QMessageBox.warning(self, "Parametres invalides", str(exc))
            self._set_busy(False)
            return
        try:
            job, result = self.workflow.print_registered_document(
                self.state.registered_document,
                context_label,
                normalized_selection,
                copy_count,
                duplex_mode,
            )
        except ApiError as exc:
            QMessageBox.warning(self, "Erreur", exc.message)
            self._set_busy(False)
            return

        self.result_title.setText("Impression réussie" if result.success else "Impression échouée")
        self.result_badge.setText("TERMINÉ" if result.success else "ÉCHEC")
        self.result_badge.setObjectName("ResultBadgeSuccess" if result.success else "ResultBadgeError")
        self.result_badge.style().unpolish(self.result_badge)
        self.result_badge.style().polish(self.result_badge)
        self.done_after_print_button.setVisible(not result.success)
        selection_label = normalized_selection or "Toutes les pages"
        if result.success:
            self.result_message.setText(
                f"Document : {self.state.registered_document.original_filename}\n"
                f"Pages : {selection_label}\n"
                f"Copies : {copy_count}\n"
                f"Total imprime : {selected_page_count * copy_count} page(s)\n"
                f"Mode : {duplex_label}"
            )
        else:
            self.result_message.setText(
                f"Document : {self.state.registered_document.original_filename}\n"
                f"Pages demandees : {selection_label}\n"
                f"Copies : {copy_count}\n"
                f"Mode : {duplex_label}\n"
                f"Erreur : {result.message}"
            )
        self._goto(self.result_page)
        self._set_busy(False)

    @guarded_ui_action
    def _continue_after_print(self) -> None:
        if self.is_busy:
            return
        self.state.selected_local_document = None
        self.state.registered_document = None
        self.current_preview_pixmaps = []
        self.documents_list.clearSelection()
        self.document_summary.setText("Sélectionnez un document PDF.")
        self.page_selection_input.clear()
        self.copy_count_input.clear()
        self.duplex_mode_input.setCurrentIndex(0)
        self.context_input.clear()
        self.preview_status.setText("")
        self._clear_preview_pages()
        self._add_preview_placeholder("Aperçu en attente.")
        self.navigation_history.clear()
        self.auto_logout_timer.stop()
        self._goto(self.method_page, remember=False)

    def _reset_workflow(self) -> None:
        if self.state.active_session_id:
            try:
                self.workflow.end_station_session(self.state.active_session_id)
            except ApiError:
                pass
        self.workflow.cleanup_session_artifacts()
        self.state = KioskSelection()
        self.current_preview_pixmaps = []
        self.navigation_history.clear()
        self.auto_logout_timer.stop()
        self.email_input.clear()
        self.password_input.clear()
        self.documents_list.clear()
        self.page_selection_input.clear()
        self.copy_count_input.clear()
        self.duplex_mode_input.setCurrentIndex(0)
        self.context_input.clear()
        self.documents_context.setText("Choisissez un document à imprimer.")
        self.document_summary.setText("Sélectionnez un document PDF.")
        self.preview_summary.setText("Aucun document.")
        self.quota_summary.setText("")
        self.preview_status.setText("")
        self._clear_preview_pages()
        self._add_preview_placeholder("Aperçu en attente.")
        self.result_badge.setText("EN ATTENTE")
        self.result_badge.setObjectName("ResultBadgeNeutral")
        self.result_badge.style().unpolish(self.result_badge)
        self.result_badge.style().polish(self.result_badge)
        self.done_after_print_button.setVisible(True)
        self.hero.set_metrics("Prêt", self.config.station_code)
        self._dispose_preview_worker()
        self._update_session_actions()
        self._goto(self.welcome_page, remember=False)

    def _back_to_methods(self) -> None:
        self._drop_history_target(self.documents_page)
        self._drop_history_target(self.method_page)
        self.state.selected_local_document = None
        self.state.registered_document = None
        self.current_preview_pixmaps = []
        self._dispose_preview_worker()
        self._reset_document_selection()
        self.page_selection_input.clear()
        self.copy_count_input.clear()
        self.duplex_mode_input.setCurrentIndex(0)
        self.context_input.clear()
        self.auto_logout_timer.stop()
        self._goto(self.method_page, remember=False)

    def _back_to_documents(self) -> None:
        self._drop_history_target(self.preview_page)
        self._drop_history_target(self.documents_page)
        self.state.registered_document = None
        self.current_preview_pixmaps = []
        self._dispose_preview_worker()
        self.page_selection_input.clear()
        self.copy_count_input.clear()
        self.duplex_mode_input.setCurrentIndex(0)
        self.context_input.clear()
        self.preview_status.setText("")
        self._clear_preview_pages()
        self._add_preview_placeholder("Aperçu en attente.")
        self.auto_logout_timer.stop()
        self._goto(self.documents_page, remember=False)

    def _goto(self, page: QWidget, remember: bool = True) -> None:
        current_page = self.stack.currentWidget()
        if remember and current_page is not None and current_page is not page:
            self.navigation_history.append(current_page)
        self.stack.setCurrentWidget(page)
        self._update_session_actions()

    def _drop_history_target(self, page: QWidget) -> None:
        while self.navigation_history and self.navigation_history[-1] is page:
            self.navigation_history.pop()

    def _go_back(self) -> None:
        if self.is_busy:
            return
        current_page = self.stack.currentWidget()
        if current_page is self.documents_page:
            self._back_to_methods()
            return
        if current_page is self.preview_page:
            self._back_to_documents()
            return
        if not self.navigation_history:
            return
        previous_page = self.navigation_history.pop()
        self._goto(previous_page, remember=False)

    @guarded_ui_action
    def _logout_user(self) -> None:
        self._reset_workflow()

    def _update_session_actions(self) -> None:
        self.logout_button.setVisible(self.state.user_id is not None)
        current_page = self.stack.currentWidget() if hasattr(self, "stack") else None
        is_step_with_manual_back = current_page is self.documents_page or current_page is self.preview_page
        is_back_hidden_page = current_page is None or current_page is self.welcome_page or current_page is self.result_page
        self.back_button.setVisible(not is_back_hidden_page and (bool(self.navigation_history) or is_step_with_manual_back))

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
