from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from app.services.api_client import ApiClient
from app.ui.admin.pages.clients_page import ClientsPage
from app.ui.admin.pages.dashboard_page import DashboardPage
from app.ui.admin.pages.history_page import HistoryPage


class AdminMainWindow(QMainWindow):
    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.setWindowTitle("CESOC Print System - Admin")
        self.resize(1440, 920)
        logo_path = Path(__file__).resolve().parents[2] / "assets" / "cesoc-logo.svg"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        shell = QWidget()
        shell.setObjectName("AppShell")
        self.setCentralWidget(shell)

        layout = QHBoxLayout(shell)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        sidebar = self._build_sidebar()
        layout.addWidget(sidebar, 0)

        self.stack = QStackedWidget()
        self.pages = [
            DashboardPage(api_client),
            ClientsPage(api_client),
            HistoryPage(api_client),
        ]
        for page in self.pages:
            self.stack.addWidget(page)
        layout.addWidget(self.stack, 1)

        self.nav_buttons[0].setChecked(True)

    def _build_sidebar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Sidebar")
        frame.setFixedWidth(270)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 22, 20, 22)
        layout.setSpacing(10)

        logo_path = Path(__file__).resolve().parents[2] / "assets" / "cesoc-logo.svg"
        if logo_path.exists():
            logo = QLabel()
            logo.setObjectName("LogoMark")
            logo.setPixmap(QIcon(str(logo_path)).pixmap(96, 96))
            layout.addWidget(logo)

        brand = QLabel("CESOC")
        brand.setObjectName("SidebarTitle")
        subtitle = QLabel("Console d'administration")
        subtitle.setObjectName("SidebarSubtitle")
        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addSpacing(20)

        labels = ["Dashboard", "Utilisateurs", "Historique"]
        self.nav_buttons: list[QPushButton] = []
        for index, label in enumerate(labels):
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, idx=index: self._switch_page(idx))
            self.nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch(1)
        footer = QLabel("Pilotage local des impressions et des sessions usagers")
        footer.setWordWrap(True)
        footer.setObjectName("SidebarSubtitle")
        layout.addWidget(footer)
        return frame

    def _switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for idx, button in enumerate(self.nav_buttons):
            button.setChecked(idx == index)
        page = self.pages[index]
        if hasattr(page, "refresh"):
            page.refresh()
