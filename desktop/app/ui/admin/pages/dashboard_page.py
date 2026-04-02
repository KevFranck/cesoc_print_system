from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.services.api_client import ApiClient
from app.services.dashboard_service import AdminDashboardService
from app.ui.shared.widgets import HeroBanner, MetricCard, PageHeader, SectionCard


class DashboardPage(QWidget):
    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.setObjectName("Page")
        self.service = AdminDashboardService(api_client)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(PageHeader("Dashboard", "Vue globale de l'activite du centre et des postes publics."))
        self.hero = HeroBanner("Pilotage des impressions", "Suivi des quotas, sessions et activite temps reel.")
        layout.addWidget(self.hero)

        grid = QGridLayout()
        grid.setSpacing(16)
        self.cards = {
            "free_stations": MetricCard("Postes libres", "Disponibilite immediate"),
            "active_sessions": MetricCard("Sessions actives", "Usagers actuellement installes"),
            "prints_today": MetricCard("Impressions du jour", "Demandes enregistrees aujourd'hui"),
            "offline_stations": MetricCard("Postes hors ligne", "Supervision materielle"),
            "occupied_stations": MetricCard("Postes occupes", "Postes actuellement utilises"),
            "quota_alert_clients": MetricCard("Alertes quota", "Clients proches de la limite journaliere"),
        }
        positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
        for card, pos in zip(self.cards.values(), positions, strict=False):
            grid.addWidget(card, *pos)
        layout.addLayout(grid)

        self.info_section = SectionCard("Lecture rapide")
        info_layout = QHBoxLayout(self.info_section.content)
        self.status_label = QLabel()
        self.status_label.setObjectName("MutedText")
        self.status_label.setWordWrap(True)
        info_layout.addWidget(self.status_label)
        layout.addWidget(self.info_section)

        self.sessions_section = SectionCard("Sessions actives")
        sessions_layout = QVBoxLayout(self.sessions_section.content)
        self.sessions_table = QTableWidget(0, 3)
        self.sessions_table.setHorizontalHeaderLabels(["Poste", "Client", "Demarche"])
        self.sessions_table.horizontalHeader().setStretchLastSection(True)
        sessions_layout.addWidget(self.sessions_table)
        layout.addWidget(self.sessions_section)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(12000)
        self.refresh()

    def refresh(self) -> None:
        summary = self.service.get_summary()
        self.cards["free_stations"].set_value(str(summary.get("free_stations", 0)))
        self.cards["active_sessions"].set_value(str(summary.get("active_sessions", 0)))
        self.cards["prints_today"].set_value(str(summary.get("prints_today", 0)))
        self.cards["offline_stations"].set_value(str(summary.get("offline_stations", 0)))
        self.cards["occupied_stations"].set_value(str(summary.get("occupied_stations", 0)))
        self.cards["quota_alert_clients"].set_value(str(summary.get("quota_alert_clients", 0)))
        self.hero.set_metrics(
            f"{summary.get('pages_today', 0)} pages",
            f"{summary.get('total_clients', 0)} clients suivis",
        )
        self.status_label.setText(
            "Le tableau de bord centralise les postes disponibles, les sessions en cours, les volumes du jour et les clients approchant leur quota."
        )
        sessions = self.service.get_active_sessions()
        self.sessions_table.setRowCount(len(sessions))
        for row, session in enumerate(sessions):
            self.sessions_table.setItem(row, 0, QTableWidgetItem(session.get("station_code") or ""))
            self.sessions_table.setItem(row, 1, QTableWidgetItem(session.get("client_name") or ""))
            self.sessions_table.setItem(row, 2, QTableWidgetItem(session.get("purpose") or ""))
