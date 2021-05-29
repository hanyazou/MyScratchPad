import asyncio

from bleak import BleakScanner
from bleak.backends._manufacturers import MANUFACTURERS as companyids

__devices__ = {}
found = False

def hex_string(data):
    results = []
    for b in data:
        results.append(hex(b))
    return ' '.join(results)

def detection_handler(device, advertisement_data):
    global __devices__
    global found
    if str(device) not in __devices__.keys():
        __devices__[str(device)] = device
        data = advertisement_data.manufacturer_data
        keys = list(data.keys())
        if 1 <= len(keys) and keys[0] in companyids:
            manufacturer = companyids[keys[0]]
        else:
            manufacturer = 'unknown'
        print('{}: {} {} {}'.format(device.address, manufacturer, device.name, device.rssi))

    data = advertisement_data.service_data
    service = '00000d00-0000-1000-8000-00805f9b34fb'
    if not service in data:
        return
    # print('    {}: {}'.format(service, hex_string(data[service])))
    if len(data[service]) != 6:
        return
    d = data[service]
    remaining_battery = d[2] & 0x7f
    temperature = d[4] & 0x7f
    if not d[4] & 0x80:
        temperature = -temperature
    humidity = d[5] & 0x7f
    print('    {}% {}C {}% {}'.format(remaining_battery, temperature, humidity, device.rssi))

async def asyncRun():
    global found
    scanner = BleakScanner()
    scanner.register_detection_callback(detection_handler)

    await scanner.start()
    print('scanning...')
    while not found:
        await asyncio.sleep(0.2)

    await scanner.stop()
    print('scanning...done')

loop = asyncio.new_event_loop()
loop.run_until_complete(asyncRun())
