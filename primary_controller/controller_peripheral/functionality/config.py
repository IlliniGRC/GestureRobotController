import os
import driver.utils as utils

class Config:
  config_path = "data"
  default_config_name = "config.settings"
  extension = ".config"

  @classmethod
  def auxiliary_init(cls):
    try:
      with open(f"{cls.config_path}/{cls.default_config_name}") as f:
        pass
    except Exception as e:
      utils.ASSERT_TRUE(False, "Config default config not found")

  @classmethod
  def list_all_configs(cls) -> list:
    ret = []
    for filename in os.listdir(cls.config_path):
      if filename.endswith(Config.extension):
        ret.append(filename)
    return ret

  def __init__(self) -> None:
    self.__imu_used_num = 0
    self.__imu_dict = {}

  def read_config_from_file(filename: str) -> None:
    try:
      with open(f"{Config.config_path}/{filename}") as f:
        pass
    except Exception as e:
      utils.ASSERT_TRUE(False, "Config file does not exist")
