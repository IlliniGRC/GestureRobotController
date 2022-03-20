import os, ujson
import driver.utils as utils

class Config:
  VERSION = "v0.1"

  # config files storage specifications
  config_path = "data"
  default_config_name = "config.settings"
  extension = ".config"
  empty_file_string = None

  # JSON attributes
  JATTR_VERSION = "Version"
  JATTR_IMU_BY_POSITION = "IMUs"
  # IMU position names must not exceed 7 characters for it to be displayed
  JATTR_IMU_THUMB = "Thumb"
  JATTR_IMU_INDEX = "Index"
  JATTR_IMU_MIDDLE = "Middle"
  JATTR_IMU_RING = "Ring"
  JATTR_IMU_LITTLE = "Little"
  JATTR_IMU_HAND = "Hand"
  # config file style
  #
  # {
  #   <VERSION_NAME> : <VERSION>
  #   <IMU_BY_POSITION_NAME> : {
  #     <IMU_XXX_NAME> : # IIC address
  #     <IMU_XXX_NAME> : # IIC address
  #     ...
  #   }
  # }

  # all available positions for IMU installation, should not exceed 12
  IMU_AVAIL_POSITIONS = [
      JATTR_IMU_THUMB, 
      JATTR_IMU_INDEX, 
      JATTR_IMU_MIDDLE, 
      JATTR_IMU_RING, 
      JATTR_IMU_LITTLE, 
      JATTR_IMU_HAND]
  
  @classmethod
  def auxiliary_init(cls):
    cls.empty_file_string = ujson.dumps(cls.get_empty_config())
    try:
      with open(f"{cls.config_path}/{cls.default_config_name}") as f:
        pass
    except Exception:
      utils.ASSERT_TRUE(False, "Config default config not found")

    utils.ASSERT_TRUE(len(Config.IMU_AVAIL_POSITIONS) <= 12, 
        "Config IMU available positions length should not exceed 12")
    for name in Config.IMU_AVAIL_POSITIONS:
      utils.ASSERT_TRUE(type(name) == str and len(name) <= 7, "Config IMU name length should not exceed 7")

  @classmethod
  def get_empty_config(cls) -> list:
    return { cls.JATTR_VERSION: cls.VERSION, cls.JATTR_IMU_BY_POSITION: {} }

  @classmethod
  def list_all_configs(cls) -> list:
    ret = []
    for filename in os.listdir(cls.config_path):
      if filename.endswith(Config.extension):
        ret.append(filename)
    return ret
  
  @classmethod
  def remove_all_configs(cls) -> None:
    configs = cls.list_all_configs()
    for config in configs:
      os.remove(f"{cls.config_path}/{config}")

  def __init__(self) -> None:
    self.__associative_file_name = None
    self.__imu_dict = {}

  def associate_with_file(self, filename: str) -> None:
    utils.ASSERT_TRUE(filename.endswith(Config.extension), f"Config <{filename}> invalid extension")
    try:
      with open(f"{Config.config_path}/{filename}"):
        pass
      self.__associative_file_name = filename
    except Exception:
      utils.ASSERT_TRUE(False, f"Config <{filename}> does not exist")

  def read_config_from_file(self) -> None:
    utils.ASSERT_TRUE(self.__associative_file_name != None, "Config read no file associated with this config")
    contents: dict = None
    with open(f"{Config.config_path}/{self.__associative_file_name}") as f:
      contents = ujson.loads(f.read())
    utils.ASSERT_TRUE(Config.JATTR_VERSION in contents, "Config invalid file style")
    utils.ASSERT_TRUE(contents[Config.JATTR_VERSION] == Config.VERSION, 
        f"Config invalid version {contents[Config.JATTR_VERSION]}, expect {Config.VERSION}")
    self.__imu_dict = contents[Config.JATTR_IMU_BY_POSITION]

  def write_config_to_file(self) -> None:
    utils.ASSERT_TRUE(self.__associative_file_name != None, "Config write no file associated with this config")
    empty_config = Config.get_empty_config()
    empty_config[Config.JATTR_IMU_BY_POSITION] = self.__imu_dict
    with open(f"{Config.config_path}/{self.__associative_file_name}", "w") as f:
      f.write(ujson.dumps(empty_config))

  def create_and_associate_config_file(self, filename: str) -> bool:
    utils.ASSERT_TRUE(filename.endswith(Config.extension), f"Config <{filename}> invalid extension")
    configs = Config.list_all_configs()
    if filename in configs:
      return False
    with open(f"{Config.config_path}/{filename}", "w") as f:
      f.write(Config.empty_file_string)
    self.__associative_file_name = filename
    return True

  def add_imu_to_config(self, imu_pos: str, iic_addr: int) -> None:
    utils.ASSERT_TRUE(imu_pos in Config.IMU_AVAIL_POSITIONS, f"Config invalid imu position name {imu_pos}")
    self.__imu_dict[imu_pos] = iic_addr

  def print_config(self) -> None:
    print(self.__imu_dict)