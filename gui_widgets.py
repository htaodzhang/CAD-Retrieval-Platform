from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFontMetrics, QFont


class CustomLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #e9f7ef;
                border: 1px solid #a0d9b4;
                border-radius: 4px;
                padding: 2px;
                font-size: 11pt;
                font-family: 'Arial';
                color: #2e7d32;
                font-weight: bold;
            }
        """)
        self.setFixedHeight(28)
        self.setMinimumWidth(100)

    def sizeHint(self):
        metrics = QFontMetrics(self.font())
        text_size = metrics.size(Qt.TextSingleLine, self.text())
        return QSize(text_size.width() + 20, text_size.height() + 10)


class ClassLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 4px;
                padding: 2px;
                font-size: 10pt;
                font-family: 'Arial';
                color: #0d47a1;
            }
        """)
        self.setFixedHeight(24)
        self.setMinimumWidth(100)
        self.setWordWrap(True)
        font = QFont()
        font.setPointSize(9)
        self.setFont(font)

    def sizeHint(self):
        metrics = QFontMetrics(self.font())
        text_size = metrics.size(Qt.TextSingleLine, self.text())
        return QSize(text_size.width() + 20, text_size.height() + 10)