import machine, _thread, time

import driver.utils as utils
from driver.uart import UARTCallback


class Communication:
  """ Communication through UART1 between main and peripheral controller. 
      A control words is formulated as follows:
      <ControlCommand><COMMAND_SPLIT><ControlDestination><INTER_COMMAND_SPLIT> """
  # Control characters
  INTER_COMMAND_SPLIT = b'\n'
  COMMAND_SPLIT = b'|'
  # Control commands
  BOOT_UP = b'boot'
  START = b'start'
  IMU = b'imu'
  BLUETOOTH = b'ble'
  CONFIRM = b'con'
  REJECT = b'rej'
  WARNING = b'warn'
  FATAL = b'ERR'
  # Control destinations
  BEGIN = b'begin'
  TERMINATE = b'terminate'
  BULK = b'bulk'
  ADDRESS = b'addr'
  SPEED = b'speed'
  NAME = b'name'

  def __init__(self) -> None:
    self.__uart1 = UARTCallback(1, tx=18, rx=17)
    self.__uart1.begin(self.__uart1_rx_callback)
    self.__message_queue = {}
    self.__message_lock = _thread.allocate_lock()
    self.__pending_categories = set()

  def __uart1_rx_callback(self, uart1: machine.UART) -> None:
    """ Callback function that called every time uart1 received message(s) """
    self.__message_lock.acquire()
    messages = uart1.read()
    if messages == None:
      self.__message_lock.release()
      return
    for message in messages.strip().split(Communication.INTER_COMMAND_SPLIT):
      preprocess = message.split(Communication.COMMAND_SPLIT, 1)
      if len(preprocess) == 1:
        utils.EXPECT_TRUE(False, f"Communication invalid message {message}")
        continue
      category, data = preprocess
      self.__pending_categories.add(category)
      if category in self.__message_queue:
        self.__message_queue[category].append(data)
      else:
        self.__message_queue[category] = [data]
    self.__message_lock.release()
  
  def pending_categories(self) -> set:
    return self.__pending_categories

  def send(self, category: bytes, *messages) -> None:
    for message in messages:
      self.__uart1.send(category.decode() + Communication.COMMAND_SPLIT.decode() +
          (message if type(message) == str else message.decode()), 
          delimiter=Communication.INTER_COMMAND_SPLIT.decode())

  def read(self, category: bytes) -> bytes:
    self.__message_lock.acquire()
    if category not in self.__message_queue or len(self.__message_queue[category]) == 0:
      self.__message_lock.release()
      return None
    ret = self.__message_queue[category][0]
    self.__message_queue[category] = self.__message_queue[category][1:]
    if len(self.__message_queue[category]) == 0:
      self.__pending_categories.remove(category)
    self.__message_lock.release()
    return ret

  def read_all(self, category: bytes) -> list:
    self.__message_lock.acquire()
    if category not in self.__message_queue or len(self.__message_queue[category]) == 0:
      self.__message_lock.release()
      return None
    ret = self.__message_queue[category]
    self.__message_queue[category] = []
    self.__message_lock.release()
    return ret

  def discard_all(self, category: bytes) -> None:
    self.__message_lock.acquire()
    if category not in self.__message_queue or len(self.__message_queue[category]) == 0:
      self.__message_lock.release()
      return
    self.__message_queue[category] = []
    self.__pending_categories.remove(category)
    self.__message_lock.release()

  def blocking_read(self, category: bytes) -> bytes:
    while True:
      msg = self.read(category)
      if msg != None:
        return msg
      time.sleep_ms(100)

  def blocking_read_all(self, category: bytes) -> list:
    while True:
      msgs = self.read_all(category)
      if msgs != None:
        return msgs
      time.sleep_ms(100)

  def wait_for_reject_or_confirm(self) -> tuple:
    while True:
      if Communication.REJECT in self.__pending_categories:
        msg = self.read(Communication.REJECT).decode()
        print(f"REJECT: {msg}")
        return False, msg
      if Communication.CONFIRM in self.__pending_categories:
        msg = self.read(Communication.CONFIRM).decode()
        return True, msg
      time.sleep_ms(100)
