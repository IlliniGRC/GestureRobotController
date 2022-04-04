import machine

import driver.utils as utils
from driver.threading import ThreadSafeQueue

class UART:
  """ UART facilities that allows async usage """
  TIMER_PERIOD_MS = 100 # UART rx polling timer interval in ms

  def __init__(self, id: int, tx: int, rx: int, baudrate: int = 115200) -> None:
    """ Create an UART instance using specified tx, rx pin and baudrate
        `id`: id of the UART instance
        `tx`: GPIO pin number for the UART TX pin
        `rx`: GPIO pin number for the UART RX pin
        `baudrate`: baudrate of the UART transmission """
    self._tx = tx
    self._rx = rx
    utils.ASSERT_TRUE(self._tx != None and self._rx != None, "UART TX and RX pins must be specified")
    self._uart = machine.UART(id, baudrate, tx=self._tx, rx=self._rx)
    self._queue = None

    self._rx_callback = None
    self._timer = None
    self._quit_signal = False

  def send(self, *buffers: str, delimiter: str="\n") -> None:
    """ Send given buffer using uart with delimiters (\\n) in between
        `*buffers`: buffers to be sent """
    for buffer in buffers:
      self._uart.write(buffer + delimiter)

  def finish(self) -> None:
    """ Stops the operation of the UART """
    self._quit_signal = True

class UARTQueue(UART):
  """ UART facilities that allows async usage using ThreadSafeQueue """

  def begin(self, queue_size: int = 20) -> ThreadSafeQueue:
    """ Begin the operation of the UART and return a thread safe queue that used to communicate
        `queue_size`: size of the buffer (ThreadSafeQueue)
        `returns`: the buffer (ThreadSafeQueue) used to communicate """
    utils.ASSERT_TRUE(self._queue == None, "UART duplicated begin")
    self._queue = ThreadSafeQueue(queue_size)
    self._timer = machine.Timer(utils.UART_TIMER_ID)
    # polling is used as callback is fired periodically using hardware timer
    self._timer.init(mode=machine.Timer.PERIODIC, period=UART.TIMER_PERIOD_MS, 
        callback=self._rx_polling)
    return self._queue

  def register_rx_callback(self, callback_func) -> None:
    """ Register a callback function that get called when there is pending UART message
        `callback_func`: callback function to be registered """
    self._rx_callback = callback_func

  def get_uart_buffer(self) -> ThreadSafeQueue:
    """ Get the buffer (ThreadSafeQueue) that used to communicate """
    return self._queue
    
  def _rx_polling(self, timer: machine.Timer) -> None:
    """ UART message detection polling thread, triggered by a periodic timer, should NOT be called """
    if self._quit_signal:
      print("UART QUIT")
      self._timer.deinit()
    message = self._uart.readline()
    if message == None:
      return
    while message != None:
      self._queue.enqueue(message.strip())
      message = self._uart.readline()
    if self._rx_callback != None:
      self._rx_callback()
      
class UARTCallback(UART):
  """ UART facilities that allows async usage using callback """

  def begin(self, callback_func) -> None:
    """ Begin the operation with a callback function that triggers on regular interval """
    utils.ASSERT_TRUE(self._rx_callback == None, "UART duplicated begin")
    self._timer = machine.Timer(utils.UART_TIMER_ID)
    # polling is used as callback is fired periodically using hardware timer
    self._timer.init(mode=machine.Timer.PERIODIC, period=UART.TIMER_PERIOD_MS, 
        callback=self._rx_polling)
    self._rx_callback = callback_func
    
  def _rx_polling(self, timer: machine.Timer) -> None:
    """ UART message detection polling thread, triggered by a periodic timer, should NOT be called """
    if self._quit_signal:
      print("UART QUIT")
      self._timer.deinit()
    self._rx_callback(self._uart)
