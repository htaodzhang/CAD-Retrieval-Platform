from PyQt5.QtWidgets import QPushButton, QMessageBox
from PyQt5.QtGui import QColor


class ButtonStyles:
    @staticmethod
    def setDefaultStyle(button):
        button.setStyleSheet("""
            QPushButton {
                font-size: 12pt;
                padding: 5px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

    @staticmethod
    def setExecuteStyle(button):
        button.setStyleSheet("""
            QPushButton {
                font-size: 13pt;
                padding: 8px;
                background-color: #4CAF50;
                color: white;
                border: 1px solid #388E3C;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)

    @staticmethod
    def setUtilityStyle(button):
        button.setStyleSheet("""
            QPushButton {
                font-size: 11pt;
                padding: 5px;
                background-color: #e3f2fd;
                border: 1px solid #bbdefb;
                border-radius: 4px;
                color: #0d47a1;
            }
            QPushButton:hover {
                background-color: #bbdefb;
            }
        """)

    @staticmethod
    def setHelpStyle(button):
        button.setStyleSheet("""
            QPushButton {
                font-size: 11pt;
                padding: 5px;
                background-color: #fff3e0;
                border: 1px solid #ffe0b2;
                border-radius: 4px;
                color: #e65100;
            }
            QPushButton:hover {
                background-color: #ffe0b2;
            }
        """)

    @staticmethod
    def setUploadedStyle(button):
        button.setStyleSheet("""
            QPushButton {
                font-size: 12pt;
                padding: 5px;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 5px;
                color: #155724;
            }
            QPushButton:hover {
                background-color: #c3e6cb;
            }
        """)


class MessageUtils:
    @staticmethod
    def showErrorMessage(parent, message):
        QMessageBox.critical(parent, "错误", message)

    @staticmethod
    def showInfoMessage(parent, message):
        QMessageBox.information(parent, "信息", message)