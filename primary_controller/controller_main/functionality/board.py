import machine, time, bluetooth, json

import driver.utils as utils
from driver.status_led import StatusLed

from functionality.wt901 import WT901
from functionality.bluetooth import BLEPeripheral as ble
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

  # uart2
  uart2 = machine.UART(2, 115200, tx=12, rx=14)

  # uart1
  uart1_com: Com = None

  # i2c
  i2c = None

  # bluetooth socket
  ble = None
  polling_buffer = bytearray(200)

  class State:
    IDLE = 0
    IMU  = 1
    BLUETOOTH  = 2

  # controller state
  state = None

  # operation state
  in_operation = False

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

    cls.ble = ble(bluetooth.BLE())
    cls.ble.on_write(cls.ble_rx_callback)

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
  def ble_rx_callback(cls, msg) -> None:
    print(len(msg))
    cls.uart1_com.send(Com.BLUETOOTH, *msg.split(b"\n"))

  @classmethod
  def estimate_polling_rate(cls, imus: list, count: int, quaternion: bool=False) -> float:
    buffer = bytearray(400)
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
  def send_imu_info_through_uart2(cls, timer: machine.Timer):
    imu: WT901
    cls.status_led.change_state(True)
    index = 0
    for imu in cls.imus:
      index = imu.get_quatacc_report(cls.polling_buffer, index)
    cls.polling_buffer[index:index + 2] = b"\r\n" # termination sequence
    cls.uart2.write(cls.polling_buffer[0:index + 2])
    cls.status_led.change_state(False)

  @classmethod
  def send_imu_info_through_bluetooth(cls, timer: machine.Timer):
    if not cls.ble.is_connected():
      return
    imu: WT901
    cls.status_led.change_state(True)
    index = 0
    for imu in cls.imus:
      index = imu.get_quatacc_report(cls.polling_buffer, index)
    cls.polling_buffer[index:index + 2] = b"\r\n" # termination sequence
    cls.ble.send(cls.polling_buffer[0:index + 2])
    cls.status_led.change_state(False)

  @classmethod
  def query_i2c_addr(cls) -> None:
    report = ""
    addresses = cls.i2c_scan()
    for address in addresses:
      report += str(address) + ","
    cls.uart1_com.send(Com.CONFIRM, report[:-1])

  @classmethod
  def query_imu_polling_speed(cls) -> None:
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

  @classmethod
  def set_imu_positions(cls):
    cls.uart1_com.send(Com.CONFIRM, Com.BULK)
    WT901.detect_imus(cls.i2c)
    WT901.deinit_all_imus()
    addresses = WT901.detected_imus.keys()
    while True: # while the peripheral still sending configs
      msg = cls.uart1_com.blocking_read(Com.IMU)
      if msg == Com.TERMINATE:
        cls.uart1_com.send(Com.CONFIRM, Com.TERMINATE)
        break
      preprocess = msg.split(b",")
      position = preprocess[0].decode()
      address = int(preprocess[1].decode())
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
      cls.uart1_com.send(Com.CONFIRM, "")
      WT901.detected_imus[address].assign_position(position)

  @classmethod
  def change_bluetooth_advertise_name(cls) -> None:
    cls.uart1_com.send(Com.CONFIRM, Com.BULK)
    while True: # while the peripheral still sending configs
      name = cls.uart1_com.blocking_read(Com.BLUETOOTH).decode()
      if len(name) <= 8 and len(name) >= 1:
        cls.ble.change_advertise_name(name)
        cls.uart1_com.send(Com.CONFIRM, Com.TERMINATE)
        break
      cls.uart1_com.send(Com.REJECT, 
          f"Bluetooth name must have a length between 1 and 8, current name <{name}> has length {len(name)}")

  @classmethod
  def polling_send_loop(cls):
    cls.uart1_com.send(Com.CONFIRM, Com.BEGIN)
    cls.imus = list(WT901.inited_positions.values())
    timer = machine.Timer(1)
    timer.init(mode=machine.Timer.PERIODIC, period=50, callback=cls.send_imu_info_through_bluetooth)
    cls.in_operation = True
    while True:
      msg = cls.uart1_com.blocking_read(Com.IMU)
      if msg == Com.TERMINATE:
        timer.deinit()
        cls.uart1_com.send(Com.CONFIRM, Com.TERMINATE)
        break
    cls.in_operation = False

  @classmethod
  def event_loop(cls):
    cls.state = cls.State.IDLE
    while True:
      if cls.state == cls.State.IDLE: # idle
        available_categories = cls.uart1_com.pending_categories()
        if Com.IMU in available_categories:
          cls.state = cls.State.IMU
        elif Com.BLUETOOTH in available_categories:
          cls.state = cls.State.BLUETOOTH
      elif cls.state == cls.State.IMU: # IMU operations
        msg = cls.uart1_com.read(Com.IMU)
        if msg == Com.ADDRESS: # query I2C address
          cls.query_i2c_addr()
        elif msg == Com.SPEED: # imu polling speed
          cls.query_imu_polling_speed()
        elif msg == Com.BULK: # setting imu position
          cls.set_imu_positions()
        elif msg == Com.BEGIN: # begin operation
          cls.polling_send_loop()
        cls.state = cls.State.IDLE
      elif cls.state == cls.State.BLUETOOTH:
        msg = cls.uart1_com.read(Com.BLUETOOTH)
        if msg == Com.ADDRESS:
          pass
        elif msg == Com.NAME:
          cls.uart1_com.send(Com.CONFIRM, cls.ble.get_current_advertise_name())
        elif msg == Com.CONNECTED:
          if Board.ble.is_connected():
            cls.uart1_com.send(Com.CONFIRM, "")
          else:
            cls.uart1_com.send(Com.REJECT, "Bluetooth not connected")
        elif msg == Com.BULK:
          cls.change_bluetooth_advertise_name()
        cls.state = cls.State.IDLE

      time.sleep_ms(100)
