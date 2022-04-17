import micropython, bluetooth, struct

import driver.utils as utils

# advertising
ADV_TYPEFLAGS             = micropython.const(0x01)
ADV_TYPE_NAME             = micropython.const(0x09)
ADV_TYPE_UUID16_COMPLETE  = micropython.const(0x3)
ADV_TYPE_UUID32_COMPLETE  = micropython.const(0x5)
ADV_TYPE_UUID128_COMPLETE = micropython.const(0x7)
ADV_TYPE_UUID16_MORE      = micropython.const(0x2)
ADV_TYPE_UUID32_MORE      = micropython.const(0x4)
ADV_TYPE_UUID128_MORE     = micropython.const(0x6)
ADV_TYPE_APPEARANCE       = micropython.const(0x19)
# irq
IRQ_CENTRAL_CONNECT    = micropython.const(1)
IRQ_CENTRAL_DISCONNECT = micropython.const(2)
IRQ_GATTS_WRITE        = micropython.const(3)
# flags
FLAG_READ              = micropython.const(0x0002)
FLAG_WRITE_NO_RESPONSE = micropython.const(0x0004)
FLAG_WRITE             = micropython.const(0x0008)
FLAG_NOTIFY            = micropython.const(0x0010)
# uart
UART_UUID    = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
UART_TX_UUID = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
UART_RX_UUID = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
UART_TX      = (UART_TX_UUID, FLAG_READ | FLAG_NOTIFY)
UART_RX      = (UART_RX_UUID, FLAG_WRITE | FLAG_WRITE_NO_RESPONSE)
UART_SERVICE = (UART_UUID, (UART_TX, UART_RX))

class BLEPeripheral:
  config_path = "data"
  default_config_storage = "ble_name.settings"
  default_ble_name = "BLECtrl"

  def __init__(self, ble):
    self.__ble = ble
    self.__ble.active(True)
    self.__ble.irq(self.__irq)
    ((self.__handle_tx, self.__handle_rx),) = self.__ble.gatts_register_services((UART_SERVICE,))

    self.__connection = None
    self.__write_callback = None

    try:
      with open(f"{BLEPeripheral.config_path}/{BLEPeripheral.default_config_storage}") as f:
        self.__name = f.read()
    except Exception:
      self.__name = BLEPeripheral.default_ble_name
    self.__adv_payload = self.get_advertising_payload(name=self.__name, services=[UART_UUID])
    # start advertising
    self.__advertise()

  def get_current_advertise_name(self) -> str:
    return self.__name
  
  def change_advertise_name(self, name: str) -> None:
    self.__name = name
    with open(f"{BLEPeripheral.config_path}/{BLEPeripheral.default_config_storage}", "w") as f:
      f.write(self.__name)
    # change advertise name
    self.__advertise(None)
    self.__adv_payload = self.get_advertising_payload(name=self.__name, services=[UART_UUID])
    # start advertising
    self.__advertise()
    return

  def get_advertising_payload(limited_disc=False, br_edr=False, name=None, services=None, appearance=0):
    payload = bytearray()

    def append_to_payload(adv_type, value):
      nonlocal payload
      payload += struct.pack("BB", len(value) + 1, adv_type) + value

    append_to_payload(
      ADV_TYPEFLAGS,
      struct.pack("B", (0x01 if limited_disc else 0x02) + (0x18 if br_edr else 0x04))
    )

    if name:
      append_to_payload(ADV_TYPE_NAME, name)
    if services:
      for uuid in services:
        b = bytes(uuid)
        if len(b) == 2:
          append_to_payload(ADV_TYPE_UUID16_COMPLETE, b)
        elif len(b) == 4:
          append_to_payload(ADV_TYPE_UUID32_COMPLETE, b)
        elif len(b) == 16:
          append_to_payload(ADV_TYPE_UUID128_COMPLETE, b)
    # See org.bluetooth.characteristic.gap.appearance.xml
    if appearance:
      append_to_payload(ADV_TYPE_APPEARANCE, struct.pack("<h", appearance))

    return payload

  def __irq(self, event, data):
    # Track connections so we can send notifications
    if event == IRQ_CENTRAL_CONNECT:
      conn_handle, _, _ = data
      print("Bluetooth new connection", conn_handle)
      self.__connection = conn_handle
      # Stop advertising 
      self.__advertise(None)
    elif event == IRQ_CENTRAL_DISCONNECT:
      conn_handle, _, _ = data
      print("Bluetooth Disconnected", conn_handle)
      self.__connection = None
      # Start advertising again to allow a new connection
      self.__advertise()
    elif event == IRQ_GATTS_WRITE:
      conn_handle, value_handle = data
      value = self.__ble.gatts_read(value_handle)
      if value_handle == self.__handle_rx and self.__write_callback:
          self.__write_callback(value)

  def send(self, data):
    if self.__connection != None:
      self.__ble.gatts_notify(self.__connection, self.__handle_tx, data)

  def is_connected(self):
    return self.__connection != None

  def __advertise(self, interval_us=int(1e6)):
    self.__ble.gap_advertise(interval_us, adv_data=self.__adv_payload)

  def on_write(self, callback):
    self.__write_callback = callback


def encrypt(text, key=0):
  if not isinstance(text, str):
    raise TypeError("{} should be a type string".format(text))
  if not isinstance(key, int):
    raise TypeError("{} should be of type int".format(key))
  return "".join([chr((ord(something) + key) % 128) for something in text])
