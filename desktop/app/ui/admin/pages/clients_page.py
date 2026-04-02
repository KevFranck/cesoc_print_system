from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.api_client import ApiClient
from app.services.dashboard_service import AdminDashboardService
from app.ui.shared.widgets import PageHeader, SearchField, SectionCard


class ClientsPage(QWidget):
    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.setObjectName("Page")
        self.service = AdminDashboardService(api_client)
        self.clients: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(PageHeader("Clients", "Recherche, creation rapide et lecture du quota restant par usager."))

        body = QHBoxLayout()
        body.setSpacing(16)

        left = QVBoxLayout()
        self.search = SearchField("Rechercher un client par nom, email ou demarche")
        self.search.textChanged.connect(self._render_table)
        left.addWidget(self.search)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Nom", "Email", "Pages restantes", "Sessions", "Demarche"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._sync_detail_panel)
        left.addWidget(self.table)
        body.addLayout(left, 2)

        right = QVBoxLayout()

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

        form_card = QFrame()
        form_card.setObjectName("SectionCard")
        form_layout = QVBoxLayout(form_card)
        title = QLabel("Ajouter un client")
        title.setObjectName("SectionTitle")
        form_layout.addWidget(title)

        self.first_name = QLineEdit()
        self.last_name = QLineEdit()
        self.email = QLineEdit()
        self.phone = QLineEdit()
        self.note = QLineEdit()

        form = QFormLayout()
        form.addRow("Prenom", self.first_name)
        form.addRow("Nom", self.last_name)
        form.addRow("Email", self.email)
        form.addRow("Telephone", self.phone)
        form.addRow("Demarche", self.note)
        form_layout.addLayout(form)

        save_button = QPushButton("Ajouter le client")
        save_button.clicked.connect(self.create_client)
        form_layout.addWidget(save_button)
        form_layout.addStretch(1)
        right.addWidget(form_card)

        body.addLayout(right, 1)
        layout.addLayout(body)
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
        self.detail_name.setText(client.get("full_name", ""))
        self.detail_info.setText(
            f"Email: {client.get('email') or 'Non renseigne'}\n"
            f"Telephone: {client.get('phone') or 'Non renseigne'}\n"
            f"Pages utilisees aujourd'hui: {client.get('used_pages_today', 0)}\n"
            f"Quota restant: {client.get('remaining_pages', 0)}\n"
            f"Sessions actives: {client.get('active_session_count', 0)}\n"
            f"Demarche: {client.get('administrative_note') or 'Non renseignee'}"
        )
