#UART  BLE
#BM70 BLE Module
#This example was inspired by
#https://github.com/hbldh/bleak/blob/master/examples/uart_service.py
#
#Added fixed BLE address for smplicity
#Not used   match_nus_uuid  function

import time
import asyncio
import sys


from bleak import BleakScanner, BleakClient
from bleak.backends.scanner import AdvertisementData
from bleak.backends.device import BLEDevice

ADDRESS = ("9C:95:6E:40:6B:43")   #RNBD451    BLE hard coded address

#Microchip BLE RNBD451 BM70 BLE Characteristics

UART_SERVICE_UUID = "49535343-4C8A-39B3-2F49-511CFF073B7E" #"6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "49535343-8841-43F4-A8D4-ECBE34729BB3" #"6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "49535343-1E4D-4BD9-BA61-23C647249616" #"6E400003-B5A3-F393-E0A9-E50E24DCCA9E"



# All BLE devices have MTU of at least 23. Subtracting 3 bytes overhead, we can
# safely send 20 bytes at a time to any device supporting this service.
UART_SAFE_SIZE = 20


async def uart_terminal():
    """This is a simple "terminal" program that uses the. 
    It reads from stdin and sends each line of data to the
    remote device. Any data received from the device is printed to stdout.
    """
    disconnected_event = asyncio.Event()

    def match_nus_uuid(device: BLEDevice, adv: AdvertisementData):
        # This assumes that the device includes the UART service UUID in the
        # advertising data. This test may need to be adjusted depending on the
        # actual advertising data supplied by the device.
        if UART_SERVICE_UUID.lower() in adv.service_uuids:
            return True

        return True  #False

    #device = await BleakScanner.find_device_by_filter(match_nus_uuid)
    #Used fixed BLE  ddress for simpicity
    
    device = await BleakScanner.find_device_by_address(ADDRESS, timeout=20.0)

    def handle_disconnect(_: BleakClient):
        print("Device was disconnected, goodbye.")
        # cancelling all tasks effectively ends the program
        #for task in asyncio.all_tasks():
            #task.cancel()

    def handle_rx(_: int, data: bytearray):
        print("received:", data)

    async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
        await client.start_notify(UART_TX_CHAR_UUID, handle_rx)

        print("Connected, start typing and press ENTER...")

        loop = asyncio.get_running_loop()

        while True:
            # This waits until you type a line and press ENTER.
            # A real terminal program might put stdin in raw mode so that things
            # like CTRL+C get passed to the remote device.
            data = await loop.run_in_executor(None, sys.stdin.buffer.readline)

            # data will be empty on EOF (e.g. CTRL+D on *nix)
            if not data:
                break

            # some devices, like devices running MicroPython, expect Windows
            # line endings (uncomment line below if needed)
            data = data.replace(b"\n", b"\r\n")
            #time.sleep(1)
            #data ='1234567890'
            await client.write_gatt_char(UART_RX_CHAR_UUID, data)
            print("sent:", data)
            time.sleep(1)
            await client.disconnect()
            time.sleep(2)
            await disconnect_event.wait()
            print("reconnect")
            await client.start_notify(UART_TX_CHAR_UUID, handle_rx)
            


if __name__ == "__main__":
    try:
        asyncio.run(uart_terminal())
    except asyncio.CancelledError:
        # task is cancelled on disconnect, so we ignore this error
        pass
    