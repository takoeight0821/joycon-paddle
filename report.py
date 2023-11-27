# based on Joy-Conの加速度をリアルタイムプロットする[joycon-python] | mio.yokohama https://mio.yokohama/?p=1205

import time
import numpy as np
from pyjoycon import device
from pyjoycon.joycon import JoyCon
from matplotlib import pyplot as plt
# ---- #
# init #
# ---- #
# JoyCon
id = device.get_L_id()
joycon = JoyCon(*id)

gravity = [0, 0, 0]
def filter(x, y, z):
    global gravity
    alpha = 0.8
    gravity[0] = alpha * gravity[0] + (1 - alpha) * x
    gravity[1] = alpha * gravity[1] + (1 - alpha) * y
    gravity[2] = alpha * gravity[2] + (1 - alpha) * z

    return [x - gravity[0], y - gravity[1], z - gravity[2]]

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
ylim = [-10000, 10000]
X, Y, Z, T = [], [], [], []
GX, GY, GZ = [], [], []
# ---- #
# plot #
# ---- #
while True:
    # get data
    input_report = joycon.get_status()
    print(input_report)
    # plot
    plt.cla()
    x = input_report["accel"]["x"]
    y = input_report["accel"]["y"]
    z = input_report["accel"]["z"]
    X.append(x)
    Y.append(y)
    Z.append(z)
    [gx, gy, gz] = filter(x, y, z)
    GX.append(gx)
    GY.append(gy)
    GZ.append(gz)
    T.append(len(T))
    if len(X) > x_lim:
        xlim[0] += 1
        xlim[1] += 1
    # plt.plot(T, X, linestyle="-.", linewidth=width, label="X-axis")
    # plt.plot(T, Y, linestyle="-.", linewidth=width, label="Y-axis")
    # plt.plot(T, Z, linestyle="-.", linewidth=width, label="Z-axis")
    plt.plot(T, GX, linewidth=width*0.8, label="X-axis(filter)")
    plt.plot(T, GY, linewidth=width*0.8, label="Y-axis(filter)")
    plt.plot(T, GZ, linewidth=width*0.8, label="Z-axis(filter)")
    plt.xlim(xlim[0], xlim[1])
    plt.ylim(ylim[0], ylim[1])
    plt.legend(bbox_to_anchor=(0, 1), loc='upper left',
               borderaxespad=0, fontsize=13)
    plt.pause(1/60)
