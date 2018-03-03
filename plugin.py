# MELCloud Plugin
# Author:     Gysmo, 2017
# Version: 0.6
#   
# Release Notes:
# v0.6 : Rewrite of the module to be easier to maintain
# v0.5.1: Problem with device creation
# v0.5 : Upgrade code to be compliant wih new functions
# v0.4 : Search devices in floors, areas and devices
# v0.3 : Add Next Update information, MAC Address  and Serial Number
#		 Add Horizontal vane
#		 Add Vertival vane
#		 Add Room Temp
# v0.2 : Add sync between Domoticz devices and MELCloud devices
#        Usefull if you use your Mitsubishi remote
# v0.1 : Initial release
"""
<plugin key="MELCloud" version="0.6" name="MELCloud plugin" author="gysmo" wikilink="http://www.domoticz.com/wiki/Plugins/MELCloud.html" externallink="http://www.melcloud.com">
    <params>
        <param field="Username" label="Email" width="200px" required="true" />
        <param field="Password" label="Password" width="200px" required="true" />
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import time
import base64
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class BasePlugin:
	pluginState = "Not Ready"
	socketOn = "FALSE"
	
	melcloud_urls = {}
	melcloud_urls["login"] = "https://app.melcloud.com/Mitsubishi.Wifi.Client/Login/ClientLogin"
	melcloud_urls["list_unit"] = "https://app.melcloud.com/Mitsubishi.Wifi.Client/User/ListDevices"
	melcloud_urls["set_unit"] = "https://app.melcloud.com/Mitsubishi.Wifi.Client/Device/SetAta"
	melcloud_urls["unit_info"] = "https://app.melcloud.com/Mitsubishi.Wifi.Client/Device/Get"
		 
	melcloud_key = None
	
	list_units = []
	
	list_switchs = []
	list_switchs.append({"id":1,"name":"Mode","typename":"Selector Switch","image":16,"levels":"Off|Warm|Cold|Vent|Dry"})
	list_switchs.append({"id":2,"name":"Fan","typename":"Selector Switch","image":7,"levels":"Level1|Level2|Level3|Level4|Level5|Auto|Silence"})
	list_switchs.append({"id":3,"name":"Temp","typename":"Selector Switch","image":15,"levels":"16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31"})
	list_switchs.append({"id":4,"name":"Vane Horizontal","typename":"Selector Switch","image":7,"levels":"1|2|3|4|5|Swing|Auto"})
	list_switchs.append({"id":5,"name":"Vane Vertical","typename":"Selector Switch","image":7,"levels":"1|2|3|4|5|Swing|Auto"})
	list_switchs.append({"id":6,"name":"Room Temp","typename":"Temperature"})
	list_switchs.append({"id":7,"name":"Unit Infos","typename":"Text"})
	
	domoticz_levels = {}
	domoticz_levels["mode"] = {"0":0,"10":1,"20":3,"30":7,"40":2}
	domoticz_levels["mode_pic"] = {"0":9,"10":15,"20":16,"30":7,"40":11}
	domoticz_levels["fan"] = {"0":1,"10":2,"20":3,"30":4,"40":255,"50":0,"60":1}
	domoticz_levels["temp"] = {"0":16,"10":17,"20":18,"30":19,"40":20,"50":21,"60":22,"70":23,"80":24,"90":25,"100":26,"110":27,"120":28,"130":29,"140":30,"150":31}
	domoticz_levels["vaneH"] = {"0":1,"10":2,"20":3,"30":4,"40":5,"50":12,"60":0}
	domoticz_levels["vaneV"] = {"0":1,"10":2,"20":3,"30":4,"40":5,"50":7,"60":0}
	
	enabled = False
	
	def __init__(self):
		#self.var = 123
		return

	def onStart(self):
		Domoticz.Heartbeat(25)
		if Parameters["Mode6"] == "Debug":
			Domoticz.Debugging(1)
		# Define connexion to MELCloud
		self.melcloud_key = self.melcloud_login()
		self.melcloud_get_units_info()
		Domoticz.Debug("Units infos " + str(self.list_units))
		if (len(Devices) == 0):
			# Init Devices
			# Creation of switches
			Domoticz.Debug("Find " + str(len(self.list_units)) + " devices in MELCloud")
			for device in self.list_units:
				Domoticz.Debug("Creating device: " + device['name'] + " with melID " + str(device['id']))
				for switch in self.list_switchs:
					# Create switchs
					if switch["typename"] == "Selector Switch":
						switch_options = {"LevelNames": switch["levels"],"LevelOffHidden": "false","SelectorStyle": "1"}
						Domoticz.Device(Name=device['name']+" - "+switch["name"], Unit=switch["id"]+device['idoffset'], TypeName=switch["typename"], Image=switch["image"], Options=switch_options, Used=1).Create()
					else:
						Domoticz.Device(Name=device['name']+" - "+switch["name"], Unit=switch["id"]+device['idoffset'], TypeName=switch["typename"], Used=1).Create()
				self.melcloud_get_unit_info(device)
				self.domoticz_update_switchs(device)

	def onStop(self):
		Domoticz.Log("Goobye from MELCloud plugin.")

	def onConnect(self, Status, Description):
		Domoticz.Log("onConnect called")

	def onMessage(self, Data, Status, Extra):
		Domoticz.Log("onMessage called")

	def onCommand(self, Unit, Command, Level, Hue):
		Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
		#~ Get switch function: mode, fan, temp ...
		switch_id = Unit
		while switch_id > 7:
			switch_id -= 7
		switch_type = self.list_switchs[switch_id-1]["name"]
		#~ Get the unit in units array
		current_unit = False
		for unit in self.list_units:
			if (unit['idoffset'] + self.list_switchs[switch_id-1]["id"]) == Unit:
				current_unit = unit
				break
		if(switch_type == 'Mode'):
			if(Level == 0):
				Domoticz.Debug("Switch Off the unit "+current_unit['name'] + "with ID offset " + str(current_unit['idoffset']))
				self.melcloud_set_power(current_unit['id'],"false")
				Devices[1+current_unit['idoffset']].Update(0, str(Level),9)
				Devices[2+current_unit['idoffset']].Update(0,str(Devices[Unit + 1].sValue))
				Devices[3+current_unit['idoffset']].Update(0,str(Devices[Unit + 2].sValue))
				Devices[4+current_unit['idoffset']].Update(0,str(Devices[Unit + 3].sValue))
				Devices[5+current_unit['idoffset']].Update(0,str(Devices[Unit + 4].sValue))
			elif(Level == 10):
				Domoticz.Debug("Set to WARM the unit "+current_unit['name'])
				self.melcloud_set_power(current_unit['id'],"true")
				self.melcloud_set_mode(current_unit['id'],1)
				Devices[1+current_unit['idoffset']].Update(1, str(Level),15)
			elif(Level == 20):
				Domoticz.Debug("Set to COLD the unit "+current_unit['name'])
				self.melcloud_set_power(current_unit['id'],"true")
				self.melcloud_set_mode(current_unit['id'],3)
				Devices[1+current_unit['idoffset']].Update(1, str(Level),16)
			elif(Level == 30):
				Domoticz.Debug("Set to Vent the unit "+current_unit['name'])
				self.melcloud_set_power(current_unit['id'],"true")
				self.melcloud_set_mode(current_unit['id'],7)
				Devices[1+current_unit['idoffset']].Update(1, str(Level),7)
			elif(Level == 40):
				Domoticz.Debug("Set to Dry the unit "+current_unit['name'])
				self.melcloud_set_power(current_unit['id'],"true")
				self.melcloud_set_mode(current_unit['id'],2)
				Devices[1+current_unit['idoffset']].Update(1, str(Level),11)
			if(Level != 0):
				Devices[2+current_unit['idoffset']].Update(1,str(Devices[Unit + 1].sValue))
				Devices[3+current_unit['idoffset']].Update(1,str(Devices[Unit + 2].sValue))
				Devices[4+current_unit['idoffset']].Update(1,str(Devices[Unit + 3].sValue))
				Devices[5+current_unit['idoffset']].Update(1,str(Devices[Unit + 4].sValue))
		elif(switch_type == 'Fan'):
			if(Level == 0):
				Domoticz.Debug("Change FAN  to Level 1 for "+current_unit['name'])
				self.melcloud_set_fan(current_unit['id'],"1")
			elif(Level == 10):
				Domoticz.Debug("Change FAN  to Level 2 for "+current_unit['name'])
				self.melcloud_set_fan(current_unit['id'],"2")
			elif(Level == 20):
				Domoticz.Debug("Change FAN  to Level 3 for "+current_unit['name'])
				self.melcloud_set_fan(current_unit['id'],"3")
			elif(Level == 30):
				Domoticz.Debug("Change FAN  to Level 4 for "+current_unit['name'])
				self.melcloud_set_fan(current_unit['id'],"4")
			elif(Level == 40):
				Domoticz.Debug("Change FAN  to Silence for "+current_unit['name'])
				self.melcloud_set_fan(current_unit['id'],"6")
			elif(Level == 50):
				Domoticz.Debug("Change FAN  to Auto for "+current_unit['name'])
				self.melcloud_set_fan(current_unit['id'],"0")
			Devices[Unit].Update(Devices[Unit].nValue, str(Level))
		elif(switch_type == 'Temp'):
			setTemp = 16
			if(Level != 0):
				setTemp = int(str(Level).strip("0")) + 16
			Domoticz.Debug("Change Temp to " + str(setTemp) + " for "+unit	['name'])
			self.melcloud_set_temp(device['id'],str(setTemp))
			Devices[Unit].Update(Devices[Unit].nValue, str(Level))
		else:
			Domoticz.Debug("Device not found")
		return True

	def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
		Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

	def onDisconnect(self):
		Domoticz.Log("onDisconnect called")

	def onHeartbeat(self):
		Domoticz.Debug("Current MEL Cloud Key ID:"+self.melcloud_key)
		for unit in self.list_units:
			self.melcloud_get_unit_info(unit)
			domCurrentTemp = self.domoticz_levels["temp"][Devices[self.list_switchs[2]["id"]+unit["idoffset"]].sValue]
			domCurrentFan = self.domoticz_levels["fan"][Devices[self.list_switchs[1]["id"]+unit["idoffset"]].sValue]
			domCurrentVaneH = self.domoticz_levels["vaneH"][Devices[self.list_switchs[3]["id"]+unit["idoffset"]].sValue]
			domCurrentVaneV = self.domoticz_levels["vaneV"][Devices[self.list_switchs[4]["id"]+unit["idoffset"]].sValue]
			Domoticz.Debug("******** "+unit['name']+" ********")
			Domoticz.Debug("Sync POWER " + str(unit['power']) \
				+ " OPERATION MODE " + str(unit['op_mode']) \
				+ " FAN SPEED " + str(unit['set_fan']) \
				+ " VANE HOZ " + str(unit['vaneH']) \
				+ " VANE VER " + str(unit['vaneV']) \
				+ " UNIT TEMP " + str(unit['set_temp']))
			if(unit['power'] is True and Devices[self.list_switchs[0]["id"]+unit["idoffset"]].nValue == 0):
				sValue = str(self.domModeLevels.index(unit['op_mode'])) + "0"
				Devices[self.list_switchs[0]["id"]+unit["idoffset"]].Update(1,sValue,self.domModePic[self.domModeLevels.index(unit['op_mode'])])
				Devices[self.list_switchs[1]["id"]+unit["idoffset"]].Update(1,str(Devices[self.list_switchs[1]["id"]+unit["idoffset"]].sValue))
				Devices[self.list_switchs[2]["id"]+unit["idoffset"]].Update(1,str(Devices[self.list_switchs[2]["id"]+unit["idoffset"]].sValue))
				Devices[self.list_switchs[3]["id"]+unit["idoffset"]].Update(1,str(Devices[self.list_switchs[3]["id"]+unit["idoffset"]].sValue))
				Devices[self.list_switchs[4]["id"]+unit["idoffset"]].Update(1,str(Devices[self.list_switchs[4]["id"]+dunit["idoffset"]].sValue))
			elif(unit['power'] is False and Devices[self.list_switchs[0]["id"]+unit["idoffset"]].nValue == 1):
				Devices[self.list_switchs[0]["id"]+unit["idoffset"]].Update(0,"0",9)
				Devices[self.list_switchs[1]["id"]+unit["idoffset"]].Update(0,str(Devices[self.list_switchs[1]["id"]+unit["idoffset"]].sValue))
				Devices[self.list_switchs[2]["id"]+unit["idoffset"]].Update(0,str(Devices[self.list_switchs[2]["id"]+unit["idoffset"]].sValue))
				Devices[self.list_switchs[3]["id"]+unit["idoffset"]].Update(0,str(Devices[self.list_switchs[3]["id"]+unit["idoffset"]].sValue))
				Devices[self.list_switchs[4]["id"]+unit["idoffset"]].Update(0,str(Devices[self.list_switchs[4]["id"]+unit["idoffset"]].sValue))
	 
	# Sync fan value from MELCloud to Domoticz
			if(unit['set_fan'] != domCurrentFan):
				for level, fan in self.domoticz_levels["fan"].items():
					if(fan == unit['set_fan']):
						Devices[self.list_switchs[1]["id"]+unit["idoffset"]].Update(Devices[self.list_switchs[1]["id"]+unit["idoffset"]].nValue,level)
	# Sync Unit temperature value from MELCloud to Domoticz
			if(unit['set_temp'] != domCurrentTemp):
				for level, temp in self.domoticz_levels["temp"].items():
					if(temp == unit['set_temp']):
						Devices[self.list_switchs[2]["id"]+unit["idoffset"]].Update(Devices[self.list_switchs[2]["id"]+unit["idoffset"]].nValue,level)
	# Sync Vane Horizontal value from MELCloud to Domoticz
			if(unit['vaneH'] != domCurrentVaneH):
				for level, vaneH in self.domoticz_levels["vaneH"].items():
					if(vaneH == unit['vaneH']):
						Devices[self.list_switchs[3]["id"]+unit["idoffset"]].Update(Devices[self.list_switchs[3]["id"]+unit["idoffset"]].nValue,level)
	# Sync Vane Vertical value from MELCloud to Domoticz
			if(unit['vaneV'] != domCurrentVaneH):
				for level, vaneV in self.domoticz_levels["vaneV"].items():
					if(vaneV == unit['vaneV']):
						Devices[self.list_switchs[4]["id"]+unit["idoffset"]].Update(Devices[self.list_switchs[4]["id"]+unit["idoffset"]].nValue,level)
	# Sync Room temperature value from MELCloud to Domoticz
			if(str(unit['room_temp']) != Devices[self.list_switchs[5]["id"]+unit["idoffset"]].sValue):
				Devices[self.list_switchs[5]["id"]+unit["idoffset"]].Update(1,str(unit['room_temp']))
				Domoticz.Debug("Sync ROOM TEMP" + str(unit['room_temp']))
	# Sync Infos value from MELCloud to Domoticz
			textInfos = "NEXT UPDATE " +  str(unit['next_comm']) + "MAC ADDR " + unit['macaddr'] + " S/N " + unit['sn']
			if(textInfos != str(Devices[self.list_switchs[6]["id"]+unit["idoffset"]].sValue)):
				Devices[self.list_switchs[6]["id"]+unit["idoffset"]].Update(1,textInfos)
			Domoticz.Debug("Infos " + str(Devices[self.list_switchs[6]["id"]+unit["idoffset"]].sValue))
		#~ return True
    
    
	def melcloud_send_data(self,url,values):
		headers = {}
		if self.melcloud_key is not None:
			headers = {'X-MitsContextKey': self.melcloud_key}
		if values is not None:
			values = urlencode(values).encode()
		req = Request(url,values,headers=headers)
		#~ try:
		response = urlopen(req).read().decode()
		return json.loads(response)
		#~ except Request.HTTPError as e:
			#~ Domoticz.Debug('Erreur http: '+str(e.code))
			#~ return False 
    
	def melcloud_login(self):
		post_fields = {'AppVersion': '1.9.3.0', \
					   'Language': '7', \
					   'CaptchaChallange': '', \
					   'CaptchaResponse': '', \
					   'Persist': 'true', \
					   'Email': Parameters["Username"], \
					   'Password': Parameters["Password"]}
					   
		response = self.melcloud_send_data(self.melcloud_urls["login"],post_fields)
		if (response["ErrorId"] == None):
			return response["LoginData"]["ContextKey"]
			Domoticz.Debug("MELCloud Login success. Key ID:"+self.melcloud_key)
		elif (response["ErrorId"] == 1):
			Domoticz.Debug("MELCloud Login fail. Check your username and password")
		else:
			Domoticz.Debug("MELCloud Login fail. Do not known the reason")
		return True
	
	def melcloud_add_unit(self,device,idoffset):
		melcloud_unit = {}
		melcloud_unit['name'] = device["DeviceName"]
		melcloud_unit['id'] = device["DeviceID"]
		melcloud_unit['macaddr'] = device["MacAddress"]
		melcloud_unit['sn'] = device["SerialNumber"]
		melcloud_unit['building_id'] = device["BuildingID"]
		melcloud_unit['power'] = ""
		melcloud_unit['op_mode'] = ""
		melcloud_unit['room_temp'] = ""
		melcloud_unit['set_temp'] = ""
		melcloud_unit['set_fan'] = ""
		melcloud_unit['vaneH'] = ""
		melcloud_unit['vaneV'] = ""
		melcloud_unit['next_comm'] = ""
		melcloud_unit['idoffset'] = idoffset
		self.list_units.append(melcloud_unit)

	def melcloud_update_unit(self,meldevice,device):
		melDevice['power'] = device['Power']
		melDevice['opmode'] = device['OperationMode']
		melDevice['roomtemp'] = device['RoomTemperature']

	def melcloud_get_units_info(self):
		melcloud_list_units = []
		response = self.melcloud_send_data(self.melcloud_urls["list_unit"],None)
		idoffset = 0
		Domoticz.Debug("Find "+str(len(response))+ " buildings")
		for building in response:
			Domoticz.Debug("Find "+str(len(building["Structure"]["Areas"]))+ " areas in building "+building["Name"])
			Domoticz.Debug("Find "+str(len(building["Structure"]["Floors"]))+ " floors in building "+building["Name"])
			Domoticz.Debug("Find "+str(len(building["Structure"]["Devices"]))+ " devices  in building "+building["Name"])

	#Search in devices		
			for device in building["Structure"]["Devices"]:
				self.melcloud_add_unit(device,idoffset)
				idoffset += len(self.list_switchs)
	#Search in areas
			for area in building["Structure"]["Areas"]:
				for device in area["Devices"]:
					self.melcloud_add_unit(device,idoffset)
					idoffset += len(self.list_switchs)
	#Search in floors
			for floor in building["Structure"]["Floors"]:
				for device in floor["Devices"]:
					self.melcloud_add_unit(device,idoffset)
					idoffset += len(self.list_switchs)
				for area in floor["Areas"]:
					for device in area["Devices"]:
						self.melcloud_add_unit(device,idoffset)	
						idoffset += len(self.list_switchs)
		return True
	
	def melcloud_set_power(self,melDeviceID,setPower):
		post_fields = {'Power': setPower, \
						'DeviceID': melDeviceID, \
						'EffectiveFlags': '1', \
						'HasPendingCommand': 'true'}
		jsonResponse = self.melcloud_send_data(self.melcloud_urls["set_unit"],post_fields)
		Domoticz.Debug("Next update for command power: " + jsonResponse["NextCommunication"])
		return True
	 
	def melcloud_set_mode(self,melDeviceID,setMode):
		post_fields = {'Power': "true", \
						'OperationMode': str(setMode), \
						'DeviceID': melDeviceID, \
						'EffectiveFlags': '6', \
						'HasPendingCommand': 'true'}
		jsonResponse = self.melcloud_send_data(self.melcloud_urls["set_unit"],post_fields)
		Domoticz.Debug("Next update for command mode: " + jsonResponse["NextCommunication"])
		return True
	 
	def melcloud_set_fan(self,melDeviceID,setFan):
		post_fields = {'SetFanSpeed': setFan, \
						'DeviceID': melDeviceID, \
						'EffectiveFlags': '8', \
						'HasPendingCommand': 'true'}
		jsonResponse = self.melcloud_send_data(self.melcloud_urls["set_unit"],post_fields)
		Domoticz.Debug("Next update for command fan: " + jsonResponse["NextCommunication"])
		return True
	 
	def melcloud_set_temp(self,melDeviceID,setTemp):
		post_fields = {'SetTemperature': setTemp, \
						'DeviceID': melDeviceID, \
						'EffectiveFlags': '4', \
						'HasPendingCommand': 'true'}
		jsonResponse = self.melcloud_send_data(self.melcloud_urls["set_unit"],post_fields)
		Domoticz.Debug("Next update for command temperature: " + jsonResponse["NextCommunication"])
		return True
	 
	def melcloud_get_unit_info(self,unit):
		url = self.melcloud_urls["unit_info"]+"?id="+str(unit['id'])+"&buildingID="+str(unit['building_id'])
		unit_infos =  self.melcloud_send_data(url,None)
		unit['power'] = unit_infos['Power']
		unit['op_mode'] = unit_infos['OperationMode']
		unit['room_temp'] = unit_infos['RoomTemperature']
		unit['set_temp'] = unit_infos['SetTemperature']
		unit['set_fan'] = unit_infos['SetFanSpeed']
		unit['vaneH'] = unit_infos['VaneHorizontal']
		unit['vaneV'] = unit_infos['VaneVertical']
		unit['next_comm'] = unit_infos['NextCommunication']
		
	def domoticz_update_switchs(self,unit):
		for level, mode in self.domoticz_levels["mode"].items():
			if(mode == unit['op_mode']):
				setModeLevel = level
		for level, pic in self.domoticz_levels["mode_pic"].items():
			if(level == setModeLevel):
				setPicID = pic				
		for level, fan in self.domoticz_levels["fan"].items():
			if(fan == unit['set_fan']):
				setDomFan = level
		for level, temp in self.domoticz_levels["temp"].items():
			if(temp == unit['set_temp']):
				setDomTemp = level
		for level, vaneH in self.domoticz_levels["vaneH"].items():
			if(vaneH == unit['vaneH']):
				setDomVaneH = level
		for level, vaneV in self.domoticz_levels["vaneV"].items():
			if(vaneV == unit['vaneV']):
				setDomVaneV = level
		
		Devices[self.list_switchs[0]["id"]+unit["idoffset"]].Update(1,setModeLevel,setPicID)
		Devices[self.list_switchs[1]["id"]+unit["idoffset"]].Update(1,setDomFan)
		Devices[self.list_switchs[2]["id"]+unit["idoffset"]].Update(1,setDomTemp)
		Devices[self.list_switchs[3]["id"]+unit["idoffset"]].Update(1,setDomVaneH)
		Devices[self.list_switchs[4]["id"]+unit["idoffset"]].Update(1,setDomVaneV)
		Devices[self.list_switchs[5]["id"]+unit["idoffset"]].Update(1,str(unit['room_temp']))
		
	def stringToBase64(self,s):
		return base64.b64encode(s.encode('utf-8')).decode("utf-8")
 

global _plugin
_plugin = BasePlugin()

def onStart():
	global _plugin
	_plugin.onStart()

def onStop():
	global _plugin
	_plugin.onStop()

def onConnect(Status, Description):
	global _plugin
	_plugin.onConnect(Status, Description)

def onMessage(Data, Status, Extra):
	global _plugin
	_plugin.onMessage(Data, Status, Extra)

def onCommand(Unit, Command, Level, Hue):
	global _plugin
	_plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect():
	global _plugin
	_plugin.onDisconnect()

def onHeartbeat():
	global _plugin
	_plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
	for x in Parameters:
		if Parameters[x] != "":
			Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
	Domoticz.Debug("Device count: " + str(len(Devices)))
	for x in Devices:
		Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
		Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
		Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
		Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
		Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
		Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
	return
