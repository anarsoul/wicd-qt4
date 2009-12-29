#!/usr/bin/env python

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys

# Import ui parts
from MainWindow import MainWindow

# Wicd specific imports
from wicd import wpath
from wicd import misc

misc.RenameProcess("wicd-client-qt4")

if __name__ == '__main__':
    wpath.chdir(__file__)
    
def main(argv):
    app = QApplication(sys.argv)

    # Constructing gui...
    mainWindow = MainWindow()
    mainWindow.show()

    # Start event processing...
    app.exec_()

if __name__ == '__main__':
    main(sys.argv)
