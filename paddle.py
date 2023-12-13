import time
import numpy as np
import pyautogui
from pyjoycon import device
from pyjoycon.joycon import JoyCon
from typing import Dict, Deque, List

def setupJoyCon():
    id = device.get_L_id()
    joycon = JoyCon(*id)
    return joycon

def getAccel(joycon: JoyCon) -> Dict[str, float]:
    return joycon.get_status()["accel"]

def appendAccel(accel: Dict[str, float], X: Deque[float], Y: Deque[float], Z: Deque[float]) -> None:
    X.append(np.abs(accel["x"]))
    Y.append(np.abs(accel["y"]))
    Z.append(np.abs(accel["z"]))

gravity: List[float] = [0, 0, 0]
def filterGravity(accel: Dict[str, float]) -> Dict[str, float]:
    global gravity
    alpha = 0.8
    gravity[0] = alpha * gravity[0] + (1 - alpha) * accel["x"]
    gravity[1] = alpha * gravity[1] + (1 - alpha) * accel["y"]
    gravity[2] = alpha * gravity[2] + (1 - alpha) * accel["z"]

    return {"x": accel["x"] - gravity[0], "y": accel["y"] - gravity[1], "z": accel["z"] - gravity[2]}

# 加速度の積分の総和
def getVelocity(X: Deque[float], Y: Deque[float], Z: Deque[float]) -> float:
    vx = np.trapz(X) / len(X)
    vy = np.trapz(Y) / len(Y)
    vz = np.trapz(Z) / len(Z)
    return vx + vy + vz


def main():
    dataLength = 60
    threshold = 1000

    X = Deque(maxlen=dataLength)
    Y = Deque(maxlen=dataLength)
    Z = Deque(maxlen=dataLength)

    joycon = setupJoyCon()
    is_pressed = False

    while True:
        accel = getAccel(joycon)
        accel = filterGravity(accel)
        print(accel)
        appendAccel(accel, X, Y, Z)
        velocity = getVelocity(X, Y, Z)
        print(velocity)

        if velocity > threshold and not is_pressed:
            is_pressed = True
            print(is_pressed)
            pyautogui.keyDown('s')
        elif velocity <= threshold and is_pressed:
            is_pressed = False
            print(is_pressed)
            pyautogui.keyUp('s')
        else:
            print("no change ", is_pressed)
        time.sleep(1/60)

if __name__ == "__main__":
    main()
        