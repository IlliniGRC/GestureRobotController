import os, json
import driver.utils as utils

class Config:
  VERSION = "v0.1"

  # config files storage specifications
  config_path = "data"
  default_config_filename = "config.settings"
  extension = "config"
  no_default_config = "None"
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
  JATTR_IMU_ARM = "Arm"
  # config file style
  #
  # {
  #   <VERSION_NAME> : <VERSION>
  #   <IMU_BY_POSITION_NAME> : {
  #     <IMU_XXX_NAME> : # I2C address
  #     <IMU_XXX_NAME> : # I2C address
  #     ...
  #   }
  # }

  # all available positions for IMU installation, should not exceed 10
  IMU_AVAIL_POSITIONS = [
      JATTR_IMU_HAND,
      JATTR_IMU_THUMB, 
      JATTR_IMU_INDEX, 
      JATTR_IMU_MIDDLE, 
      JATTR_IMU_RING, 
      JATTR_IMU_LITTLE, 
      JATTR_IMU_ARM]
  
  @classmethod
  def auxiliary_init(cls):
    cls.empty_file_string = json.dumps(cls.get_empty_config())
    try:
      with open(f"{cls.config_path}/{cls.default_config_filename}"):
        pass
    except Exception:
      utils.ASSERT_TRUE(False, "Config default config not found")

    utils.ASSERT_TRUE(len(Config.IMU_AVAIL_POSITIONS) <= 10, 
        "Config IMU available positions length should not exceed 12")
    for name in Config.IMU_AVAIL_POSITIONS:
      utils.ASSERT_TRUE(type(name) == str and len(name) <= 7, 
          "Config IMU name length should not exceed 7")

  @classmethod
  def set_default_config(cls, filename: str) -> bool:
    if filename not in cls.list_all_configs() and filename != cls.no_default_config:
      utils.EXPECT_TRUE(False, f"Config nonexist file {filename}")
      return False
    with open(f"{cls.config_path}/{cls.default_config_filename}", "w") as f:
      f.write(filename)
    return True

  @classmethod
  def get_default_config(cls) -> str:
    try:
      with open(f"{cls.config_path}/{cls.default_config_filename}", "r") as f:
        default_config = f.read().strip()
    except Exception:
      utils.ASSERT_TRUE(False, "Config default config not found")
    if default_config not in cls.list_all_configs():
      default_config = cls.no_default_config
      cls.set_default_config(default_config)
    return default_config

  @classmethod
  def get_empty_config(cls) -> list:
    return { cls.JATTR_VERSION: cls.VERSION, cls.JATTR_IMU_BY_POSITION: {} }

  @classmethod
  def list_all_configs(cls) -> list:
    ret = []
    for filename in os.listdir(cls.config_path):
      if filename.endswith(f".{Config.extension}"):
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
    utils.EXPECT_TRUE(filename in Config.list_all_configs(), 
        f"Config <{filename}> does not exist")
    self.__associative_file_name = filename

  def read_config_from_file(self) -> bool:
    if self.__associative_file_name == None:
      utils.EXPECT_TRUE(False, "Config read no file associated with this config")
      return False
    contents: dict = None
    try:
      with open(f"{Config.config_path}/{self.__associative_file_name}") as f:
        contents = json.loads(f.read())
    except Exception:
      utils.EXPECT_TRUE(False, "Config invalid file style, cannot be parsed as json file")
      return False
    if Config.JATTR_VERSION not in contents:
      utils.EXPECT_TRUE(False, "Config version not found")
      return False
    if contents[Config.JATTR_VERSION] != Config.VERSION:
      utils.EXPECT_TRUE(False, 
          f"Config invalid version <{contents[Config.JATTR_VERSION]}>, expect <{Config.VERSION}>")
      return False
    self.__imu_dict = contents[Config.JATTR_IMU_BY_POSITION]
    return True

  def write_config_to_file(self) -> None:
    utils.ASSERT_TRUE(self.__associative_file_name != None, "Config write no file associated with this config")
    empty_config = Config.get_empty_config()
    empty_config[Config.JATTR_IMU_BY_POSITION] = self.__imu_dict
    with open(f"{Config.config_path}/{self.__associative_file_name}", "w") as f:
      f.write(json.dumps(empty_config))

  def create_and_associate_config_file(self, filename: str) -> bool:
    utils.ASSERT_TRUE(filename.endswith(f".{Config.extension}"), f"Config <{filename}> invalid extension")
    if filename in Config.list_all_configs():
      return False
    with open(f"{Config.config_path}/{filename}", "w") as f:
      f.write(Config.empty_file_string)
    self.__associative_file_name = filename
    return True

  def add_imu_to_config(self, imu_pos: str, i2c_addr: int, override: bool=False) -> int:
    utils.ASSERT_TRUE(imu_pos in Config.IMU_AVAIL_POSITIONS, f"Config invalid imu position name <{imu_pos}>")
    if not override and imu_pos in self.__imu_dict:
      return self.__imu_dict[imu_pos]
    self.__imu_dict[imu_pos] = i2c_addr
    return None

  def print_config(self) -> None:
    print(self.__imu_dict)