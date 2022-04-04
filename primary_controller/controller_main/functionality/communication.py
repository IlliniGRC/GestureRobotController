import machine, _thread

import driver.utils as utils
from driver.uart import UARTCallback


class Communication:
  # Control characters
  INTER_COMMAND_SPLIT = b'\n'
  COMMAND_SPLIT = b'|'
  # Control Words
  START = b'start'
  IMU = b'IMU'

  def __init__(self) -> None:
    self.__uart1 = UARTCallback(1, tx=18, rx=17)
    self.__uart1.begin(self.__uart1_rx_callback)
    self.__message_queue = {}
    self.__message_lock = _thread.allocate_lock()

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
      if category in self.__message_queue:
        self.__message_queue[category].append(data)
      else:
        self.__message_queue[category] = [data]
    self.__message_lock.release()

  def send(self, category: bytes, *messages) -> None:
    for message in messages:
      self.__uart1.send(category.decode() + Communication.COMMAND_SPLIT.decode() +
          (message if type(message) == str else message.decode()), 
          delimiter=Communication.INTER_COMMAND_SPLIT.decode())

  def read(self, category: bytes) -> str:
    self.__message_lock.acquire()
    if category not in self.__message_queue or len(self.__message_queue[category]) == 0:
      self.__message_lock.release()
      return None
    ret = self.__message_queue[category][0]
    self.__message_queue[category] = self.__message_queue[category][1:]
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
    