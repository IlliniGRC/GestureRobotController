import random, time
import driver.utils as utils
from driver.display import OLED
from functionality.board import Board
from functionality.menu import Menu

class SnakeGame:
  class _SnakeBody:
    def __init__(self, init_x: int, init_y: int, board_width: int, board_height: int) -> None:
      self.__board_width = board_width
      self.__board_height = board_height

      utils.ASSERT_TRUE(init_x > 0 and init_x < self.__board_width, "Snake invalid initial X position")
      utils.ASSERT_TRUE(init_y > 0 and init_y < self.__board_height, "Snake invalid initial Y position")
      
      self.tail_idx = 0 # inclusive
      self.head_idx = 0 # inclusive
      self.buffer_len = self.__board_width * self.__board_height
      self.x_sequence = bytearray(self.buffer_len)
      self.y_sequence = bytearray(self.buffer_len)
      self.x_sequence[0] = init_x
      self.y_sequence[0] = init_y
      self.need_extend_length = False
      self.body_set = set()
      self.body_set.add(init_y * self.__board_width + init_x)

    def get_head(self) -> tuple:
      return (self.x_sequence[self.head_idx], self.y_sequence[self.head_idx])

    def extend_length(self) -> None:
      self.need_extend_length = True

    def collide_with_body(self, x, y) -> bool:
      return (y * self.__board_width + x) in self.body_set
    
    def collide_with_wall(self, x, y) -> bool:
      return x < 0 or x >= self.__board_width or y < 0 or y > self.__board_height

    def step_forward(self, next_x, next_y) -> tuple:
      undisplay = None
      if self.need_extend_length:
        self.need_extend_length = False
      else:
        tail_x = self.x_sequence[self.tail_idx]
        tail_y = self.y_sequence[self.tail_idx]
        undisplay = (tail_x, tail_y)
        self.tail_idx = (self.tail_idx + 1) % self.buffer_len
        self.body_set.remove(tail_y * self.__board_width + tail_x)

      self.head_idx = (self.head_idx + 1) % self.buffer_len
      self.x_sequence[self.head_idx] = next_x
      self.y_sequence[self.head_idx] = next_y
      self.body_set.add(next_y * self.__board_width + next_x)
      return undisplay

    def reset(self, init_x: int, init_y: int):
      utils.ASSERT_TRUE(init_x > 0 and init_x < self.__board_width, "Snake invalid initial X position")
      utils.ASSERT_TRUE(init_y > 0 and init_y < self.__board_height, "Snake invalid initial Y position")
      self.tail_idx = 0 # inclusive
      self.head_idx = 0 # inclusive
      self.x_sequence[0] = init_x
      self.y_sequence[0] = init_y
      self.need_extend_length = False
      self.body_set.clear()
      self.body_set.add(init_y * self.__board_width + init_x)

  dir_up, dir_right, dir_down, dir_left = 0, 1, 2, 3
    
  def __init__(self, display: OLED, init_x: int, init_y: int, x_offset: int=35, y_offset: int=3) -> None:
    self.__x_offset = x_offset
    self.__y_offset = y_offset
    self.__board_width = OLED.WIDTH - 2 * self.__x_offset
    self.__board_height = OLED.HEIGHT - 2 * self.__y_offset

    self.__dir = SnakeGame.dir_up
    self.__snake_body = SnakeGame._SnakeBody(init_x, init_y, self.__board_width, self.__board_height)
    self.__direction_changed = False
    self.__food_x, self.__food_y = self.generate_food()
    self.__display = display
    self.__display_direct = display.get_direct_control()
    self.display_pixel(self.__food_x, self.__food_y, 1)
    self.display_boarder()
    self.display_update()
    

  def generate_food(self) -> tuple:
    return (random.randrange(self.__board_width), random.randrange(self.__board_height))

  def update(self) -> bool:
    next_x, next_y = self.__snake_body.get_head()
    if self.__dir == SnakeGame.dir_up:
      next_y -= 1
    elif self.__dir == SnakeGame.dir_right:
      next_x += 1
    elif self.__dir == SnakeGame.dir_down:
      next_y += 1
    elif self.__dir == SnakeGame.dir_left:
      next_x -= 1
    else:
      utils.ASSERT_TRUE(False, "Snake invalid direction")

    if self.__snake_body.collide_with_wall(next_x, next_y) or self.__snake_body.collide_with_body(next_x, next_y):
      buf_len = self.__snake_body.buffer_len
      score = (self.__snake_body.head_idx + buf_len - self.__snake_body.tail_idx) % buf_len
      self.game_over(score)
      return False

      
    if next_x == self.__food_x and next_y == self.__food_y:
      self.__snake_body.extend_length()
      self.__food_x, self.__food_y = self.generate_food()
      while self.__snake_body.collide_with_body(self.__food_x, self.__food_y):
        self.__food_x, self.__food_y = self.generate_food()
      Board.vibrate(1)

    undisplay = self.__snake_body.step_forward(next_x, next_y)

    self.__display.lock.acquire()
    self.display_pixel(next_x, next_y, 1)
    self.display_pixel(self.__food_x, self.__food_y, 1)
    if undisplay != None:
      self.display_pixel(undisplay[0], undisplay[1], 0)
    self.display_update()
    self.__display.lock.release()

    self.__direction_changed = False
    return True

  def change_direction(self, dir: int) -> bool:
    if self.__direction_changed:
      return False
    self.__dir = dir
    self.__direction_changed = True

  def rotate_clockwise(self) -> bool:
    self.change_direction((self.__dir + 1) % 4)

  def rotate_anticlockwise(self) -> bool:
    self.change_direction((self.__dir + 3) % 4)

  def game_over(self, score: int) -> None:
    self.display_game_over(score)
    self.display_update()
    Board.vibrate(3)

  def restart(self, init_x, init_y) -> None:
    self.__dir = SnakeGame.dir_up
    self.__snake_body.reset(init_x, init_y)
    self.__direction_changed = False
    self.__food_x, self.__food_y = self.generate_food()
    Board.main_display.clear_screen()
    self.display_pixel(self.__food_x, self.__food_y, 1)
    self.display_boarder()
    self.display_update()

  def display_boarder(self):
    l = self.__x_offset - 1
    r = OLED.WIDTH - self.__x_offset
    u = self.__y_offset - 1
    d = OLED.HEIGHT - self.__y_offset
    self.__display_direct.line(l, u, l, d, 1)
    self.__display_direct.line(l, u, r, u, 1)
    self.__display_direct.line(r, d, l, d, 1)
    self.__display_direct.line(r, d, r, u, 1)

  def display_pixel(self, x: int, y: int, color: int):
    self.__display_direct.pixel(x + self.__x_offset, y + self.__y_offset, color)

  def display_game_over(self, score: int):
    self.__display_direct.text("GAME OVER", 28, 16)
    self.__display_direct.text(f"Score: {score}", 28, 28)

  def display_update(self):
    self.__display_direct.show()


def begin_snake_game(display: OLED) -> None:
  init_x, init_y = 29, 29
  game = SnakeGame(display, init_x, init_y)
  while snake_game(game):
    game.restart(init_x, init_y)
  display.clear_screen()
  
def snake_game(game: SnakeGame) -> bool:
  while game.update():
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
