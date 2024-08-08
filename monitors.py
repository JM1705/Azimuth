import subprocess
import re

def get_monitors():
    output = subprocess.run(["which", "xrandr"], capture_output=True)
    which_output = output.stderr.decode("utf-8")
    if which_output.startswith("which: no "):
        raise Exception("xrandr not installed")
    
    output = subprocess.run(["xrandr"], capture_output=True)
    xrandr_output = output.stdout.decode("utf-8")

    monitors = {}
    index = 0
    for line in xrandr_output.split("\n"):
        if "connected" in line:
            # print(line)
            resolution = re.search("([0-9]*)x([0-9]*)", line)
            res_x = int(resolution.group(1))
            res_y = int(resolution.group(2))
            monitors[index] = [res_x, res_y]
            index += 1
    return monitors
