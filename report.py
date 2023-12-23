# based on Joy-Conの加速度をリアルタイムプロットする[joycon-python] | mio.yokohama https://mio.yokohama/?p=1205

from collections import deque
from matplotlib import pyplot as plt
from pyjoycon import device
from pyjoycon.joycon import JoyCon
from typing import Dict
import logging
import numpy as np
import time

def velocity(accels):
    return np.trapz(accels) / len(accels)

# ---- #
# init #
# ---- #
logging.basicConfig(filename= "report_" + time.strftime("%Y%m%d-%H%M%S") + ".log", encoding='utf-8', level=logging.INFO)

# JoyCon
lid = device.get_L_id()
ljoycon = JoyCon(*lid)
rid = device.get_R_id()
rjoycon = JoyCon(*rid)

gravity = [0, 0, 0]
def filter(x, y, z):
    global gravity
    alpha = 0.8
    gravity[0] = alpha * gravity[0] + (1 - alpha) * x
    gravity[1] = alpha * gravity[1] + (1 - alpha) * y
    gravity[2] = alpha * gravity[2] + (1 - alpha) * z

    return [x - gravity[0], y - gravity[1], z - gravity[2]]

def addAverage(left: Dict[str, float], right: Dict[str, float]) -> None:
    return {"x": (left["x"] + right["x"]) / 2, "y": (left["y"] + right["y"]) / 2, "z": (left["z"] + right["z"]) / 2}

# set figure
x_lim = 50
width = 2.5
t = np.zeros(100)
y = np.zeros(100)
plt.ion()
plt.figure()
li = plt.plot(t, y)
plt.ylim(0, 5)
xlim = [0, x_lim]
ylim = [-100, 5000]
X, Y, Z, T = deque(maxlen=x_lim), deque(maxlen=x_lim), deque(maxlen=x_lim), deque(maxlen=x_lim)
GX, GY, GZ = deque(maxlen=x_lim), deque(maxlen=x_lim), deque(maxlen=x_lim)
GXV, GYV, GZV = deque(maxlen=x_lim), deque(maxlen=x_lim), deque(maxlen=x_lim)
GV = deque(maxlen=x_lim)

# ---- #
# plot #
# ---- #
while True:
    # get data
    linput_report = ljoycon.get_status()
    laccel = linput_report["accel"]
    rinput_report = rjoycon.get_status()
    raccel = rinput_report["accel"]
    accel = addAverage(laccel, raccel)
    # plot
    plt.cla()
    x = accel["x"]
    y = accel["y"]
    z = accel["z"]
    X.append(x)
    Y.append(y)
    Z.append(z)
    [gx, gy, gz] = filter(x, y, z)
    GX.append(np.abs(gx))
    GY.append(np.abs(gy))
    GZ.append(np.abs(gz))
    GXV.append(velocity(np.abs(GX)))
    GYV.append(velocity(np.abs(GY)))
    GZV.append(velocity(np.abs(GZ)))
    GV.append(GXV[-1] + GYV[-1] + GZV[-1])
    if len(T) == 0:
        T.append(0)
    else:
        T.append(T[-1]+1)
    logging.info("accel T: %d, X: %d, Y: %d, Z: %d, GX: %d, GY: %d, GZ: %d", T[-1], X[-1], Y[-1], Z[-1], GX[-1], GY[-1], GZ[-1])
    logging.info("velocity T: %d, GXV: %d, GYV: %d, GZV: %d, GV: %d", T[-1], GXV[-1], GYV[-1], GZV[-1], GV[-1])
    if len(X) >= x_lim:
        xlim[0] += 1
        xlim[1] += 1
    plt.plot(T, GX, linewidth=width*0.8, label="X-axis accel")
    plt.plot(T, GY, linewidth=width*0.8, label="Y-axis accel")
    plt.plot(T, GZ, linewidth=width*0.8, label="Z-axis accel")
    plt.plot(T, GV, linewidth=width*0.8, linestyle=':', label="velocity")
    # plot threshold line
    plt.plot(T, [1000]*len(T), linewidth=width, linestyle='--', color='black', label="threshold")
    plt.xlim(xlim[0], xlim[1])
    plt.ylim(ylim[0], ylim[1])
    plt.legend(bbox_to_anchor=(0, 1), loc='upper left',
               borderaxespad=0, fontsize=13)
    plt.pause(1/60)
