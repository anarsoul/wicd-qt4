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
from ui_networkProps import Ui_networkProps

from wicd import dbusmanager
from wicd import misc
from WicdQt4Utils import qstr, qlanguage

class NetworkProps(QDialog, Ui_networkProps):
    """ Network properties dialog class """
    def __init__(self, parent = None):
    """ Constructor """
        super(NetworkProps, self).__init__(parent)
        self.setupUi(self)
        self.useStaticIP.connect(self.useStaticIP, SIGNAL('toggled(bool)'), self.useStaticIPToggled)
        self.useStaticDNS.connect(self.useStaticDNS, SIGNAL('toggled(bool)'), self.useStaticDNSToggled)
        self.useGlobalDNS.connect(self.useGlobalDNS, SIGNAL('toggled(bool)'), self.useGlobalDNSToggled)
        self.useDHCPHostname.connect(self.useDHCPHostname, SIGNAL('toggled(bool)'), self.useDHCPHostnameToggled)

        self.setupDBus()

    def loadSettings(self, getProp):
    """ Updates GUI elements with values from settings """
        formatEntry = lambda prop: misc.noneToBlankString(getProp(prop))
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
    """ Updates settings according to GUI elements """
        if self.useStaticIP.isChecked():
            setProp('ip', misc.noneToString(self.ipEdit.text()))
            setProp('netmask', misc.noneToString(self.netmaskEdit.text()))
            setProp('gateway', misc.noneToString(self.gatewayEdit.text()))
        else:
            setProp('ip', '')
            setProp('netmask', '')
            setProp('gateway', '')

        if self.useStaticDNS.isChecked() and not self.useGlobalDNS.isChecked():
            setProp('use_static_dns', True)
            setProp('use_global_dns', False)
            setProp('dns_domain', misc.noneToString(self.dnsDomainEdit.text()))
            setProp("search_domain", misc.noneToString(self.searchDomainEdit.text()))
            setProp("dns1", misc.noneToString(self.dns1Edit.text()))
            setProp("dns2", misc.noneToString(self.dns2Edit.text()))
            setProp("dns3", misc.noneToString(self.dns3Edit.text()))
        elif self.useStaticDNS.isChecked() and self.useGlobalDNS.isChecked():
            setProp('use_static_dns', True)
            setProp('use_global_dns', True)
        else:
            setProp('use_static_dns', False)
            setProp('use_global_dns', False)
            setProp('dns_domain', '')
            setProp('search_domain', '')
            setProp('dns1', '')
            setProp('dns2', '')
            setProp('dns3', '')
            setProp('use_dhcphostname', self.useDHCPHostname.isChecked())
            setProp('dhcphostname',misc.noneToString(self.dhcpHostnameEdit.text()))

    def loadWirelessSettings(self, getProp):
    """ Updates wireless-related GUI elements with values from settings """
        pass

    def saveWirelessSettings(self, setProp):
    """ Updates wireless-related settings according to GUI elements """
        pass

    def setCheckboxes(self, getProp):
    """ Set checkboxes according to settings """
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
    """ Setups DBus-related things """
        dbus_ifaces = dbusmanager.get_dbus_ifaces()
        self.daemon = dbus_ifaces['daemon']
        self.wireless = dbus_ifaces['wireless']
        self.wired = dbus_ifaces['wired']

    def updateCheckboxes(self):
    """ Updates checkboxes according to settings """
        self.useStaticIPToggled(self.useStaticIP.isChecked())
        self.useStaticDNSToggled(self.useStaticDNS.isChecked())
        self.useGlobalDNSToggled(self.useGlobalDNS.isChecked())
        self.useDHCPHostnameToggled(self.useDHCPHostname.isChecked())

    def useStaticIPToggled(self, checked):
    """ useStaticIP toggle signal handler """
        self.useStaticDNS.setEnabled(not checked)
        if checked:
            self.useStaticDNS.setChecked(True)
        self.ipEdit.setEnabled(checked)
        self.netmaskEdit.setEnabled(checked)
        self.gatewayEdit.setEnabled(checked)

    def useStaticDNSToggled(self, checked):
    """ useStaticDNS toggle signal handler """
        self.useGlobalDNS.setEnabled(checked)
        for edit in [self.dns1Edit, self.dns2Edit, self.dns3Edit,
            self.dnsDomainEdit, self.searchDomainEdit]:
            if not checked:
                edit.setEnabled(False)
            else:
                edit.setEnabled(not self.useGlobalDNS.isChecked())

    def useGlobalDNSToggled(self, checked):
    """ useGlobalDNS toggle signal handler """
        if self.useStaticDNS.isChecked():
            for edit in [self.dns1Edit, self.dns2Edit, self.dns3Edit,
                self.dnsDomainEdit, self.searchDomainEdit]:
                edit.setEnabled(not checked)
    def useDHCPHostnameToggled(self, checked):
    """ useDHCPHostname toggle signal handler """
        pass
