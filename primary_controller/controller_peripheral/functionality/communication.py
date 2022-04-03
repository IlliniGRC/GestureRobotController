import _thread

import driver.utils as utils
from driver.uart import UART


class Communication:
  # Control Words
  START = "start"
  IMU = "IMU"


  def __init__(self) -> None:
    self.__uart1 = UART(1, tx=18, rx=17)
    self.__uart1.register_rx_callback(self.__uart1_rx_callback)
    self.__uart1_pending = False
    self.__uart1_pending_lock = _thread.allocate_lock()
    self.__message_queue = {}
    self.__uart1_queue = self.__uart1.begin()

  def __uart1_rx_callback(self) -> None:
    """ Callback function that called every time uart1 received message(s) """
    self.__uart1_pending_lock.acquire()
    self.__uart1_pending = True
    self.__uart1_pending_lock.release()

  def update(self) -> None:
    if not self.__uart1_pending:
      return
    self.__uart1_pending_lock.acquire()
    while not self.__uart1_queue.is_empty():
      message = self.__uart1_queue.dequeue()
      preprocess = message.split(" ", 1)
      if len(preprocess) == 1:
        utils.EXPECT_TRUE(False, f"Communication invalid message {message}")
        continue
      category, data = preprocess
      if category in self.__message_queue:
        self.__message_queue[category].append(data)
      else:
        self.__message_queue[category] = [data]
    self.__uart1_pending = False
    self.__uart1_pending_lock.release()

  def get_message(self, category: str) -> str:
    if category not in self.__message_queue or len(self.__message_queue[category] == 0):
      return None
    ret = self.__message_queue[0]
    self.__message_queue = self.__message_queue[1:]
    return ret

  def get_all_message(self, category: str) -> list:
    if category not in self.__message_queue or len(self.__message_queue[category] == 0):
      return None
    ret = self.__message_queue
    self.__message_queue = []
    return ret
