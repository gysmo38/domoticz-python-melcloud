
import json
from Domoticz import Connection
from Domoticz import Device
from Domoticz import Devices
from Domoticz import Parameters

# your params

Parameters['Mode1'] = '0'
Parameters['Username'] = 'xxxxxxxxxxxxx@xxx.xxx'  # your account mail
Parameters['Password'] = 'xxxxxxxxxx'             # your account password
Parameters['Mode6'] = '0'


def runtest(plugin):

    # fake onStart
    plugin.melcloud_conn = Connection(Name="MELCloud", Transport="TCP/IP",
                                      Protocol="HTTPS", Address=plugin.melcloud_baseurl,
                                      Port=plugin.melcloud_port)
    plugin.melcloud_conn.bp = plugin
    plugin.melcloud_conn.Connect()

    # First Heartbeat
    plugin.onHeartbeat()

    # Second Heartbeat
    plugin.onHeartbeat()

    exit(0)
