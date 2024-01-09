import logging
import time
import numpy as np
import pyautogui
from pyjoycon import device
from pyjoycon.joycon import JoyCon
from typing import Dict, Deque, List, Tuple

logFormatter = logging.Formatter('%(asctime)s %(message)s')
rootLogger = logging.getLogger()

fileHandler = logging.FileHandler("paddle_" + time.strftime("%Y%m%d-%H%M%S") + ".log")
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

rootLogger.setLevel(logging.DEBUG)

def setupJoyCon() -> Tuple[JoyCon, JoyCon]:
    lid = device.get_L_id()
    ljoycon = JoyCon(*lid)
    rid = device.get_R_id()
    rjoycon = JoyCon(*rid)
    return (ljoycon, rjoycon)

def getAccel(joycon: JoyCon) -> Dict[str, float]:
    return joycon.get_status()["accel"]

def addAverage(left: Dict[str, float], right: Dict[str, float]) -> Dict[str, float]:
    return {"x": (left["x"] + right["x"]) / 2, "y": (left["y"] + right["y"]) / 2, "z": (left["z"] + right["z"]) / 2}

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

    # (ljoycon, rjoycon) = setupJoyCon()
    lid = device.get_L_id()
    rid = device.get_R_id()
    logging.info(f"setup: {lid}, {rid}")
    ljoycon = None
    rjoycon = None

    is_pressed = False

    lAcc = 0
    rAcc = 0

    while True:
        # watch for connection
        deviceIds = device.get_device_ids()
        logging.info(f"device_ids: {deviceIds}")

        if not lid in deviceIds:
            logging.warn("L JoyCon is disconnected")
            del ljoycon
            ljoycon = None
        elif ljoycon is None:
            logging.warn("L JoyCon is connected")
            try:
                ljoycon = JoyCon(*lid)
            except Exception as e:
                # ignore assertion error on _spi_flash_read and retry in next loop
                logging.error(e)
                del ljoycon
                ljoycon = None
        
        if not rid in deviceIds:
            logging.warn("R JoyCon is disconnected")
            del rjoycon
            rjoycon = None
        elif rjoycon is None:
            logging.warn("R JoyCon is connected")
            try:
                rjoycon = JoyCon(*rid)
            except Exception as e:
                logging.error(e)
                del rjoycon
                rjoycon = None
        
        if not ljoycon is None:
            lAcc = getAccel(ljoycon)
        
        if not rjoycon is None:
            rAcc = getAccel(rjoycon)

        accel = addAverage(lAcc, rAcc)
        accel = filterGravity(accel)
        logging.info(f"accel: {accel}")
        appendAccel(accel, X, Y, Z)
        velocity = getVelocity(X, Y, Z)
        logging.info(f"velocity: {velocity}")

        if velocity > threshold and not is_pressed:
            is_pressed = True
            logging.info("pressed")
            pyautogui.keyDown('s')
        elif velocity <= threshold and is_pressed:
            is_pressed = False
            logging.info("released")
            pyautogui.keyUp('s')
        else:
            logging.info("no change")
        time.sleep(1/60)

if __name__ == "__main__":
    main()
        