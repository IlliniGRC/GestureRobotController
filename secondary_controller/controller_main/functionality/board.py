import machine, time, bluetooth, json

import driver.utils as utils
from driver.status_led import StatusLed

from functionality.bluetooth import BLEPeripheral as ble

class Board:
  """ Have only classmethods, interfacing high-level functionalities with lower-level facilities """
  # status led
  status_led = None

  # uart1 
  uart1 = None
  rx_buffer = bytearray(200)

  # bluetooth socket
  ble = None

  class State:
    IDLE = 0
    OPERATION = 1

  # controller state
  state = None

  # operation state
  in_operation = False

  HOLD = b"hld"
  CHASSIS = b"chs"
  GIMBAL = b"gim"
  SHOOTER = b"sho"

  @classmethod
  def main_init(cls) -> None:
    """ Initializations that fulfill basic requirements for system to operate """
    # set processor speed to 240MHz
    #   available freq: [20MHz, 40MHz, 80MHz, 160MHz, 240MHz]
    machine.freq(240000000)

    # Status led initialization must be the first
    cls.status_led = StatusLed()


  @classmethod
  def auxiliary_init(cls) -> None:
    """ Initializations that fulfill full requirements for system to operate """
    cls.uart1 = machine.UART(1, 115200, tx=22, rx=23)

    cls.ble = ble(bluetooth.BLE())
    cls.ble.on_write(cls.ble_rx_callback)

  @classmethod
  def hold_detect(cls, timer: machine.Timer):
    if cls.in_operation:
      cls.in_operation = False
    else:
      cls.uart1.write(cls.HOLD + b"|\n")

  @classmethod
  def ble_rx_callback(cls, msg: bytes) -> None:
    cls.in_operation = True
    Board.status_led.change_state(True)
    print(msg)
    cls.uart1.write(msg)
    Board.status_led.change_state(False)

  @classmethod
  def event_loop(cls):
    timer = machine.Timer(2)
    timer.init(mode=machine.Timer.PERIODIC, period=500, callback=cls.hold_detect)

    cls.state = cls.State.IDLE
    while True:
      if cls.state == cls.State.IDLE: # idle
        Board.status_led.change_state(True)
        if cls.ble.is_connected():
          cls.state = cls.State.OPERATION
      elif cls.state == cls.State.OPERATION: # Bluetooth operations
        Board.status_led.change_state(False)
        while True:
          msg_length = cls.uart1.readinto(cls.rx_buffer)
          if not cls.ble.is_connected():
            break
          if msg_length != None and msg_length != 0:
            cls.rx_buffer[msg_length] = b"\n"
            cls.ble.send(cls.rx_buffer[:msg_length + 1])
          time.sleep_ms(100)
        cls.state = cls.State.IDLE
      time.sleep_ms(100)
