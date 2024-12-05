#!/usr/bin/env python
# -*- coding: utf-8 -*-


from enigma import eEPGCache,getDesktop, quitMainloop, eListbox, eListboxPythonMultiContent, gFont, eRect, eSize, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_VALIGN_TOP, RT_WRAP, BT_SCALE, iServiceInformation,eServiceCenter,eServiceReference
from Screens.Screen import Screen
from ServiceReference import ServiceReference
import shutil
from Screens.HelpMenu import HelpableScreen
from Screens.Standby import TryQuitMainloop
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.config import config, ConfigClock, getConfigListEntry, ConfigSubsection, ConfigPassword, ConfigEnableDisable, configfile, ConfigInteger, ConfigText, ConfigYesNo, ConfigDirectory, ConfigSelection, ConfigIP
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import NumberActionMap, HelpableActionMap,ActionMap
from Components.GUIComponent import GUIComponent
from os import unlink
from shutil import copyfile
from Plugins.Plugin import PluginDescriptor
from timer import TimerEntry
from threading import Timer,Thread,Event
from Screens.MessageBox import MessageBox
import os
import platform
import subprocess    
import fnmatch
import time
from time import localtime,mktime
from Components.MenuList import MenuList
from Components.Task import Task,Job,job_manager as JobManager
import traceback
from datetime import datetime,timedelta
import signal
import socket
import traceback
import sys
import binascii
from Screens.InputBox import InputBox
from RecordTimer import AFTEREVENT,RecordTimerEntry
from Screens.InfoBar import MoviePlayer 
from enigma import eDVBResourceManager


HAS_OPENWEBIF = False
try:
	from Plugins.Extensions.OpenWebif.controllers.stream import StreamAdapter
	HAS_OPENWEBIF = True
except:
	pass


#Add Optional - Erstellung Log-Datei 

pversion = "V0.01"
config.plugins.tunerscript = ConfigSubsection()
config.plugins.tunerscript.active = ConfigYesNo(default = True)
config.plugins.tunerscript.background = ConfigYesNo(default = True)
config.plugins.tunerscript.tuneron = ConfigText(default = "/usr/script/tuneron.sh", fixed_size = False)
config.plugins.tunerscript.tuneroff = ConfigText(default = "/usr/script/tuneroff.sh", fixed_size = False)
config.plugins.tunerscript.wtuneron = ConfigInteger(default = 1, limits = (1, 999))
config.plugins.tunerscript.wtuneroff = ConfigInteger(default = 5, limits = (1, 999))
config.plugins.tunerscript.onstartup = ConfigYesNo(default = False)
config.plugins.tunerscript.onshutdown = ConfigYesNo(default = True)


def autostart(session):
	try:
		global objtunerscript
		objtunerscript = tunerscript(session)

		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			try:
				res_mgr.frontendUseMaskChanged.connect(objtunerscript.onEvent)
			except:
				try:
					res_mgr.frontendUseMaskChanged.get().append(objtunerscript.onEvent)
				except:
					pass

	except:
		print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
		traceback.print_exc()
		

def shutdown():
	try:
		print "[TUNERSCRIPT] shutdown"
		objtunerscript.shutdown()
	except:
		print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
		traceback.print_exc()


class tunerscript():

	def __init__(self,session):
		try:
			
			print "[TUNERSCRIPT] init tunerscript()"

			self.laststate = False
			self.scriptstate = False
			
			self.thread = None
			self.timeron = -1
			self.timeroff = -1
			self.session = session

			if config.plugins.tunerscript.active.value and config.plugins.tunerscript.onstartup.value:
				self.scriptstate=True
				self.startscript(config.plugins.tunerscript.tuneron.value)
				

		except:
			print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
			traceback.print_exc()


	def shutdown(self):
		try:
			if config.plugins.tunerscript.active.value:

				print "[TUNERSCRIPT] self.shutdown()"
				self.timeron = -2
				if config.plugins.tunerscript.onshutdown.value:
					self.scriptstate=False
					self.startscript(config.plugins.tunerscript.tuneroff.value)

		except:
			print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
			traceback.print_exc()


	def onEvent(self, mask):
		try:

			if config.plugins.tunerscript.active.value:

				self.mask = mask
				self.tuners = []


				usetuner=False
				bit = 1;
				for tunernumber in range(32):
					if bool(mask & bit):
						self.tuners.append(tunernumber)
						usetuner=True
					bit = bit << 1
				
				print "[TUNERSCRIPT] Tuner in use:", usetuner
				

				if self.thread is None:
					print "[TUNERSCRIPT] starting Thread"
					self.thread = Timer(1,self._thread)
					self.thread.start()
				

				self.laststate = usetuner


		except:
			print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
			traceback.print_exc()



	def startscript(self,script):
		try:
			msg=""
			if os.path.isfile(script):
				s=script
				if config.plugins.tunerscript.background.value:
					s=s + " &"
				print "[TUNERSCRIPT] startscript", s
				os.system(s)
			else:
				print "[TUNERSCRIPT] file not found"
				msg = "Script " + script + " nicht gefunden"

		except:
			print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
			msg=sys.exc_info()[0] + " " + sys.exc_info()[1]
			traceback.print_exc()

		if msg != "":
			msg = "[TUNERSCRIPT] \n\n" + msg
			self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, timeout = 15)


	def _thread(self):
		try:
			
			print "[TUNERSCRIPT] Thread",self.timeron,self.timeroff,self.laststate,self.scriptstate


			
			if self.laststate and not self.scriptstate: self.timeron+=1
			elif not self.laststate and self.scriptstate: self.timeroff+=1
			elif ((self.laststate and self.scriptstate) or (not self.laststate and not self.scriptstate)): 
				self.timeron=-1
				self.timeroff=-1

			nextrun=False
			if (self.timeron>=0 or self.timeroff>=0) and self.timeron>-2:

				if self.timeron>=0:
					if self.timeron>=config.plugins.tunerscript.wtuneron.value:
						self.scriptstate=True
						self.timeron=-1
						self.startscript(config.plugins.tunerscript.tuneron.value)
					else:
						nextrun=True
					
				if self.timeroff>=0:
					if self.timeroff>=config.plugins.tunerscript.wtuneroff.value:
						self.scriptstate=False
						self.timeroff=-1
						self.startscript(config.plugins.tunerscript.tuneroff.value)
					else:
						nextrun=True


			if nextrun:
				self.threadoff = Timer(1,self._thread)
				self.threadoff.start()
			else:
				print "[TUNERSCRIPT] Thread stopped"
				self.thread = None




		except:
			print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
			traceback.print_exc()



class TUNERSCRIPT_Config(ConfigListScreen,Screen):

	
	def __init__(self, session):
		try:
			Screen.__init__(self, session)
	
			self.list = []	
			
			print "[TUNERSCRIPT] init TUNERSCRIPT_config"
	
			ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)
			self.onChangedEntry = []
	
			self.skinName = ["Tunerscriptconfig", "Setup"]
			self.setup_title = _("[TUNERSCRIPT] "+pversion)
			self.session = session
	
			self.createsetup()
			self["config"].setList(self.list)
	

			self["setupActions"] =  ActionMap(["ColorActions","OkCancelActions"],
				{
				"green": self.green,
				"red": self.cancel,
				"cancel": self.cancel,
				"ok": self.ok,
				}, -1)
	

			self.title=_("Bitte wählen")
			try:
				self["title"] = StaticText(self.title)
			except:
				print 'self["config"] was not found in skin'	
				
			try:
				self['key_red'] = StaticText(_('Cancel'))
				self['key_green'] = StaticText(_('Ok'))
				self['key_yellow'] = StaticText(_(" "))
				self['key_blue'] = StaticText(_(" "))
			except:
				pass


		except:
			print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
			traceback.print_exc()



	def cancel(self):
		try:
			print "[TUNERSCRIPT] close AutocutProviderScreen"
			self.close(None)
		except:
			print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
			traceback.print_exc()


	def up(self):
		try:
			self["config"].up()
		except:
			print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
			traceback.print_exc()

	def down(self):
		try:
			self["config"].down()
		except:
			print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
			traceback.print_exc()

	def left(self):
		try:
			self["config"].pageUp()
		except:
			print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
			traceback.print_exc()

	def right(self):
		try:
			self["config"].pageDown()
		except:
			print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
			traceback.print_exc()


	def ok(self):
		try:

			ret=None
			cur = self["config"].getCurrent()
			if cur is not None:
				cur[1].value = not cur[1].value
				print "[TUNERSCRIPT] ok",cur[0],"/",cur[1].value
			self.changedEntry()

		except:
			print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
			traceback.print_exc()


	def createsetup(self):
		try:

			print "[TUNERSCRIPT] createsetup"

			index=len(self.list)-1
			while index>=0:
				del self.list[index]
				index-=1


			self.list.append(getConfigListEntry(_("Plugin aktiv"), config.plugins.tunerscript.active))
			if config.plugins.tunerscript.active.value:
				self.list.append(getConfigListEntry(_(" ")))
				self.list.append(getConfigListEntry(_("Script im Hintergrund ausführen"), config.plugins.tunerscript.background ))
				self.list.append(getConfigListEntry(_(" ")))
				self.list.append(getConfigListEntry(_("Script einschalten"), config.plugins.tunerscript.tuneron ))
				self.list.append(getConfigListEntry(_("Script bei Systemstart ausführen"), config.plugins.tunerscript.onstartup ))
				self.list.append(getConfigListEntry(_("Verzögerung ein (sec)"), config.plugins.tunerscript.wtuneron ))
				self.list.append(getConfigListEntry(_(" ")))
				self.list.append(getConfigListEntry(_("Script ausschalten"), config.plugins.tunerscript.tuneroff ))
				self.list.append(getConfigListEntry(_("Script beim Herunterfahren ausführen"), config.plugins.tunerscript.onshutdown ))
				self.list.append(getConfigListEntry(_("Verzögerung aus (sec)"), config.plugins.tunerscript.wtuneroff ))


		except:
			print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
			traceback.print_exc()

	def changedEntry(self):
		try:
			print "[TUNERSCRIPT] changedEntry"
			self.createsetup()
			cur = self["config"].getCurrent()
			self["config"].setList(self.list)
			if cur and cur is not None:
				self["config"].updateConfigListView(cur)


		except:
			print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
			traceback.print_exc()

		
	def green(self):
		try:
			provider=[]
			print "[TUNERSCRIPT] green tunerscriptScreen"
			for x in self["config"].list:
				if len(x)>1:
					print "[TUNERSCRIPT] save",x[0],"=",x[1].value
					x[1].save()

			self.close(None)
		 
		except:
			print "[TUNERSCRIPT] ERROR", sys.exc_info()[0],sys.exc_info()[1]
			traceback.print_exc()
