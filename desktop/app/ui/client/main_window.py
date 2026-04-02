from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import QTimer

from app.services.api_client import ApiClient
from app.services.config_service import ClientStationConfig
from app.services.dashboard_service import AdminDashboardService
from app.services.station_service import ClientStationService
from app.ui.shared.widgets import HeroBanner, SectionCard


class ClientMainWindow(QMainWindow):
    def __init__(self, api_client: ApiClient, config: ClientStationConfig) -> None:
        super().__init__()
        self.service = ClientStationService(api_client, config)
        self.job_service = AdminDashboardService(api_client)
        self.config = config
        self.current_session: dict | None = None
        self.setWindowTitle(f"CESOC Poste Public - {config.station_code}")
        self.resize(980, 720)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        self.hero = HeroBanner(
            f"Poste {config.station_code}",
            "Accueil du poste public avec supervision du client actif et du quota restant.",
        )
        layout.addWidget(self.hero)

        self.station_card = SectionCard("Etat du poste")
        station_layout = QVBoxLayout(self.station_card.content)
        self.station_status = QLabel()
        self.station_status.setObjectName("MetricValue")
        self.client_name = QLabel()
        self.client_name.setObjectName("SectionTitle")
        self.remaining = QLabel()
        self.remaining.setObjectName("MutedText")
        self.network_hint = QLabel()
        self.network_hint.setObjectName("MutedText")
        station_layout.addWidget(self.station_status)
        station_layout.addWidget(self.client_name)
        station_layout.addWidget(self.remaining)
        station_layout.addWidget(self.network_hint)
        layout.addWidget(self.station_card)

        actions = SectionCard("Impression")
        actions_layout = QVBoxLayout(actions.content)
        form = QFormLayout()
        self.document_name = QLineEdit()
        self.document_name.setPlaceholderText("Exemple: formulaire_caf.pdf")
        self.page_count = QLineEdit()
        self.page_count.setPlaceholderText("Nombre de pages")
        self.document_context = QLineEdit()
        self.document_context.setPlaceholderText("Contexte administratif")
        form.addRow("Document", self.document_name)
        form.addRow("Pages", self.page_count)
        form.addRow("Demarche", self.document_context)
        actions_layout.addLayout(form)
        actions_row = QHBoxLayout()
        self.choose_button = QPushButton("Choisir un document")
        self.submit_button = QPushButton("Soumettre impression")
        self.submit_button.setObjectName("SecondaryButton")
        self.submit_button.clicked.connect(self.submit_print_job)
        actions_row.addWidget(self.choose_button)
        actions_row.addWidget(self.submit_button)
        actions_layout.addLayout(actions_row)
        layout.addWidget(actions)

        self.history_card = SectionCard("Historique local de session")
        history_layout = QVBoxLayout(self.history_card.content)
        self.history_label = QLabel("Aucune operation locale pour le moment.")
        self.history_label.setObjectName("MutedText")
        history_layout.addWidget(self.history_label)
        layout.addWidget(self.history_card)
        layout.addStretch(1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(7000)
        self.refresh()

    def refresh(self) -> None:
        station = self.service.get_station()
        session = self.service.get_active_session()
        self.current_session = session
        self.station_status.setText(f"Etat: {station.get('status', 'offline')}")
        self.network_hint.setText(f"API: {self.config.api_base_url} | Poste: {self.config.station_code}")
        if session:
            client_id = session["client_id"]
            remaining = self.service.get_remaining_pages(client_id)
            self.client_name.setText(f"Client actif: {session.get('client_name') or f'#{client_id}'}")
            self.remaining.setText(
                f"Quota restant: {remaining.get('remaining_pages', 0)} / {remaining.get('daily_quota', 10)} pages"
            )
            self.hero.set_metrics("Session en cours", station.get("name", station.get("code", "")))
            self.history_label.setText(f"Session #{session['id']} active pour: {session.get('purpose', 'Demarche')}")
            self.submit_button.setEnabled(True)
        else:
            self.client_name.setText("Aucun client assigne")
            self.remaining.setText("Le poste attend une affectation par le personnel.")
            self.hero.set_metrics("Disponible", station.get("name", station.get("code", "")))
            self.history_label.setText("Aucune session active detectee pour ce poste.")
            self.submit_button.setEnabled(False)

    def submit_print_job(self) -> None:
        if not self.current_session:
            QMessageBox.warning(self, "Session requise", "Aucune session active n'est disponible sur ce poste.")
            return
        try:
            page_count = int(self.page_count.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Le nombre de pages doit etre numerique.")
            return
        payload = {
            "client_id": self.current_session["client_id"],
            "station_code": self.config.station_code,
            "session_id": self.current_session["id"],
            "document_name": self.document_name.text().strip() or "document.pdf",
            "page_count": page_count,
            "administrative_context": self.document_context.text().strip() or self.current_session.get("purpose", "Demarche"),
        }
        result = self.job_service.create_print_job(payload)
        if not result:
            QMessageBox.warning(self, "Erreur", "Impossible de soumettre l'impression pour cette session.")
            return
        self.history_label.setText(
            f"Document {result.get('document_name')} enregistre pour {result.get('page_count')} pages."
        )
        self.document_name.clear()
        self.page_count.clear()
        self.document_context.clear()
        self.refresh()
