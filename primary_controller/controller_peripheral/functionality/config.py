import os, json
import driver.utils as utils

class Config:
  VERSION = "v0.1"

  # config files storage specifications
  config_path = "data"
  default_config_storage = "config.settings"
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
    """ Initializations that fulfill full requirements for system to operate """
    cls.empty_file_string = json.dumps(cls.get_empty_config_dict())
    try:
      with open(f"{cls.config_path}/{cls.default_config_storage}"):
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
    """ Change the default config to another file, file name must include extension
        `filename`: name of the new default config file, can be `config.no_default_config`
            indicating that there is no default config file """
    if filename not in cls.get_all_config_names() and filename != cls.no_default_config:
      utils.EXPECT_TRUE(False, f"Config nonexist file {filename}")
      return False
    with open(f"{cls.config_path}/{cls.default_config_storage}", "w") as f:
      f.write(filename)
    return True

  @classmethod
  def get_default_config(cls) -> str:
    """ Get the default config file name , include extension
        `returns`: default config file name, `config.no_default_config` if no or invalid default config """
    try:
      # get default config name
      with open(f"{cls.config_path}/{cls.default_config_storage}", "r") as f:
        default_config = f.read().strip()
    except Exception:
      utils.EXPECT_TRUE(False, f"Config <{cls.default_config_storage}> not found")
      cls.set_default_config(cls.no_default_config)
    if default_config not in cls.get_all_config_names():
      # default config not found, reset file
      utils.EXPECT_TRUE(False, f"Config default config <{default_config}> not found")
      default_config = cls.no_default_config
      cls.set_default_config(cls.no_default_config)
    return default_config

  @classmethod
  def get_empty_config_dict(cls) -> dict:
    """ Get a standard empty config in dictionary format 
        `returns`: an dictionary of empty config """
    return { cls.JATTR_VERSION: cls.VERSION, cls.JATTR_IMU_BY_POSITION: {} }

  @classmethod
  def get_all_config_names(cls) -> list:
    """ Get all the config names, with extension at the end of each name
        `returns`: list of all config names found in the system """
    ret = []
    for filename in os.listdir(cls.config_path):
      if filename.endswith(f".{Config.extension}"):
        ret.append(filename)
    return ret
  
  @classmethod
  def remove_config(cls, filename: str) -> bool:
    """ Remove designated the configs from the system, reset default config if necessary
        `filename`: name of file that desired to be removed 
        `returns`: whether the file exists prior to deletion """
    configs = cls.get_all_config_names()
    if cls.get_default_config() == filename:
      cls.set_default_config(Config.no_default_config)
    if filename in configs:
      os.remove(f"{cls.config_path}/{filename}")
      return True
    return False
  
  @classmethod
  def remove_all_configs(cls) -> None:
    """ Remove all the configs from the system """
    configs = cls.get_all_config_names()
    for config in configs:
      os.remove(f"{cls.config_path}/{config}")

  def __init__(self) -> None:
    """ Initialize an empty config with no associate file """
    self.__associative_file_name = None
    self.__imu_dict = {}

  def associate_with_file(self, filename: str) -> bool:
    """ Associate the config with an existing file using its file name with file extension included
        `filename`: name of the config file in the system, include extension 
        `returns`: whether the association is successful """
    if filename not in Config.get_all_config_names():
      utils.EXPECT_TRUE(False, f"Config <{filename}> does not exist")
      return False
    self.__associative_file_name = filename
    return True

  def read_config_from_file(self) -> bool:
    """ Read config file using the associated file name of the config, contents are stored
        in the `Config` object
        `returns`: `False` if read failed, `True` otherwise """
    if self.__associative_file_name == None:
      # no associative file
      utils.EXPECT_TRUE(False, "Config read no file associated with this config")
      return False
    try:
      with open(f"{Config.config_path}/{self.__associative_file_name}") as f:
        contents = json.loads(f.read())
    except Exception:
      # cannot be parsed as json
      utils.EXPECT_TRUE(False, "Config invalid file style, cannot be parsed as json file")
      return False
    if Config.JATTR_VERSION not in contents:
      # no version attribute in the file
      utils.EXPECT_TRUE(False, "Config version not found")
      return False
    if contents[Config.JATTR_VERSION] != Config.VERSION:
      # config file version mismatch
      utils.EXPECT_TRUE(False, 
          f"Config invalid version <{contents[Config.JATTR_VERSION]}>, expect <{Config.VERSION}>")
      return False
    self.__imu_dict = contents[Config.JATTR_IMU_BY_POSITION]
    return True

  def write_config_to_file(self) -> None:
    """ Write current config to the associated file, contents are from current `Config` object """
    utils.ASSERT_TRUE(self.__associative_file_name != None, 
        "Config write no file associated with this config")
    empty_config = Config.get_empty_config_dict()
    empty_config[Config.JATTR_IMU_BY_POSITION] = self.__imu_dict
    with open(f"{Config.config_path}/{self.__associative_file_name}", "w") as f:
      f.write(json.dumps(empty_config))

  def create_and_associate_config_file(self, filename: str) -> bool:
    """ Create a new config file and associate current `Config` object with it, file name must
        include extension
        `returns`: `False` if file already exists, abort. `True` if file created successfully """
    utils.ASSERT_TRUE(filename.endswith(f".{Config.extension}"), 
        f"Config <{filename}> invalid extension")
    if filename in Config.get_all_config_names():
      return False
    with open(f"{Config.config_path}/{filename}", "w") as f:
      f.write(Config.empty_file_string)
    self.__associative_file_name = filename
    return True

  def add_imu_to_config(self, imu_pos: str, i2c_addr: int, override: bool=False) -> int:
    """ Add a IMU to config with desired position
        `imu_pos`: IMU position on human body
        `i2c_addr`: I2C address of the IMU
        `override`: whether to override if the position is already initialized 
        `returns`: conflict I2C address if applicable """
    utils.ASSERT_TRUE(imu_pos in Config.IMU_AVAIL_POSITIONS, f"Config invalid imu position name <{imu_pos}>")
    if not override and imu_pos in self.__imu_dict:
      return self.__imu_dict[imu_pos]
    self.__imu_dict[imu_pos] = i2c_addr
    return None

  def get_config_string(self, readable: bool= True) -> str:
    """ Get config as displayable text, for both human read and transmission 
        `readable`: whether is human-readable text 
        `returns`: config file as string """
    ret = ""
    if readable:
      max_len = max([len(pos) for pos in Config.IMU_AVAIL_POSITIONS])
      for position in Config.IMU_AVAIL_POSITIONS:
        addr = hex(self.__imu_dict[position]) if position in self.__imu_dict else "Unused"
        ret += f"{position}: " + " " * (max_len - len(position)) + addr + "\n"
    else:
      for position in Config.IMU_AVAIL_POSITIONS:
        if position in self.__imu_dict:
          addr = str(self.__imu_dict[position])
          ret += f"{position},{addr}\n"
    return ret[:-1]
