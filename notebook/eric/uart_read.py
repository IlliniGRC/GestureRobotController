# %%
from serial import Serial

ser = Serial()
ser.port = 'COM4'
ser.baudrate = 9600
try:
  ser.close()
except Exception as e:
  pass
ser.open()

while int.from_bytes(ser.read(1), "big") != 0x55:
  pass
ser.read(10)

while True:
  pack = list(ser.read(11))
  checksum = sum(pack[:-1]) & 0xFF
  if pack[0] == 0x55 and checksum == pack[-1]:
    match pack[1]:
      # Euler angle
      case 0x53:
        roll  = (pack[3] << 8 | pack[2]) / 32768.0 * 180
        pitch = (pack[5] << 8 | pack[4]) / 32768.0 * 180
        yaw   = (pack[7] << 8 | pack[6]) / 32768.0 * 180
        print("% 7.3f % 7.3f % 7.3f" % (roll, pitch, yaw))
      # quaternion
      case 0x59:
        pass


# %%
