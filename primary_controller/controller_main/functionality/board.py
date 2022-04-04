from functionality.communication import Communication
import machine, _thread, time, array

import driver.utils as utils
from driver.uart import UART
from driver.status_led import StatusLed

from functionality.wt901 import WT901

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
  uart1_com = None

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
    cls.uart1_com = Communication()

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

  @classmethod
  def estimate_polling_rate(cls, imus: list, iter_count: int) -> None:
    start = time.time_ns()
    buffer = bytearray(150)
    for _ in range(iter_count):
      index = 0
      for imu in imus:
        index = imu.get_angle_report(buffer, index)
      # print(buffer)
    end = time.time_ns()
    print(buffer)
    print(f"WT901 Pooling Rate: {iter_count * 10e8 / (end - start)} it/s")

  # imus = [WT901(0x50, Board.i2c), WT901(0x52, Board.i2c), WT901(0x54, Board.i2c), WT901(0x50, Board.i2c), WT901(0x52, Board.i2c), WT901(0x54, Board.i2c)]
