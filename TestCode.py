
import json
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
         Data = plugin.melcloud_conn.data
         Status = int(Data["Status"])
         if (Status == 200):
             strData = Data["Data"].decode("utf-8", "ignore")
             response = json.loads(strData)
             if(plugin.melcloud_state == "UNIT_INFO"):
                 print()
                 print("Update unit {0} information.".format(unit['name']))
                 for k, v in response.items():
                     if k == 'WeatherObservations':
                         print('WeatherObservations')
                         for wo in v:
                             print()
                             for wok, wov in wo.items():
                                 print("\t{} :\t{}".format(wok, wov))
                         print()
                     else:
                         print("{} :\t{}".format(k, v))
                 print()
                 plugin.onMessage(None, plugin.melcloud_conn.data)
    plugin.onStop()
