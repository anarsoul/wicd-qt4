#!/usr/bin/env python
# -* coding: utf-8 -*-
#
#   Copyright (C) 2009 - 2010 Vasily Khoruzhick
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License Version 2 as
#   published by the Free Software Foundation.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

# GUI
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_mainWindow import Ui_mainWindow
from NetworkProps import NetworkProps

# DBus
from dbus import DBusException

# Wicd
from wicd import dbusmanager
from wicd import misc
from wicd import wpath
from wicd.translations import language

from WicdQt4Utils import qstr, qlanguage, catchdbus

class MainWindow(QWidget, Ui_mainWindow):
    """ Main window class """
    def __init__(self, parent = None):
    """ Constructor """
        super(MainWindow, self).__init__(parent)
        # Setting up GUI, and connecting signals
        self.setupUi(self)
        self.scanning = False
        self.connecting = False
        self.connectProgress.setVisible(False)
        self.cancelBut.setVisible(False)
        self.cancelBut.connect(self.cancelBut, SIGNAL('clicked()'), self.cancelClicked)
        self.refreshBut.connect(self.refreshBut, SIGNAL('clicked()'), self.scanClicked)
        self.aboutBut.connect(self.aboutBut, SIGNAL('clicked()'), self.aboutClicked)
        self.disconnectAllBut.connect(self.disconnectAllBut, SIGNAL('clicked()'), self.cancelClicked)
        self.preferencesBut.connect(self.preferencesBut, SIGNAL('clicked()'), self.notImplemented)
        self.quitBut.connect(self.quitBut, SIGNAL('clicked()'), lambda: QApplication.instance().quit())
        self.networkBut.connect(self.networkBut, SIGNAL('clicked()'), self.notImplemented)

        QApplication.instance().connect(QApplication.instance(), SIGNAL('aboutToQuit()'), self.onExit)

        # Settings up dbus-related things
        self.curState = None
        self.daemon = self.wireless = self.wired = None
        self.setupDBus()

        bus = dbusmanager.get_bus()
        #bus.add_signal_receiver(tray_icon.icon_info.wired_profile_chooser,
        #                        'LaunchChooser', 'org.wicd.daemon')
        bus.add_signal_receiver(self.updateStatus,
                                'StatusChanged', 'org.wicd.daemon')
        bus.add_signal_receiver(self.scanEnded, 'SendEndScanSignal',
                                'org.wicd.daemon.wireless')
        bus.add_signal_receiver(self.scanStarted,
                                'SendStartScanSignal', 'org.wicd.daemon.wireless')
        bus.add_signal_receiver(self.handleNoDBus,
                                "DaemonClosing", 'org.wicd.daemon')
        bus.add_signal_receiver(lambda: self.setupDBus(force=False), "DaemonStarting",
                                "org.wicd.daemon")
        self.updateStatus()
        QTimer.singleShot(1000, lambda: self.updateStatus(True))

    def notImplemented(self):
    """ Throws 'not implemented' message box """
        QMessageBox.information(self, 'Not Implemented!', 'Sorry, but this functions is not implemented yet!')

    def aboutClicked(self):
    """ About button click handler, opens about dialog """
        QMessageBox.information(self, 'About', 'wicd-qt4 development version')

    def scanClicked(self):
    """ Scan button click handler, initiates scan process """
        self.wireless.Scan(False)

    def scanStarted(self):
    """ scanStarted signal handler, adjustes GUI to display that scan is in progress """
        label = QLabel(qlanguage('scanning_stand_by'))
        label.setAlignment(Qt.AlignCenter)
        label.setEnabled(False)
        self.scrollArea.setWidget(label)
        label.show()
        pass
    
    def scanEnded(self):
    """ scanEnded signal handler, adjestes GUI to display scan results """
        self.updateNetworkList()
        self.updateStatus()

    def onExit(self):
    """ onExit handler, shutdown dbus-related things """
        if self.DBUS_AVAIL:
            try:
                self.daemon.SetGUIOpen(False)
            except DBusException:
                pass

    @catchdbus
    def cancelClicked(self):
    """ Cancel button click handler, cancels scan process """
        self.cancelBut.setEnabled(False)
        self.daemon.CancelConnect()
        self.daemon.SetForcedDisconnect(True)

    @catchdbus
    def updateNetworkList(self):
    """ Updates network list """
        # Add wired list
        wiredList = self.wired.GetWiredProfileList()

        # Add wireless list
        numberOfNetworks = self.wireless.GetNumberOfNetworks()
        if numberOfNetworks > 0:
            widget = QWidget()
            vbox = QVBoxLayout()
            for network_id in range(0, numberOfNetworks):
                is_active = self.wireless.GetCurrentNetworkID(self.wireless.GetIwconfig()) == network_id
                vbox.addWidget(self.getWirelessNetWidget(network_id, is_active))
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
                vbox.addWidget(line)
            vbox.addItem(QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))
            vbox.setSpacing(0)
            widget.setLayout(vbox)
            self.scrollArea.setWidget(widget)
        else:
            label = QLabel(qlanguage('no_wireless_networks_found'))
            label.setAlignment(Qt.AlignCenter)
            label.setEnabled(False)
            self.scrollArea.setWidget(label)
            label.show()

    @catchdbus
    def getWirelessSignal(self, id):
    """ Returns signal level of wireless network with given id """
        if self.daemon.GetSignalDisplayType() == 1:
            return self.wireless.GetWirelessProperty(id, 'strength')
        else:
            return self.wireless.GetWirelessProperty(id, 'quality')

    def getWirelessNetWidget(self, id, is_active):
    """ Creates widget that describes wireless network with given id. Set is_active
        to True if PC is connected to wireless network with given id."""
        # outer widget
        widget = QWidget()
        hbox = QHBoxLayout()
        hbox.addWidget(self.getSignalImage(self.getWirelessSignal(id)))

        # right part of wireless network
        widgetRightPart = QWidget()
        vbox = QVBoxLayout()

        # hbox with wireless network properties
        widgetNetProps = QWidget()
        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel('<b>' + self.getWirelessNetStr(id) + '</b>'))
        hbox2.addWidget(QLabel(self.daemon.FormatSignalForPrinting(str(self.getWirelessSignal(id)))))
        if self.wireless.GetWirelessProperty(id, 'encryption'):
            hbox2.addWidget(QLabel(self.wireless.GetWirelessProperty(id, 'encryption_method')))
        else:
            hbox2.addWidget(QLabel('Unsecured'))
        hbox2.addWidget(QLabel('Channel ' + str(self.wireless.GetWirelessProperty(id, 'channel'))))
        hbox2.setSpacing(10)
        widgetNetProps.setLayout(hbox2)
        vbox.addWidget(widgetNetProps)

        # autoconnect check box
        checkBox = QCheckBox('Automatically connect to this network')
        if self.wireless.GetWirelessProperty(id, 'automatic'):
            checkBox.setChecked(True)
        checkBox.connect(checkBox, SIGNAL('stateChanged(int)'), lambda state: self.updateAutoconnect(id, state == Qt.Checked))
        vbox.addWidget(checkBox)
        
        # hbox with buttons
        widgetButtons = QWidget()
        hbox3 = QHBoxLayout()
        if is_active:
            connectBut = QPushButton('Disconnect')
            connectBut.connect(connectBut, SIGNAL('clicked()'), self.disconnect)
        else:
            connectBut = QPushButton('Connect')
            connectBut.connect(connectBut, SIGNAL('clicked()'), lambda: self.wireless.ConnectWireless(id))
        hbox3.addWidget(connectBut)
        propBut = QPushButton('Properties')
        propBut.connect(propBut, SIGNAL('clicked()'), lambda: self.openWirelessProps(id))
        hbox3.addWidget(propBut)
        widgetButtons.setLayout(hbox3)
        vbox.addWidget(widgetButtons)

        vbox.setSpacing(0)
        widgetRightPart.setLayout(vbox)
        hbox.addWidget(widgetRightPart)
        hbox.addItem(QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))
        widget.setLayout(hbox)
        return widget

    def openWirelessProps(self, id):
    """ Opens properties dialog of wireless network with given ID """
        dialog = NetworkProps(self)
        dialog.loadSettings(lambda prop: self.getWirelessProp(id, prop))
        dialog.loadWirelessSettings(lambda prop: self.getWirelessProp(id, prop))
        dialog.exec_()     
        dialog.saveSettings(lambda prop, value: self.setWirelessProp(id, prop, value))
        dialog.saveWirelessSettings(lambda prop, value: self.setWirelessProp(id, prop, value))

    @catchdbus
    def getWirelessProp(self, id, prop):
    """ Returns property 'prop' of wireless network with given id """
        return self.wireless.GetWirelessProperty(id, prop)

    @catchdbus
    def setWirelessProp(self, id, prop, value):
    """ Set property 'prop' of wireless network with given id to given value"""
        return self.wireless.SetWirelessProperty(id, prop, value)

    @catchdbus
    def updateAutoconnect(self, id, auto):
    """ Saves autoupdate property of wireless network with given ID """
        self.wireless.SetWirelessProperty(id, 'automatic', auto)
        self.wireless.SaveWirelessNetworkProperty(id, 'automatic')

    @catchdbus
    def getSignalImage(self, level):
    """ Returns appropriate to 'level' QImage widget """
        if self.daemon.GetWPADriver() == 'ralink legacy' or \
           self.daemon.GetSignalDisplayType() == 1:
            if level >= -60:
                signal_img = 'signal-100.png'
            elif level >= -70:
                signal_img = 'signal-75.png'
            elif level >= -80:
                signal_img = 'signal-50.png'
            else:
                signal_img = 'signal-25.png'
        else:
            if level > 75:
                signal_img = 'signal-100.png'
            elif level > 50:
                signal_img = 'signal-75.png'
            elif level > 25:
                signal_img = 'signal-50.png'
            else:
                signal_img = 'signal-25.png'
        label = QLabel()
        label.setPixmap(QPixmap(wpath.images + signal_img))
        return label

    @catchdbus
    def getWirelessNetStr(self, network_id):
    """ Returns wireless essid """
        return self.wireless.GetWirelessProperty(network_id, 'essid')

    @catchdbus
    def updateStatus(self, state = None, info = None, timerFired = False):
    """ Updates GUI status """
        self.connecting = False
        self.cancelBut.setVisible(False)
        self.connectProgress.setVisible(False)
        if self.DBUS_AVAIL:
            if not state or not info:
                [state, info] = self.daemon.GetConnectionStatus()
            if state == misc.WIRED:
                self.setWiredState(info)
            elif state == misc.WIRELESS:
                self.setWirelessState(info)
            elif state == misc.CONNECTING:
                self.cancelBut.setVisible(True)
                self.cancelBut.setEnabled(True)
                self.connectProgress.setVisible(True)
                self.connecting = True
                self.setConnectingState()
            else:
                self.setNotConnectedState(info)
        if self.curState != state:
            self.updateNetworkList()
            self.curState = state
        if timerFired:
            QTimer.singleShot(1000, lambda: self.updateStatus(True))


    @catchdbus
    def disconnect(self):
    """ Disconnect button click handler, disconnects from current network """
        self.scrollArea.setEnabled(False)
        self.daemon.Disconnect()
    
    def setWiredState(self, info):
    """ Updates current state with 'Connected to wired' value """
        self.scrollArea.setEnabled(True)
        self.statusLabel.setText('Connected to wired')
        print info

    def setWirelessState(self, info):
    """ Updates current state with 'Connected to wireless' value """
        wirelessIP = info[0]
        network = info[1]
        strength = info[2]
        cur_net_id = info[3]
        connection_speed = info[4]
        self.statusLabel.setText('Connected to %s at %s (IP: %s)' % (network, 
            self.daemon.FormatSignalForPrinting(strength), wirelessIP))
        self.scrollArea.setEnabled(True)

    def setConnectingState(self):
    """ Updates current state with 'Connecting' value """
        if self.connecting:
            self.scrollArea.setEnabled(False)
            if self.wired.CheckIfWiredConnecting():
                self.statusLabel.setText(language['wired_network'] + ': ' +
                    qlanguage(str(self.wired.CheckWiredConnectingMessage())))
            elif self.wireless.CheckIfWirelessConnecting():
                self.statusLabel.setText(self.wireless.GetCurrentNetwork(self.wireless.GetIwconfig()) + ': ' +
                    qlanguage(str(self.wireless.CheckWirelessConnectingMessage())))

            QTimer.singleShot(500, self.setConnectingState)

    def setNotConnectedState(self, info):
    """ Updates current state with 'Not connected' value """
        self.scrollArea.setEnabled(True)
        self.statusLabel.setText('Not connected')
        print info

    def setupDBus(self, force=True):
    """ Performs setup of DBus-related things """
        print "Connecting to daemon..."
        try:
            dbusmanager.connect_to_dbus()
        except DBusException:
            if force:
                print "Can't connect to the daemon, trying to start it automatically..."
                misc.PromptToStartDaemon()
                try:
                    dbusmanager.connect_to_dbus()
                except DBusException:
                    error(None, "Could not connect to wicd's D-Bus interface.  " +
                              "Check the wicd log for error messages.")
                    return False
            else:  
                return False
                    
        dbus_ifaces = dbusmanager.get_dbus_ifaces()
        self.daemon = dbus_ifaces['daemon']
        self.wireless = dbus_ifaces['wireless']
        self.wired = dbus_ifaces['wired']
        self.DBUS_AVAIL = True
        print "Connected."
    def handleNoDBus(self):
    """ Handles DBus daemon restarts """
        """ Called when dbus announces its shutting down. """
        self.DBUS_AVAIL = False
        #gui.handle_no_dbus(from_tray=True)
        print "Wicd daemon is shutting down!"
