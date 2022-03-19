import machine
from time import sleep_ms

def start_signal():
  # Set processor speed to 240MHz
  #   Available freq: [20MHz, 40MHz, 80MHz, 160MHz, 240MHz]
  machine.freq(240000000)

  # LED flash, report complete
  led_pin = machine.Pin(2, machine.Pin.OUT)
  flash_time = 3
  for _ in range(flash_time * 2):
    led_pin.value(1 - led_pin.value())
    sleep_ms(50)
    
if __name__ == '__main__':
  start_signal()
