from driver.ssd1306 import SSD1306
import driver.utils as utils
from driver.display import OLED
import gc

class Menu:
  """ Simplifies the creation and displaying of menus and special menus (e.g. keyboard) """
  # rotate choice
  CHANGE_NEXT = 0
  CHANGE_PREV = 1

  main_menu = None
  settings_menu = None
  general_menu = None
  configs_menu = None
  volume_menu = None

  # special menu
  keyboard = None
  #   \x08 backspace \x06 confirm \x18 cancel
  keyboard_sequence = "QWERTYUIOP-ASDFGHJKL_ZXCVBNM\x08\x06\x18"
  
  # generic menus
  YN_menu = None  # Yes No
  YCN_menu = None # Yes Cancel No
  RQ_menu = None  # Restart Quit
  B_menu = None   # Back 

  @classmethod
  def auxiliary_init(cls):
    """ Initializations that fulfill full requirements for system to operate """
    cls.main_menu = Menu()
    cls.main_menu.add_choice(4, 14, ["Start Operation"])
    cls.main_menu.add_choice(32, 32, ["Settings"])

    cls.settings_menu = Menu()
    cls.settings_menu.add_choice(36, 4, ["General"])
    cls.settings_menu.add_choice(40, 16, ["Config"])
    cls.settings_menu.add_choice(44, 28, ["Snake"])
    cls.settings_menu.add_choice(36, 40, ["Mystery"])
    cls.settings_menu.add_choice(48, 52, ["Back"])

    cls.general_menu = Menu()
    cls.general_menu.add_choice(40, 10, ["Volume"])
    cls.general_menu.add_choice(16, 24, ["Estimate IMU", "Polling Rate"])
    cls.general_menu.add_choice(48, 46, ["Back"])

    cls.configs_menu = Menu()
    cls.configs_menu.add_choice(20, 9, ["Load Config"])
    cls.configs_menu.add_choice(12, 22, ["Create Config"])
    cls.configs_menu.add_choice(20, 35, ["View Config"])
    cls.configs_menu.add_choice(48, 48, ["Back"])

    cls.volume_menu = Menu()
    cls.volume_menu.add_choice(38, 35, ["-"])
    cls.volume_menu.add_choice(82, 35, ["+"])
    cls.volume_menu.add_choice(48, 48, ["Back"])

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
    """ An item of the menu """
    # alignment methods for multi-line choice
    ALIGN_LEFT   = 0x0
    ALIGN_MIDDLE = 0x1
    ALIGN_RIGHT  = 0x2
    
    def __init__(self, x: int, y: int, texts: list, align: int, border_width: int) -> None:
      """ Create one menu item using following properties
          `x`: horizontal offset of the choice on the screen
          `y`: vertical offset of the choice on the screen 
          `texts`: displayed texts of the choice, must be a list containing items as lines
          `align`: alignment methods for multi-line choice
          `border_width`: width of highlight boarder when the choice is highlighted """
      utils.ASSERT_TRUE(x >= border_width and x < OLED.WIDTH - border_width, "Menu invalid start x")
      utils.ASSERT_TRUE(y >= border_width and y < OLED.HEIGHT - border_width, "Menu invalid start y")
      utils.ASSERT_TRUE(type(texts) == list, "Menu tests must be list")
      utils.ASSERT_TRUE(align >= self.ALIGN_LEFT and align <= self.ALIGN_RIGHT, "Menu invalid alignment")
      self.x = x
      self.y = y
      self.texts = texts
      self.text_width = max([len(t) for t in texts]) * OLED.CHAR_WIDTH
      self.text_height = len(texts) * OLED.CHAR_HEIGHT
      self.horizontal_offset = [0 for _ in range(len(texts))]

      self.highlight_x = self.x - border_width
      self.highlight_y = self.y - border_width
      self.highlight_width = self.text_width + 2 * border_width
      self.highlight_height = self.text_height + 2 * border_width
      
      for i in range(len(texts)):
        text = self.texts[i]
        if align == self.ALIGN_LEFT:
          self.horizontal_offset[i] = 0
        elif align == self.ALIGN_RIGHT:
          self.horizontal_offset[i] = self.text_width - len(text) * OLED.CHAR_WIDTH
        else:
          self.horizontal_offset[i] = (self.text_width - len(text) * OLED.CHAR_WIDTH) // 2

  def __init__(self) -> None:
    """ Create an empty menu """
    self.__choices = []
    self.__highlight_index = 0
    self.__visible_indexes = set()
    self.__x_offset = 0
    self.__y_offset = 0
    
  def change_x_offset(self, new_x: int) -> None:
    """ Change the horizontal offset of the whole menu """
    self.__x_offset = new_x

  def change_y_offset(self, new_y: int) -> None:
    """ Change the vertical offset of the whole menu """
    self.__y_offset = new_y

  def add_choice(self, x: int, y: int, texts: list, align: int=_MenuItem.ALIGN_MIDDLE, 
      border_width: int=1) -> None:
    """ Append a new choice to the end of menu
        `x`: horizontal offset of the choice on the screen
        `y`: vertical offset of the choice on the screen 
        `texts`: displayed texts of the choice, must be a list containing items as lines
        `align`: alignment methods for multi-line choice
        `border_width`: width of highlight boarder when the choice is highlighted """
    self.__visible_indexes.add(len(self.__choices))
    self.__choices.append(Menu._MenuItem(x, y, texts, align, border_width))

  def replace_choice(self, idx: int, x: int, y: int, texts: list, align: int=_MenuItem.ALIGN_MIDDLE, 
      border_width: int=1) -> None:
    """ Replace the choice at given index of the menu to a new choice
        `idx`: the destinated index of the menu item wished to be replaced
        `x`: horizontal offset of the choice on the screen
        `y`: vertical offset of the choice on the screen 
        `texts`: displayed texts of the choice, must be a list containing items as lines
        `align`: alignment methods for multi-line choice
        `border_width`: width of highlight boarder when the choice is highlighted """
    utils.ASSERT_TRUE(idx >= 0 and idx < len(self.__choices), "Menu invalid replace index")
    self.__choices[idx] = Menu._MenuItem(x, y, texts, align, border_width)
    gc.collect()

  def insert_choice(self, idx: int, x: int, y: int, texts: list, align: int=_MenuItem.ALIGN_MIDDLE, 
      border_width: int=1) -> int:
    """ Insert the choice at given index of the menu to a new choice
        `idx`: the destinated index of the menu item wished to be inserted
        `x`: horizontal offset of the choice on the screen
        `y`: vertical offset of the choice on the screen 
        `texts`: displayed texts of the choice, must be a list containing items as lines
        `align`: alignment methods for multi-line choice
        `border_width`: width of highlight boarder when the choice is highlighted """
    utils.ASSERT_TRUE(idx >= 0 and idx <= len(self.__choices), "Menu invalid insert index")
    new_item = Menu._MenuItem(x, y, texts, align, border_width)
    self.__choices.insert(idx, new_item)
    real_idx = self.__choices.index(new_item)
    self.__visible_indexes = set([i if i < real_idx else i + 1 for i in self.__visible_indexes])
    self.__visible_indexes.add(real_idx)
    if real_idx < self.__highlight_index:
      self.__highlight_index += 1
    return real_idx

  def remove_choice(self, idx: int) -> _MenuItem:
    """ Remove the choice at given index of the menu to a new choice
        `idx`: the destinated index of the menu item wished to be removed
        Notice: If successfully removed, all menu items that have higher index number than the 
        removed one will have their index reduced by one """
    utils.ASSERT_TRUE(idx >= 0 and idx < len(self.__choices), "Menu invalid change index")
    self.__visible_indexes = set([i if i < idx else i - 1 for i in self.__visible_indexes])
    self.__visible_indexes.discard(idx)
    if idx < self.__highlight_index:
      self.__highlight_index -= 1
    gc.collect()
    return self.__choices.pop(idx)

  def change_choice_visibility(self, idx: int, visible: bool) -> None:
    """ Change the visibility of a choice at given index of the menu
        `idx`: the destinated index of the menu item wished its visibility to be changed 
        `visible`: if the menu item is visible """
    if idx >= 0 and idx < len(self.__choices):
      if visible:
        self.__visible_indexes.add(idx)
      else:
        self.__visible_indexes.discard(idx)
    else:
      utils.EXPECT_TRUE(False, "Menu invalid change visibility index")

  def display_choices(self, display: OLED, redraw_invisible_choices: bool=True) -> None:
    """ Display all choices on given display
        `display`: the destinated index of the menu item wished its visibility to be changed 
        `redraw_invisible_choice`: if the invisible items needed to be redrawn as invisible """
    utils.ASSERT_TRUE(len(self.__choices) != 0, "Menu empty")
    utils.ASSERT_TRUE(len(self.__visible_indexes) != 0, "Menu display choices empty")
    if self.__highlight_index not in self.__visible_indexes:
      utils.EXPECT_TRUE(False, "Menu invalid choice")
      # no good choice of indexing sets
      self.__highlight_index = self.__visible_indexes.pop()
      self.__visible_indexes.add(self.__highlight_index)

    display.lock.acquire()
    display_direct = display.get_direct_control()
    for idx in range(len(self.__choices)):
      choice: Menu._MenuItem = self.__choices[idx]
      if idx == self.__highlight_index:
        continue
      elif idx in self.__visible_indexes:
        self.__display_single_choice(display_direct, choice)
      else:
        if redraw_invisible_choices:
          display_direct.fill_rect(choice.highlight_x, choice.highlight_y, 
              choice.highlight_width, choice.highlight_height, 0)
    self.__display_single_choice(display_direct, self.__choices[self.__highlight_index], highlight=True)
    display_direct.show()
    display.lock.release()

  def undisplay_choices(self, display: OLED, redraw_invisible_choices: bool=True, 
      reset_offsets: bool=True) -> None:
    """ Display all choices on given display
        `display`: the destinated index of the menu item wished its visibility to be changed 
        `redraw_invisible_choice`: if the invisible items needed to be redrawn as invisible 
        `reset_offsets`: reset the offsets of the menu to zero """
    display.lock.acquire()
    display_direct = display.get_direct_control()
    for idx in range(len(self.__choices)):
      choice: Menu._MenuItem = self.__choices[idx]
      if idx == self.__highlight_index or idx in self.__visible_indexes:
        self.__display_single_choice_background(display_direct, choice, 0)
      else:
        if redraw_invisible_choices:
          self.__display_single_choice_background(display_direct, choice, 0)
    display_direct.show()
    display.lock.release()
    if reset_offsets:
      self.__x_offset = 0
      self.__y_offset = 0

  def rotate_highlight(self, direction: int) -> int:
    """ Rotate the hightlight option using direction specified
        `direction`: either Menu.CHANGE_PREV or Menu.CHANGE_NEXT
        `returns`: current choice index that is highlighted """
    utils.EXPECT_TRUE(direction == Menu.CHANGE_NEXT or direction == Menu.CHANGE_PREV, 
        "Menu invalid change direction")
    l = len(self.__choices)
    step = l - 1 if direction == Menu.CHANGE_PREV else 1
    self.__highlight_index = (self.__highlight_index + step) % l
    while self.__highlight_index not in self.__visible_indexes:
      self.__highlight_index = (self.__highlight_index + step) % l
    return self.__highlight_index

  def change_highlight(self, idx: int) -> None:
    """ Change the hightlight option using index specified
        `index`: index of the menu item wished to be highlighted """
    utils.ASSERT_TRUE(idx in range(len(self.__choices)), "Menu invalid change highlight, not in choices")
    utils.EXPECT_TRUE(idx in self.__visible_indexes, "Menu invalid change hightlight, not in visible choices")
    self.__highlight_index = idx

  def choose(self, reset_idx: int=-1) -> int:
    """ Choose the current highlighted choice and return the index of that choice in the menu
        `reset_idx`: index of the menu item wished to be highlighted after selection, -1 if non-restoring """
    ret = self.__highlight_index
    if reset_idx != -1:
      self.change_highlight(reset_idx)
    return ret

  def __display_single_choice_background(self, display_direct: SSD1306, choice: _MenuItem, color: int) -> None:
    """ Display the background for the specified choice 
        `display_direct`: the display framebuffer to draw on 
        `choice`: the choice to be rendered
        `color`: color of background """
    x = self.__x_offset + choice.highlight_x
    y = self.__y_offset + choice.highlight_y
    display_direct.fill_rect(x, y, choice.highlight_width, choice.highlight_height, color)

  def __display_single_choice(self, display_direct: SSD1306, choice: _MenuItem, highlight: bool=False) -> None:
    """ Display the specified choice 
        `display_direct`: the display framebuffer to draw on 
        `choice`: the choice to be rendered
        `highlight`: if the choice is highlighted """
    self.__display_single_choice_background(display_direct, choice, int(highlight))
    for i in range(len(choice.texts)):
      x = self.__x_offset + choice.x + choice.horizontal_offset[i]
      y = self.__y_offset + choice.y + i * OLED.CHAR_HEIGHT
      display_direct.text(choice.texts[i], x, y, int(not highlight))

  def print_status(self) -> None:
    """ Report status of current menu, for debug use """
    print(f"No. of Choices: {len(self.__choices)}")
    print(f"Visible Choices: {self.__visible_indexes}")
    print(f"Highlight: {self.__highlight_index}")
    for i, choice in enumerate(self.__choices):
      print(f" Choice: {i}, X: {choice.x}, Y: {choice.y}, Texts: {choice.texts}")
