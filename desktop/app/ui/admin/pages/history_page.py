from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.services.api_client import ApiClient
from app.services.dashboard_service import AdminDashboardService
from app.ui.shared.widgets import PageHeader, SearchField


class HistoryPage(QWidget):
    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.setObjectName("Page")
        self.service = AdminDashboardService(api_client)
        self.jobs: list[dict] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(PageHeader("Historique", "Suivi des demandes d'impression et filtrage rapide."))

        filter_row = QHBoxLayout()
        self.search = SearchField("Rechercher par client, poste, document ou contexte")
        self.search.textChanged.connect(self._render_table)
        filter_row.addWidget(self.search)
        layout.addLayout(filter_row)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Document", "Client", "Poste", "Pages", "Statut", "Contexte"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        self.jobs = self.service.get_print_jobs()
        self._render_table()

    def _render_table(self) -> None:
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
