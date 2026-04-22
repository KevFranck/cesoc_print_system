from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
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
            "success_rate": MetricCard("Taux de reussite", "Part des impressions terminees"),
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
        self.period_table = QTableWidget(0, 8)
        self.period_table.setHorizontalHeaderLabels(
            ["Periode", "Jobs", "Pages", "Reussies", "Echecs", "Taux reussite", "Pages/job", "Usagers"]
        )
        self.period_table.horizontalHeader().setStretchLastSection(True)
        self.period_table.setAlternatingRowColors(True)
        self.period_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        period_layout.addWidget(self.period_table)
        layout.addWidget(period_section)

        users_section = SectionCard("Top utilisateurs")
        users_layout = QVBoxLayout(users_section.content)
        self.users_table = QTableWidget(0, 6)
        self.users_table.setHorizontalHeaderLabels(["Utilisateur", "Email", "Jobs", "Pages", "Echecs", "Taux echec"])
        self.users_table.horizontalHeader().setStretchLastSection(True)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
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
            self.cards["success_rate"].set_value(self._format_rate(report.get("success_count", 0), report.get("report_jobs_count", 0)))
            self.hero.set_metrics(
                f"{summary.get('pages_today', 0)} pages aujourd'hui",
                f"{summary.get('total_clients', 0)} utilisateurs suivis",
            )
            period_points = report.get("period_points", [])
            top_users = report.get("top_users", [])
            self.status_label.setText(self._build_reading_summary(report, period_points, top_users))

            period_points = report.get("period_points", [])
            self.period_table.setRowCount(len(period_points))
            for row, point in enumerate(period_points):
                self.period_table.setItem(row, 0, QTableWidgetItem(point.get("label", "")))
                self.period_table.setItem(row, 1, QTableWidgetItem(str(point.get("jobs_count", 0))))
                self.period_table.setItem(row, 2, QTableWidgetItem(str(point.get("pages_count", 0))))
                self.period_table.setItem(row, 3, QTableWidgetItem(str(point.get("success_count", 0))))
                self.period_table.setItem(row, 4, QTableWidgetItem(str(point.get("failed_count", 0))))
                self.period_table.setItem(row, 5, QTableWidgetItem(self._format_rate(point.get("success_count", 0), point.get("jobs_count", 0))))
                self.period_table.setItem(row, 6, QTableWidgetItem(self._format_average(point.get("pages_count", 0), point.get("jobs_count", 0))))
                self.period_table.setItem(row, 7, QTableWidgetItem(str(point.get("unique_users", 0))))
            self.period_table.resizeColumnsToContents()

            self.users_table.setRowCount(len(top_users))
            for row, user in enumerate(top_users):
                self.users_table.setItem(row, 0, QTableWidgetItem(user.get("client_name", "")))
                self.users_table.setItem(row, 1, QTableWidgetItem(user.get("email", "") or ""))
                self.users_table.setItem(row, 2, QTableWidgetItem(str(user.get("jobs_count", 0))))
                self.users_table.setItem(row, 3, QTableWidgetItem(str(user.get("pages_count", 0))))
                self.users_table.setItem(row, 4, QTableWidgetItem(str(user.get("failed_count", 0))))
                self.users_table.setItem(row, 5, QTableWidgetItem(self._format_rate(user.get("failed_count", 0), user.get("jobs_count", 0))))
            self.users_table.resizeColumnsToContents()
        finally:
            self._refresh_in_progress = False

    @guarded_ui_action
    def _change_period(self, period: str) -> None:
        self.current_period = period
        self.period_buttons[period].setChecked(True)
        self.refresh()

    @guarded_ui_action
    def _export_report(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        default_name = f"cesoc-report-{self.current_period}-{timestamp}.csv"
        target, _ = QFileDialog.getSaveFileName(self, "Exporter le rapport", default_name, "CSV (*.csv)")
        if not target:
            return
        self.service.export_report_csv(self.current_report, Path(target))

    def _build_reading_summary(self, report: dict, period_points: list[dict], top_users: list[dict]) -> str:
        total_jobs = int(report.get("report_jobs_count") or 0)
        total_pages = int(report.get("report_pages_count") or 0)
        failed_count = int(report.get("failed_count") or 0)
        average = self._format_average(total_pages, total_jobs)
        success_rate = self._format_rate(report.get("success_count", 0), total_jobs)
        busiest_period = max(period_points, key=lambda item: int(item.get("pages_count") or 0), default=None)
        top_user = max(top_users, key=lambda item: int(item.get("pages_count") or 0), default=None)

        if not total_jobs:
            return "Aucune impression n'est encore disponible pour ce rapport. Les tableaux se rempliront automatiquement apres les premiers jobs."

        parts = [
            f"{total_jobs} job(s), {total_pages} page(s), {average} page(s) par job en moyenne.",
            f"Taux de reussite: {success_rate}; echecs a surveiller: {failed_count}.",
        ]
        if busiest_period:
            parts.append(
                f"Periode la plus chargee: {busiest_period.get('label', '')} avec {busiest_period.get('pages_count', 0)} page(s)."
            )
        if top_user:
            parts.append(
                f"Utilisateur le plus actif: {top_user.get('client_name', 'Non renseigne')} avec {top_user.get('pages_count', 0)} page(s)."
            )
        return " ".join(parts)

    def _format_rate(self, numerator: object, denominator: object) -> str:
        denominator_int = int(denominator or 0)
        if denominator_int <= 0:
            return "0%"
        return f"{round((int(numerator or 0) / denominator_int) * 100, 1)}%"

    def _format_average(self, numerator: object, denominator: object) -> str:
        denominator_int = int(denominator or 0)
        if denominator_int <= 0:
            return "0"
        return str(round(int(numerator or 0) / denominator_int, 2))
