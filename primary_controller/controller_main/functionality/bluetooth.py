from micropython import const
import bluetooth
import struct
import time
from machine import Pin
from machine import Timer
import json

_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID16_COMPLETE = const(0x3)
_ADV_TYPE_UUID32_COMPLETE = const(0x5)
_ADV_TYPE_UUID128_COMPLETE = const(0x7)
_ADV_TYPE_UUID16_MORE = const(0x2)
_ADV_TYPE_UUID32_MORE = const(0x4)
_ADV_TYPE_UUID128_MORE = const(0x6)
_ADV_TYPE_APPEARANCE = const(0x19)


def advertising_payload(limited_disc=False, br_edr=False, name=None, services=None, appearance=0):
    payload = bytearray()

    def _append(adv_type, value):
        nonlocal payload
        payload += struct.pack('BB', len(value) + 1, adv_type) + value

    _append(
        _ADV_TYPE_FLAGS,
        struct.pack('B', (0x01 if limited_disc else 0x02) + (0x18 if br_edr else 0x04)),
    )

    if name:
        _append(_ADV_TYPE_NAME, name)

    if services:
        for uuid in services:
            b = bytes(uuid)
            if len(b) == 2:
                _append(_ADV_TYPE_UUID16_COMPLETE, b)
            elif len(b) == 4:
                _append(_ADV_TYPE_UUID32_COMPLETE, b)
            elif len(b) == 16:
                _append(_ADV_TYPE_UUID128_COMPLETE, b)

    # See org.bluetooth.characteristic.gap.appearance.xml
    if appearance:
        _append(_ADV_TYPE_APPEARANCE, struct.pack('<h', appearance))

    return payload


_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
_UART_TX = (
    bluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E'),
    _FLAG_READ | _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E'),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)

msg = ''


class BLESimplePeripheral:
    def __init__(self, ble, name='BLE'):
        self.led = Pin(2, Pin.OUT)
        self.timer1 = Timer(3)
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        self._write_callback = None
        self.timer1.init(period=100, mode=Timer.PERIODIC, callback=lambda t: self.led.value(not self.led.value()))
        self._payload = advertising_payload(name=name, services=[_UART_UUID])
        self._advertise()

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            self.led.on()
            self.timer1.deinit()
            conn_handle, _, _ = data
            print('New connection', conn_handle)
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            self.timer1.init(period=100, mode=Timer.PERIODIC, callback=lambda t: self.led.value(not self.led.value()))
            conn_handle, _, _ = data
            print('Disconnected', conn_handle)
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx and self._write_callback:
                self._write_callback(value)

    def send(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_tx, data)

    def is_connected(self):
        return len(self._connections) > 0

    def _advertise(self, interval_us=500000):
        print('Starting advertising')
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def on_write(self, callback):
        self._write_callback = callback


# Angle = {
#     'Roll': 1.1,
#     'Pitch': 1.2,
#     'Yaw': 1.3
# }

Quaternions = {
    'Q0': 2.1,
    'Q1': 2.2,
    'Q2': 2.3,
    'Q3': 2.4
}

Accelerometer = {
    'X': 3.1,
    'Y': 3.2,
    'Z': 3.3
}

# Gyroscope = {
#     'X': 4.1,
#     'Y': 4.2,
#     'Z': 4.3
# }

# Magnetometer = {
#     'X': 5.1,
#     'Y': 5.2,
#     'Z': 5.3
# }

frame_raw = {
    # 'Angle': Angle,
    'Quaternions': Quaternions,
    'Accelerometer': Accelerometer,
    # 'Gyroscope': Gyroscope,
    # 'Magnetometer': Magnetometer
}

frame = json.dumps(frame_raw)


def encrypt(text, key=0):
    if not isinstance(text, str):
        raise TypeError('{} should be a type string'.format(text))
    if not isinstance(key, int):
        raise TypeError('{} should be of type int'.format(key))
    return ''.join([chr((ord(something) + key) % 128) for something in text])


def demo():
    ble = BLESimplePeripheral(bluetooth.BLE())

    def on_rx(v):
        ble.send(v)

    ble.on_write(on_rx)

    while True:
        if ble.is_connected():
            ble.send(encrypt(frame, 7))
            ble.send('\r\n')
        time.sleep_ms(1000)


if __name__ == '__main__':
    demo()