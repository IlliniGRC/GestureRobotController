import time
import driver.utils as utils

from functionality.board import Board
from functionality.menu import Menu
from functionality.communication import Communication as Com

# controls if start screen should be shown
show_start_screen = True

def main():
  """ Main function, contains event loop """
  # led flash
  Board.status_led.show_bootup()
  # auxiliary initializations
  Board.auxiliary_init()
  # buzzer and vmotor indicating running
  Board.buzzer.sound_bootup()
  Board.vmotor.slight_vibration()

  # waiting for main controller to connect
  while True:
    msg = Board.uart1_com.read_all(Com.START)
    if msg != None:
      Board.uart1_com.send(Com.START, Com.BOOT_UP)
      break
    time.sleep_ms(100)

  # wait for start screen to finish if not already
  while not utils.start_screen_exited():
    time.sleep_ms(200)

  # undisplay initialization screen
  if show_start_screen:
    Board.main_display.notify_to_quit()

  # begin operation
  Board.begin_operation()
  time.sleep_ms(100)

  # Example useage of Board.button
  #
  # while True:
  #   # BUTTON
  #   if Board.is_button_pending():
  #     messages = Board.get_all_button_message()
  #     print(f"BUTTON: {messages}")
  #   time.sleep_ms(10)

  # Begin menu loop
  Board.load_menu()

if __name__ == '__main__':
  # !!! Do NOT modify this function !!!
  # allow REPL to run in parallel with main function
  utils.execute_main(main, start_screen=show_start_screen)
