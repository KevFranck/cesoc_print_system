from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
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
from app.ui.shared.widgets import PageHeader


class SessionsPage(QWidget):
    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.setObjectName("Page")
        self.service = AdminDashboardService(api_client)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(PageHeader("Sessions", "Affectation des postes, suivi des usagers et cloture rapide."))

        body = QHBoxLayout()
        body.setSpacing(16)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Session", "Poste", "Client", "Demarche", "Debut"])
        self.table.horizontalHeader().setStretchLastSection(True)
        body.addWidget(self.table, 2)

        actions = QFrame()
        actions.setObjectName("SectionCard")
        actions_layout = QVBoxLayout(actions)

        start_title = QLabel("Demarrer une session")
        start_title.setObjectName("SectionTitle")
        actions_layout.addWidget(start_title)

        self.station_combo = QComboBox()
        self.client_combo = QComboBox()
        self.purpose = QLineEdit()
        self.notes = QLineEdit()
        form = QFormLayout()
        form.addRow("Poste", self.station_combo)
        form.addRow("Client", self.client_combo)
        form.addRow("Demarche", self.purpose)
        form.addRow("Notes", self.notes)
        actions_layout.addLayout(form)

        start_btn = QPushButton("Demarrer")
        start_btn.clicked.connect(self.start_session)
        actions_layout.addWidget(start_btn)

        actions_layout.addSpacing(10)
        end_title = QLabel("Terminer une session")
        end_title.setObjectName("SectionTitle")
        actions_layout.addWidget(end_title)
        self.end_session_combo = QComboBox()
        self.end_notes = QLineEdit()
        end_form = QFormLayout()
        end_form.addRow("Session active", self.end_session_combo)
        end_form.addRow("Notes", self.end_notes)
        actions_layout.addLayout(end_form)
        end_btn = QPushButton("Cloturer")
        end_btn.setObjectName("SecondaryButton")
        end_btn.clicked.connect(self.end_session)
        actions_layout.addWidget(end_btn)
        actions_layout.addStretch(1)

        body.addWidget(actions, 1)
        layout.addLayout(body)
        self.refresh()

    def refresh(self) -> None:
        stations = self.service.get_stations()
        clients = self.service.get_clients()
        active_sessions = self.service.get_active_sessions()

        self.station_combo.clear()
        for station in stations:
            if station.get("status") != "occupied":
                self.station_combo.addItem(f"{station['code']} - {station['name']}", station["code"])

        self.client_combo.clear()
        for client in clients:
            self.client_combo.addItem(
                f"{client['full_name']} - {client.get('remaining_pages', 0)} pages restantes",
                client["id"],
            )

        self.end_session_combo.clear()
        for session in active_sessions:
            self.end_session_combo.addItem(
                f"#{session['id']} - {session.get('station_code', '')} - {session.get('client_name', '')}",
                session["id"],
            )

        self.table.setRowCount(len(active_sessions))
        for row, session in enumerate(active_sessions):
            self.table.setItem(row, 0, QTableWidgetItem(str(session.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(session.get("station_code") or ""))
            self.table.setItem(row, 2, QTableWidgetItem(session.get("client_name") or ""))
            self.table.setItem(row, 3, QTableWidgetItem(session.get("purpose") or ""))
            self.table.setItem(row, 4, QTableWidgetItem(str(session.get("started_at", ""))))

    def start_session(self) -> None:
        station_code = self.station_combo.currentData()
        client_id = self.client_combo.currentData()
        if not station_code or client_id is None:
            QMessageBox.warning(self, "Erreur", "Selectionne un poste disponible et un client.")
            return
        payload = {
            "station_code": station_code,
            "client_id": int(client_id),
            "purpose": self.purpose.text().strip() or "Demarche administrative",
            "notes": self.notes.text().strip() or None,
        }
        result = self.service.start_session(payload)
        if not result:
            QMessageBox.warning(self, "Erreur", "Impossible de demarrer la session.")
            return
        self.purpose.clear()
        self.notes.clear()
        self.refresh()

    def end_session(self) -> None:
        session_id = self.end_session_combo.currentData()
        if session_id is None:
            QMessageBox.warning(self, "Erreur", "Aucune session active selectionnee.")
            return
        result = self.service.api_client.safe_post(
            "/sessions/end",
            {"session_id": int(session_id), "notes": self.end_notes.text().strip() or None},
        )
        if not result:
            QMessageBox.warning(self, "Erreur", "Impossible de terminer la session.")
            return
        self.end_notes.clear()
        self.refresh()
