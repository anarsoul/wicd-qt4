#!/usr/bin/env python
# -* coding: utf-8 -*-

# GUI
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_networkProps import Ui_networkProps

from wicd import dbusmanager
from wicd import misc
from WicdQt4Utils import qstr, qlanguage

class NetworkProps(QDialog, Ui_networkProps):
    def __init__(self, parent = None):
        super(NetworkProps, self).__init__(parent)
        self.setupUi(self)
        self.useStaticIP.connect(self.useStaticIP, SIGNAL('toggled(bool)'), self.useStaticIPToggled)
        self.useStaticDNS.connect(self.useStaticDNS, SIGNAL('toggled(bool)'), self.useStaticDNSToggled)
        self.useGlobalDNS.connect(self.useGlobalDNS, SIGNAL('toggled(bool)'), self.useGlobalDNSToggled)
        self.useDHCPHostname.connect(self.useDHCPHostname, SIGNAL('toggled(bool)'), self.useDHCPHostnameToggled)

        self.setupDBus()

    def loadSettings(self, getProp):
        formatEntry = lambda(prop): misc.noneToBlankString(getProp(prop))
        self.ipEdit.setText(formatEntry('ip'))
        self.netmaskEdit.setText(formatEntry('netmask'))
        self.gatewayEdit.setText(formatEntry('gateway'))
        self.dns1Edit.setText(formatEntry('dns1'))
        self.dns2Edit.setText(formatEntry('dns2'))
        self.dns3Edit.setText(formatEntry('dns3'))
        self.dnsDomainEdit.setText(formatEntry('dns_domain'))
        self.searchDomainEdit.setText(formatEntry('search_domain'))
        self.useGlobalDNS.setChecked(bool(getProp('use_global_dns')))

        dhcpname = getProp('dhcphostname')
        if dhcpname is None:
            dhcpname = os.uname()[1]

        self.dhcpHostnameEdit.setText(qstr(dhcpname))
        self.setCheckboxes(getProp)

    def saveSettings(self, setProp):
        pass

    def setCheckboxes(self, getProp):
        stringToNone = misc.stringToNone
        if stringToNone(self.ipEdit.text()):
            self.useStaticIP.setChecked(True)
            self.useStaticDNS.setEnabled(True)
        else:
            self.useStaticIP.setChecked(False)
            self.useStaticDNS.setEnabled(False)

        if stringToNone(self.dns1Edit.text()) or self.useGlobalDNS.isChecked():
            self.useStaticDNS.setChecked(True)
        else:
            self.useStaticDNS.setChecked(False)
        self.updateCheckboxes()

    def setupDBus(self):
        dbus_ifaces = dbusmanager.get_dbus_ifaces()
        self.daemon = dbus_ifaces['daemon']
        self.wireless = dbus_ifaces['wireless']
        self.wired = dbus_ifaces['wired']

    def updateCheckboxes(self):
        self.useStaticIPToggled(self.useStaticIP.isChecked())
        self.useStaticDNSToggled(self.useStaticDNS.isChecked())
        self.useGlobalDNSToggled(self.useGlobalDNS.isChecked())
        self.useDHCPHostnameToggled(self.useDHCPHostname.isChecked())

    def useStaticIPToggled(self, checked):
        self.useStaticDNS.setEnabled(not checked)
        if checked:
            self.useStaticDNS.setChecked(True)
        self.ipEdit.setEnabled(checked)
        self.netmaskEdit.setEnabled(checked)
        self.gatewayEdit.setEnabled(checked)

    def useStaticDNSToggled(self, checked):
        self.useGlobalDNS.setEnabled(checked)
        for edit in [self.dns1Edit, self.dns2Edit, self.dns3Edit,
            self.dnsDomainEdit, self.searchDomainEdit]:
            if not checked:
                edit.setEnabled(False)
            else:
                edit.setEnabled(not self.useGlobalDNS.isChecked())

    def useGlobalDNSToggled(self, checked):
        if self.useStaticDNS.isChecked():
            for edit in [self.dns1Edit, self.dns2Edit, self.dns3Edit,
                self.dnsDomainEdit, self.searchDomainEdit]:
                edit.setEnabled(not checked)
    def useDHCPHostnameToggled(self, checked):
        pass
