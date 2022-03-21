import machine, _thread, time, random, framebuf, math

from driver.ssd1306 import SSD1306, SSD1306_I2C
import driver.utils as utils


class Drawing:
  """ Storage class for various drawings """
  controller_logo = None
  micropython_logo = None
  warning_sign = None

  @classmethod 
  def main_init(cls) -> None:
    """ Initializations that fulfill basic requirements for system to operate """
    cls.controller_logo = Drawing((), False).create_controller_logo()
    cls.micropython_logo = Drawing((), False).create_micropython_logo()

  @classmethod 
  def auxiliary_init(cls) -> None:
    """ Initializations that fulfill full requirements for system to operate """
    cls.warning_sign = Drawing((), False).create_warning_sign()

  def __init__(self, dimension: tuple, create_canvas: bool = True) -> None:
    """ Create a new Drawing
        `dimension`: the dimension of the drawing, in the form of (x, y)
        `create_canvas`: whether a storage space (bytearray) is created during initialization """
    self.__dim = dimension
    if create_canvas:
      byte_height = math.ceil(dimension[1] / 8)
      self.__canvas = framebuf.FrameBuffer(bytearray(dimension[0], byte_height), 
          self.__dim[0], self.__dim[1], framebuf.MONO_VLSB)

  def get_dimension(self) -> tuple:
    """ Get the dimension of current Drawing
        `returns`: the dimension of the drawing, in the form of (x, y) """
    return self.__dim

  def create_controller_logo(self) -> None:
    """ Create a controller logo """
    img = [
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 128, 192, 192, 192,
      192, 192, 192, 128,  32,  16,   8,  72,  36,  20, 148,  82,  74,  42, 170, 170,
      170, 170,  42,  74,  82, 148,  20,  36,  72,   8,  16,  32, 128, 192, 192, 192,
      192, 192, 192, 128,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0, 192, 240, 120, 124, 127, 127,   7, 103,
      231, 103,   7, 127, 124, 120, 124, 252, 252, 252, 252, 252, 252, 253, 252, 252,
      252, 252, 253, 252, 252, 252, 252, 252, 252, 124, 120, 124, 127,   7,  39, 119,
      39,   7, 127, 127, 124, 120, 240, 192,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0, 128, 254, 255, 255, 240, 240, 247, 247,   7,  50,
      56,  50,   7, 247, 247, 112,  48,  63,  63,  63, 120, 248, 248, 255, 191, 191,
      191, 191, 255, 248, 248, 125,  63,  63,  63,  48, 114, 247, 242,   0,  32, 112,
      32,   0, 242, 247, 242, 240, 255, 255, 254, 128,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0, 224, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
      255, 255, 127,  31,  56,  32,  96,  64,  64,  96,  32,  48,  31,   7,   7,   7,
        7,   7,   7,  31,  48,  32,  96,  64,  64,  96,  32,  56,  31, 127, 255, 255,
      255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 224,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   7,  15,  31,  63,  63,  63,  63,  63,  63,  31,  15,
        3,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   3,
      15,  31,  63,  63,  63,  63,  63,  63,  31,  15,   7,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
        0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0]
    self.__dim = (96, 44)
    self.__canvas = framebuf.FrameBuffer(bytearray(img), 
        self.__dim[0], self.__dim[1], framebuf.MONO_VLSB)
    return self

  def create_micropython_logo(self):
    """ Create a micropython logo"""
    self.__dim = (128, 32)
    self.__canvas = framebuf.FrameBuffer(bytearray(128 * 32 // 8), 
        self.__dim[0], self.__dim[1], framebuf.MONO_VLSB)
    self.__canvas.fill_rect(0, 0, 32, 32, 1)
    self.__canvas.fill_rect(2, 2, 28, 28, 0)
    self.__canvas.vline(9, 8, 22, 1)
    self.__canvas.vline(16, 2, 22, 1)
    self.__canvas.vline(23, 8, 22, 1)
    self.__canvas.fill_rect(26, 24, 2, 4, 1)
    self.__canvas.text('POWERED BY', 40, 6, 1)
    self.__canvas.text('MicroPython', 40, 18, 1)
    return self

  def create_warning_sign(self):
    """ Create a warning sign"""
    img = [  
      0,   0,   0,   0, 192,  96,  24, 230, 230,  24,  96, 192,   0,   0,   0,   0, 
      0,  48,  44,  35,  32,  32,  32,  43,  43,  32,  32,  32,  35,  44,  48,   0]
    self.__dim = (16, 15)
    self.__canvas = framebuf.FrameBuffer(bytearray(img), self.__dim[0], self.__dim[1], framebuf.MONO_VLSB)
    return self

  def get_framebuf(self) -> framebuf.FrameBuffer:
    """ Get the framebuf of current drawing, used when trying to render to display
        `returns`: the framebuf of given Drawing"""
    return self.__canvas


class OLED:
  """ Drives the SSD1306 OLED using IIC, async operation supported """
  IIC_ADDR = (0x3C, ) # all available IIC address that SSD1306 can be on
  WIDTH, HEIGHT = 128, 64 # dimension of the screen
  CHAR_WIDTH, CHAR_HEIGHT = 8, 8 # dimension of character on the screen
  INVERSE_PALETTE = framebuf.FrameBuffer(bytearray([1, 0]), 1, 2, framebuf.MONO_VLSB) # palette used to invert display
  
  def __init__(self, addr: int = 0x3C) -> None:
    """ Create an OLED instance using given IIC address
        `addr`: IIC address of the SSD1306"""
    utils.ASSERT_TRUE(addr in OLED.IIC_ADDR, "Invalid OLED IIC address")
    self.__i2c = machine.SoftI2C(sda = machine.Pin(4), scl = machine.Pin(5))
    self.__ssd1306 = SSD1306_I2C(OLED.WIDTH, OLED.HEIGHT, self.__i2c, addr)
    self.__quit_signal = False
    self.__quit_signal_lock = _thread.allocate_lock()

    self.lock = _thread.allocate_lock()

  def __read_quit_signal(self, reset: bool = False) -> bool:
    """ Read the quit signal once, non-blocking, should NOT be called
        `reset`: reset the quit signal if asserted
        `returns`: if the OLED is ordered to quit current screen """
    if not self.__quit_signal_lock.acquire(False):
      return False
    ret = self.__quit_signal
    if reset:
      self.__quit_signal = False
    self.__quit_signal_lock.release()
    return ret

  def __wait_for_quit_signal(self) -> None:
    """ Wait fot the quit signal to be asserted, blocking. Quit singal will be reset. 
        Should NOT be called"""
    while True:
      if not self.__quit_signal_lock.acquire(False):
        continue
      if self.__quit_signal:
        self.__quit_signal = False
        self.__quit_signal_lock.release()
        return
      self.__quit_signal_lock.release()
      time.sleep_ms(50)

  def notify_to_quit(self) -> bool:
    """ Notify the OLED to quit current screen. A warning is generated if there is nothing 
        occupying the display """
    if self.lock.locked():
      self.__quit_signal_lock.acquire()
      self.__quit_signal = True
      self.__quit_signal_lock.release()
      return True
    utils.EXPECT_TRUE(False, "OLED no current job")
    return False

  def clear_screen(self) -> None:
    """ Clear the given screen and show the empty screen """
    self.__ssd1306.fill(0)
    self.__ssd1306.show()

  def display_buffer(self, buffer: framebuf.FrameBuffer, position: tuple, 
                     inverse: bool = False, timeout_s: float = -1) -> bool:
    """ Display given framebuffer onto the screen
        `buffer`: the framebuffer to be displayed onto the screen
        `position`: display offset relative to left-top corner of screen, in the form of (x, y)
        `inverse`: invert the color of the buffer before display
        `timeout_s`: maximum time to wait before acquiring control of the screen """
    if not self.lock.acquire(True, timeout_s):
      return False

    if inverse:
      self.__ssd1306.blit(buffer, position[0], position[1], -1, OLED.INVERSE_PALETTE)
    else:
      self.__ssd1306.blit(buffer, position[0], position[1])
    self.__ssd1306.show()
    
    self.lock.release()
  
  def get_direct_control(self) -> SSD1306:
    """ Get the direct control of the SSD1306, useful when need dedicated drawings 
        `returns`: the SSD1306"""
    return self.__ssd1306

  def display_test_screen(self, ms: int = 500, timeout_s: float = -1) -> bool:
    """ Display test screen containing lots of "Hello World"s
        `ms`: display update interval
        `timeout_s`: maximum time to wait before acquiring control of the screen """
    if not self.lock.acquire(True, timeout_s):
      return False
    
    offset = 0;
    while True:
      self.__ssd1306.fill(0)
      for i in range(8):
        text = "Hello World" + str((i + offset) % 8)
        self.__ssd1306.text(text, 0, i * 8, 1)
      self.__ssd1306.show()
      offset = (offset + 1) % 8
      if self.__read_quit_signal(True):
        self.clear_screen()
        self.lock.release()
        return
      time.sleep_ms(ms)

  def display_random_lines(self, line_cnt: int = 5, ms: int = 500, timeout_s: float = -1) -> bool:
    """ Display random lines on the screen
        `ms`: display update interval
        `timeout_s`: maximum time to wait before acquiring control of the screen """
    if not self.lock.acquire(True, timeout_s):
      return False

    while True:
      self.__ssd1306.fill(0)
      for _ in range(line_cnt):
        x1 = random.randrange(0, OLED.WIDTH)
        x2 = random.randrange(0, OLED.WIDTH)
        y1 = random.randrange(0, OLED.HEIGHT)
        y2 = random.randrange(0, OLED.HEIGHT)
        self.__ssd1306.line(x1, y1, x2, y2, 1)
      self.__ssd1306.show()
      if self.__read_quit_signal(True):
        self.clear_screen()
        self.lock.release()
        return
      time.sleep_ms(ms)

  def display_start_screen(self) -> None:
    """ Display the start screen """
    self.lock.acquire()

    interval = 3
    step = 8
    utils.ASSERT_TRUE(OLED.WIDTH / step == OLED.WIDTH // step, "Invalid start screen step size")
    utils.ASSERT_TRUE(OLED.WIDTH // step - interval > 0, "Invalid start screen interval size")
    micropython_framebuf = Drawing.micropython_logo.get_framebuf()
    controller_framebuf = Drawing.controller_logo.get_framebuf()
    
    controller_dim = Drawing.controller_logo.get_dimension()
    lft_off, top_off = (OLED.WIDTH - controller_dim[0]) // 2, (64 - controller_dim[1]) // 2
    self.__ssd1306.fill(1)
    self.__ssd1306.blit(controller_framebuf, lft_off, top_off, -1, OLED.INVERSE_PALETTE)
    self.__ssd1306.show()
    time.sleep_ms(1000)
    
    for i in range(interval):
      self.__ssd1306.fill_rect(OLED.WIDTH - step * (i + 1), 0, step, 64, 0)
      self.__ssd1306.show()
      time.sleep_ms(10)
    
    for i in range(OLED.WIDTH / step - interval):
      self.__ssd1306.fill_rect(OLED.WIDTH - step * (i + interval + 1), 0, step * (i + interval + 1), 64, 0)
      self.__ssd1306.blit(micropython_framebuf, OLED.WIDTH - step * (i + 1), 8)
      self.__ssd1306.show()
      time.sleep_ms(10)
    
    for i in range(interval):
      self.__ssd1306.fill(0)
      self.__ssd1306.blit(micropython_framebuf, (interval - i - 1) * step, 8)
      self.__ssd1306.show()
      time.sleep_ms(10)

    time.sleep_ms(500)
    self.__ssd1306.text("Initializing...", 4, 54, 1)
    self.__ssd1306.show()

    utils.start_screen_exit_sig = True
    self.__wait_for_quit_signal()

    self.__ssd1306.fill(0)
    self.__ssd1306.show()

    self.lock.release()

  def display_no_connection(self):
    """ Display the no connection screen """
    if not self.lock.acquire():
      return False
    
    self.__ssd1306.fill(0)
    self.__ssd1306.blit(Drawing.controller_logo.get_framebuf(), 12, 8)
    self.__ssd1306.blit(Drawing.warning_sign.get_framebuf(), 86, 24)
    self.__ssd1306.text("No Connection", 12, 54, 1)
    self.__ssd1306.show()

    utils.start_screen_exit_sig = True
    self.__wait_for_quit_signal()

    self.__ssd1306.fill(0)
    self.__ssd1306.show()
      
    self.lock.release()

  def display_fatal(self):
    """ Display fatal error screen, TO BE IMPLEMENTED """
    if not self.lock.acquire():
      return False
    self.lock.release()
