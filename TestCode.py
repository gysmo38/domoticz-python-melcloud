
from Domoticz import Device
from Domoticz import Devices
from Domoticz import Images
from Domoticz import Parameters

# your params

Parameters['Mode1'] = '0'
Parameters['Username'] = 'xxxxxxxxxxxxx@xxx.xxx'  # your account mail
Parameters['Password'] = 'xxxxxxxxxx'             # your account password
Parameters['Mode6'] = '0'


def runtest(plugin):

    plugin.onStart()
    plugin.onConnect('Connection', 0, 'Description')
    plugin.melcloud_login()
    plugin.onMessage(None, plugin.melcloud_conn.data)
    print(u'melcloud_state: {}'.format(plugin.melcloud_state))
    plugin.onMessage(None, plugin.melcloud_conn.data)
    plugin.onHeartbeat()
    plugin.onMessage(None, plugin.melcloud_conn.data)
    plugin.onHeartbeat()
    plugin.onMessage(None, plugin.melcloud_conn.data)
    for unit in plugin.list_units:
         plugin.melcloud_get_unit_info(unit)
         plugin.onMessage(None, plugin.melcloud_conn.data)
    plugin.onStop()
