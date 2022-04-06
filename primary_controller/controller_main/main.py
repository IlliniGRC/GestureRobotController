import time
import driver.utils as utils

from functionality.board import Board
from functionality.wt901 import WT901
from functionality.communication import Communication as Com

def main():
  """ Main function, contains event loop """
  # auxiliary initializations
  Board.auxiliary_init()

  # waiting for peripheral controller to connect
  while True:
    msg = Board.uart1_com.read_all(Com.BOOT_UP)
    if msg != None:
      break
    Board.uart1_com.send(Com.BOOT_UP, "")
    Board.status_led.show_info()
    time.sleep_ms(1000)

  time.sleep_ms(200)
  Board.uart1_com.discard_all(Com.BOOT_UP)
  
  Board.event_loop()

if __name__ == '__main__':
  # !!! Do NOT modify this function !!!
  # allow REPL to run in parallel with main function
  utils.execute_main(main)
