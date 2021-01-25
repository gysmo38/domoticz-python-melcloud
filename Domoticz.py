import requests
import json
import chardet

Parameters = {"Mode5": "Debug"}
Devices = {}
Images = {}
debug_Level = 0


def Debug(textStr):
    if debug_Level >= 62:
        print(u'Debug : {}'.format(textStr))


def Error(textStr):
    print(u'Error : {}'.format(textStr))


def Status(textStr):
    print(u'Status : {}'.format(textStr))


def Log(textStr):
    print(u'Log : {}'.format(textStr))


def Debugging(value):
    global debug_Level
    debug_Level = int(value)
    Log(u'debug_Level: {}'.format(debug_Level))


def Heartbeat(value):
    pass


def UpdateDevice(num, Image='', nValue=0, sValue=''):
    pass


class Connection:

    @property
    def Name(self):
        return self._name

    @property
    def data(self):
        return self._data

    @property
    def bp(self):
        return self._bp

    @bp.setter
    def bp(self, value):
        self._bp = value

    def __init__(self, Name="", Transport="", Protocol="", Address="", Port=""):
        self._name = Name
        self._transport = Transport
        self._ptrotocol = Protocol.lower()
        self._address = Address
        self._port = Port
        self._requestUrl = u'{}://{}:{}'.format(self._ptrotocol, self._address, self._port)
        self._data = None
        self._bp = None

    def Connect(self):
        Debug(u'requestUrl: {}'.format(self._requestUrl))
        self._bp.onConnect('Connection', 0, 'Description')
        return None

    def Connecting(self):
        return True

    def Connected(self):
        return True

    def Send(self, params):
        params['Headers']['accept'] = 'application/json'
        if params['Verb'] == 'POST':
            url = u'{}/{}'.format(self._requestUrl, params['URL'])
            r = requests.post(url, data=params['Data'], headers=params['Headers'])

            # build onMessage params
            data = {}
            data["Status"] = r.status_code
            data["Data"] = bytes(json.dumps(r.json()), 'utf-8')

            r.encoding = 'utf-8'
            self._data = {}
            self._data["Status"] = r.status_code
            self._data["Data"] = bytes(json.dumps(r.json()), 'utf-8')

            self.bp.onMessage(self, data)
            return
        elif params['Verb'] == 'GET':
            url = u'{}/{}'.format(self._requestUrl, params['URL'])
            r = requests.get(url, data=params['Data'], headers=params['Headers'])

            # build onMessage params and onMessage call
            data = {}
            data["Status"] = r.status_code
            data["Data"] = bytes(json.dumps(r.json()), 'utf-8')
            self.bp.onMessage(self, data)

            r.encoding = 'utf-8'
            self._data = {}
            self._data["Status"] = r.status_code
            self._data["Data"] = bytes(json.dumps(r.json()), 'utf-8')
        return True


class Device:
    global Devices

    @property
    def nValue(self):
        return self._nValue

    @nValue.setter
    def nValue(self, value):
        self._nValue = value

    @property
    def sValue(self):
        return self._sValue

    @sValue.setter
    def nValue(self, value):
        self._sValue = value

    @property
    def ID(self):
        return self._id

    @ID.setter
    def ID(self, value):
        self._id = value

    @property
    def DeviceID(self):
        return self._device_id

    @DeviceID.setter
    def DeviceID(self, value):
        self._device_id = value

    @property
    def Typename(self):
        return self._typeName

    @Typename.setter
    def Typename(self, value):
        self._typeName = value

    @property
    def Name(self):
        return self._name

    @Name.setter
    def Name(self, value):
        self._name = value

    @property
    def LastLevel(self):
        return 0

    @property
    def Image(self):
        return self._image

    @Image.setter
    def Image(self, value):
        self._image = value

    def __init__(self, Name="", Unit=0, TypeName="", Used=0, Type=0, Subtype=0, Image="", Options=""):
        self._nValue = 0
        self._sValue = ''
        self._name = Name
        self._unit = Unit
        self._typeName = TypeName
        self._used = Used
        self._type = Type
        self._subtype = Subtype
        self._image = Image
        self._options = Options
        self._id = len(Devices.keys()) + 101
        self._device_id = len(Devices.keys()) + 4001
        Debug(u'ID: {}'.format(self._id))

    def Update(self, nValue=0, sValue='', Options='', Image=None):
        self._nvalue = nValue
        self._svalue = sValue
        self._image = Image
        txt_log = self.__str__()
        Log(txt_log)

    def __str__(self):
        txt_log = u'Info - Update device Name : {} nValue : {} sValue : {} Options : {} Image: {}\n'
        txt_log = txt_log.format(self._name, self._nvalue, self._svalue, self._options, self._image)
        return txt_log

    def Create(self):
        self._id = len(Devices.keys()) + 101
        self._device_id = len(Devices.keys()) + 4001
        txt_log = u'Info - Create device : \n\tName : {}\n\tUnit : {}\n\tTypeName : {}\n\tUsed : {}\n\tType : {}\n\tSubtype : {}'
        txt_log += u'\n\tImage : {}\n\tOptions : {}'
        txt_log = txt_log.format(self._name, self._unit, self._typeName,
                                 self._used, self._type, self._subtype, self._image, self._options)
        Log(txt_log)
        Devices[len(Devices.keys())] = self
        Debug(u'ID: {}'.format(self._id))


class Image:

    @property
    def Name(self):
        return self._name

    @Name.setter
    def ID(self, value):
        self._name = value

    @property
    def Base(self):
        return self._base

    @Base.setter
    def ID(self, value):
        self._base = value

    @property
    def ID(self):
        return self._filename

    @ID.setter
    def ID(self, value):
        self._filename = value

    def __init__(self, Filename=""):
        self._filename = Filename
        self._name = Filename
        self._base = Filename

    def Create(self):
        Images[self._filename.split(u' ')[0]] = self
