import machine, _thread, time, random, framebuf, array, gc

from driver.ssd1306 import SSD1306, SSD1306_I2C
import driver.utils as utils


class Drawing:
  """ Storage class for various drawings """
  
  @classmethod
  def get_controller_logo(cls) -> framebuf:
    """ Create a controller logo """
    img = bytearray(b"\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\xc0\xc0\xc0\
\xc0\xc0\xc0\x80\x20\x10\x08\x48\x24\x14\x94\x52\x4a\x2a\xaa\xaa\
\xaa\xaa\x2a\x4a\x52\x94\x14\x24\x48\x08\x10\x20\x80\xc0\xc0\xc0\
\xc0\xc0\xc0\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\xc0\xf0\x78\x7c\x7f\x7f\x07\x67\
\xe7\x67\x07\x7f\x7c\x78\x7c\xfc\xfc\xfc\xfc\xfc\xfc\xfd\xfc\xfc\
\xfc\xfc\xfd\xfc\xfc\xfc\xfc\xfc\xfc\x7c\x78\x7c\x7f\x07\x27\x77\
\x27\x07\x7f\x7f\x7c\x78\xf0\xc0\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x80\xfe\xff\xff\xf0\xf0\xf7\xf7\x07\x32\
\x38\x32\x07\xf7\xf7\x70\x30\x3f\x3f\x3f\x78\xf8\xf8\xff\xbf\xbf\
\xbf\xbf\xff\xf8\xf8\x7d\x3f\x3f\x3f\x30\x72\xf7\xf2\x00\x20\x70\
\x20\x00\xf2\xf7\xf2\xf0\xff\xff\xfe\x80\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\xe0\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\
\xff\xff\x7f\x1f\x38\x20\x60\x40\x40\x60\x20\x30\x1f\x07\x07\x07\
\x07\x07\x07\x1f\x30\x20\x60\x40\x40\x60\x20\x38\x1f\x7f\xff\xff\
\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xe0\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x07\x0f\x1f\x3f\x3f\x3f\x3f\x3f\x3f\x1f\x0f\
\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\
\x0f\x1f\x3f\x3f\x3f\x3f\x3f\x3f\x1f\x0f\x07\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    canvas = framebuf.FrameBuffer(bytearray(img), 96, 39, framebuf.MONO_VLSB)
    return canvas

  @classmethod
  def get_micropython_logo(cls) -> framebuf:
    """ Create a micropython logo"""
    canvas = framebuf.FrameBuffer(bytearray(128 * 32 // 8), 128, 32, framebuf.MONO_VLSB)
    canvas.fill_rect(0, 0, 32, 32, 1)
    canvas.fill_rect(2, 2, 28, 28, 0)
    canvas.vline(9, 8, 22, 1)
    canvas.vline(16, 2, 22, 1)
    canvas.vline(23, 8, 22, 1)
    canvas.fill_rect(26, 24, 2, 4, 1)
    canvas.text('POWERED BY', 40, 6, 1)
    canvas.text('MicroPython', 40, 18, 1)
    return canvas

  @classmethod
  def get_warning_sign(cls) -> framebuf:
    """ Create a warning sign"""
    img = array.array("b", [  
      0,   0,   0,   0, 192,  96,  24, 230, 230,  24,  96, 192,   0,   0,   0,   0, 
      0,  48,  44,  35,  32,  32,  32,  43,  43,  32,  32,  32,  35,  44,  48,   0])
    canvas = framebuf.FrameBuffer(bytearray(img), 16, 15, framebuf.MONO_VLSB)
    return canvas

class OLED:
  """ Drives the SSD1306 OLED using I2C, async operation supported """
  I2C_ADDR = (0x3C, 0x3D) # all available I2C address that SSD1306 can be on
  WIDTH, HEIGHT = 128, 64 # dimension of the screen
  CHAR_WIDTH, CHAR_HEIGHT = 8, 8 # dimension of character on the screen
  INVERSE_PALETTE = framebuf.FrameBuffer(bytearray([1, 0]), 1, 2, framebuf.MONO_VLSB) # palette used to invert display
  
  def __init__(self, addr: int = 0x3C) -> None:
    """ Create an OLED instance using given I2C address
        `addr`: I2C address of the SSD1306"""
    utils.ASSERT_TRUE(addr in OLED.I2C_ADDR, "Invalid OLED I2C address")
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

  def save_current_screen(self) -> None:
    self.__ssd1306.save_buffer()

  def redisplay_saved_screen(self) -> None:
    self.__ssd1306.redisplay_buffer()

  def display_loading_screen(self) -> None:
    """ Display the loading screen without acquiring display lock """
    self.__ssd1306.fill(0)
    self.__ssd1306.text("Loading...", 24, 28, 1)
    self.__ssd1306.show()

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
    micropython_framebuf = Drawing.get_micropython_logo()
    controller_framebuf = Drawing.get_controller_logo()
    
    controller_dim = (96, 44)
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
    gc.collect()

  def display_no_connection(self):
    """ Display the no connection screen """
    if not self.lock.acquire():
      return False
    
    self.__ssd1306.fill(0)
    self.__ssd1306.blit(Drawing.get_controller_logo(), 12, 8)
    self.__ssd1306.blit(Drawing.get_warning_sign(), 86, 24)
    self.__ssd1306.text("No Connection", 12, 54, 1)
    self.__ssd1306.show()

    utils.start_screen_exit_sig = True
    self.__wait_for_quit_signal()

    self.__ssd1306.fill(0)
    self.__ssd1306.show()
      
    self.lock.release()
    gc.collect()

  def display_fatal(self):
    """ Display fatal error screen, TO BE IMPLEMENTED """
    if not self.lock.acquire():
      return False
    self.lock.release()
