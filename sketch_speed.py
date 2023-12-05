# 加速度を数値積分して速度を求めるデモ
# 正弦関数を元に加速度を作り、それを数値積分して速度を求める
# 比較のため、正弦関数の積分（-cos）を実際の速度としてプロットする

import math
import numpy as np
import matplotlib.pyplot as plt

start = 0 # sec
end = 10 # sec

def accel(t):
    return np.abs(np.sin(t))

def fast_accel(t):
    return 2*np.abs(np.sin(t))

def velocity(t):
    return np.trapz(accel(t))

def fast_velocity(t):
    return np.trapz(fast_accel(t))

def plot():
    dt = 0.01 # sec
    t = np.arange(start, end, dt) 
    a = accel(t)
    v = []
    for i in range(len(t)):
        first = max(0, i - 100) # 最大1秒前までの積分
        v.append(velocity(t[first:i])/100) # 1秒で割ることで平均を求める

    a2 = fast_accel(t)
    v2 = []
    for i in range(len(t)):
        first = max(0, i - 100) # 最大1秒前までの積分
        v2.append(fast_velocity(t[first:i])/100) # 1秒で割ることで平均を求める
    plt.plot(t, a, label="accel")
    plt.plot(t, a2, label="fast accel", linestyle="--")
    plt.plot(t, v, label="velocity")
    plt.plot(t, v2, label="fast velocity", linestyle="--")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    plot()