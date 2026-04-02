from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


class PageHeader(QFrame):
    def __init__(self, title: str, subtitle: str) -> None:
        super().__init__()
        self.setObjectName("TopBar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("MutedText")
        subtitle_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)


class MetricCard(QFrame):
    def __init__(self, title: str, subtitle: str) -> None:
        super().__init__()
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        self.value_label = QLabel("0")
        self.value_label.setObjectName("MetricValue")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("MetricLabel")
        subtitle_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(subtitle_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class HeroBanner(QFrame):
    def __init__(self, title: str, text: str) -> None:
        super().__init__()
        self.setObjectName("HeroCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        left = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("HeroTitle")
        text_label = QLabel(text)
        text_label.setObjectName("HeroText")
        text_label.setWordWrap(True)
        left.addWidget(title_label)
        left.addWidget(text_label)
        left.addStretch(1)

        right = QVBoxLayout()
        self.metric_value = QLabel("0")
        self.metric_value.setObjectName("HeroMetricValue")
        self.metric_label = QLabel("")
        self.metric_label.setObjectName("HeroMetricLabel")
        self.metric_label.setWordWrap(True)
        right.addWidget(self.metric_value)
        right.addWidget(self.metric_label)
        right.addStretch(1)
        layout.addLayout(left, 2)
        layout.addLayout(right, 1)

    def set_metrics(self, value: str, label: str) -> None:
        self.metric_value.setText(value)
        self.metric_label.setText(label)


class SectionCard(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("SectionCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")
        self.content = QWidget()
        layout.addWidget(title_label)
        layout.addWidget(self.content)


class ToolbarCard(QFrame):
    def __init__(self, title: str, subtitle: str, button_text: str | None = None) -> None:
        super().__init__()
        self.setObjectName("TopBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)

        text_block = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("MutedText")
        subtitle_label.setWordWrap(True)
        text_block.addWidget(title_label)
        text_block.addWidget(subtitle_label)
        layout.addLayout(text_block, 1)

        self.action_button = None
        if button_text:
            self.action_button = QPushButton(button_text)
            layout.addWidget(self.action_button)


class SearchField(QLineEdit):
    def __init__(self, placeholder: str) -> None:
        super().__init__()
        self.setPlaceholderText(placeholder)
