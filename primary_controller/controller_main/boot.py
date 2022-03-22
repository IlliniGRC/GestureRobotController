import machine, os

def remove_all_files_under_dir():
  files = os.listdir()
  for file in files:
    os.remove(file)

def remove_all_files():
  files = os.listdir()
  for file in files:
    if file != "boot.py" and file.find(".") != -1:
      os.remove(file)
  os.chdir("driver")
  remove_all_files_under_dir()
  os.chdir("..")
  os.chdir("functionality")
  remove_all_files_under_dir()

if __name__ == '__main__':
  pin13 = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
  if pin13.value() == 0:
    status_led = machine.Pin(2, machine.Pin.OUT)
    status_led.on()
    os.remove("main.py")
