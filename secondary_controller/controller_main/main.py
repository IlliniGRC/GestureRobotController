import driver.utils as utils

from functionality.board import Board

def main():
  """ Main function, contains event loop """
  # auxiliary initializations
  Board.auxiliary_init()

  Board.status_led.show_bootup()

  Board.event_loop()

if __name__ == '__main__':
  # !!! Do NOT modify this function !!!
  # allow REPL to run in parallel with main function
  utils.execute_main(main)
