#!/usr/bin/python3

import asyncio
from bleak import BleakScanner
from bleak import BleakClient

funcs = [ "DC", "AC", "DC", "AC", "Ohm", "Cap", "Hz", "Duty" , "Temp", "Temp", "Diode", "Cont", "hFE", "", "", "" ]
units = [ "V",  "V",  "A",  "A",  "Ohm", "F",   "Hz", "%" ,    "℃",     "℉",     "V",     "Ohm",        "hFE", "", "", "" ]
scales = [ "", "n", "u", "m", "", "k", "M" "" ]
readtypes = [ "Hold", "Delta", "Auto", "Low Battery", "Min", "Max" ]

def detection_callback(device, advertisement_data):
    print(device.address, "RSSI:", device.rssi, advertisement_data)

def notification_handler(sender, data):
    d0 = (data[1] << 8| data[0])
    d1 = (data[3] << 8| data[2])
    d2 = (data[5] << 8| data[4])
    func = (d0 >> 6) & 0xf
    scale = (d0 >> 3) & 0x7
    decimal = (d0 >> 0) & 0x3
    if d2 & 0x8000:
        value = -(d2 & 0x7fff)
    else:
        value = d2
    # print("{0:04x} {1:04x} {2:04x} ".format(d0, d1, d2), end='')
    print("{0:>5} {1:10.4f} {2}{3}".format(funcs[func], value / (10 ** decimal), scales[scale], units[func]), end='')
    for i in range(len(readtypes)):
        if d1 & (1 << i):
            print(" {}".format(readtypes[i]), end='')
    print("")

async def run(loop):
    scanner = BleakScanner()
    # scanner.register_detection_callback(detection_callback)
    await scanner.start()
    await asyncio.sleep(1.0)
    await scanner.stop()
    devices = await scanner.get_discovered_devices()

    device = None
    for d in devices:
        if d.name == "BDM":
            device = d

    if device is None:
        return

    # print(d.address, d.__dict__)
    client = BleakClient(device, loop=loop)
    if not await client.connect():
        return
    print("Connected to {} {}".format(device.address, device.name))

    print("Services and Characteristics:")
    services = await client.get_services()
    value_uuid = None
    for s in services:
        print("  ", s.uuid, s.description)
        for c in s.characteristics:
            print("    ", c.uuid, c.description)
            if s.uuid.startswith("0000fff0") and c.uuid.startswith("0000fff4"):
                value_uuid = c.uuid

    if value_uuid is None:
        return

    # value = await client.read_gatt_char(value_uuid)
    # print("value=", ''.join('{:02x}'.format(x) for x in value))
    await client.start_notify(value_uuid, notification_handler)
    while True:
        await asyncio.sleep(30.0)
    await client.stop_notify(value_uuid)

loop = asyncio.get_event_loop()
loop.run_until_complete(run(loop))
