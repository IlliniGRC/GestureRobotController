import machine, _thread

import driver.utils as utils
from driver.uart import UART
from driver.status_led import StatusLed

def uart1_rx_callback() -> None:
  """ Callback function that called every time uart1 received message(s) """
  Board.uart1_pending_lock.acquire()
  Board.uart1_pending = True
  Board.uart1_pending_lock.release()

class Board:
  """ Have only classmethods, interfacing high-level functionalities with lower-level facilities """
  # status led
  status_led = None

  # uart1
  uart1 = None
  uart1_queue = None
  uart1_pending = False
  uart1_pending_lock = _thread.allocate_lock()

  # i2c
  i2c = None

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
    cls.uart1 = UART(1, tx = 18, rx = 17)
    cls.uart1.register_rx_callback(uart1_rx_callback)
    # uart begin earlier for receiving message from Main
    cls.uart1_queue = cls.uart1.begin()

    cls.i2c = machine.SoftI2C(sda = machine.Pin(4), scl = machine.Pin(5))

  @classmethod
  def begin_operation(cls) -> None:
    """ Begin operation of all facilities """
    pass

  @classmethod
  def end_operation(cls) -> None:
    """ End operation of all facilities """
    cls.uart1.finish()

  @classmethod
  def is_uart1_pending(cls) -> bool:
    """ Whether uart1 have pending messages 
        `returns`: whether uart1 have pending messages """
    return cls.uart1_pending

  @classmethod
  def get_uart1_message(cls) -> str:
    """ Get one of the pending uart message
        `returns`: first pending uart message, None if no pending messages """
    cls.uart1_pending_lock.acquire()
    message = cls.uart1_queue.dequeue()
    if cls.uart1_queue.is_empty():
      cls.uart1_pending = False
    cls.uart1_pending_lock.release()
    return message

  @classmethod
  def get_all_uart1_message(cls) -> list:
    """ Get all of the pending uart messages
        `returns`: list of pending uart messages """
    cls.uart1_pending_lock.acquire()
    messages = []
    while not cls.uart1_queue.is_empty():
      messages.append(cls.uart1_queue.dequeue())
    cls.uart1_pending = False
    cls.uart1_pending_lock.release()
    return messages
