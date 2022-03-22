import machine, _thread, time

from driver.threading import Thread


class StatusLed:
  """ Using on-board LED to convey message """
  bootup_seq  = [50, 50, 50, 50, 50, 50]
  info_seq    = [50, 50]
  warning_seq = [200, 200, 200, 200]
  error_seq   = [500, 500]

  def __init__(self):
    """ Initialize using the LED located on GPIO2 """
    self.__pin = machine.Pin(2, machine.Pin.OUT)
    self.__info_thread = Thread(self.__show_info)
    self.__warning_thread = Thread(self.__show_warning)
    self.__lock = _thread.allocate_lock()

  def show_bootup(self) -> None:
    """ Show bootup sequence, blocking """
    self.__lock.acquire()
    self.display_led_sequence(StatusLed.bootup_seq)
    self.__lock.release()

  def show_info(self) -> bool:
    """ Show info sequence, non-blocking """
    self.__info_thread.run()

  def __show_info(self, timeout_ms: float = -1) -> bool:
    """ Show info sequence, blocking """
    if not self.__lock.acquire(True, timeout_ms):
      return False
    self.display_led_sequence(StatusLed.info_seq)
    self.__lock.release()
    return True

  def show_warning(self) -> bool:
    """ Show warning sequence, non-blocking """
    self.__warning_thread.run()

  def __show_warning(self, timeout_ms: float = -1) -> bool:
    """ Show warning sequence, blocking """
    if not self.__lock.acquire(True, timeout_ms):
      return False
    self.display_led_sequence(StatusLed.warning_seq)
    self.__lock.release()
    return True

  def show_error(self) -> None:
    """ Show error sequence, blocking """
    self.__lock.acquire()
    while True:
      self.display_led_sequence(StatusLed.error_seq)
    # Blocking, does not release lock

  def display_led_sequence(self, seq_ms: list):
    """ Show user-defined sequence, blocking """
    self.__pin.value(1)
    for delay in seq_ms:
      time.sleep_ms(delay)
      self.__pin.value(1 - self.__pin.value())
    self.__pin.value(0)
