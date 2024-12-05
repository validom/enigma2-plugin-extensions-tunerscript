#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Plugins.Plugin import PluginDescriptor
import tunerscript


def autostart(reason, **kwargs):
	try:
		if kwargs.has_key("session") and reason == 0:
			tunerscript.autostart(kwargs["session"])
		elif reason == 1:
			tunerscript.shutdown()
	except:
		import traceback
		import sys
		print "[AUTOCUT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
		traceback.print_exc()

def main(session, **kwargs):
	try:
#		reload(tunerscript)
		session.open(tunerscript.TUNERSCRIPT_Config)
	except:
		import traceback
		import sys
		print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
		traceback.print_exc()


def Plugins(path,**kwargs):
	list = []
	list.append(PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart))
	list.append(PluginDescriptor(name="Tunerscript", description=_(tunerscript.pversion), where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main))
	return list


