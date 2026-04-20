from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.runtime import guarded_ui_action
from app.services.api_client import ApiClient
from app.services.dashboard_service import AdminDashboardService
from app.ui.shared.widgets import HeroBanner, MetricCard, PageHeader, ScrollSection, SectionCard


class DashboardPage(QWidget):
    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.setObjectName("Page")
        self.service = AdminDashboardService(api_client)
        self._refresh_in_progress = False

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(16)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(PageHeader("Dashboard", "Pilotage des impressions avec vues journalieres, mensuelles et annuelles."))
        self.hero = HeroBanner("Rapports d'impression", "Suivi des volumes, des echecs, des usagers actifs et exports CSV.")
        layout.addWidget(self.hero)

        controls_card = SectionCard("Analyse")
        controls_layout = QHBoxLayout(controls_card.content)
        self.period_buttons: dict[str, QPushButton] = {}
        for label, period in [("Journalier", "daily"), ("Mensuel", "monthly"), ("Annuel", "yearly")]:
            button = QPushButton(label)
            button.setObjectName("FilterChip")
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.clicked.connect(lambda checked=False, p=period: self._change_period(p))
            controls_layout.addWidget(button)
            self.period_buttons[period] = button
        controls_layout.addStretch(1)
        export_button = QPushButton("Exporter le rapport CSV")
        export_button.clicked.connect(self._export_report)
        controls_layout.addWidget(export_button)
        layout.addWidget(controls_card)

        grid = QGridLayout()
        grid.setSpacing(16)
        self.cards = {
            "report_jobs_count": MetricCard("Jobs sur la periode", "Volume total observe"),
            "report_pages_count": MetricCard("Pages sur la periode", "Pages demandees ou imprimees"),
            "success_count": MetricCard("Impressions reussies", "Jobs termines avec succes"),
            "failed_count": MetricCard("Impressions en echec", "Demandes a analyser ou relancer"),
            "unique_users": MetricCard("Usagers actifs", "Utilisateurs differents sur la periode"),
            "average_pages_per_job": MetricCard("Moyenne pages / job", "Charge moyenne par impression"),
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

        period_section = SectionCard("Evolution de la periode")
        period_layout = QVBoxLayout(period_section.content)
        self.period_table = QTableWidget(0, 6)
        self.period_table.setHorizontalHeaderLabels(
            ["Periode", "Jobs", "Pages", "Reussies", "Echecs", "Usagers"]
        )
        self.period_table.horizontalHeader().setStretchLastSection(True)
        period_layout.addWidget(self.period_table)
        layout.addWidget(period_section)

        users_section = SectionCard("Top utilisateurs")
        users_layout = QVBoxLayout(users_section.content)
        self.users_table = QTableWidget(0, 5)
        self.users_table.setHorizontalHeaderLabels(["Utilisateur", "Email", "Jobs", "Pages", "Echecs"])
        self.users_table.horizontalHeader().setStretchLastSection(True)
        users_layout.addWidget(self.users_table)
        layout.addWidget(users_section)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.current_period = "daily"
        self.current_report: dict = {}
        self.period_buttons["daily"].setChecked(True)
        root_layout.addWidget(ScrollSection(content))
        self.refresh()

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        if not self.timer.isActive():
            self.timer.start(15000)

    def hideEvent(self, event) -> None:  # type: ignore[override]
        self.timer.stop()
        super().hideEvent(event)

    @guarded_ui_action
    def refresh(self) -> None:
        if self._refresh_in_progress:
            return
        self._refresh_in_progress = True
        try:
            report = self.service.get_report(self.current_period)
            self.current_report = report
            summary = report.get("totals", {})
            self.cards["report_jobs_count"].set_value(str(report.get("report_jobs_count", 0)))
            self.cards["report_pages_count"].set_value(str(report.get("report_pages_count", 0)))
            self.cards["success_count"].set_value(str(report.get("success_count", 0)))
            self.cards["failed_count"].set_value(str(report.get("failed_count", 0)))
            self.cards["unique_users"].set_value(str(report.get("unique_users", 0)))
            self.cards["average_pages_per_job"].set_value(str(report.get("average_pages_per_job", 0.0)))
            self.hero.set_metrics(
                f"{summary.get('pages_today', 0)} pages aujourd'hui",
                f"{summary.get('total_clients', 0)} utilisateurs suivis",
            )
            self.status_label.setText(
                "Le dashboard relie les volumes par periode, le taux d'echec, les usagers actifs et les alertes quota pour preparer les rapports d'activite."
            )
            period_points = report.get("period_points", [])
            self.period_table.setRowCount(len(period_points))
            for row, point in enumerate(period_points):
                self.period_table.setItem(row, 0, QTableWidgetItem(point.get("label", "")))
                self.period_table.setItem(row, 1, QTableWidgetItem(str(point.get("jobs_count", 0))))
                self.period_table.setItem(row, 2, QTableWidgetItem(str(point.get("pages_count", 0))))
                self.period_table.setItem(row, 3, QTableWidgetItem(str(point.get("success_count", 0))))
                self.period_table.setItem(row, 4, QTableWidgetItem(str(point.get("failed_count", 0))))
                self.period_table.setItem(row, 5, QTableWidgetItem(str(point.get("unique_users", 0))))

            top_users = report.get("top_users", [])
            self.users_table.setRowCount(len(top_users))
            for row, user in enumerate(top_users):
                self.users_table.setItem(row, 0, QTableWidgetItem(user.get("client_name", "")))
                self.users_table.setItem(row, 1, QTableWidgetItem(user.get("email", "") or ""))
                self.users_table.setItem(row, 2, QTableWidgetItem(str(user.get("jobs_count", 0))))
                self.users_table.setItem(row, 3, QTableWidgetItem(str(user.get("pages_count", 0))))
                self.users_table.setItem(row, 4, QTableWidgetItem(str(user.get("failed_count", 0))))
        finally:
            self._refresh_in_progress = False

    @guarded_ui_action
    def _change_period(self, period: str) -> None:
        self.current_period = period
        self.period_buttons[period].setChecked(True)
        self.refresh()

    @guarded_ui_action
    def _export_report(self) -> None:
        default_name = f"cesoc-report-{self.current_period}.csv"
        target, _ = QFileDialog.getSaveFileName(self, "Exporter le rapport", default_name, "CSV (*.csv)")
        if not target:
            return
        self.service.export_report_csv(self.current_report, Path(target))
