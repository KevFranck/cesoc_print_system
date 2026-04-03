from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.api_client import ApiClient
from app.services.dashboard_service import AdminDashboardService
from app.ui.shared.widgets import FormField, PageHeader, ScrollSection, SearchField, SectionCard


class ClientsPage(QWidget):
    """Vue admin centrée sur les utilisateurs, leur quota et les bonus manuels."""

    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.setObjectName("Page")
        self.service = AdminDashboardService(api_client)
        self.clients: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(PageHeader("Clients", "Recherche, creation rapide et lecture du quota restant par usager."))

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        left_panel = QWidget()
        left = QVBoxLayout(left_panel)
        left.setContentsMargins(0, 0, 0, 0)
        self.search = SearchField("Rechercher un client par nom, email ou demarche")
        self.search.textChanged.connect(self._render_table)
        left.addWidget(self.search)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Nom", "Email", "Pages restantes", "Sessions", "Demarche"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._sync_detail_panel)
        self.table.setMinimumHeight(440)
        left.addWidget(self.table)
        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right = QVBoxLayout(right_panel)
        right.setContentsMargins(0, 0, 0, 0)

        self.detail_card = SectionCard("Fiche client")
        detail_layout = QVBoxLayout(self.detail_card.content)
        self.detail_name = QLabel("Aucun client selectionne")
        self.detail_name.setObjectName("SectionTitle")
        self.detail_info = QLabel("Selectionne une ligne pour afficher les details du dossier.")
        self.detail_info.setObjectName("MutedText")
        self.detail_info.setWordWrap(True)
        detail_layout.addWidget(self.detail_name)
        detail_layout.addWidget(self.detail_info)
        right.addWidget(self.detail_card)

        bonus_card = QFrame()
        bonus_card.setObjectName("SectionCard")
        bonus_layout = QVBoxLayout(bonus_card)
        bonus_title = QLabel("Deblocage manuel")
        bonus_title.setObjectName("SectionTitle")
        bonus_layout.addWidget(bonus_title)
        self.bonus_pages = QLineEdit()
        self.bonus_pages.setPlaceholderText("Nombre de pages a ajouter")
        self.bonus_reason = QLineEdit()
        self.bonus_reason.setPlaceholderText("Raison du deblocage manuel")
        bonus_layout.addWidget(FormField("Pages bonus", self.bonus_pages))
        bonus_layout.addWidget(FormField("Motif", self.bonus_reason))
        grant_button = QPushButton("Ajouter des pages")
        grant_button.clicked.connect(self.grant_bonus)
        bonus_layout.addWidget(grant_button)
        right.addWidget(bonus_card)

        form_card = QFrame()
        form_card.setObjectName("SectionCard")
        form_layout = QVBoxLayout(form_card)
        title = QLabel("Ajouter un client")
        title.setObjectName("SectionTitle")
        form_layout.addWidget(title)

        self.first_name = QLineEdit()
        self.first_name.setPlaceholderText("Prenom")
        self.last_name = QLineEdit()
        self.last_name.setPlaceholderText("Nom de famille")
        self.email = QLineEdit()
        self.email.setPlaceholderText("adresse@email.com")
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("Telephone")
        self.note = QLineEdit()
        self.note.setPlaceholderText("Demarche ou note administrative")

        form_layout.addWidget(FormField("Prenom", self.first_name))
        form_layout.addWidget(FormField("Nom", self.last_name))
        form_layout.addWidget(FormField("Email", self.email))
        form_layout.addWidget(FormField("Telephone", self.phone))
        form_layout.addWidget(FormField("Demarche", self.note))

        save_button = QPushButton("Ajouter le client")
        save_button.clicked.connect(self.create_client)
        form_layout.addWidget(save_button)
        form_layout.addStretch(1)
        right.addWidget(form_card)
        right.addStretch(1)

        splitter.addWidget(ScrollSection(right_panel))
        splitter.setSizes([900, 420])
        layout.addWidget(splitter, 1)
        self.refresh()

    def refresh(self) -> None:
        self.clients = self.service.get_clients()
        self._render_table()
        self._sync_detail_panel()

    def create_client(self) -> None:
        payload = {
            "first_name": self.first_name.text().strip(),
            "last_name": self.last_name.text().strip(),
            "email": self.email.text().strip() or None,
            "phone": self.phone.text().strip() or None,
            "administrative_note": self.note.text().strip() or None,
        }
        if not payload["first_name"] or not payload["last_name"]:
            QMessageBox.warning(self, "Erreur", "Le prenom et le nom sont obligatoires.")
            return
        response = self.service.create_client(payload)
        if not response:
            QMessageBox.warning(self, "Erreur", "Impossible de creer le client.")
            return
        for widget in [self.first_name, self.last_name, self.email, self.phone, self.note]:
            widget.clear()
        self.refresh()

    def grant_bonus(self) -> None:
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection requise", "Selectionne d'abord un utilisateur.")
            return
        client = selected_items[0].data(Qt.ItemDataRole.UserRole)
        try:
            pages = int(self.bonus_pages.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Le nombre de pages bonus doit etre numerique.")
            return
        result = self.service.grant_bonus_pages(
            int(client["id"]),
            {
                "pages": pages,
                "reason": self.bonus_reason.text().strip() or "Deblocage manuel",
                "granted_by": "Console Admin",
            },
        )
        if not result:
            QMessageBox.warning(self, "Erreur", "Impossible d'ajouter des pages bonus.")
            return
        self.bonus_pages.clear()
        self.bonus_reason.clear()
        self.refresh()

    def _render_table(self) -> None:
        query = self.search.text().strip().lower()
        filtered = [
            client
            for client in self.clients
            if not query
            or query in client.get("full_name", "").lower()
            or query in (client.get("email") or "").lower()
            or query in (client.get("administrative_note") or "").lower()
        ]
        self.table.setRowCount(len(filtered))
        for row, client in enumerate(filtered):
            name_item = QTableWidgetItem(client.get("full_name", ""))
            name_item.setData(Qt.ItemDataRole.UserRole, client)
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(client.get("email") or ""))
            self.table.setItem(row, 2, QTableWidgetItem(str(client.get("remaining_pages", 0))))
            self.table.setItem(row, 3, QTableWidgetItem(str(client.get("active_session_count", 0))))
            self.table.setItem(row, 4, QTableWidgetItem(client.get("administrative_note") or ""))
        if filtered:
            self.table.selectRow(0)

    def _sync_detail_panel(self) -> None:
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.detail_name.setText("Aucun client selectionne")
            self.detail_info.setText("Selectionne une ligne pour afficher les details du dossier.")
            return
        client = selected_items[0].data(Qt.ItemDataRole.UserRole)
        quota = self.service.get_quota_status(int(client["id"]))
        self.detail_name.setText(client.get("full_name", ""))
        self.detail_info.setText(
            f"Email: {client.get('email') or 'Non renseigne'}\n"
            f"Telephone: {client.get('phone') or 'Non renseigne'}\n"
            f"Pages utilisees aujourd'hui: {quota.get('printed_pages_today', client.get('used_pages_today', 0))}\n"
            f"Bonus pages: {quota.get('bonus_pages', 0)}\n"
            f"Quota restant: {quota.get('remaining_pages', client.get('remaining_pages', 0))}\n"
            f"Jobs refuses aujourd'hui: {quota.get('rejected_jobs_today', 0)}\n"
            f"Sessions actives: {client.get('active_session_count', 0)}\n"
            f"Demarche: {client.get('administrative_note') or 'Non renseignee'}"
        )
