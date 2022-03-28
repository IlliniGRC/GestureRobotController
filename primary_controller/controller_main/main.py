import time
import driver.utils as utils

from functionality.board import Board
from functionality.wt901 import WT901

def main():
  """ Main function, contains event loop """
  # auxiliary initializations
  Board.auxiliary_init()

  # Example useage of Board.uart1 and Board.button
  #
  # while True:
  #   # UART
  #   if Board.is_uart1_pending():
  #     messages = Board.get_all_uart1_message()
  #     print(f"UART: {messages}")
  #   time.sleep_ms(50)

  imu0x50 = WT901(0x50, Board.i2c)
  imu0x52 = WT901(0x52, Board.i2c)

  while True:
    # UART
    if Board.is_uart1_pending():
      messages = Board.get_all_uart1_message()
      print(f"UART: {messages}")

    # print(f"50: {imu0x50.get_angle()}", end="")
    # print(f"52: {imu0x52.get_angle()}")
    time.sleep_ms(100)


if __name__ == '__main__':
  # !!! Do NOT modify this function !!!
  # allow REPL to run in parallel with main function
  utils.execute_main(main)
