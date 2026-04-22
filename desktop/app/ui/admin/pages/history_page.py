from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.core.runtime import guarded_ui_action
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.services.api_client import ApiClient
from app.services.dashboard_service import AdminDashboardService
from app.ui.shared.widgets import PageHeader, ScrollSection, SearchField


class HistoryPage(QWidget):
    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.setObjectName("Page")
        self.service = AdminDashboardService(api_client)
        self.jobs: list[dict] = []
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(16)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(PageHeader("Historique", "Suivi des demandes d'impression et filtrage rapide."))

        filter_row = QHBoxLayout()
        self.search = SearchField("Rechercher par client, poste, document ou contexte")
        self.search.textChanged.connect(self._render_table)
        filter_row.addWidget(self.search)
        export_button = QPushButton("Exporter l'historique CSV")
        export_button.clicked.connect(self._export_history)
        filter_row.addWidget(export_button)
        layout.addLayout(filter_row)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Document", "Client", "Poste", "Pages", "Statut", "Contexte"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumHeight(460)
        layout.addWidget(self.table)
        root_layout.addWidget(ScrollSection(content))
        self.refresh()

    @guarded_ui_action
    def refresh(self) -> None:
        self.jobs = self.service.get_print_jobs()
        self._render_table()

    @guarded_ui_action
    def _render_table(self, *_args: object) -> None:
        query = self.search.text().strip().lower()
        filtered = [
            job
            for job in self.jobs
            if not query
            or query in job.get("document_name", "").lower()
            or query in (job.get("client_name") or "").lower()
            or query in (job.get("station_code") or "").lower()
            or query in (job.get("administrative_context") or "").lower()
        ]
        self.table.setRowCount(len(filtered))
        for row, job in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(job.get("document_name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(job.get("client_name") or ""))
            self.table.setItem(row, 2, QTableWidgetItem(job.get("station_code") or ""))
            self.table.setItem(row, 3, QTableWidgetItem(str(job.get("page_count", 0))))
            self.table.setItem(row, 4, QTableWidgetItem(job.get("status", "")))
            self.table.setItem(row, 5, QTableWidgetItem(job.get("administrative_context", "")))

    @guarded_ui_action
    def _export_history(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        default_name = f"cesoc-history-{timestamp}.csv"
        target, _ = QFileDialog.getSaveFileName(self, "Exporter l'historique", default_name, "CSV (*.csv)")
        if not target:
            return
        self.service.export_jobs_csv(self.jobs, Path(target))
