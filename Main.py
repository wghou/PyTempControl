import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from WindowApp.MainForm import MainForm




if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainForm()
    w.show()
    sys.exit(app.exec_())