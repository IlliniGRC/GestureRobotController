import machine, _thread, time

import driver.utils as utils


class Button:
  """ Controlling the button class """
  pull_up_avail_pins = (18, 19, 21, 22, 23, 25, 26, 27, 32, 33)
  button_pins = []

  @classmethod
  def get_all_allocated_button_pins(cls) -> list:
    """ Get all buttons that allocated by now"""
    return cls.button_pins

  def __init__(self, id: int) -> None:
    """ Initialize a new button using GPIO id
        `id`: id of the GPIO the button is on """
    utils.ASSERT_TRUE(id not in Button.button_pins, "Button already initialized with this pin")
    utils.ASSERT_TRUE(id in Button.pull_up_avail_pins, "Button GPIO does not support pullup")
    self.__id = id
    Button.button_pins.append(self.__id)
    self.__pin = machine.Pin(id, machine.Pin.IN, machine.Pin.PULL_UP)
  
  def begin(self, pressed_callback, debounce_delay_ms: int = 13.5) -> None:
    """ Set the button into triggering mode, every time the button is pressed, callback is called
        `pressed_callback`: callback funciton called when the button is pressed,
        `debounce_delay_ms`: software debounce delay time, default value is optimum """
    self.__rx_callback = pressed_callback
    self.__last_debounce_time = time.time_ns()
    self.__debounce_delay = int(debounce_delay_ms * 10e6)
    self.__pin.irq(self.__button_pressed_irq, machine.Pin.IRQ_FALLING)

  def __button_pressed_irq(self, pin: machine.Pin) -> None:
    """ Internal irq function that called on voltage level of that pin falling. Should NOT be called
        `pin`: pin instance that triggered the callback """
    val = pin.value()
    current_debounce_time = time.time_ns()
    if current_debounce_time - self.__last_debounce_time > self.__debounce_delay:
      self.__last_debounce_time = current_debounce_time
      if val == 0:
        self.__rx_callback(self.__id)


class PWMOutput:
  """ Controls output devices that uses PWM output """
  class _Info:
    """ Internal class used to store PWM related variables """
    def __init__(self, size: int=50) -> None:
      """ Create a new PWM Information instance
          `size`: internal buffer size """
      self.start = 0
      self.len = 0
      self.size = size
      self.seq = bytearray(size)
    
    def append(self, seq: bytearray) -> bool:
      """ Append sequence to the end of the internal buffer
          `seq`: sequence to be appended to the internal buffer """
      if self.size - self.len < len(seq):
        return False
      end = (self.start + self.len) % self.size
      cutoff = self.size - end
      self.len += len(seq)
      if cutoff < len(seq):
        self.seq[end:] = seq[:cutoff]
        self.seq[:len(seq) - cutoff] = seq[cutoff:]
      else:
        self.seq[end:end + len(seq)] = seq
    
    def dequeue(self) -> int:
      """ Get one message from the start of the internal buffer """
      if self.len == 0:
        return -1
      ret = self.seq[self.start]
      self.start = (self.start + 1) % self.size
      self.len -= 1
      return ret
  
  timer = None
  active_tasks = {}
  active_tasks_lock = _thread.allocate_lock()

  @classmethod
  def auxiliary_init(cls, timer_period_ms: int=100) -> None:
    """ Initializations that fulfill full requirements for system to operate """
    cls.timer = machine.Timer(utils.MOTOR_TIMER_ID)
    cls.timer.init(mode=machine.Timer.PERIODIC, period=timer_period_ms, callback=PWMOutput.__update_callback)

  @classmethod
  def __update_callback(cls, timer: machine.Timer) -> None:
    """ Internal irq function that called on timer triggering. Should NOT be called
        `timer`: timer instance that triggered the callback """
    cls.active_tasks_lock.acquire()
    for id in cls.active_tasks.keys():
      motor, info = cls.active_tasks[id]
      duty = info.dequeue()
      if duty == -1:
        continue
      motor.change_duty_cycle(duty << 2)
    cls.active_tasks_lock.release()
    

  def __init__(self, id: int) -> None:
    """ Initialize a new PWM controlled output using GPIO id
        `id`: id of the GPIO wished to be controlled using PWM """
    utils.ASSERT_TRUE(id not in PWMOutput.active_tasks.keys(), f"Duplicate PWMOut on pin [{id}]")
    self.__id = id
    self.__pin = machine.Pin(id, machine.Pin.OUT)
    self.__pwm = machine.PWM(self.__pin, freq=5000, duty=0)
    PWMOutput.active_tasks[self.__id] = (self, PWMOutput._Info())

  def change_duty_cycle(self, duty: int) -> None:
    """ Change the duty cycle of the PWM output 
        `duty`: int in range [0, 1024), representing a duty cycle of [duty / 1024] """
    self.__pwm.duty(duty)

class VibrationMotor(PWMOutput):
  """ Class extends from PWMOutput that used to control vibration motor """
  slight_seq = bytearray([102, 102,  0])
  medium_seq = bytearray([102, 154, 154, 102,  0])
  heavy_seq  = bytearray([102, 154, 205, 205, 205, 205, 154, 102, 0])

  def slight_vibration(self) -> None:
    """ Vibration motor slightly vibrates, non-blocking """
    self.custom_vibration(VibrationMotor.slight_seq)

  def medium_vibration(self) -> None:
    """ Vibration motor moderately vibrates, non-blocking """
    self.custom_vibration(VibrationMotor.medium_seq)

  def heavy_vibration(self) -> None:
    """ Vibration motor heavily vibrates, non-blocking """
    self.custom_vibration(VibrationMotor.heavy_seq)

  def custom_vibration(self, seq: bytearray) -> bool:
    """ Command the vibration motor using user defined sequence 
        `seq`: user defined sequence, should be a bytearray, each of the entry is in the range
            [0, 256), representing a duty cycle of [entry / 1024]. each of the entry represents
            the vibration strength in consecutive 100ms period """
    if seq[-1] != 0:
      seq.append(0)
    PWMOutput.active_tasks_lock.acquire()
    ret = PWMOutput.active_tasks[self.__id][1].append(seq)
    PWMOutput.active_tasks_lock.release()
    return ret
