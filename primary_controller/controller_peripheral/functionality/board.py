import machine, _thread, time, gc

import driver.utils as utils
from driver.display import Drawing, OLED
from driver.status_led import StatusLed
from driver.threading import ThreadSafeQueue
from driver.io import Button, Buzzer, PWMOutput, VibrationMotor

from functionality.menu import Menu
from functionality.snake import SnakeGame
from functionality.config import Config
from functionality.text_viewer import TextViewer
from functionality.communication import Communication as Com

def uart1_rx_callback() -> None:
  """ Callback function that called every time uart1 received message(s) """
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

  # uart1 communication
  uart1_com = None

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

  # text viewer
  text_viewer = None

  @classmethod
  def main_init(cls) -> None:
    """ Initializations that fulfill basic requirements for system to operate """
    # set processor speed to 240MHz
    #   available freq: [20MHz, 40MHz, 80MHz, 160MHz, 240MHz]
    machine.freq(int(240e6))

    # Status led initialization must be the first
    cls.status_led = StatusLed()
    
    cls.main_display = OLED(0x3C)
    cls.secondary_display = OLED(0x3D)


  @classmethod
  def auxiliary_init(cls) -> None:
    """ Initializations that fulfill full requirements for system to operate """
    PWMOutput.auxiliary_init()
    
    Menu.auxiliary_init()
    Config.auxiliary_init()
    
    cls.uart1_com = Com()
    
    cls.button25 = Button(25)
    cls.button26 = Button(26)
    cls.button27 = Button(27)
    cls.button_queue = ThreadSafeQueue()

    cls.vmotor = VibrationMotor(22)

    volume = 50
    try:
      with open("data/volume.settings", "r") as f:
        volume = int(f.read())
    except Exception:
      pass
    cls.buzzer = Buzzer(23, volume)

    cls.text_viewer = TextViewer()

  @classmethod
  def begin_operation(cls) -> None:
    """ Begin operation of all facilities """
    cls.button25.begin(botton_pressed_callback)
    cls.button26.begin(botton_pressed_callback)
    cls.button27.begin(botton_pressed_callback)

  @classmethod
  def end_operation(cls) -> None:
    """ End operation of all facilities """
    cls.uart1_com.finish()

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
    message = cls.button_queue.dequeue()
    if cls.button_queue.is_empty():
      cls.button_pending = False
    cls.button_pending_lock.release()
    return message

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
  def begin_snake_game(cls, display: OLED, init_x: int=29, init_y: int=29, 
      x_offset: int=35, y_offset: int=3, max_score: int=50) -> None:
    gc.collect()
    game = SnakeGame(display, init_x, init_y, x_offset, y_offset, max_score + 1)
    while cls.snake_game(game):
      game.restart(init_x, init_y)
    display.clear_screen()
    gc.collect()
    
  @classmethod
  def snake_game(cls, game: SnakeGame) -> bool:
    while game.update(cls.vmotor):
      if Board.is_button_pending():
        button_message = Board.get_button_message()
        if button_message == 25:
          game.rotate_anticlockwise()
        if button_message == 27:
          game.rotate_clockwise()
      time.sleep_ms(90)

    Menu.RQ_menu.change_y_offset(39)
    Menu.RQ_menu.display_choices(Board.main_display)
    while True:
      # BUTTON
      if Board.is_button_pending():
        message = Board.get_button_message()
        if message == Board.BUTTON1:
          Menu.RQ_menu.rotate_highlight(Menu.CHANGE_PREV)
        elif message == Board.BUTTON3:
          Menu.RQ_menu.rotate_highlight(Menu.CHANGE_NEXT)
        elif message == Board.BUTTON2:
          choice_idx = Menu.RQ_menu.choose(0)
          break
        Menu.RQ_menu.display_choices(Board.main_display)

      time.sleep_ms(10)

    Menu.RQ_menu.undisplay_choices(Board.main_display)
    return choice_idx == 0

  @classmethod
  def display_menu_and_get_choice(cls, menu: Menu, display: OLED, 
      reset_idx: int=-1, undisplay: bool=True) -> int:
    """ Display given menu on given display, expecting user to use on-board buttons
        to select desired option, return the choice index after user finished choosing,
        blocking. Notice, the method will acquire display lock internally
        `menu`: the menu to be displayed onto screen
        `display`: the OLED for the menu to be displayed on
        `reset_idx`: index of choice to be highlighted after choosing, -1 if no need to reset
        `undisplay`: undisplay the choices after choosing """
    gc.collect()
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
    gc.collect()
    return choice_idx

  @classmethod
  def user_keyboard_input(cls, display: OLED, keyboard: Menu) -> str:
    """ Helpper function, display keyboard to the user on given display, expect user to input 
        one character. Will clear screen on confirm or cancel, will not reset keyboard highlight.
        Notice, this method is helpper function for <display_keyboard_and_get_input>, do NOT 
        call directly.
        `display`: the OLED for keyboard to be displayed on """
    choice_idx = cls.display_menu_and_get_choice(keyboard, display, -1, undisplay=False)
    ret = Menu.keyboard_sequence[choice_idx]
    if ret == '\x06' or ret == '\x18':
      keyboard.undisplay_choices(display)
      keyboard.change_highlight(0)
    return ret

  @classmethod
  def display_keyboard_and_get_input(cls, display: OLED, title: str, title_x_offset: int=0,
      initial_string: str="", initial_key: str="Q") -> str:
    """ Display keyboard to the user on given display, expecting user to use on-board buttons 
        to input character sequences. Sequences are directly reflected onto the specified display,
        return the character sequence after user finished inputing, blocking 
        `display`: the OLED for keyboard to be displayed on
        `title`: title to be displayed when prompting user for keyboard input
        `title_x_offset`: x offset of the title to be displayed 
        `initial_string`: initial string displayed at start of input session
        `initial_key`: default key the keyboard is on at start of input session """
    # internal parameters
    title_y_offset = 3
    ustring_x_offset = 10
    ustring_y_offset = 13
    ustring_max_len = 14

    gc.collect()
    display_direct = display.get_direct_control()

    keyboard = Menu()
    line_start = 10
    for i in range(11):
      keyboard.add_choice(line_start + i * 10, 24, [Menu.keyboard_sequence[i]])
    line_start = 15
    for i in range(10):
      keyboard.add_choice(line_start + i * 10, 33, [Menu.keyboard_sequence[i + 11]])
    line_start = 20
    for i in range(7):
      keyboard.add_choice(line_start + i * 10, 42, [Menu.keyboard_sequence[i + 21]])
    keyboard.add_choice(92, 42, ["<-"])
    keyboard.add_choice(8, 51, ["Confirm"])
    keyboard.add_choice(72, 51, ["Cancel"])

    initial_string, initial_key = initial_string.upper(), initial_key.upper()
    utils.ASSERT_TRUE(len(initial_string) <= ustring_max_len, 
        f"Keyboard input preset sequence <{initial_string}> exceed maximum length {ustring_max_len}")
    utils.ASSERT_TRUE(len(initial_key) == 1 and initial_key in Menu.keyboard_sequence,
        f"Keyboard input preset key <{initial_key}> not in available keyboard list")

    display.lock.acquire()
    display_direct.text(title, title_x_offset, title_y_offset, 1)

    user_string = initial_string
    keyboard.change_highlight(Menu.keyboard_sequence.index(initial_key))

    while True:
      display_direct.fill_rect(0, ustring_y_offset, 128, OLED.CHAR_HEIGHT, 0)
      display_direct.text(">" + user_string, ustring_x_offset - OLED.CHAR_WIDTH, ustring_y_offset, 1)
      if len(user_string) < ustring_max_len:
        display_direct.fill_rect(ustring_x_offset + len(user_string) * OLED.CHAR_WIDTH, 
            ustring_y_offset, 3, OLED.CHAR_HEIGHT - 1, 1)

      display.lock.release()
      char = Board.user_keyboard_input(display, keyboard)
      display.lock.acquire()

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
    display.lock.release()
    gc.collect()
    return user_string

  @classmethod
  def begin_text_viewer(cls, display: OLED, text: str, 
      wrap_content:bool=True, delimiter: str="\n") -> None:
    """ Begin the operation of a text viewer using specified string
        `display`: the OLED for text to be displayed on
        `wrap_content`: whether to wrap the content in case line length exceed screen width
        `delimiter`: used when determine line split point """
    gc.collect()
    display_direct = display.get_direct_control()
    display.lock.acquire()
    display.display_loading_screen()
    display_direct.show()
    cls.text_viewer.set_text_to_view(text, wrap_content, delimiter)
    display_direct.fill(0)
    display.lock.release()
    cls.text_viewer.view_on_display(display)
    
    while True:
      if Board.is_button_pending():
        message = Board.get_button_message()
        if message == Board.BUTTON1:
          cls.text_viewer.PNE_menu_rotate(Menu.CHANGE_PREV)
        elif message == Board.BUTTON3:
          cls.text_viewer.PNE_menu_rotate(Menu.CHANGE_NEXT)
        elif message == Board.BUTTON2:
          should_exit = cls.text_viewer.PNE_menu_choose()
          if should_exit:
            break
        display.lock.acquire()
        display.get_direct_control().fill(0)
        display.lock.release()
        cls.text_viewer.view_on_display(display)
      time.sleep_ms(50)
    gc.collect()
    display.clear_screen()
  
  @classmethod
  def estimate_polling_rate_and_display(cls, display: OLED) -> None:
    gc.collect()
    display_direct = display.get_direct_control()

    # ask main controller to estimate polling speed of IMUs
    cls.uart1_com.send(Com.IMU, Com.SPEED)
    # acquire display lock and start displaying waiting message
    display.lock.acquire()
    display_direct.fill(0)
    display_direct.text("Estimation", 24, 20, 1)
    display_direct.text("In Progress...", 8, 36, 1)
    display_direct.show()
    # wait until main controller responds with reject or confirm
    status, msg = cls.uart1_com.wait_for_reject_or_confirm()
    if status: # confirm
      try:
        preprocess = msg.split(",")
        preprocess[0][0] == "E" and preprocess[1][0] == "Q"
      except Exception: # invalid report format
        utils.EXPECT_TRUE(False, "IMU estimation report format invlid")
        status = False
    if status: # confirm and valid report format
      display_direct.fill(0)
      # Euclidean report
      display_direct.text("Euclidean:", 24, 4, 1)
      displayed_msg = f"{preprocess[0][1:]} it/s"
      display_direct.text(displayed_msg, 
          64 - len(displayed_msg) * OLED.CHAR_WIDTH // 2, 16)
      # quarternion report
      display_direct.text("Quarternion:", 16, 28, 1)
      displayed_msg = f"{preprocess[1][1:]} it/s"
      display_direct.text(displayed_msg, 
          64 - len(displayed_msg) * OLED.CHAR_WIDTH // 2, 40)
    else: # reject
      display_direct.fill(0)
      display_direct.text("No available IMU", 0, 24, 1)
    # display back menu
    Menu.B_menu.change_x_offset(47)
    Menu.B_menu.change_y_offset(51)
    display.lock.release()
    cls.display_menu_and_get_choice(Menu.B_menu, display)
    # clear screen and release display lock
    display.clear_screen()
    gc.collect()

  @classmethod
  def create_config(cls, display: OLED) -> None:
    gc.collect()
    display_direct = display.get_direct_control()
    # display loading screen
    display.lock.acquire()
    display.display_loading_screen()
    display_direct.show()
    display.lock.release()
    user_string = ""
    while True:
      user_string = Board.display_keyboard_and_get_input(display, "File Name", 2, user_string)
      if user_string == None: # Cancel
        return
      else: # Confirm
        config = Config()
        filename = f"{user_string}.{Config.extension}"
        if not config.create_and_associate_config_file(filename):
          # duplicated config file name
          display.lock.acquire()
          config_ext = f".{Config.extension}"
          display_direct.text("Config", 4, 4)
          display_direct.fill_rect(4, 14, 120, 24, 1)
          display_direct.text(user_string, 4, 16, 0)
          display_direct.text(config_ext, 120 - len(config_ext) * OLED.CHAR_WIDTH, 28, 0)
          display_direct.text("already exists", 8, 40)
          display_direct.show()
          Menu.B_menu.change_x_offset(47)
          Menu.B_menu.change_y_offset(51)
          display.lock.release()
          cls.display_menu_and_get_choice(Menu.B_menu, display)
          display.lock.acquire()
          display_direct.fill(0)
          display.lock.release()
          # ask user to re-enter a filename with current entered sequence retained
          continue
        break
    # display loading screen
    display.lock.acquire()
    display.display_loading_screen()
    display_direct.show()
    display.lock.release()
    # get all I2C addresses from the main controller
    cls.uart1_com.send(Com.IMU, Com.ADDRESS)
    preprocess = cls.uart1_com.blocking_read(Com.CONFIRM).decode()
    addresses = set([int(address) for address in preprocess.split(",")])
    # let user assign I2C addresses
    cls.begin_address_assignment(display, addresses, config)
    # creation complete
    config_ext = f".{Config.extension}"
    display.lock.acquire()
    display_direct.fill(0)
    display_direct.text("Config", 4, 4)
    display_direct.fill_rect(4, 14, 120, 24, 1)
    display_direct.text(user_string, 4, 16, 0)
    display_direct.text(config_ext, 120 - len(config_ext) * OLED.CHAR_WIDTH, 28, 0)
    display_direct.text("created", 36, 40)
    display_direct.show()
    Menu.B_menu.change_x_offset(47)
    Menu.B_menu.change_y_offset(51)
    display.lock.release()
    cls.display_menu_and_get_choice(Menu.B_menu, display)
    display.clear_screen()

  @classmethod
  def begin_address_assignment(cls, display: OLED, addresses: set, config: Config):
    gc.collect()
    display_direct = display.get_direct_control()
    # IMU position selection menu
    imu_select_menu = Menu()
    for i, position in enumerate(Config.IMU_AVAIL_POSITIONS):
      x_center, y_offset = 32 + 64 * (i % 2), 12 + 10 * (i // 2)
      imu_select_menu.add_choice(
          x_center - len(position) * OLED.CHAR_WIDTH // 2, y_offset, [position])
    # prompt user for assigning positions to IMUs  
    address = addresses.pop()
    while True:
      position = cls.display_imus_and_get_choice(display, address, imu_select_menu)
      conflict = config.add_imu_to_config(position, address)
      if conflict != None: # conflict
        display.lock.acquire()
        display_direct.fill(0)
        display_direct.text("Position", 0, 4)
        display_direct.fill_rect(71, 3, len(position) * OLED.CHAR_WIDTH + 2, 9, 1)
        display_direct.text(position, 72, 4, 0)
        display_direct.text("is occupied by", 0, 13)
        display_direct.text("IMU at address", 0, 22)
        hex_address = hex(conflict)
        text_start = 64 - len(hex_address) * OLED.CHAR_WIDTH // 2
        display_direct.fill_rect(text_start - 1, 30, len(hex_address) * OLED.CHAR_WIDTH + 2, 9, 1)
        display_direct.text(hex_address, text_start, 31, 0)
        display_direct.text("Override?", 28, 40)
        display.lock.release()
        Menu.YN_menu.change_y_offset(51)
        choice_idx = cls.display_menu_and_get_choice(Menu.YN_menu, display, 1)
        if choice_idx == 0: # yes
          # force add current, overriding conflicted
          config.add_imu_to_config(position, address, True)
          addresses.add(conflict)
          # get next unallocated address
          address = addresses.pop()
      else: # no conflict
        config.add_imu_to_config(position, address)
        if len(addresses) == 0:
          # all addresses are allocated
          break
        # get next unallocated address
        address = addresses.pop()
    # write config to file
    config.write_config_to_file()

  @classmethod
  def display_imus_and_get_choice(cls, display: OLED, address: int, imu_menu: Menu) -> str:
    display_direct = display.get_direct_control()
    display.lock.acquire()
    display_direct.fill(0)
    display_direct.text(f"IMU @ {hex(address)}", 0, 0)
    display.lock.release()
    choice_idx = cls.display_menu_and_get_choice(imu_menu, display, undisplay=False)
    return Config.IMU_AVAIL_POSITIONS[choice_idx]

  @classmethod
  def change_volume(cls, display: OLED) -> None:
    gc.collect()
    display_direct = display.get_direct_control()

    while True:
      volume = Board.buzzer.get_volume()
      display_direct.fill(0)
      display_direct.text("Volume", 40, 9, 1)
      display_direct.text(f"{volume:3}", 4, 22, 1)
      rect_start, rect_end = 30, 116
      # empty outside
      display_direct.rect(rect_start, 22, rect_end - rect_start, 7, 1)
      if volume != 0:
        # filled inside
        rect_width = int((rect_end - rect_start) * volume / 100)
        display_direct.fill_rect(rect_start, 22, rect_width, 7, 1)
    
      choice_idx = Board.display_menu_and_get_choice(Menu.volume_menu, display, -1, False)
      if choice_idx == 0: # -
        Board.buzzer.set_volume(volume - Buzzer.VOLUME_GRANULARITY 
            if volume >= Buzzer.VOLUME_GRANULARITY else volume)
      elif choice_idx == 1: # +
        Board.buzzer.set_volume(volume + Buzzer.VOLUME_GRANULARITY 
            if volume <= 100 - Buzzer.VOLUME_GRANULARITY else volume)
      elif choice_idx == 2: # Back
        display_direct.fill(0)
        display_direct.show()
        Menu.volume_menu.change_highlight(0) # reset highlight
        gc.collect()
        return

  @classmethod
  def load_menu(cls):
    """ Main menu loop, blocks forever """
    # get direct control of the main display
    display_direct = Board.main_display.get_direct_control()

    # set current display to main menu
    current_menu = Menu.main_menu

    # menu loop
    while True:
      if current_menu == Menu.main_menu:
        choice_idx = Board.display_menu_and_get_choice(current_menu, Board.main_display, 0)

        if choice_idx == 0: # Start Operation
          current_menu = Menu.main_menu
        elif choice_idx == 1: # Settings
          current_menu = Menu.settings_menu

      elif current_menu == Menu.settings_menu:
        choice_idx = Board.display_menu_and_get_choice(current_menu, Board.main_display, -1)

        if choice_idx == 0: # Load Config
          current_menu = Menu.general_menu
        elif choice_idx == 1:
          current_menu = Menu.configs_menu
        elif choice_idx == 2: # Snake
          Board.begin_snake_game(Board.main_display, max_score=40)
          current_menu = Menu.settings_menu
        elif choice_idx == 3: # Mystery
          Board.buzzer.sound_mystery()
          current_menu.change_highlight(0) # reset highlight
          current_menu = Menu.main_menu
        elif choice_idx == 4: # Back
          current_menu.change_highlight(0) # reset highlight
          current_menu = Menu.main_menu

      elif current_menu == Menu.general_menu:
        choice_idx = Board.display_menu_and_get_choice(current_menu, Board.main_display, -1)

        if choice_idx == 0: # Change Volume
          cls.change_volume(Board.main_display)
          current_menu = Menu.general_menu
        elif choice_idx == 1: # View IMU polling rate
          cls.estimate_polling_rate_and_display(Board.main_display)
          current_menu = Menu.general_menu
        elif choice_idx == 2: # Back
          current_menu.change_highlight(0) # reset highlight
          current_menu = Menu.settings_menu

      elif current_menu == Menu.configs_menu:
        choice_idx = Board.display_menu_and_get_choice(current_menu, Board.main_display, -1)

        if choice_idx == 0: # Load Config
          current_menu = Menu.configs_menu
        elif choice_idx == 1: # Create Config
          cls.create_config(Board.main_display)
        elif choice_idx == 2: # View Config
          with open("driver/status_led.py", "r") as f:
            # normal file contains "\r\n" as new line character
            Board.begin_text_viewer(Board.main_display, f.read(), True, "\r\n") 
            current_menu = Menu.configs_menu

        elif choice_idx == 3: # Back
          current_menu.change_highlight(0) # reset highlight
          current_menu = Menu.settings_menu
