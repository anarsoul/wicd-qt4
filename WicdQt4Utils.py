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

from PyQt4.QtCore import *
from wicd import misc
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
