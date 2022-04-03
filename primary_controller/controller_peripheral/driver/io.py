import machine, _thread, time, array

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
    utils.ASSERT_TRUE(id in Button.pull_up_avail_pins, "Button GPIO does not support pull-up")
    self.__id = id
    Button.button_pins.append(self.__id)
    self.__pin = machine.Pin(id, machine.Pin.IN, machine.Pin.PULL_UP)
  
  def begin(self, pressed_callback, debounce_delay_ms: int = 13.5) -> None:
    """ Set the button into triggering mode, every time the button is pressed, callback is called
        `pressed_callback`: callback function called when the button is pressed,
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
  DUTY_MODE = 0
  FREQ_MODE = 1

  class _Info:
    """ Internal class used to store PWM related variables """
    def __init__(self, size: int=50) -> None:
      """ Create a new PWM Information instance
          `size`: internal buffer size """
      if size % 2 != 0:
        utils.EXPECT_TRUE(False, f"PWM Output buffer size should be even, use {size + 1} instead of {size}")
        size += 1
      self.start = 0
      self.len = 0
      self.size = size
      self.seq = array.array('i', (0 for _ in range(size)))
    
    def append(self, seq: array.array) -> bool:
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
      """ Get next action from the internal buffer """
      if self.len == 0:
        return -1
      value = self.seq[self.start]
      duration = self.seq[(self.start + 1) % self.size]
      if duration <= 1: 
        self.start = (self.start + 2) % self.size
        self.len -= 2
      else:
        self.seq[(self.start + 1) % self.size] -= 1
      return value
  
  timer = None
  active_tasks = {}
  active_tasks_lock = _thread.allocate_lock()

  @classmethod
  def auxiliary_init(cls, timer_period_ms: int=50) -> None:
    """ Initializations that fulfill full requirements for system to operate """
    cls.timer = machine.Timer(utils.PWM_OUT_TIMER_ID)
    cls.timer.init(mode=machine.Timer.PERIODIC, period=timer_period_ms, callback=PWMOutput.__update_callback)

  @classmethod
  def __update_callback(cls, timer: machine.Timer) -> None:
    """ Internal irq function that called on timer triggering. Should NOT be called
        `timer`: timer instance that triggered the callback """
    cls.active_tasks_lock.acquire()
    for id in cls.active_tasks.keys():
      pwm_pin, mode, info = cls.active_tasks[id]
      val = info.dequeue()
      if val == -1:
        continue
      if mode == cls.DUTY_MODE:
        pwm_pin.change_duty_cycle(val)
      elif mode == cls.FREQ_MODE:
        pwm_pin.change_frequency(val)
    cls.active_tasks_lock.release()
    

  def __init__(self, id: int, mode: int, buf_size: int=50) -> None:
    """ Initialize a new PWM controlled output using GPIO id
        `id`: id of the GPIO wished to be controlled using PWM """
    utils.ASSERT_TRUE(id not in PWMOutput.active_tasks.keys(), f"Duplicate PWMOut on pin [{id}]")
    utils.ASSERT_TRUE(mode == PWMOutput.DUTY_MODE or mode == PWMOutput.FREQ_MODE, f"Invalid PWMOut mode")
    self.__id = id
    self.__pin = machine.Pin(id, machine.Pin.OUT)
    self.__pwm = machine.PWM(self.__pin, freq=5000, duty=0)
    PWMOutput.active_tasks[self.__id] = (self, mode, PWMOutput._Info(buf_size))

  def change_duty_cycle(self, duty: int) -> None:
    """ Change the duty cycle of the PWM output 
        `duty`: int in range [0, 1024), representing a duty cycle of [duty / 1024] """
    self.__pwm.duty(duty)

  def change_frequency(self, freq: int) -> None:
    """ Change the duty cycle of the PWM output 
        `freq`: destinated frequency """
    self.__pwm.freq(freq)

  def append_sequence(self, seq: array.array, seq_end: str):
    if seq[-2] != seq_end:
      seq.append(seq_end)
      seq.append(1)
    PWMOutput.active_tasks_lock.acquire()
    ret = PWMOutput.active_tasks[self.__id][2].append(seq)
    PWMOutput.active_tasks_lock.release()
    return ret

class VibrationMotor(PWMOutput):
  """ Class extends from PWMOutput that used to control vibration motor """
  SEQ_END = 0
  slight_seq = array.array('i', [410, 2,  SEQ_END, 1])
  medium_seq = array.array('i', [410, 1, 615, 2, 410, 1,  SEQ_END, 1])
  heavy_seq  = array.array('i', [410, 1, 615, 1, 819, 4, 615, 1, 410, 1, SEQ_END, 1])

  def __init__(self, id: int, buf_size: int = 50) -> None:
    super().__init__(id, PWMOutput.DUTY_MODE, buf_size)
    self.__pwm.duty(0)

  def slight_vibration(self) -> None:
    """ Vibration motor slightly vibrates, non-blocking """
    self.custom_vibration(VibrationMotor.slight_seq)

  def medium_vibration(self) -> None:
    """ Vibration motor moderately vibrates, non-blocking """
    self.custom_vibration(VibrationMotor.medium_seq)

  def heavy_vibration(self) -> None:
    """ Vibration motor heavily vibrates, non-blocking """
    self.custom_vibration(VibrationMotor.heavy_seq)

  def custom_vibration(self, seq: array.array) -> bool:
    """ Command the vibration motor using user defined sequence 
        `seq`: user defined sequence, should be a integer array, each of the entry is in the range
            [0, 256), representing a duty cycle of [entry / 1024]. each of the entry represents
            the vibration strength in consecutive 100ms period """
    utils.ASSERT_TRUE(len(seq) % 2 == 0, "Vibration Motor Sequence length not even")
    self.append_sequence(seq, VibrationMotor.SEQ_END)

class Buzzer(PWMOutput):
  """ Note: Frequency less than or equal to 610 cannot make the buzzer correctly function"""
  SEQ_END = 1
  A =  array.array('i', [28, 55, 110, 220, 440, 880, 1760, 3520, 7040])
  AB = array.array('i', [29, 55, 117, 233, 466, 932, 1865, 3729, 7459])
  B =  array.array('i', [31, 58, 123, 247, 494, 988, 1976, 3951, 7902])
  C =  array.array('i', [16, 33, 65, 131, 262, 523, 1047, 2093, 4186])
  CD = array.array('i', [17, 35, 69, 139, 277, 554, 1109, 2217, 4435])
  D =  array.array('i', [18, 37, 73, 147, 294, 587, 1175, 2349, 4699])
  DE = array.array('i', [19, 39, 78, 156, 311, 622, 1245, 2489, 4978])
  E =  array.array('i', [21, 41, 82, 165, 330, 659, 1319, 2637, 5274])
  F =  array.array('i', [22, 44, 87, 175, 349, 698, 1397, 2794, 5588])
  FG = array.array('i', [23, 46, 93, 185, 370, 740, 1480, 2960, 5920])
  G =  array.array('i', [25, 49, 98, 196, 392, 784, 1568, 3136, 6272])
  GA = array.array('i', [26, 52, 104, 208, 415, 831, 1661, 3322, 6645])
  PAUSE = 1

  START_UP = array.array('i', [C[6], 2, D[6], 2, E[6], 2, F[6], 2, G[6], 2, SEQ_END, 2])
  
  NGGYU = array.array("i", [
    G[5], 4, A[5], 4, C[6], 4, A[5], 4, E[6], 11, PAUSE, 1, E[6], 12, D[6], 18, 
    G[5], 4, A[5], 4, C[6], 4, A[5], 4, D[6], 11, PAUSE, 1, D[6], 12, C[6], 18, 
    G[5], 4, A[5], 4, C[6], 4, A[5], 4, C[6], 12, D[6], 12, B[5], 4, A[5], 4, G[5], 4, D[6], 8, C[6], 22, 
    G[5], 4, A[5], 4, C[6], 4, A[5], 4, E[6], 11, PAUSE, 1, E[6], 12, D[6], 16, 
    G[5], 4, A[5], 4, C[6], 4, A[5], 4, G[6], 12, B[5], 12, C[6], 18, 
    G[5], 4, A[5], 4, C[6], 4, A[5], 4, C[6], 12, D[6], 12, B[5], 4, A[5], 4, G[5], 4, D[6], 8, C[6], 22])

  def __init__(self, id: int, buf_size: int = 200) -> None:
    super().__init__(id, PWMOutput.FREQ_MODE, buf_size)
    self.__pwm.freq(1)
    self.__pwm.duty(50)
  
  def change_volume(self, percentage: float) -> None:
    utils.EXPECT_TRUE(percentage >= 0 and percentage <= 1, "Buzzer invalid volume percentage")
    self.__pwm.duty(int(100 * percentage))

  def sound_bootup(self) -> None:
    self.custom_sound(Buzzer.START_UP)

  def never_gonna_give_you_up(self) -> None:
    self.custom_sound(Buzzer.NGGYU)

  def custom_sound(self, seq: array.array) -> None:
    """ Command the buzzer using user defined sequence 
        `seq`: user defined sequence, should be a integer array, each of the entry is in the range
            [0, 256), representing a duty cycle of [entry / 1024]. each of the entry represents
            the vibration strength in consecutive 100ms period """
    utils.ASSERT_TRUE(len(seq) % 2 == 0, "Buzzer Sequence length not even")
    self.append_sequence(seq, Buzzer.SEQ_END)
