#!/usr/bin/env python
# -* coding: utf-8 -*-

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

def qstr(arg):
    return QString.fromLocal8Bit(arg)

def qlanguage(arg):
    return qstr(language[arg])

def catchdbus(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DBusException, e:
            if e.get_dbus_name() != None and "DBus.Error.AccessDenied" in e.get_dbus_name():
                error(None, language['access_denied'].replace("$A","<b>"+wpath.wicd_group+"</b>"))
                raise DBusException(e)
            else:
                print "warning: ignoring exception %s" % e
            return None
    wrapper.__name__ = func.__name__
    wrapper.__module__ = func.__module__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__
    return wrapper

class MainWindow(QWidget, Ui_mainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
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
        QMessageBox.information(self, 'Not Implemented!', 'Sorry, but this functions is not implemented yet!')

    def aboutClicked(self):
        QMessageBox.information(self, 'About', 'wicd-qt4 development version')

    def scanClicked(self):
        self.wireless.Scan(False)

    def scanStarted(self):
        label = QLabel(qlanguage('scanning_stand_by'))
        label.setAlignment(Qt.AlignCenter)
        label.setEnabled(False)
        self.scrollArea.setWidget(label)
        label.show()
        pass
    
    def scanEnded(self):
        self.updateNetworkList()
        self.updateStatus()

    def onExit(self):
        if self.DBUS_AVAIL:
            try:
                self.daemon.SetGUIOpen(False)
            except DBusException:
                pass

    @catchdbus
    def cancelClicked(self):
        self.cancelBut.setEnabled(False)
        self.daemon.CancelConnect()
        self.daemon.SetForcedDisconnect(True)

    @catchdbus
    def updateNetworkList(self):
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
        if self.daemon.GetSignalDisplayType() == 1:
            return self.wireless.GetWirelessProperty(id, 'strength')
        else:
            return self.wireless.GetWirelessProperty(id, 'quality')

    def getWirelessNetWidget(self, id, is_active):
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
        checkBox.connect(checkBox, SIGNAL('stateChanged(int)'), lambda(state): self.updateAutoconnect(id, state == Qt.Checked))
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
        dialog = NetworkProps(self)
        self.setPropsValues(dialog, lambda(prop): self.getWirelessProp(id, prop))
        dialog.exec_()     

    def setPropsValues(self, dialog, getProp):
        formatEntry = lambda(prop): misc.noneToBlankString(getProp(prop))
        dialog.ipEdit.setText(formatEntry('ip'))
        dialog.netmaskEdit.setText(formatEntry('netmask'))
        dialog.gatewayEdit.setText(formatEntry('gateway'))
        dialog.dns1Edit.setText(formatEntry('dns1'))
        dialog.dns2Edit.setText(formatEntry('dns2'))
        dialog.dns3Edit.setText(formatEntry('dns3'))
        dialog.dnsDomainEdit.setText(formatEntry('dns_domain'))
        dialog.searchDomainEdit.setText(formatEntry('search_domain'))
        dialog.useGlobalDNS.setChecked(bool(getProp('use_global_dns')))

        dhcpname = getProp('dhcphostname')
        if dhcpname is None:
            dhcpname = os.uname()[1]

        dialog.dhcpHostnameEdit.setText(qstr(dhcpname))
        self.updateCheckboxes(dialog, getProp)

    def updateCheckboxes(self, dialog, getProp):
        stringToNone = misc.stringToNone
        if stringToNone(dialog.ipEdit.text()):
            dialog.useStaticIP.setChecked(True)
            dialog.useStaticDNS.setEnabled(True)
        else:
            dialog.useStaticIP.setChecked(False)
            dialog.useStaticDNS.setEnabled(False)

        if stringToNone(dialog.dns1Edit.text()) or dialog.useGlobalDNS.isChecked():
            dialog.useStaticDNS.setChecked(True)
        else:
            dialog.useStaticDNS.setChecked(False)
        dialog.updateCheckboxes()


    @catchdbus
    def getWirelessProp(self, id, prop):
        return self.wireless.GetWirelessProperty(id, prop)

    @catchdbus
    def updateAutoconnect(self, id, auto):
        self.wireless.SetWirelessProperty(id, 'automatic', auto)
        self.wireless.SaveWirelessNetworkProperty(id, 'automatic')

    @catchdbus
    def getSignalImage(self, level):
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
        return self.wireless.GetWirelessProperty(network_id, 'essid')

    @catchdbus
    def updateStatus(self, state = None, info = None, timerFired = False):
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
        self.scrollArea.setEnabled(False)
        self.daemon.Disconnect()
    
    def setWiredState(self, info):
        self.scrollArea.setEnabled(True)
        self.statusLabel.setText('Connected to wired')
        print info

    def setWirelessState(self, info):
        wirelessIP = info[0]
        network = info[1]
        strength = info[2]
        cur_net_id = info[3]
        connection_speed = info[4]
        self.statusLabel.setText('Connected to %s at %s (IP: %s)' % (network, 
            self.daemon.FormatSignalForPrinting(strength), wirelessIP))
        self.scrollArea.setEnabled(True)

    def setConnectingState(self):
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
        self.scrollArea.setEnabled(True)
        self.statusLabel.setText('Not connected')
        print info

    def setupDBus(self, force=True):
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
    def handleNoDBus():
        """ Called when dbus announces its shutting down. """
        self.DBUS_AVAIL = False
        #gui.handle_no_dbus(from_tray=True)
        print "Wicd daemon is shutting down!"
