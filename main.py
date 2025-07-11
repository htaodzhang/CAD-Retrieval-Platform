import os
import sys
from gui_core import CADRetrievalApp
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = CADRetrievalApp()
    sys.exit(app.exec_())