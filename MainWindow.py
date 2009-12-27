#!/usr/bin/env python

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_mainWindow import Ui_mainWindow

class MainWindow(QWidget, Ui_mainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.scanning = False
        self.refreshBut.connect(self.refreshBut, SIGNAL('clicked()'), self.scanClicked)

    def scanClicked(self):
        wireless.Scan(False)
        pass

    def scanStarted(self):
        pass
	
    def scanEnded(self):
        pass
