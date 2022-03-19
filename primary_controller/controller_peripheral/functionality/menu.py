from driver.ssd1306 import SSD1306
import driver.utils as utils
from driver.display import OLED
import gc

class Menu:
  # rotate choice
  CHANGE_NEXT = 0
  CHANGE_PREV = 1

  main_menu = None
  settings_menu = None

  # special menu
  keyboard = None
  #   \x08 backspace \x06 confirm \x18 cancel
  keyboard_sequence = "QWERTYUIOP-ASDFGHJKL_ZXCVBNM\x08\x06\x18"
  
  # generaic menus
  YN_menu = None  # Yes No
  YCN_menu = None # Yes Cancel No
  RQ_menu = None  # Restart Quit
  B_menu = None   # Back 

  @classmethod
  def auxiliary_init(cls):
    """ Initializations that fulfill full requirements for system to operate """
    cls.main_menu = Menu()
    cls.main_menu.add_choice(4, 14, ["Start Operation"])
    cls.main_menu.add_choice(32, 28, ["Settings"])
    cls.main_menu.add_choice(44, 44, ["Snake"])

    cls.settings_menu = Menu()
    cls.settings_menu.add_choice(20, 9, ["Load Config"])
    cls.settings_menu.add_choice(12, 22, ["Create Config"])
    cls.settings_menu.add_choice(20, 35, ["View Config"])
    cls.settings_menu.add_choice(48, 48, ["Back"])

    cls.keyboard = Menu()
    line_start = 10
    for i in range(11):
      cls.keyboard.add_choice(line_start + i * 10, 24, [cls.keyboard_sequence[i]])
    line_start = 15
    for i in range(10):
      cls.keyboard.add_choice(line_start + i * 10, 33, [cls.keyboard_sequence[i + 11]])
    line_start = 20
    for i in range(7):
      cls.keyboard.add_choice(line_start + i * 10, 42, [cls.keyboard_sequence[i + 21]])
    cls.keyboard.add_choice(92, 42, ["<-"])
    cls.keyboard.add_choice(8, 51, ["Confirm"])
    cls.keyboard.add_choice(72, 51, ["Cancel"])

    cls.YN_menu = Menu()
    cls.YN_menu.add_choice(20, 1, ["Yes"])
    cls.YN_menu.add_choice(88, 1, ["No"])
    cls.YN_menu.change_highlight(1)

    cls.YCN_menu = Menu()
    cls.YCN_menu.add_choice(4, 1, ["Yes"])
    cls.YCN_menu.add_choice(40, 1, ["Cancel"])
    cls.YCN_menu.add_choice(104, 1, ["No"])
    cls.YCN_menu.change_highlight(2)

    cls.RQ_menu = Menu()
    cls.RQ_menu.add_choice(13, 1, ["Restart"])
    cls.RQ_menu.add_choice(83, 1, ["Quit"])

    cls.B_menu = Menu()
    cls.B_menu.add_choice(1, 1, ["Back"])

  class _MenuItem:
    ALIGN_LEFT   = 0x0
    ALIGN_MIDDLE = 0x1
    ALIGN_RIGHT  = 0x2
    
    def __init__(self, x: int, y: int, texts: list, align: int, boarder_width: int) -> None:
      utils.ASSERT_TRUE(x >= boarder_width and x < OLED.WIDTH - boarder_width, "Menu invalid start x")
      utils.ASSERT_TRUE(y >= boarder_width and y < OLED.HEIGHT - boarder_width, "Menu invalid start y")
      utils.ASSERT_TRUE(align >= self.ALIGN_LEFT and align <= self.ALIGN_RIGHT, "Menu invalid alignment")
      self.x = x
      self.y = y
      self.texts = texts
      self.text_width = max([len(t) for t in texts]) * OLED.CHAR_WIDTH
      self.text_height = len(texts) * OLED.CHAR_HEIGHT
      self.horizontal_offset = [0 for _ in range(len(texts))]

      self.highlight_x = self.x - boarder_width
      self.highlight_y = self.y - boarder_width
      self.highlight_width = self.text_width + 2 * boarder_width
      self.highlight_height = self.text_height + 2 * boarder_width
      
      for i in range(len(texts)):
        text = self.texts[i]
        if align == self.ALIGN_LEFT:
          self.horizontal_offset[i] = 0
        elif align == self.ALIGN_RIGHT:
          self.horizontal_offset[i] = self.text_width - len(text) * OLED.CHAR_WIDTH
        else:
          self.horizontal_offset[i] = (self.text_width - len(text) * OLED.CHAR_WIDTH) // 2

  def __init__(self) -> None:
    self.__choices = []
    self.__highlight_idx = 0
    self.__visiable_idxs = set()
    self.__x_offset = 0
    self.__y_offset = 0
    
  def change_x_offset(self, new_x: int) -> None:
    self.__x_offset = new_x

  def change_y_offset(self, new_y: int) -> None:
    self.__y_offset = new_y

  def add_choice(self, x: int, y: int, texts: list, align: int=_MenuItem.ALIGN_MIDDLE, 
      boarder_width: int=1) -> None:
    self.__visiable_idxs.add(len(self.__choices))
    self.__choices.append(Menu._MenuItem(x, y, texts, align, boarder_width))

  def replace_choice(self, idx, x: int, y: int, texts: list, align: int=_MenuItem.ALIGN_MIDDLE, 
      boarder_width: int=1) -> None:
    utils.ASSERT_TRUE(idx >= 0 and idx < len(self.__choices), "Menu invalid replace index")
    self.__choices[idx] = Menu._MenuItem(x, y, texts, align, boarder_width)
    gc.collect()

  def insert_choice(self, idx, x: int, y: int, texts: list, align: int=_MenuItem.ALIGN_MIDDLE, 
      boarder_width: int=1) -> int:
    utils.ASSERT_TRUE(idx >= 0 and idx <= len(self.__choices), "Menu invalid insert index")
    new_item = Menu._MenuItem(x, y, texts, align, boarder_width)
    self.__choices.insert(idx, new_item)
    real_idx = self.__choices.index(new_item)
    self.__visiable_idxs = set([i if i < real_idx else i + 1 for i in self.__visiable_idxs])
    self.__visiable_idxs.add(real_idx)
    if real_idx < self.__highlight_idx:
      self.__highlight_idx += 1
    return real_idx

  def remove_choice(self, idx) -> _MenuItem:
    utils.ASSERT_TRUE(idx >= 0 and idx < len(self.__choices), "Menu invalid change index")
    self.__visiable_idxs = set([i if i < idx else i - 1 for i in self.__visiable_idxs])
    self.__visiable_idxs.discard(idx)
    if idx < self.__highlight_idx:
      self.__highlight_idx -= 1
    gc.collect()
    return self.__choices.pop(idx)

  def change_choice_visability(self, idx: int, visability: bool) -> None:
    if idx >= 0 and idx < len(self.__choices):
      if visability:
        self.__visiable_idxs.add(idx)
      else:
        self.__visiable_idxs.discard(idx)
    else:
      utils.EXPECT_TRUE(False, "Menu invalid change visability index")

  def display_choices(self, display: OLED, redraw_undisplayed_choice: bool=True) -> None:
    utils.ASSERT_TRUE(len(self.__choices) != 0, "Menu empty")
    utils.ASSERT_TRUE(len(self.__visiable_idxs) != 0, "Menu display choices empty")
    if self.__highlight_idx not in self.__visiable_idxs:
      utils.EXPECT_TRUE(False, "Menu invalid choice")
      # no good choice of indexing sets
      self.__highlight_idx = self.__visiable_idxs.pop()
      self.__visiable_idxs.add(self.__highlight_idx)

    display.lock.acquire()
    display_direct = display.get_direct_control()
    for idx in range(len(self.__choices)):
      choice: Menu._MenuItem = self.__choices[idx]
      if idx == self.__highlight_idx:
        continue
      elif idx in self.__visiable_idxs:
        self.__display_single_choice(display_direct, choice)
      else:
        if redraw_undisplayed_choice:
          display_direct.fill_rect(choice.highlight_x, choice.highlight_y, 
              choice.highlight_width, choice.highlight_height, 0)
    self.__display_single_choice(display_direct, self.__choices[self.__highlight_idx], highlight=True)
    display_direct.show()
    display.lock.release()

  def undisplay_choices(self, display: OLED, redraw_undisplayed_choice: bool=True, reset_offsets: bool=True) -> None:
    display.lock.acquire()
    display_direct = display.get_direct_control()
    for idx in range(len(self.__choices)):
      choice: Menu._MenuItem = self.__choices[idx]
      if idx == self.__highlight_idx or idx in self.__visiable_idxs:
        self.__display_single_choice_background(display_direct, choice, 0)
      else:
        if redraw_undisplayed_choice:
          self.__display_single_choice_background(display_direct, choice, 0)
    display_direct.show()
    display.lock.release()
    if reset_offsets:
      self.__x_offset = 0
      self.__y_offset = 0

  def rotate_highlight(self, direction: int) -> int:
    utils.EXPECT_TRUE(direction == Menu.CHANGE_NEXT or direction == Menu.CHANGE_PREV, "Menu invalid change direction")
    l = len(self.__choices)
    step = l - 1 if direction == Menu.CHANGE_PREV else 1
    self.__highlight_idx = (self.__highlight_idx + step) % l
    while self.__highlight_idx not in self.__visiable_idxs:
      self.__highlight_idx = (self.__highlight_idx + step) % l
    return self.__highlight_idx

  def change_highlight(self, idx: int) -> int:
    utils.ASSERT_TRUE(idx in range(len(self.__choices)), "Menu invalid change highlight, not in choices")
    utils.EXPECT_TRUE(idx in self.__visiable_idxs, "Menu invalid change hightlight, not in visiablie choices")
    self.__highlight_idx = idx
    return self.__highlight_idx

  def choose(self, reset_idx: int=-1) -> int:
    ret = self.__highlight_idx
    if reset_idx != -1:
      self.change_highlight(reset_idx)
    return ret

  def __display_single_choice_background(self, display_direct: SSD1306, 
      choice: _MenuItem, color: int) -> None:
    x = self.__x_offset + choice.highlight_x
    y = self.__y_offset + choice.highlight_y
    display_direct.fill_rect(x, y, choice.highlight_width, choice.highlight_height, color)

  def __display_single_choice(self, display_direct: SSD1306, 
      choice: _MenuItem, highlight: bool=False) -> None:
    self.__display_single_choice_background(display_direct, choice, int(highlight))
    for i in range(len(choice.texts)):
      x = self.__x_offset + choice.x + choice.horizontal_offset[i]
      y = self.__y_offset + choice.y + i * OLED.CHAR_HEIGHT
      display_direct.text(choice.texts[i], x, y, int(not highlight))

  def print_status(self) -> None:
    print(f"No. of Choices: {len(self.__choices)}")
    print(f"Visiable Choices: {self.__visiable_idxs}")
    print(f"Highlight: {self.__highlight_idx}")
    for i, choice in enumerate(self.__choices):
      print(f" Choice: {i}, X: {choice.x}, Y: {choice.y}, Texts: {choice.texts}")
