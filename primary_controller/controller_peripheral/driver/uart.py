import machine

import driver.utils as utils
from driver.threading import ThreadSafeQueue


class UARTQueue:
  """ UART facilities that allows async usage """

  def __init__(self, id: int, tx: int, rx: int, baudrate: int = 115200) -> None:
    """ Create an UART instance using specified tx, rx pin and baudrate
        `id`: id of the UART instance
        `tx`: GPIO pin number for the UART TX pin
        `rx`: GPIO pin number for the UART RX pin
        `baudrate`: baudrate of the UART transmission """
    self.__tx = tx
    self.__rx = rx
    utils.ASSERT_TRUE(self.__tx != None and self.__rx != None, "UART TX and RX pins must be specified")
    self.__uart = machine.UART(id, baudrate, tx=self.__tx, rx=self.__rx)
    self.__queue = None

    self.__rx_callback = None
    self.__timer = None
    self.__quit_signal = False

  def begin(self, queue_size: int = 20) -> ThreadSafeQueue:
    """ Begin the operation of the UART and return a thread safe queue that used to communicate
        `queue_size`: size of the buffer (ThreadSafeQueue)
        `returns`: the buffer (ThreadSafeQueue) used to communicate """
    utils.ASSERT_TRUE(self.__queue == None, "UART duplicated begin")
    self.__queue = ThreadSafeQueue(queue_size)
    self.__timer = machine.Timer(utils.UART_TIMER_ID)
    # polling is used as callback is fired periodically using hardware timer
    self.__timer.init(mode=machine.Timer.PERIODIC, period=200, callback=self.__rx_polling)
    return self.__queue

  def send(self, *buffers: str) -> None:
    """ Send given buffer using uart with delimiters (\\n) in between
        `*buffers`: buffers to be sent """
    for buffer in buffers:
      self.__uart.write(buffer + "\n")

  def finish(self) -> None:
    """ Stops the operation of the UART """
    self.__quit_signal = True

  def register_rx_callback(self, callback_func) -> None:
    """ Register a callback function that get called when there is pending UART message
        `callback_func`: callback function to be registered """
    self.__rx_callback = callback_func

  def get_uart_buffer(self) -> ThreadSafeQueue:
    """ Get the buffer (ThreadSafeQueue) that used to communicate """
    return self.__queue
    
  def __rx_polling(self, timer: machine.Timer) -> None:
    """ UART message detection polling thread, triggered by a periodic timer, should NOT be called """
    if self.__quit_signal:
      print("UART QUIT")
      self.__timer.deinit()
    message = self.__uart.readline()
    if message == None:
      return
    while message != None:
      self.__queue.enqueue(message.strip())
      message = self.__uart.readline()
    if self.__rx_callback != None:
      self.__rx_callback()
      
class UARTCallback:
  """ UART facilities that allows async usage """

  def __init__(self, id: int, tx: int, rx: int, baudrate: int = 115200) -> None:
    """ Create an UART instance using specified tx, rx pin and baudrate
        `id`: id of the UART instance
        `tx`: GPIO pin number for the UART TX pin
        `rx`: GPIO pin number for the UART RX pin
        `baudrate`: baudrate of the UART transmission """
    self.__tx = tx
    self.__rx = rx
    utils.ASSERT_TRUE(self.__tx != None and self.__rx != None, "UART TX and RX pins must be specified")
    self.__uart = machine.UART(id, baudrate, tx=self.__tx, rx=self.__rx)

    self.__rx_callback = None
    self.__timer = None
    self.__quit_signal = False

  def begin(self, callback_func) -> None:
    """ Begin the operation with a callback function that triggers on regular interval """
    utils.ASSERT_TRUE(self.__rx_callback == None, "UART duplicated begin")
    self.__timer = machine.Timer(utils.UART_TIMER_ID)
    # polling is used as callback is fired periodically using hardware timer
    self.__timer.init(mode=machine.Timer.PERIODIC, period=200, callback=self.__rx_polling)
    self.__rx_callback = callback_func

  def send(self, *buffers: str) -> None:
    """ Send given buffer using uart with delimiters (\\n) in between
        `*buffers`: buffers to be sent """
    for buffer in buffers:
      self.__uart.write(buffer + "\n")

  def finish(self) -> None:
    """ Stops the operation of the UART """
    self.__quit_signal = True
    
  def __rx_polling(self, timer: machine.Timer) -> None:
    """ UART message detection polling thread, triggered by a periodic timer, should NOT be called """
    if self.__quit_signal:
      print("UART QUIT")
      self.__timer.deinit()
    self.__rx_callback(self.__uart)
