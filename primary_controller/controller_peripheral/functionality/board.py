import machine, _thread, time, gc

import driver.utils as utils
from driver.display import OLED, Drawing
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
    
    try:
      cls.main_display = OLED(0x3C)
    except Exception:
      utils.ASSERT_TRUE(False, "Main display does not exist")

    try:
      cls.secondary_display = OLED(0x3D)
    except Exception:
      utils.EXPECT_TRUE(False, "Secondary display does not exist")


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
  def second_display_priority(cls) -> OLED:
    return cls.secondary_display if cls.secondary_display != None else cls.main_display

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
  def display_menu_and_get_choice(cls, display: OLED, menu: Menu, 
      reset_idx: int=-1, undisplay: bool=True) -> int:
    """ Display given menu on given display, expecting user to use on-board buttons
        to select desired option, return the choice index after user finished choosing,
        blocking. Notice, the method will acquire display lock internally. Will NOT clear
        the screen after operation is done
        `display`: the OLED for the menu to be displayed on
        `menu`: the menu to be displayed onto screen
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
    choice_idx = cls.display_menu_and_get_choice(display, keyboard, -1, undisplay=False)
    ret = Menu.keyboard_sequence[choice_idx]
    if ret == '\x06' or ret == '\x18':
      keyboard.undisplay_choices(display)
      keyboard.change_highlight(0)
    return ret

  @classmethod
  def display_keyboard_and_get_input(cls, display: OLED, title: str, title_x_offset: int=0,
      initial_string: str="", initial_key: str="Q", max_len: int=14) -> str:
    """ Display keyboard to the user on given display, expecting user to use on-board buttons 
        to input character sequences. Sequences are directly reflected onto the specified display,
        return the character sequence after user finished inputing, blocking. Screen will be 
        cleared after operation is done.
        `display`: the OLED for keyboard to be displayed on
        `title`: title to be displayed when prompting user for keyboard input
        `title_x_offset`: x offset of the title to be displayed 
        `initial_string`: initial string displayed at start of input session
        `initial_key`: default key the keyboard is on at start of input session """
    # internal parameters
    title_y_offset = 3
    ustring_x_offset = 10
    ustring_y_offset = 13
    ustring_max_len = min(14, max_len)

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
    display_direct.fill(0)
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
    display.lock.release()
    gc.collect()
    return user_string

  @classmethod
  def begin_text_viewer(cls, display: OLED, text: str, 
      wrap_content:bool=True, delimiter: str="\n") -> None:
    """ Begin the operation of a text viewer using specified string, will clear screen after
        operation is done
        `display`: the OLED for text to be displayed on
        `wrap_content`: whether to wrap the content in case line length exceed screen width
        `delimiter`: used when determine line split point """
    gc.collect()
    display_direct = display.get_direct_control()
    display.lock.acquire()
    display.display_loading_screen()
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
    display.lock.acquire()
    display_direct.fill(0)
    display.lock.release()
    gc.collect()
  
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
    display.lock.release()
    Menu.B_menu.change_x_offset(47)
    Menu.B_menu.change_y_offset(51)
    cls.display_menu_and_get_choice(display, Menu.B_menu, undisplay=False)
    # clear screen and release display lock
    display.lock.acquire()
    display_direct.fill(0)
    display.lock.release()
    gc.collect()

  @classmethod
  def create_config(cls, display: OLED) -> None:
    gc.collect()
    display_direct = display.get_direct_control()
    # display loading screen
    display.lock.acquire()
    display.display_loading_screen()
    display.lock.release()

    # get all I2C addresses from the main controller
    cls.uart1_com.send(Com.IMU, Com.ADDRESS)
    preprocess = cls.uart1_com.blocking_read(Com.CONFIRM).decode()
    if len(preprocess) == 0: # no IMUs available
      display.lock.acquire()
      display_direct.fill(0)
      display_direct.text("No IMU Detected", 4, 4)
      display_direct.text("Attach at Least", 4, 16)
      display_direct.text("One IMU to", 18, 28)
      display_direct.text("Create Config", 12, 40)
      display.lock.release()
      Menu.B_menu.change_x_offset(47)
      Menu.B_menu.change_y_offset(51)
      cls.display_menu_and_get_choice(display, Menu.B_menu, undisplay=False)
      display.lock.acquire()
      display_direct.fill(0)
      display.lock.release()
      return

    user_string = ""
    while True:
      user_string = Board.display_keyboard_and_get_input(display, title="File Name", 
          title_x_offset=2, initial_string=user_string, 
          max_len=14 - len(Config.extension) - 1)
      if user_string == None: # Cancel
        return
      else: # Confirm
        if len(user_string) == 0: # empty string
          display.lock.acquire()
          display_direct.text("Config cannot", 12, 9)
          display_direct.text("have an empty", 12, 22)
          display_direct.text("name", 48, 35)
          display.lock.release()
          Menu.B_menu.change_x_offset(47)
          Menu.B_menu.change_y_offset(51)
          cls.display_menu_and_get_choice(display, Menu.B_menu, undisplay=False)
          display.lock.acquire()
          display_direct.fill(0)
          display.lock.release()
          # ask user to re-enter a filename
          continue
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
          display.lock.release()
          Menu.B_menu.change_x_offset(47)
          Menu.B_menu.change_y_offset(51)
          cls.display_menu_and_get_choice(display, Menu.B_menu, undisplay=False)
          display.lock.acquire()
          display_direct.fill(0)
          display.lock.release()
          # ask user to re-enter a filename with current entered sequence retained
          continue
        break
    # display loading screen
    display.lock.acquire()
    display.display_loading_screen()
    display.lock.release()
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
    display.lock.release()
    Menu.B_menu.change_x_offset(47)
    Menu.B_menu.change_y_offset(51)
    cls.display_menu_and_get_choice(display, Menu.B_menu, undisplay=False)
    display.lock.acquire()
    display_direct.fill(0)
    display.lock.release()
    gc.collect()

  @classmethod
  def display_error_log(cls, display: OLED, error_log: str):
    gc.collect()
    display.lock.acquire()
    display.save_current_screen()
    display.lock.release()

    prepend = "A recoverable\nerror has\noccurred during\noperation:\n"
    cls.begin_text_viewer(display, prepend + error_log)

    display.lock.acquire()
    display.redisplay_saved_screen()
    display.get_direct_control().show()
    display.lock.release()
    gc.collect()

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
        display_direct.inv_text(position, 72, 4)
        display_direct.text(position, 72, 4, 0)
        display_direct.text("is occupied by", 0, 13)
        display_direct.text("IMU at address", 0, 22)
        hex_address = hex(conflict)
        display_direct.inv_text(hex_address, 64 - len(hex_address) * OLED.CHAR_WIDTH // 2, 31)
        display_direct.text("Override?", 28, 40)
        display.lock.release()
        Menu.YN_menu.change_y_offset(51)
        choice_idx = cls.display_menu_and_get_choice(display, Menu.YN_menu, 1)
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
    gc.collect()

  @classmethod
  def display_imus_and_get_choice(cls, display: OLED, address: int, 
      imu_menu: Menu) -> str:
    display_direct = display.get_direct_control()
    display.lock.acquire()
    display_direct.fill(0)
    display_direct.text(f"IMU @ {hex(address)}", 0, 0)
    display.lock.release()
    choice_idx = cls.display_menu_and_get_choice(display, imu_menu, undisplay=False)
    return Config.IMU_AVAIL_POSITIONS[choice_idx]

  @classmethod
  def manage_config(cls, display: OLED) -> bool:
    gc.collect()
    display_direct = display.get_direct_control()
    configs = Config.get_all_config_names()
    if len(configs) == 0: # no config
      display.lock.acquire()
      display_direct.text("No Configs", 24, 14)
      display_direct.text("To View", 36, 28)
      display.lock.release()
      Menu.B_menu.change_x_offset(47)
      Menu.B_menu.change_y_offset(41)
      cls.display_menu_and_get_choice(display, Menu.B_menu, undisplay=False)
      display.lock.acquire()
      display_direct.fill(0)
      display.lock.release()
      return False
    # loading take some time
    display.display_loading_screen()
    # parameters
    choice_x_offset = 4
    choice_offset = 0
    max_configs_displayed = 5
    page_num_center = 42 # ((1 + 8 + 1) + (75 - 1)) / 2

    # default config setup
    default_config_idx = -1
    default_config_filename = Config.get_default_config()
    # initial menu setup
    all_config_menu = Menu()
    all_config_menu.add_choice(1, 55, ["<"])
    all_config_menu.add_choice(75, 55, [">"])
    all_config_menu.add_choice(95, 55, ["Back"])
    for i in range(min(max_configs_displayed, len(configs))):
      config = configs[i]
      x_text_offset = 64 - len(config) * OLED.CHAR_WIDTH // 2
      all_config_menu.add_choice(x_text_offset, 2 + 10 * i, 
          [config], x_border_width=x_text_offset - choice_x_offset)
      if config == default_config_filename:
        default_config_idx = i
    # initial menu visibility setup
    all_config_menu.change_highlight(3)
    all_config_menu.change_choice_visibility(0, False)
    if len(configs) <= max_configs_displayed:
      all_config_menu.change_choice_visibility(1, False)
    
    while True: # all config menu loop
      # display page number
      offset_page = choice_offset + 1
      page_num_display = f"{offset_page}/{max(1, len(configs) - max_configs_displayed + 1)}"
      page_num_x_offset = int(page_num_center - OLED.CHAR_WIDTH * (0.5 + len(str(offset_page))))
      display.lock.acquire()
      display_direct.fill(0)
      display_direct.fill_rect(9, 55, 65, 8, 0)
      display_direct.text(page_num_display, page_num_x_offset, 55)
      if default_config_idx != -1:
        display_direct.fill_rect(0, 2 + 10 * default_config_idx, 2, 8, 1)
      display.lock.release()

      choice_idx = cls.display_menu_and_get_choice(display, 
          all_config_menu, undisplay=False)
      if choice_idx == 0 or choice_idx == 1:
        # reset default config index as menu items change
        default_config_idx = -1
        choice_offset += 1 if choice_idx == 1 else -1
        for i in range(max_configs_displayed):
          config = configs[i + choice_offset]
          x_text_offset = 64 - len(config) * OLED.CHAR_WIDTH // 2
          all_config_menu.replace_choice(i + 3, x_text_offset, 2 + 10 * i, 
              [config], x_border_width=x_text_offset - choice_x_offset)
          if config == default_config_filename:
            default_config_idx = i
        # default config highlight
        if default_config_idx != -1:
          display_direct.fill_rect(0, 2 + 10 * default_config_idx, 2, 8, 1)
        # forward and backward button visibility
        if choice_offset == 0: # cannot backward
          all_config_menu.change_choice_visibility(1, True)
          all_config_menu.change_highlight(1)
          all_config_menu.change_choice_visibility(0, False)
        elif choice_offset == len(configs) - max_configs_displayed: # cannot forward
          all_config_menu.change_choice_visibility(0, True)
          all_config_menu.change_highlight(0)
          all_config_menu.change_choice_visibility(1, False)
      elif choice_idx == 2: # back
        display.lock.acquire()
        display_direct.fill(0)
        display.lock.release()
        gc.collect()
        return False
      else: # a config is picked
        config_idx = choice_idx - 3 + choice_offset
        # file manipulation menu
        target_file = configs[config_idx]
        manipulation_menu = Menu()
        manipulation_menu.add_choice(8, 16, ["Set as Default"])
        manipulation_menu.add_choice(20, 28, ["View Config"])
        manipulation_menu.add_choice(12, 40, ["Delete Config"])
        manipulation_menu.add_choice(48, 52, ["Back"])
        while True: # individual config menu loop
          display.lock.acquire()
          display_direct.fill(0)
          x_text_offset = 64 - len(target_file) * OLED.CHAR_WIDTH // 2
          display_direct.text(target_file, x_text_offset, 4)
          display_direct.rect(choice_x_offset, 2, 128 - 2 * choice_x_offset, 12, 1)
          display.lock.release()
          choice_idx = cls.display_menu_and_get_choice(display, 
              manipulation_menu, undisplay=False)
          if choice_idx == 0: # set as default
            display.lock.acquire()
            display_direct.fill_rect(0, 14, 128, 50, 0)
            display_direct.text("Confirm Set as", 8, 22)
            display_direct.text("Default Config?", 4, 34)
            display.lock.release()
            Menu.YN_menu.change_y_offset(47)
            choice_idx = cls.display_menu_and_get_choice(display, 
                Menu.YN_menu, 1, undisplay=False)
            if choice_idx == 0: # yes
              Config.set_default_config(target_file)
              default_config_idx = config_idx - choice_offset
              default_config_filename = target_file
              break
            else: # no
              continue
          elif choice_idx == 1: # view config
            temp = Config()
            temp.associate_with_file(target_file)
            temp.read_config_from_file()
            display.lock.acquire()
            display_direct.fill(0)
            display.lock.release()
            cls.begin_text_viewer(display, temp.get_config_string())
          elif choice_idx == 2: # delete config
            display.lock.acquire()
            display_direct.fill_rect(0, 16, 128, 48, 0)
            display_direct.text("Confirm Delete?", 4, 28)
            display.lock.release()
            Menu.YN_menu.change_y_offset(47)
            choice_idx = cls.display_menu_and_get_choice(display, 
                Menu.YN_menu, 1, undisplay=False)
            if choice_idx == 0: # yes
              Config.remove_config(target_file)
              gc.collect()
              return True # signal to display the outer menu again
            else: # no
              continue
          elif choice_idx == 3: # back
            break

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
    
      choice_idx = Board.display_menu_and_get_choice(display, Menu.volume_menu, undisplay=False)
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
  def start_operation(cls, display: OLED) -> None:
    gc.collect()
    display_direct = display.get_direct_control()
    # display loading screen
    display.lock.acquire()
    display.display_loading_screen()
    display.lock.release()
    # check if a config is selected
    config_name = Config.get_default_config()
    if config_name == Config.no_default_config:
      # no default config, report warning
      display.lock.acquire()
      display_direct.fill(0)
      display_direct.text("No default", 24, 12)
      display_direct.text("config selected", 4, 28)
      display.lock.release()
      Menu.B_menu.change_x_offset(47)
      Menu.B_menu.change_y_offset(43)
      cls.display_menu_and_get_choice(display, Menu.B_menu, undisplay=False)
      display.lock.acquire()
      display_direct.fill(0)
      display.lock.release()
      return
    # check if bluetooth is connected
    cls.uart1_com.send(Com.BLUETOOTH, Com.CONNECTED)
    ret, _ = cls.uart1_com.wait_for_reject_or_confirm()
    if not ret:
      cls.uart1_com.send(Com.BLUETOOTH, Com.NAME)
      display.lock.acquire()
      display_direct.fill(0)
      display_direct.text("Bluetooth", 16, 4)
      display_direct.text("Not Connected", 0, 12)
      display_direct.blit(Drawing.get_warning_sign(), 108, 3)
      display_direct.text("Connect to", 24, 24)
      display.lock.release()
      
      name = cls.uart1_com.blocking_read(Com.CONFIRM)

      display.lock.acquire()
      display_direct.fill_rect(64 - len(name) * OLED.CHAR_WIDTH // 2, 33, 
          len(name) * OLED.CHAR_WIDTH, 9, 1)
      display_direct.text(name, 64 - len(name) * OLED.CHAR_WIDTH // 2, 34, 0)
      display_direct.text("To Continue", 20, 44)
      display.lock.release()
      Menu.B_menu.change_x_offset(47)
      Menu.B_menu.change_y_offset(53)
      cls.display_menu_and_get_choice(display, Menu.B_menu, undisplay=False)
      display.lock.acquire()
      display_direct.fill(0)
      display.lock.release()
      return
    # load default config
    config = Config()
    config.associate_with_file(config_name)
    utils.ASSERT_TRUE(config.read_config_from_file(), "Start Operation association failed")
    # send to main controller
    messages = config.get_config_string(readable=False).split("\n")
    Board.uart1_com.send(Com.IMU, Com.BULK)
    ret = Board.uart1_com.blocking_read(Com.CONFIRM)
    utils.ASSERT_TRUE(ret == Com.BULK,
        f"Operation bulk communication failed at begining, unexpected <{ret.decode()}>")
    # send config to main controller
    success = True
    for message in messages:
      Board.uart1_com.send(Com.IMU, message)
      ret, ret_message = Board.uart1_com.wait_for_reject_or_confirm()
      if not ret: # IMU not detected by main controller
        cls.display_error_log(cls.second_display_priority(), ret_message)
        display.lock.acquire()
        display_direct.fill(0)
        display.lock.release()
        success = False
        break
    Board.uart1_com.send(Com.IMU, Com.TERMINATE)
    ret = Board.uart1_com.blocking_read(Com.CONFIRM)
    utils.ASSERT_TRUE(ret == Com.TERMINATE, 
        f"Operation bulk communication failed at termination, unexpected <{ret.decode()}>")
    if not success:
      return
    # operation begin
    Board.uart1_com.send(Com.IMU, Com.BEGIN)
    ret = Board.uart1_com.blocking_read(Com.CONFIRM)
    utils.ASSERT_TRUE(ret == Com.BEGIN, 
        f"Operation failed at begining, unexpected <{ret.decode()}>")

    display.lock.acquire()
    display_direct.fill(0)
    display_direct.text("In Operation", 16, 24)
    display.lock.release()
    Menu.B_menu.change_x_offset(47)
    Menu.B_menu.change_y_offset(43)
    Menu.B_menu.display_choices(display)
    Board.uart1_com.discard_all(Com.BLUETOOTH)
    while True:
      if Board.is_button_pending():
        if Board.get_button_message() == Board.BUTTON2:
          break
      if Com.BLUETOOTH in Board.uart1_com.pending_categories():
        msg = Board.uart1_com.read(Com.BLUETOOTH).decode()
        request, num = msg.split(",")
        request = request.lower()
        print(request, num)
        if request == "m":
          if num == "0":
            Board.vmotor.custom_vibration(VibrationMotor.slight_seq)
          elif num == "1":
            Board.vmotor.custom_vibration(VibrationMotor.medium_seq)
          elif num == "2":
            Board.vmotor.custom_vibration(VibrationMotor.heavy_seq)
          elif num == "3":
            Board.vmotor.custom_vibration(VibrationMotor.double_seq)
          elif num == "4":
            Board.vmotor.custom_vibration(VibrationMotor.triple_seq)
          else:
            utils.EXPECT_TRUE(False, f"Bluetooth invalid vmotor request index <{num}>")
        elif request == "b":
          if num == "0":
            Board.buzzer.custom_sound(Buzzer.double_seq)
          elif num == "1":
            Board.buzzer.custom_sound(Buzzer.triple_seq)
          elif num == "2":
            Board.buzzer.custom_sound(Buzzer.long_seq)
          elif num == "3":
            Board.buzzer.custom_sound(Buzzer.double_long_seq)
          else:
            utils.EXPECT_TRUE(False, f"Bluetooth invalid buzzer request index <{num}>")
        elif request == "vr":
          try:
            volume = int(num)
          except Exception:
            utils.EXPECT_TRUE(False, f"Bluetooth invalid relative volume <{num}>")
          Board.buzzer.set_volume(Board.buzzer.get_volume() + volume)
        elif request == "va":
          try:
            volume = int(num)
          except Exception:
            utils.EXPECT_TRUE(False, f"Bluetooth invalid absolute volume <{num}>")
          Board.buzzer.set_volume(volume)
        else:
          utils.EXPECT_TRUE(False, f"Bluetooth invalid request <{request}>")
      time.sleep_ms(100)
    Menu.B_menu.undisplay_choices(display)
    Board.get_all_button_message()

    # operation over
    Board.uart1_com.send(Com.IMU, Com.TERMINATE)
    ret = Board.uart1_com.blocking_read(Com.CONFIRM)
    utils.ASSERT_TRUE(ret == Com.TERMINATE, 
        f"Operation failed at termination, unexpected <{ret.decode()}>")

    display.lock.acquire()
    display_direct.fill(0)
    display.lock.release()
  
  @classmethod
  def change_bluetooth_advertise_name(cls, display: OLED) -> None:
    display_direct = display.get_direct_control()

    display.lock.acquire()
    display.display_loading_screen()
    display.lock.release()

    cls.uart1_com.send(Com.BLUETOOTH, Com.BULK)
    ret = Board.uart1_com.blocking_read(Com.CONFIRM)
    utils.ASSERT_TRUE(ret == Com.BULK,
        f"Bluetooth bulk communication failed at begining, unexpected <{ret.decode()}>")

    while True:
      name = cls.display_keyboard_and_get_input(display, title="Bluetooth Name", 
          title_x_offset=2, max_len=8)
      cls.uart1_com.send(Com.BLUETOOTH, name)
      status, msg = cls.uart1_com.wait_for_reject_or_confirm()
      if status:
        break
      cls.display_error_log(cls.second_display_priority(), msg)
      
    utils.ASSERT_TRUE(msg == Com.TERMINATE.decode(), 
        f"Bluetooth bulk failed at termination, unexpected <{ret.decode()}>")

    display.lock.acquire()
    display_direct.fill(0)
    display_direct.text("Bluetooth name", 8, 14)
    display_direct.text("has changed to", 8, 24)
    display_direct.fill_rect(64 - len(name) * OLED.CHAR_WIDTH // 2, 33, 
        len(name) * OLED.CHAR_WIDTH, 9, 1)
    display_direct.text(name, 64 - len(name) * OLED.CHAR_WIDTH // 2, 34, 0)
    display.lock.release()
    Menu.B_menu.change_x_offset(47)
    Menu.B_menu.change_y_offset(43)
    cls.display_menu_and_get_choice(display, Menu.B_menu, undisplay=False)

    display.lock.acquire()
    display_direct.fill(0)
    display.lock.release()

  @classmethod
  def display_board_info(cls, display: OLED) -> None:
    display.lock.acquire()
    display.display_loading_screen()
    display.lock.release()

    report = ""
  
    cls.uart1_com.send(Com.BLUETOOTH, Com.NAME)
    ret = Board.uart1_com.blocking_read(Com.CONFIRM).decode()
    report += f"Bluetooth Name:\n  {ret}\n"

    cls.uart1_com.send(Com.BLUETOOTH, Com.CONNECTED)
    ret, _ = Board.uart1_com.wait_for_reject_or_confirm()
    if ret:
      report += f"Ble Status:\n  Connected\n"
    else:
      report += f"Ble Status:\n  Unconnected\n"

    current_config_name = Config.get_default_config().split(".")[0]
    report += f"Current Config\n  {current_config_name}\n"

    cls.uart1_com.send(Com.IMU, Com.ADDRESS)
    ret = Board.uart1_com.blocking_read(Com.CONFIRM).decode()
    if len(ret) == 0:
      addresses = []
    else:
      addresses = [int(address) for address in ret.split(",")]
    report += f"Number of IMUs\nConnected: {len(addresses)}\n"

    if len(ret) != 0:
      report += f"The IMUs are on I2C Addresses:\n"
      for address in addresses:
        report += f"  {hex(address)}\n"

    cls.begin_text_viewer(Board.main_display, report)

  @classmethod
  def load_menu(cls):
    """ Main menu loop, blocks forever """
    # set current display to main menu
    current_menu = Menu.main_menu

    # menu loop
    while True:
      if current_menu == Menu.main_menu:
        choice_idx = Board.display_menu_and_get_choice(Board.main_display, current_menu)

        if choice_idx == 0: # Start Operation
          Board.start_operation(Board.main_display)
          current_menu = Menu.main_menu
        elif choice_idx == 1: # Settings
          current_menu = Menu.settings_menu
        elif choice_idx == 2: # Information
          Board.display_board_info(Board.main_display)
          current_menu = Menu.main_menu

      elif current_menu == Menu.settings_menu:
        choice_idx = Board.display_menu_and_get_choice(Board.main_display, current_menu)

        if choice_idx == 0: # General Menu
          current_menu = Menu.general_menu
        elif choice_idx == 1: # Configs Menu
          current_menu = Menu.configs_menu
        elif choice_idx == 2: # Others Menu
          current_menu = Menu.others_menu
        elif choice_idx == 3: # Back
          current_menu.change_highlight(0) # reset highlight
          current_menu = Menu.main_menu

      elif current_menu == Menu.general_menu:
        choice_idx = Board.display_menu_and_get_choice(Board.main_display, current_menu)

        if choice_idx == 0: # Change Volume
          Board.change_volume(Board.main_display)
          current_menu = Menu.general_menu
        elif choice_idx == 1: # Change Bluetooth name
          Board.change_bluetooth_advertise_name(Board.main_display)
          current_menu = Menu.general_menu
        elif choice_idx == 2: # View IMU polling rate
          Board.estimate_polling_rate_and_display(Board.main_display)
          current_menu = Menu.general_menu
        elif choice_idx == 3: # Back
          current_menu.change_highlight(0) # reset highlight
          current_menu = Menu.settings_menu

      elif current_menu == Menu.configs_menu:
        choice_idx = Board.display_menu_and_get_choice(Board.main_display, current_menu)

        if choice_idx == 0: # Create Config
          Board.create_config(Board.main_display)
        elif choice_idx == 1: # Manage Config
          while Board.manage_config(Board.main_display):
            pass
          current_menu = Menu.configs_menu
        elif choice_idx == 2: # Back
          current_menu.change_highlight(0) # reset highlight
          current_menu = Menu.settings_menu
      
      elif current_menu == Menu.others_menu:
        choice_idx = Board.display_menu_and_get_choice(Board.main_display, current_menu)
        
        if choice_idx == 0: # Snake
          Board.begin_snake_game(Board.main_display, max_score=40)
          current_menu = Menu.others_menu
        elif choice_idx == 1: # Mystery
          Board.buzzer.custom_sound(Buzzer.mystery)
          current_menu.change_highlight(0) # reset highlight
          current_menu = Menu.main_menu
        elif choice_idx == 2: # Back
          current_menu.change_highlight(0) # reset highlight
          current_menu = Menu.settings_menu
