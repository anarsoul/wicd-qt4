#!/usr/bin/env python
# -* coding: utf-8 -*-

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
