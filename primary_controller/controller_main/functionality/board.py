import machine, _thread, time, array

import driver.utils as utils
from driver.status_led import StatusLed

from functionality.wt901 import WT901
from functionality.communication import Communication as Com

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
  uart1_com: Com = None

  # i2c
  i2c = None

  class State:
    IDLE = 0
    IMU = 1

  # controller state
  state = None

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
    cls.uart1_com = Com()

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
  def i2c_scan(cls) -> list:
    """ Get all I2C device addresses connected to this device """
    return cls.i2c.scan()

  @classmethod
  def estimate_polling_rate(cls, imus: list, count: int, quaternion: bool=False) -> float:
    buffer = bytearray(200)
    iter_count = count // len(imus)
    if quaternion:
      start = time.time_ns()
      for _ in range(iter_count):
        index = 0
        for imu in imus:
          index = imu.get_quaternion_report(buffer, index)
      end = time.time_ns()
    else:
      start = time.time_ns()
      for _ in range(iter_count):
        index = 0
        for imu in imus:
          index = imu.get_angle_report(buffer, index)
      end = time.time_ns()
    return iter_count * len(imus) * 10e8 / (end - start)

  @classmethod
  def event_loop(cls):
    cls.state = cls.State.IDLE
    while True:
      if cls.state == cls.State.IDLE: # idle
        available_categories = cls.uart1_com.pending_categories()
        if Com.IMU in available_categories:
          cls.state = cls.State.IMU
      elif cls.state == cls.State.IMU: # IMU operations
        msg = cls.uart1_com.read(Com.IMU)
        if msg == Com.ADDRESS: # query I2C address
          report = ""
          addresses = cls.i2c_scan()
          for address in addresses:
            report += str(address) + ","
          cls.uart1_com.send(Com.CONFIRM, report[:-1])
          cls.state = cls.State.IDLE
        elif msg == Com.SPEED: # imu polling speed
          cls.status_led.show_info()
          time.sleep_ms(100)
          WT901.detect_imus(cls.i2c)
          if len(WT901.detected_imus) == 0: # No IMUs available
            cls.uart1_com.send(Com.REJECT, f"No IMUs detected")
          else:
            imus = list(WT901.detected_imus.values())
            try:
              cls.uart1_com.send(Com.CONFIRM, 
                  f"E{cls.estimate_polling_rate(imus, 4000)},Q{cls.estimate_polling_rate(imus, 4000, True)}")
            except Exception:
              cls.uart1_com.send(Com.REJECT, f"IMU disconnected during process")
          cls.state = cls.State.IDLE
        elif msg == Com.BULK: # setting imu position
          cls.uart1_com.send(Com.CONFIRM, Com.BULK)
          WT901.detect_imus(cls.i2c)
          WT901.deinit_all_imus()
          addresses = WT901.detected_imus.keys()
          while True: # while the peripheral still sending configs
            msg = cls.uart1_com.blocking_read(Com.IMU)
            if msg == Com.TERMINATE:
              cls.uart1_com.send(Com.TERMINATE, Com.BULK)
              cls.state = cls.State.IDLE
              break
            preprocess = msg.split(b',')
            address = int(preprocess[0].decode())
            position = preprocess[1].decode()
            if address not in addresses:
              warning_msg = f"Invalid WT901 I2C Address <{hex(address)}>"
              utils.EXPECT_TRUE(False, warning_msg)
              cls.uart1_com.send(Com.REJECT, warning_msg)
              continue
            if position not in WT901.avail_positions:
              warning_msg = f"Invalid WT901 I2C Position <{position}>"
              utils.EXPECT_TRUE(False, warning_msg)
              cls.uart1_com.send(Com.REJECT, warning_msg)
              continue
            if position in WT901.inited_positions:
              warning_msg = f"Duplicated WT901 I2C Position <{position}>"
              utils.EXPECT_TRUE(False, warning_msg)
              cls.uart1_com.send(Com.REJECT, warning_msg)
              continue
            WT901.detected_imus[address].assign_position(position)
            cls.uart1_com.send(Com.CONFIRM, "")
        elif msg == Com.BEGIN: # begin operation
          cls.uart1_com.send(Com.CONFIRM, Com.BEGIN)
          while True:
            time.sleep_ms(100)
            
      time.sleep_ms(100)
