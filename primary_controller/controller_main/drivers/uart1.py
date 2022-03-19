import machine

class UART1:
  def __init__(self) -> None:
    self.__uart = machine.UART(1, 115200)

  def send(self):
    self.__uart.write()