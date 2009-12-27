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

        self.daemon = self.wireless = self.wired = None
        self.setupDBus()

        bus = dbusmanager.get_bus()
        #bus.add_signal_receiver(tray_icon.icon_info.wired_profile_chooser,
        #                        'LaunchChooser', 'org.wicd.daemon')
        #bus.add_signal_receiver(tray_icon.icon_info.update_tray_icon,
        #                        'StatusChanged', 'org.wicd.daemon')
        bus.add_signal_receiver(lambda: self.scanEnded(), 'SendEndScanSignal',
                                'org.wicd.daemon.wireless')
        bus.add_signal_receiver(lambda: self.scanStarted(),
                                'SendStartScanSignal', 'org.wicd.daemon.wireless')
        bus.add_signal_receiver(lambda: self.handleNoDBus(), #or 
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
        wirelessList = []
        for network_id in range(0, self.wireless.GetNumberOfNetworks()):
            wirelessList.append(self.getWirelessNetStr(network_id))
        print 'wired list: %s' % str(wiredList)
        print 'wireless list: %s' % str(wirelessList)

    def getWirelessNetStr(self, network_id):
        return 'Nothing'

    @catchdbus
    def updateStatus(self, timerFired = False):
        if self.DBUS_AVAIL:
            [state, info] = self.daemon.GetConnectionStatus()
            if state == misc.WIRED:
                self.setWiredState(info)
            elif state == misc.WIRELESS:
                self.setWirelessState(info)
            elif state == misc.CONNECTING:
                self.setConnectingState(info)
            else:
                self.setNotConnectedState(info)
        if timerFired:
            QTimer.singleShot(1000, lambda: self.updateStatus(True))

    def setWiredState(self, info):
        print info

    def setWirelessState(self, info):
        wirelessIP = info[0]
        network = info[1]
        strength = info[2]
        cur_net_id = info[3]
        connection_speed = info[4]
        self.statusLabel.setText('Connected to %s (Level: %s, IP: %s)' % (network, 
            self.daemon.FormatSignalForPrinting(strength), wirelessIP))

    def setConnectingState(self, info):
        print info

    def setNotConnectedState(self, info):
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

