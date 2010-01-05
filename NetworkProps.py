#!/usr/bin/env python
# -* coding: utf-8 -*-

# GUI
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_networkProps import Ui_networkProps

class NetworkProps(QDialog, Ui_networkProps):
    def __init__(self, parent = None):
        super(NetworkProps, self).__init__(parent)
        self.setupUi(self)
        self.useStaticIP.connect(self.useStaticIP, SIGNAL('toggled(bool)'), self.useStaticIPToggled)
        self.useStaticDNS.connect(self.useStaticDNS, SIGNAL('toggled(bool)'), self.useStaticDNSToggled)
        self.useGlobalDNS.connect(self.useGlobalDNS, SIGNAL('toggled(bool)'), self.useGlobalDNSToggled)
        self.useDHCPHostname.connect(self.useDHCPHostname, SIGNAL('toggled(bool)'), self.useDHCPHostnameToggled)

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
