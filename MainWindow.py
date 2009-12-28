#!/usr/bin/env python

# GUI
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_mainWindow import Ui_mainWindow

# DBus
from dbus import DBusException

# Wicd
from wicd import dbusmanager
from wicd import misc
from wicd import wpath

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
        self.refreshBut.connect(self.refreshBut, SIGNAL('clicked()'), self.scanClicked)

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

    def scanClicked(self):
        self.wireless.Scan(False)

    def scanStarted(self):
        label = QLabel('Scanning...')
        label.setAlignment(Qt.AlignCenter)
        label.setEnabled(False)
        self.scrollArea.setWidget(label)
        label.show()
        pass
    
    def scanEnded(self):
        label = QLabel('Done!')
        label.setAlignment(Qt.AlignCenter)
        label.setEnabled(False)
        self.scrollArea.setWidget(label)
        label.show()

        self.updateNetworkList()
        self.updateStatus()

    @catchdbus
    def updateNetworkList(self):
        wiredList = self.wired.GetWiredProfileList()
        print 'wired list: %s' % str(wiredList)

        widget = QWidget()
        vbox = QVBoxLayout()
        for network_id in range(0, self.wireless.GetNumberOfNetworks()):
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
        hbox3.addWidget(propBut)
        widgetButtons.setLayout(hbox3)
        vbox.addWidget(widgetButtons)

        vbox.setSpacing(0)
        widgetRightPart.setLayout(vbox)
        hbox.addWidget(widgetRightPart)
        hbox.addItem(QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))
        widget.setLayout(hbox)
        return widget

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
        if self.DBUS_AVAIL:
            if not state or not info:
                [state, info] = self.daemon.GetConnectionStatus()
            if state == misc.WIRED:
                self.setWiredState(info)
            elif state == misc.WIRELESS:
                self.setWirelessState(info)
            elif state == misc.CONNECTING:
                self.setConnectingState(info)
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

    def setConnectingState(self, info):
        self.scrollArea.setEnabled(False)
        self.statusLabel.setText('Connecting...')
        print info

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
