#!/usr/bin/env python

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import atexit
import sys
from dbus import DBusException

# Import ui parts
from ui_mainWindow import Ui_mainWindow

# Wicd specific imports
from wicd import wpath
from wicd import dbusmanager
from wicd import misc

misc.RenameProcess("wicd-client-qt4")

if __name__ == '__main__':
    wpath.chdir(__file__)
    
daemon = wireless = wired = lost_dbus_id = None
DBUS_AVAIL = False

class MainWindow(QWidget, Ui_mainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

class Handler(QObject):
    def __init__(self):
        super(Handler, self).__init__()

    def handle(self):
        global wireless
        print 'Handle!'
        wireless.Scan(False)

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

def setup_dbus(force=True):
    global daemon, wireless, wired, DBUS_AVAIL, lost_dbus_id
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
                
    #if lost_dbus_id:
    #    gobject.source_remove(lost_dbus_id)
    #    lost_dbus_id = None
    dbus_ifaces = dbusmanager.get_dbus_ifaces()
    daemon = dbus_ifaces['daemon']
    wireless = dbus_ifaces['wireless']
    wired = dbus_ifaces['wired']
    DBUS_AVAIL = True
    print "Connected."
    return True

def handle_no_dbus():
    """ Called when dbus announces its shutting down. """
    global DBUS_AVAIL
    DBUS_AVAIL = False
    #gui.handle_no_dbus(from_tray=True)
    print "Wicd daemon is shutting down!"
    #lost_dbus_id = misc.timeout_add(5, lambda:error(None, language['lost_dbus'], 
    #                                                block=False))
    return False

def on_exit():
    print 'on_exit'
    if DBUS_AVAIL:
        try:
            daemon.SetGUIOpen(False)
        except DBusException:
            pass

def scan_ended():
    print 'Scan ended'

def scan_started():
    print 'Scan started'

@catchdbus
def main(argv):
    """ The main frontend program.

    Keyword arguments:
    argv -- The arguments passed to the script.

    """
    #try:
    #    opts, args = getopt.getopt(sys.argv[1:], 'nhao', ['help', 'no-tray',
    #                                                     'no-animate',
    #                                                     'only-notifications'])
    #except getopt.GetoptError:
    #    # Print help information and exit
    #    usage()
    #    sys.exit(2)

    #use_tray = True
    #animate = True
    #display_app = True
    #for opt, a in opts:
    #    if opt in ('-h', '--help'):
    #        usage()
    #        sys.exit(0)
    #    elif opt in ('-n', '--no-tray'):
    #        use_tray = False
    #    elif opt in ('-a', '--no-animate'):
    #        animate = False
    #    elif opt in ('-o', '--only-notifications'):
    #        print "only displaying notifications"
    #        use_tray = False
    #        display_app = False
    #    else:
    #        usage()
    #        sys.exit(2)
    
    print 'Loading...'
    setup_dbus()
    atexit.register(on_exit)

    # Check to see if wired profile chooser was called before icon
    # was launched (typically happens on startup or daemon restart).
    #if DBUS_AVAIL and daemon.GetNeedWiredProfileChooser():
    #    daemon.SetNeedWiredProfileChooser(False)
    #    tray_icon.icon_info.wired_profile_chooser()
        
    bus = dbusmanager.get_bus()
    #bus.add_signal_receiver(tray_icon.icon_info.wired_profile_chooser,
    #                        'LaunchChooser', 'org.wicd.daemon')
    #bus.add_signal_receiver(tray_icon.icon_info.update_tray_icon,
    #                        'StatusChanged', 'org.wicd.daemon')
    bus.add_signal_receiver(scan_ended, 'SendEndScanSignal',
                            'org.wicd.daemon.wireless')
    bus.add_signal_receiver(scan_started,
                            'SendStartScanSignal', 'org.wicd.daemon.wireless')
    bus.add_signal_receiver(handle_no_dbus, #or 
                            "DaemonClosing", 'org.wicd.daemon')
    bus.add_signal_receiver(lambda: setup_dbus(force=False), "DaemonStarting",
                            "org.wicd.daemon")
    print 'Done loading.'

    app = QApplication(sys.argv)

    # Constructing gui...
    handler = Handler()
    mainWindow = MainWindow()
    mainWindow.show()
    mainWindow.refreshBut.connect(mainWindow.refreshBut, SIGNAL('clicked()'), handler.handle)

    # Start event processing...
    app.exec_()

if __name__ == '__main__':
    main(sys.argv)
