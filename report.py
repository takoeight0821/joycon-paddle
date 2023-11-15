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
# ---- #
# plot #
# ---- #
while True:
    # get data
    input_report = joycon.get_status()
    print(input_report)
    # plot
    plt.cla()
    X.append(input_report["accel"]["x"])
    Y.append(input_report["accel"]["y"])
    Z.append(input_report["accel"]["z"])
    T.append(len(T))
    if len(X) > x_lim:
        xlim[0] += 1
        xlim[1] += 1
    plt.plot(T, X, linewidth=width, label="X-axis")
    plt.plot(T, Y, linewidth=width, label="Y-axis")
    plt.plot(T, Z, linewidth=width, label="Z-axis")
    plt.xlim(xlim[0], xlim[1])
    plt.ylim(ylim[0], ylim[1])
    plt.legend(bbox_to_anchor=(0, 1), loc='upper left',
               borderaxespad=0, fontsize=13)
    plt.pause(1/60)
