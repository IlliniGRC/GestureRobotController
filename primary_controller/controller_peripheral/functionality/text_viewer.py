import math

from driver.display import OLED

from functionality.menu import Menu

class TextViewer:

  def __init__(self) -> None:
    self.__PNE_menu = Menu() # <(prev) >(next) Exit
    self.__PNE_menu.add_choice(1, 55, ["<"])
    self.__PNE_menu.add_choice(75, 55, [">"])
    self.__PNE_menu.add_choice(95, 55, ["Exit"])
    self.__page_num_center = 42 # ((1 + 8 + 1) + (75 - 1)) / 2
    self.__reset_PNE_menu()
    self.__pages = []
    self.__chars_in_line = OLED.WIDTH // OLED.CHAR_WIDTH
    self.__lines_in_page = OLED.HEIGHT // OLED.CHAR_HEIGHT - 2
    self.__current_page = 0
    self.__total_pages = 0

  def __reset_PNE_menu(self) -> None:
    self.__PNE_menu.change_choice_visibility(0, False)
    self.__PNE_menu.change_choice_visibility(1, True)
    self.__PNE_menu.change_highlight(1)

  def __set_PNE_menu_zero_or_one_page(self) -> None:
    self.__PNE_menu.change_choice_visibility(0, False)
    self.__PNE_menu.change_choice_visibility(1, False)
    self.__PNE_menu.change_highlight(2)

  def __get_page_num_display(self) -> tuple:
    offset_page = self.__current_page + 1
    page_num_display = f"{offset_page}/{self.__total_pages}"
    x_offset = self.__page_num_center - OLED.CHAR_WIDTH * (0.5 + len(str(offset_page)))
    y_offset = 55
    return int(x_offset), int(y_offset), page_num_display

  def set_text_to_view(self, text: str, wrap_content: bool, delimiter: str):
    self.__pages.clear()
    if text != None and text != "":
      preprocess = text.split(delimiter)
      if not wrap_content:
        for page_num in range(int(math.ceil(len(preprocess) / self.__lines_in_page))):
          page = []
          for line_num in range(
              min(self.__lines_in_page, len(preprocess) - page_num * self.__lines_in_page)):
            index = page_num * self.__lines_in_page + line_num
            page.append((True, preprocess[index][:self.__chars_in_line]))
          self.__pages.append(page)
      else:
        page = []
        for line in preprocess:
          view_line_num = 0
          first_line_indicator = True
          while view_line_num < len(line):
            page.append((first_line_indicator, line[view_line_num:view_line_num + self.__chars_in_line]))
            first_line_indicator = False
            view_line_num += self.__chars_in_line
          view_line_num = 0
          while view_line_num < len(page) - self.__lines_in_page:
            self.__pages.append(page[view_line_num:view_line_num + self.__lines_in_page])
            view_line_num += self.__lines_in_page
          page = page[view_line_num:]
        if len(page) != 0:
          self.__pages.append(page)
    self.__current_page = 0
    self.__total_pages = len(self.__pages)
    self.__reset_PNE_menu()

  def PNE_menu_rotate(self, direction: int) -> None:
    self.__PNE_menu.rotate_highlight(direction)

  def PNE_menu_choose(self) -> bool:
    choice_idx = self.__PNE_menu.choose()
    if choice_idx == 0: # prev
      self.__prev_page()
    elif choice_idx == 1: # next
      self.__next_page()
    elif choice_idx == 2: # exit
      self.__reset_PNE_menu()
      self.__current_page = 0
      return True
    return False

  def __next_page(self) -> None:
    if self.__total_pages <= 1 or self.__current_page == self.__total_pages - 1:
      return
    if self.__current_page == 0:
      self.__PNE_menu.change_choice_visibility(0, True)
    elif self.__current_page == self.__total_pages - 2:
      self.__PNE_menu.change_choice_visibility(1, False)
      self.__PNE_menu.change_highlight(0)
    self.__current_page += 1
      
  def __prev_page(self) -> None:
    if self.__total_pages <= 1 or self.__current_page == 0:
      return
    if self.__current_page == self.__total_pages - 1:
      self.__PNE_menu.change_choice_visibility(1, True)
    elif self.__current_page == 1:
      self.__PNE_menu.change_choice_visibility(0, False)
      self.__PNE_menu.change_highlight(1)
    self.__current_page -= 1
      
  def view_on_display(self, display: OLED) -> None:
    display_direct = display.get_direct_control()
    display.lock.acquire()
    if self.__total_pages == 0:
      display_direct.text("No Content", 24, 28, 1)
      self.__set_PNE_menu_zero_or_one_page()
    else:
      if self.__total_pages == 1:
        self.__set_PNE_menu_zero_or_one_page()
      current_page_texts = self.__pages[self.__current_page]
      for line_num in range(len(current_page_texts)):
        line_indicator, line = current_page_texts[line_num]
        y_offset = line_num * (OLED.CHAR_HEIGHT + 1)
        if line_indicator:
          display_direct.pixel(0, y_offset, 1)
        display_direct.text(line, 0, y_offset)
      x, y, page_num_display = self.__get_page_num_display()
      display_direct.text(page_num_display, x, y)
    display.lock.release()

    self.__PNE_menu.display_choices(display)

