import machine, _thread, time

from driver.ssd1306 import SSD1306
from driver.display import Drawing, OLED
from driver.uart import UART
from driver.status_led import StatusLed
from driver.threading import ThreadSafeQueue
from driver.io import Button, PWMOutput, VibrationMotor

from functionality.menu import Menu

def uart1_rx_callback() -> None:
  """ Callback function that called every time uart1 receieved message(s) """
  Board.uart1_pending_lock.acquire()
  Board.uart1_pending = True
  Board.uart1_pending_lock.release()

def botton_pressed_callback(button_id: int) -> None:
  """ Callback function that called every time a button is pressed """
  Board.button_pending_lock.acquire()
  Board.button_queue.enqueue(button_id)
  Board.button_pending = True
  Board.button_pending_lock.release()

class Board:
  """ Have only classmethods, interfacing high-level functionalities with lower-level facilities """
  # displays
  main_display = None
  secondary_display = None

  # status led
  status_led = None

  # uart1
  uart1 = None
  uart1_queue = None
  uart1_pending = False
  uart1_pending_lock = _thread.allocate_lock()

  # buttons
  button25 = None
  button26 = None
  button27 = None
  button_queue = None
  button_pending = False
  button_pending_lock = _thread.allocate_lock()
  BUTTON1, BUTTON2, BUTTON3 = 25, 26, 27

  # PWM outputs
  vmotor = None
  buzzer = None

  @classmethod
  def main_init(cls) -> None:
    """ Initializations that fulfill basic requirements for system to operate """
    # set processor speed to 240MHz
    #   available freq: [20MHz, 40MHz, 80MHz, 160MHz, 240MHz]
    machine.freq(240000000)

    # Status led initialization must be the first
    cls.status_led = StatusLed()

    Drawing.main_init()
    
    cls.main_display = OLED(0x3C)


  @classmethod
  def auxiliary_init(cls) -> None:
    """ Initializations that fulfill full requirements for system to operate """
    Drawing.auxiliary_init()
    PWMOutput.auxiliary_init()
    Menu.auxiliary_init()
    
    cls.uart1 = UART(1, tx = 18, rx = 17)
    cls.uart1.register_rx_callback(uart1_rx_callback)
    # uart begin eariler for receieving message from Main
    cls.uart1_queue = cls.uart1.begin()
    
    cls.button25 = Button(25)
    cls.button26 = Button(26)
    cls.button27 = Button(27)
    cls.button_queue = ThreadSafeQueue()

    cls.vmotor = VibrationMotor(22)
    # pwm23 reserved for buzzer

  @classmethod
  def begin_operation(cls) -> None:
    """ Begin operation of all facilities """
    cls.button25.begin(botton_pressed_callback)
    cls.button26.begin(botton_pressed_callback)
    cls.button27.begin(botton_pressed_callback)

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
    messasge = cls.uart1_queue.dequeue()
    if cls.uart1_queue.is_empty():
      cls.uart1_pending = False
    cls.uart1_pending_lock.release()
    return messasge

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
  def is_button_pending(cls) -> bool:
    """ Whether buttons have pending pressing events 
        `returns`: whether buttons have pending pressing events """
    return cls.button_pending

  @classmethod
  def get_button_message(cls) -> int:
    """ Get one of the pending button pressing event
        `returns`: first pending button GPIO number, None if no pending pressing event """
    cls.button_pending_lock.acquire()
    messasge = cls.button_queue.dequeue()
    if cls.button_queue.is_empty():
      cls.button_pending = False
    cls.button_pending_lock.release()
    return messasge

  @classmethod
  def get_all_button_message(cls) -> list:
    """ Get all of the pending button pressing events
        `returns`: list of pending button pressing events """
    cls.button_pending_lock.acquire()
    messages = []
    while not cls.button_queue.is_empty():
      messages.append(cls.button_queue.dequeue())
    cls.button_pending = False
    cls.button_pending_lock.release()
    return messages

  @classmethod
  def vibrate(cls, level: int) -> None:
    """ Activate the vibration motor
        `level`: level of vibration, 1: slight, 2: medium, 3: heavy """
    if level == 1:
      cls.vmotor.slight_vibration()
    elif level == 2:
      cls.vmotor.medium_vibration()
    elif level == 3:
      cls.vmotor.heavy_vibration()

  @classmethod
  def display_menu_and_get_choice(cls, menu: Menu, display: OLED, 
      reset_idx: int=-1, undisplay: bool=True) -> int:
    """ Display given menu on given display, expecting user to use on-board buttons
        to select desired option, return the choice index after user finished choosing,
        blocking 
        `menu`: the menu to be displayed onto screen
        `display`: the OLED for the menu to be displayed on
        `reset_idx`: index of choice to be highlighted after choosing, -1 if no need to reset
        `undisplay`: undisplay the choices after choosing """
    menu.display_choices(display)
    choice_idx = -1
    while True:
      if Board.is_button_pending():
        message = Board.get_button_message()
        if message == Board.BUTTON1:
          menu.rotate_highlight(Menu.CHANGE_PREV)
        elif message == Board.BUTTON3:
          menu.rotate_highlight(Menu.CHANGE_NEXT)
        elif message == Board.BUTTON2:
          choice_idx = menu.choose(reset_idx)
          break
        menu.display_choices(display)
      time.sleep_ms(50)
    if undisplay:
      menu.undisplay_choices(display)
    return choice_idx

  @classmethod
  def user_keyboard_input(cls, display: OLED) -> str:
    """ Display keyboard to the user on given display, expect user to input one character 
        `display`: the OLED for the menu to be displayed on """
    choice_idx = cls.display_menu_and_get_choice(Menu.keyboard, display, -1, undisplay=False)
    ret = Menu.keyboard_sequence[choice_idx]
    if ret == '\x06' or ret == '\x18':
      Menu.keyboard.undisplay_choices(display)
      Menu.keyboard.change_highlight(0)
    return ret

  @classmethod
  def display_keyboard_and_get_input(cls, display: OLED, title: str, title_x_offset: int=0) -> str:
    """ Display keyboard to the user on given display, expecting user to use on-board buttons 
        to input character sequences. Sequences are directly reflected onto the specified display,
        return the character sequence after user finished inputing, blocking 
        `display`: the OLED for the menu to be displayed on
        `title`: title to be displayed when prompting user for keyboard input
        `title_x_offset`: x offset of the title to be displayed """
    # internal parameters
    title_y_offset = 3
    ustring_x_offset = 10
    ustring_y_offset = 13
    ustring_max_len = 14

    display_direct = display.get_direct_control()
    display_direct.text(title, title_x_offset, title_y_offset, 1)

    user_string = ""

    while True:
      display_direct.fill_rect(0, ustring_y_offset, 128, OLED.CHAR_HEIGHT, 0)
      display_direct.text(">" + user_string, ustring_x_offset - OLED.CHAR_WIDTH, ustring_y_offset, 1)
      if len(user_string) < ustring_max_len:
        display_direct.fill_rect(ustring_x_offset + len(user_string) * OLED.CHAR_WIDTH, 
            ustring_y_offset, 3, OLED.CHAR_HEIGHT - 1, 1)

      char = Board.user_keyboard_input(display)

      if char == '\x08': # backspace
        user_string = user_string[:-1]
      elif char == '\x06': # confirm
        break
      elif char == '\x18': # cancel
        user_string = None
        break
      else: # characters
        if len(user_string) < ustring_max_len:
          user_string = user_string + char

    display_direct.fill(0)
    display_direct.show()
    return user_string

