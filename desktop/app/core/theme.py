from __future__ import annotations


def build_stylesheet() -> str:
    return """
    QWidget {
        background: #101826;
        color: #e9eef5;
        font-family: 'Segoe UI';
        font-size: 14px;
    }
    QLabel {
        background: transparent;
    }
    QMainWindow, QFrame#AppShell, QWidget#Page {
        background: #101826;
    }
    QFrame#Sidebar {
        background: #16212f;
        border-radius: 24px;
    }
    QLabel#SidebarTitle {
        color: #ffffff;
        font-size: 22px;
        font-weight: 700;
    }
    QLabel#SidebarSubtitle {
        color: rgba(255, 255, 255, 0.78);
        font-size: 12px;
    }
    QLabel#LogoMark {
        background: transparent;
        min-height: 72px;
    }
    QPushButton#NavButton {
        background: transparent;
        color: #f4fffb;
        border: none;
        text-align: left;
        padding: 12px 14px;
        border-radius: 14px;
        font-weight: 600;
    }
    QPushButton#NavButton:hover, QPushButton#NavButton:checked {
        background: #243447;
        color: white;
    }
    QFrame#TopBar, QFrame#Card, QFrame#HeroCard, QFrame#SectionCard {
        background: #172231;
        border: 1px solid #253446;
        border-radius: 20px;
    }
    QFrame#HeroCard {
        background: #1a2738;
        border: 1px solid #31445c;
    }
    QLabel#HeroTitle, QLabel#HeroText, QLabel#HeroMetricValue, QLabel#HeroMetricLabel {
        background: transparent;
        color: white;
    }
    QLabel#HeroTitle {
        font-size: 28px;
        font-weight: 700;
    }
    QLabel#HeroText {
        color: #c9d5e3;
    }
    QLabel#CardTitle, QLabel#SectionTitle {
        font-size: 18px;
        font-weight: 700;
        color: #f5f7fb;
    }
    QLabel#MutedText {
        color: #9cabc0;
    }
    QLabel#MetricValue {
        font-size: 30px;
        font-weight: 700;
        color: #8dc7f2;
    }
    QLabel#MetricLabel {
        color: #9aa9bc;
        font-size: 13px;
    }
    QLabel#FormLabel {
        color: #c0cfdd;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding-left: 2px;
    }
    QPushButton {
        background: #3d6f9b;
        color: white;
        border: none;
        border-radius: 14px;
        padding: 12px 16px;
        font-weight: 600;
    }
    QPushButton:hover {
        background: #4a83b5;
    }
    QPushButton:disabled {
        background: #2a3543;
        color: #8fa0b5;
    }
    QPushButton#SecondaryButton {
        background: #1d2a3b;
        color: #dce5f0;
        border: 1px solid #314255;
    }
    QPushButton#SecondaryButton:hover {
        background: #243447;
    }
    QPushButton#FilterChip {
        background: #1b2838;
        color: #bfd0e1;
        border: 1px solid #314255;
        border-radius: 16px;
        padding: 10px 18px;
        min-width: 120px;
    }
    QPushButton#FilterChip:hover {
        background: #233447;
        color: #eff5fb;
    }
    QPushButton#FilterChip:checked {
        background: #4a83b5;
        color: #ffffff;
        border: 1px solid #69a2d6;
    }
    QPushButton#KioskPrimaryButton, QPushButton#KioskChoiceButton {
        min-height: 64px;
        font-size: 18px;
        border-radius: 18px;
    }
    QPushButton#KioskGhostButton {
        background: transparent;
        color: #d3e1ef;
        border: 1px solid #3a4e66;
        border-radius: 16px;
        padding: 10px 18px;
        font-weight: 600;
    }
    QPushButton#KioskGhostButton:hover {
        background: #1c2b3b;
        border: 1px solid #5f7f9f;
    }
    QPushButton#KioskChoiceButton {
        background: #1a2738;
        color: #edf5ff;
        border: 1px solid #2f4257;
        text-align: left;
        padding: 16px 18px;
    }
    QPushButton#KioskChoiceButton:hover {
        background: #223349;
        border: 1px solid #4a698a;
    }
    QLabel#KioskTitle {
        font-size: 30px;
        font-weight: 700;
        color: #f3f7fc;
    }
    QLabel#KioskText {
        font-size: 16px;
        color: #afbccd;
    }
    QLabel#ResultBadgeNeutral, QLabel#ResultBadgeSuccess, QLabel#ResultBadgeError {
        border-radius: 16px;
        padding: 8px 18px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.08em;
        min-width: 132px;
    }
    QLabel#ResultBadgeNeutral {
        background: #213346;
        color: #dbe7f4;
        border: 1px solid #39526b;
    }
    QLabel#ResultBadgeSuccess {
        background: #1f4b43;
        color: #e9fff8;
        border: 1px solid #3b7a6d;
    }
    QLabel#ResultBadgeError {
        background: #4a2530;
        color: #ffe9ef;
        border: 1px solid #7a4150;
    }
    QLineEdit, QTextEdit, QComboBox {
        background: #141f2d;
        border: 1px solid #34465a;
        border-radius: 14px;
        padding: 12px 14px;
        color: #eef4fb;
    }
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
        border: 1px solid #5e86af;
    }
    QTableWidget {
        background: #141f2d;
        border: 1px solid #253446;
        border-radius: 16px;
        gridline-color: #213143;
        selection-background-color: #30506d;
        selection-color: #f6fbff;
        alternate-background-color: #172231;
    }
    QListWidget {
        background: #141f2d;
        border: 1px solid #253446;
        border-radius: 16px;
        color: #f1f6fd;
        padding: 8px;
    }
    QListWidget::item {
        padding: 10px;
        border-radius: 12px;
    }
    QListWidget::item:selected {
        background: #30506d;
        color: #ffffff;
    }
    QListWidget::item:hover {
        background: #233447;
    }
    QScrollArea {
        border: none;
        background: transparent;
    }
    QSplitter::handle {
        background: transparent;
        width: 10px;
        height: 10px;
    }
    QHeaderView::section {
        background: #1a2738;
        color: #dce5f0;
        padding: 10px;
        border: none;
        font-weight: 700;
    }
    """
