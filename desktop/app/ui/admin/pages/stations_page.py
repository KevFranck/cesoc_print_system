from __future__ import annotations

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
from app.ui.shared.widgets import PageHeader, SearchField


class StationsPage(QWidget):
    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.setObjectName("Page")
        self.service = AdminDashboardService(api_client)
        self.stations: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(PageHeader("Postes", "Disponibilite des stations publiques et creation rapide des postes."))

        body = QHBoxLayout()
        body.setSpacing(16)

        left = QVBoxLayout()
        self.search = SearchField("Filtrer par code, nom, emplacement ou etat")
        self.search.textChanged.connect(self._render_table)
        left.addWidget(self.search)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Code", "Nom", "Emplacement", "Etat", "Client actif"])
        self.table.horizontalHeader().setStretchLastSection(True)
        left.addWidget(self.table)
        body.addLayout(left, 2)

        form_card = QFrame()
        form_card.setObjectName("SectionCard")
        form_layout = QVBoxLayout(form_card)
        title = QLabel("Enregistrer un poste")
        title.setObjectName("SectionTitle")
        form_layout.addWidget(title)

        self.code = QLineEdit()
        self.name = QLineEdit()
        self.location = QLineEdit()
        self.status = QLineEdit("available")
        config_form = QFormLayout()
        config_form.addRow("Code", self.code)
        config_form.addRow("Nom", self.name)
        config_form.addRow("Emplacement", self.location)
        config_form.addRow("Etat", self.status)
        form_layout.addLayout(config_form)

        save_button = QPushButton("Ajouter le poste")
        save_button.clicked.connect(self.create_station)
        form_layout.addWidget(save_button)
        form_layout.addStretch(1)
        body.addWidget(form_card, 1)

        layout.addLayout(body)
        self.refresh()

    def refresh(self) -> None:
        self.stations = self.service.get_stations()
        self._render_table()

    def create_station(self) -> None:
        payload = {
            "code": self.code.text().strip(),
            "name": self.name.text().strip(),
            "location": self.location.text().strip() or None,
            "status": self.status.text().strip() or "available",
        }
        if not payload["code"] or not payload["name"]:
            QMessageBox.warning(self, "Erreur", "Le code et le nom du poste sont obligatoires.")
            return
        result = self.service.create_station(payload)
        if not result:
            QMessageBox.warning(self, "Erreur", "Impossible de creer le poste.")
            return
        for widget in [self.code, self.name, self.location]:
            widget.clear()
        self.status.setText("available")
        self.refresh()

    def _render_table(self) -> None:
        query = self.search.text().strip().lower()
        filtered = [
            station
            for station in self.stations
            if not query
            or query in station.get("code", "").lower()
            or query in station.get("name", "").lower()
            or query in (station.get("location") or "").lower()
            or query in station.get("status", "").lower()
        ]
        self.table.setRowCount(len(filtered))
        for row, station in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(station.get("code", "")))
            self.table.setItem(row, 1, QTableWidgetItem(station.get("name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(station.get("location") or ""))
            self.table.setItem(row, 3, QTableWidgetItem(station.get("status", "")))
            self.table.setItem(row, 4, QTableWidgetItem(station.get("active_client_name") or "Aucun"))
