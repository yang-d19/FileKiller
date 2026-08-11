"""Small presentation-only widgets used by the main window."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class BubbleWidget(QWidget):
    """Frameless speech bubble shown after the pointing animation."""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 15)
        self.lbl_text = QLabel(text)
        self.lbl_text.setStyleSheet(
            """
            QLabel {
                color: #1c1c1e;
                padding: 15px 30px;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                font-size: 20px;
                font-weight: 600;
            }
            """
        )
        self.lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_text)
        self.setLayout(layout)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 240))

        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(
            0,
            0,
            float(rect.width()),
            float(rect.height() - 15),
            20.0,
            20.0,
        )

        tail = QPainterPath()
        tail.moveTo(float(rect.width()) / 2 - 15, float(rect.height() - 15))
        tail.lineTo(float(rect.width()) / 2, float(rect.height()))
        tail.lineTo(float(rect.width()) / 2 + 15, float(rect.height() - 15))
        path.addPath(tail)
        painter.drawPath(path)


class ChoicesWidget(QWidget):
    """Confirmation choices displayed under the speech bubble."""

    choiceMade = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QHBoxLayout()
        layout.setSpacing(15)
        self.btn1 = QPushButton("是的 😡")
        self.btn2 = QPushButton("嘤嘤嘤就是这个 🥺")

        button_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 240);
                color: #1c1c1e;
                border: 1px solid #e5e5ea;
                border-radius: 18px;
                padding: 12px 25px;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #007aff;
                color: #ffffff;
                border: 1px solid #007aff;
            }
            QPushButton:pressed {
                background-color: #005bb5;
                color: #ffffff;
            }
        """
        for button in (self.btn1, self.btn2):
            button.setStyleSheet(button_style)
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15)
            shadow.setOffset(0, 5)
            shadow.setColor(QColor(0, 0, 0, 30))
            button.setGraphicsEffect(shadow)
            button.clicked.connect(self.on_click)
            layout.addWidget(button)

        self.setLayout(layout)

    def on_click(self):
        self.hide()
        self.choiceMade.emit()
