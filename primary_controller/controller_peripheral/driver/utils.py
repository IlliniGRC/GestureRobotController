import os
from functionality.board import Board
from driver.threading import Thread

# Timer IDs used by different utilities
UART_TIMER_ID = 2
PWM_OUT_TIMER_ID = 3

start_screen_exit_sig = None # If start screen have exited
def execute_main(func, start_screen: bool = True) -> None:
  """ Execute the main function, call all the main_init functions before running the main thread
      `start_screen`: whether the start screen animation is played"""
  # main initializations
  Board.main_init()

  # display start screen if needed
  global start_screen_exit_sig
  start_screen_exit_sig = True
  if start_screen:
    start_screen_exit_sig = False
    start_screen_thread = Thread(Board.main_display.display_start_screen)
    start_screen_thread.run()

  # execute main
  main_thread = Thread(func)
  main_thread.run()

def start_screen_exited() -> bool:
  """ Check if the start screen animation have exited
      `returns`: whether the animation exited """
  global start_screen_exit_sig
  return start_screen_exit_sig


# Assertion -------------------------------------------------------------------

def EXPECT_TRUE(condition: bool, message: str) -> None:
  """ Expect condition to be true, generate a warning if violated, non-blocking """
  if not condition:
    print(f"Warning: {message}")
    Board.status_led.show_warning()
  
def ASSERT_TRUE(condition: bool, message: str) -> None:
  """ Assert condition to be true, generate an error if violated, blocking """
  if not condition:
    print(f"ERROR: {message}")
    Board.status_led.show_error()
  

# For REPL use ----------------------------------------------------------------

def remove_main_file() -> None:
  """ Remove the main file in case REPL not responding """
  os.remove("main.py")

def print_file(filename: str) -> None:
  """ Print given file to REPL
      `filename`: name of the file """
  with open(filename) as file:
    for line in file:
      print(line, end="")

def storage_status() -> None:
  """ Print current storage status to REPL """
  fs_bsize, fs_frsize, f_blocks, f_bfree, *_ = os.statvfs("/")
  print(f"Filesystem block size:        {fs_bsize} kB")
  print(f"Fragment size:                {fs_frsize} kB")
  print(f"Total size of Filesystem:     {f_blocks} blocks")
  print(f"Available size of Filesystem: {f_bfree} blocks") 
