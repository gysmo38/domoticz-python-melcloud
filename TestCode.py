
import json
from Domoticz import Connection
from Domoticz import Device
from Domoticz import Devices
from Domoticz import Parameters

# your params

Parameters['Mode1'] = '0'
Parameters['Username'] = 'xxxxxxxxxxxxx@xxx.xxx'  # your account mail
Parameters['Password'] = 'xxxxxxxxxx'             # your account password
Parameters['Mode6'] = 'Debug'                     # Debug or Normal


def runtest(plugin):

    plugin.onStart()

    # First Heartbeat
    plugin.onHeartbeat()

    # Second Heartbeat
    plugin.onHeartbeat()

    exit(0)
