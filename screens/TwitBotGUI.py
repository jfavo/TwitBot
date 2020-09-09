from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow
import sys

from screens import WidgitManager

widgitManager = WidgitManager.WidgitManager()
botManager = None

class Window(QMainWindow):
    def __init__(self):
        super().__init__()

    def show_current_screen(self):
        widgitManager.show_intro()

def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show_current_screen()
    sys.exit(app.exec())
