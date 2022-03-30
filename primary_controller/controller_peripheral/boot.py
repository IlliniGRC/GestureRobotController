import os

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
  pass
