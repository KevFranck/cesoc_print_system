from __future__ import annotations


def build_stylesheet() -> str:
    return """
    QWidget {
        background: #f4f7fb;
        color: #132238;
        font-family: 'Segoe UI';
        font-size: 14px;
    }
    QMainWindow, QFrame#AppShell, QWidget#Page {
        background: #f4f7fb;
    }
    QFrame#Sidebar {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #10233d, stop:1 #183c64);
        border-radius: 24px;
    }
    QLabel#SidebarTitle {
        color: #eef6ff;
        font-size: 22px;
        font-weight: 700;
    }
    QLabel#SidebarSubtitle {
        color: rgba(238, 246, 255, 0.72);
        font-size: 12px;
    }
    QPushButton#NavButton {
        background: transparent;
        color: #d8e7fb;
        border: none;
        text-align: left;
        padding: 12px 14px;
        border-radius: 14px;
        font-weight: 600;
    }
    QPushButton#NavButton:hover, QPushButton#NavButton:checked {
        background: rgba(131, 211, 255, 0.18);
        color: white;
    }
    QFrame#TopBar, QFrame#Card, QFrame#HeroCard, QFrame#SectionCard {
        background: #ffffff;
        border: 1px solid rgba(16, 35, 61, 0.08);
        border-radius: 20px;
    }
    QFrame#HeroCard {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #12355b, stop:1 #179ecb);
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
        color: rgba(255, 255, 255, 0.8);
    }
    QLabel#CardTitle, QLabel#SectionTitle {
        font-size: 18px;
        font-weight: 700;
        color: #11263f;
    }
    QLabel#MutedText {
        color: #61758d;
    }
    QLabel#MetricValue {
        font-size: 30px;
        font-weight: 700;
        color: #10233d;
    }
    QLabel#MetricLabel {
        color: #6a7f97;
        font-size: 13px;
    }
    QPushButton {
        background: #103456;
        color: white;
        border: none;
        border-radius: 12px;
        padding: 10px 14px;
        font-weight: 600;
    }
    QPushButton:hover {
        background: #164774;
    }
    QPushButton#SecondaryButton {
        background: #e9f6fb;
        color: #12496a;
    }
    QLineEdit, QTextEdit, QComboBox {
        background: white;
        border: 1px solid #d8e2ed;
        border-radius: 12px;
        padding: 10px 12px;
    }
    QTableWidget {
        background: white;
        border: 1px solid #dfe7f0;
        border-radius: 16px;
        gridline-color: #edf2f7;
        selection-background-color: #d6effd;
        selection-color: #10233d;
    }
    QHeaderView::section {
        background: #eef4f9;
        color: #445c75;
        padding: 10px;
        border: none;
        font-weight: 700;
    }
    """
