import subprocess
logger = subprocess.Popen(["py", "-3.13", "logger.py"])
display = subprocess.Popen(["py", "-3.13", "display_data.py"])
logger.wait()
display.wait()