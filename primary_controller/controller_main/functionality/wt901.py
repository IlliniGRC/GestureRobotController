import machine, math

import driver.utils as utils

class WT901:
  # positions
  NOT_ASSIGNED = "X"
  THUMB = "Thumb"
  INDEX = "Index"
  MIDDLE = "Middle"
  RING = "Ring"
  LITTLE = "Little"
  HAND = "Hand"
  ARM = "Arm"
  avail_positions = [THUMB, INDEX, MIDDLE, RING, LITTLE, HAND, ARM]
  inited_positions = {}
  detected_imus = {}
  # Control words
  SAVE      = 0x00
  CALSW     = 0x01
  RSW       = 0x02
  RRATE     = 0x03
  BAUD      = 0x04
  AXOFFSET  = 0x05
  AYOFFSET  = 0x06
  AZOFFSET  = 0x07
  GXOFFSET  = 0x08
  GYOFFSET  = 0x09
  GZOFFSET  = 0x0a
  HXOFFSET  = 0x0b
  HYOFFSET  = 0x0c
  HZOFFSET  = 0x0d
  D0MODE    = 0x0e
  D1MODE    = 0x0f
  D2MODE    = 0x10
  D3MODE    = 0x11
  D0PWMH    = 0x12
  D1PWMH    = 0x13
  D2PWMH    = 0x14
  D3PWMH    = 0x15
  D0PWMT    = 0x16
  D1PWMT    = 0x17
  D2PWMT    = 0x18
  D3PWMT    = 0x19
  I2CADDR   = 0x1a
  LEDOFF    = 0x1b
  GPSBAUD   = 0x1c
  YYMM      = 0x30
  DDHH      = 0x31
  MMSS      = 0x32
  MS        = 0x33
  AX        = 0x34
  AY        = 0x35
  AZ        = 0x36
  GX        = 0x37
  GY        = 0x38
  GZ        = 0x39
  HX        = 0x3a
  HY        = 0x3b
  HZ        = 0x3c      
  Roll      = 0x3d
  Pitch     = 0x3e
  Yaw       = 0x3f
  TEMP      = 0x40
  D0Status  = 0x41
  D1Status  = 0x42
  D2Status  = 0x43
  D3Status  = 0x44
  PressureL = 0x45
  PressureH = 0x46
  HeightL   = 0x47
  HeightH   = 0x48
  LonL      = 0x49
  LonH      = 0x4a
  LatL      = 0x4b
  LatH      = 0x4c
  GPSHeight = 0x4d
  GPSYAW    = 0x4e
  GPSVL     = 0x4f
  GPSVH     = 0x50 

  DIO_MODE_AIN   = 0
  DIO_MODE_DIN   = 1
  DIO_MODE_DOH   = 2
  DIO_MODE_DOL   = 3
  DIO_MODE_DOPWM = 4
  DIO_MODE_GPS   = 5

  @classmethod
  def auxiliary_init(cls):
    identity_test = set(cls.NOT_ASSIGNED[0])
    for label, *_ in cls.avail_positions:
      utils.ASSERT_TRUE(label not in identity_test, f"WT901 duplicated identities <{label}>")
      identity_test.add(label)

  @classmethod
  def detect_imus(cls, i2c: machine.SoftI2C):
    addresses = i2c.scan()
    for address in addresses:
      if address not in cls.detected_imus:
        cls.detected_imus[address] = WT901(address, i2c)

  @classmethod
  def deinit_all_imus(cls):
    for imu in cls.detected_imus.values():
      imu.assign_position(cls.NOT_ASSIGNED)

  def __init__(self, i2c_addr, i2c: machine.SoftI2C) -> None:
    self.__i2c = i2c
    self.__i2c_addr = i2c_addr
    self.__position = WT901.NOT_ASSIGNED
    self.__report_header = self.__position[0]

  def assign_position(self, position: str) -> None:
    utils.ASSERT_TRUE(position in WT901.avail_positions, f"WT901 no such position <{position}>")
    utils.ASSERT_TRUE(position not in WT901.inited_positions, f"WT901 position <{position}> already initialized")
    self.__position = position
    self.__report_header = position[0]
    WT901.inited_positions[position] = self

  def get_angle_raw(self):
    ret = self.__i2c.readfrom_mem(self.__i2c_addr, WT901.Roll, 6)
    return ret[1] << 8 | ret[0], ret[3] << 8 | ret[2], ret[5] << 8 | ret[4]

  def get_angle_degree(self):
    roll, pitch, yaw = self.get_angle_raw()
    return roll / 32768 * 180, pitch / 32768 * 180, yaw / 32768 * 180

  def get_angle_radian(self):
    roll, pitch, yaw = self.get_angle_raw()
    return roll / 32768 * math.pi, pitch / 32768 * math.pi, yaw / 32768 * math.pi

  def get_angle_report(self, buf: bytearray, start_idx: int) -> int:
    buf[start_idx] = ord(self.__report_header)
    buf[start_idx + 1:start_idx + 7] = self.__i2c.readfrom_mem(self.__i2c_addr, WT901.Roll, 6)
    buf[start_idx + 7] = 10 # encoding for \n
    return start_idx + 8
