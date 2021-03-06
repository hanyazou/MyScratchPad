import asyncio

from bleak import BleakScanner
from bleak.backends._manufacturers import MANUFACTURERS as companyids

class BleReader:
    @staticmethod
    def hex_string(data):
        results = []
        for b in data:
            results.append(hex(b))
        return ' '.join(results)

    def __init__(self):
        self.__devices = {}
        self.__found = False
        self.__services = {}

    def detection_handler(self, device, advertisement_data):
        if str(device) not in self.__devices.keys():
            # print('### new device {} {}'.format(device, advertisement_data))
            self.__devices[str(device)] = { 'device': device, 'instances': [] }
            for service in advertisement_data.service_uuids:
                # print('search {} in {}'.format(service, list(self.__services.keys())))
                service = service.lower()
                if not service in self.__services:
                    continue
                plugin = self.__services[service][0]['class']
                print('    {}: serivice={}, plugin={}, connect={}'.format(device, service, plugin.name, plugin.services[service]['connect']))

            data = advertisement_data.manufacturer_data
            keys = list(data.keys())
            if 1 <= len(keys) and keys[0] in companyids:
                manufacturer = companyids[keys[0]]
            else:
                manufacturer = 'unknown'

            print('{}: {} {} {}'.format(device.address, manufacturer, device.name, device.rssi))

        for service in advertisement_data.service_data:
            # print('service={} {}'.format(service, self.__services.keys()))
            if service in self.__services:
                data = advertisement_data.service_data[service]
                print('{}: {} {}'.format(device.address,
                                         self.__services[service][0]['class'].name,
                                         self.hex_string(data)))
                self.__services[service][0]['class'].update(
                    device, device.address, service, None, data)

    async def asyncRun(self, loop):
        scanner = BleakScanner()
        scanner.register_detection_callback(self.detection_handler)

        await scanner.start()
        print('scanning...')
        while not self.__found:
            await asyncio.sleep(0.2)

        await scanner.stop()
        print('scanning...done')

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.asyncRun(loop))

    def install_plugin(self, plugin):
        for service in plugin.services.keys():
            print('install plugin={}, service={}'.format(plugin.__name__, plugin.services[service]))
            if not service in self.__services:
                self.__services[service] = []
            self.__services[service].append({ 'class': plugin, })

class BlePlugin:
    name = 'SwitchBot'
    services = {
        '00000d00-0000-1000-8000-00805f9b34fb': {
            'connect': False,
        },
    }

    @staticmethod
    def update(device, address, service, characteristic, data):
        if len(data) != 6:
            return
        remaining_battery = data[2] & 0x7f
        temperature = data[4] & 0x7f
        if not data[4] & 0x80:
            temperature = -temperature
        humidity = data[5] & 0x7f
        print('    {}% {}C {}% {}'.format(remaining_battery, temperature, humidity, device.rssi))

class BlePlugin2:
    name = 'FS9721-LP3'
    services = {
        '0000ffb0-0000-1000-8000-00805f9b34fb': {
            'connect': True,
        },
    }

    def update(self, device, address, service, characteristic, data):
        print('    PLUGIN: {}'.format(self.name))

__plugins__ = [
    BlePlugin,
    BlePlugin2,
]

br = BleReader()

for plugin in __plugins__:
    br.install_plugin(plugin)

br.run()
