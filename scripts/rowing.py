import logging
import time
import numpy as np
import pyautogui
from pyjoycon import device
from pyjoycon.joycon import JoyCon
from typing import Dict, Deque, List, Tuple
import urllib.request

logFormatter = logging.Formatter('%(asctime)s %(message)s')
rootLogger = logging.getLogger()

fileHandler = logging.FileHandler("rowing_" + time.strftime("%Y%m%d-%H%M%S") + ".log")
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

rootLogger.setLevel(logging.DEBUG)

# the address of the play sound server.
serverAddress = "http://192.168.11.2:8080"

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

# def appendAccel(accel: Dict[str, float], X: Deque[float], Y: Deque[float], Z: Deque[float]) -> None:
#     X.append(np.abs(accel["x"]))
#     Y.append(np.abs(accel["y"]))
#     Z.append(np.abs(accel["z"]))

class GravityFilter:
    alpha: float
    gravity: List[float]

    def __init__(self, alpha: float) -> None:
        self.alpha = alpha
        self.gravity = [0, 0, 0]
    
    def filter(self, accel: Dict[str, float]) -> Dict[str, float]:
        self.gravity[0] = self.alpha * self.gravity[0] + (1 - self.alpha) * accel["x"]
        self.gravity[1] = self.alpha * self.gravity[1] + (1 - self.alpha) * accel["y"]
        self.gravity[2] = self.alpha * self.gravity[2] + (1 - self.alpha) * accel["z"]
        return {"x": accel["x"] - self.gravity[0], "y": accel["y"] - self.gravity[1], "z": accel["z"] - self.gravity[2]}

# gravity: List[float] = [0, 0, 0]
# def filterGravity(accel: Dict[str, float]) -> Dict[str, float]:
#     global gravity
#     alpha = 0.8
#     gravity[0] = alpha * gravity[0] + (1 - alpha) * accel["x"]
#     gravity[1] = alpha * gravity[1] + (1 - alpha) * accel["y"]
#     gravity[2] = alpha * gravity[2] + (1 - alpha) * accel["z"]
# 
#     return {"x": accel["x"] - gravity[0], "y": accel["y"] - gravity[1], "z": accel["z"] - gravity[2]}

class History:
    X: Deque[float]
    Y: Deque[float]
    Z: Deque[float]
    
    def __init__(self, length: int) -> None:
        self.X = Deque(maxlen=length)
        self.Y = Deque(maxlen=length)
        self.Z = Deque(maxlen=length)
    
    def append(self, accel: Dict[str, float]) -> None:
        self.X.append(np.abs(accel["x"]))
        self.Y.append(np.abs(accel["y"]))
        self.Z.append(np.abs(accel["z"]))
    
    # 加速度の積分の総和
    def velocity(self) -> float:
        vx = np.trapz(self.X) / len(self.X)
        vy = np.trapz(self.Y) / len(self.Y)
        vz = np.trapz(self.Z) / len(self.Z)
        return vx + vy + vz

# def getVelocity(X: Deque[float], Y: Deque[float], Z: Deque[float]) -> float:
#     vx = np.trapz(X) / len(X)
#     vy = np.trapz(Y) / len(Y)
#     vz = np.trapz(Z) / len(Z)
#     return vx + vy + vz

def main():
    dataLength = 60
    threshold = 700

    # X = Deque(maxlen=dataLength)
    # Y = Deque(maxlen=dataLength)
    # Z = Deque(maxlen=dataLength)
    avgHistory = History(dataLength)

    # (ljoycon, rjoycon) = setupJoyCon()
    lid = device.get_L_id()
    rid = device.get_R_id()
    logging.info(f"setup: {lid}, {rid}")
    ljoycon = None
    rjoycon = None

    is_pressed = False

    lAcc = 0
    rAcc = 0
    
    avgFilter = GravityFilter(0.8)

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

        avgAccel = addAverage(lAcc, rAcc)
        avgAccel = avgFilter.filter(avgAccel)
        logging.info(f"accel: {avgAccel}")
        avgHistory.append(avgAccel)
        # appendAccel(accel, X, Y, Z)
        avgVelocity = avgHistory.velocity()
        # velocity = getVelocity(X, Y, Z)
        logging.info(f"velocity: {avgVelocity}")

        if avgVelocity > threshold and not is_pressed:
            is_pressed = True
            logging.info("pressed")
            pyautogui.keyDown('s')
            try:
                #pass
                urllib.request.urlopen(serverAddress + "/start").read()
            except Exception as e:
                logging.error(e)
        elif avgVelocity <= threshold and is_pressed:
            is_pressed = False
            logging.info("released")
            pyautogui.keyUp('s')
            try:
                #pass
                urllib.request.urlopen(serverAddress + "/stop").read()
            except Exception as e:
                logging.error(e)
        else:
            logging.info("no change")
        time.sleep(1/60)

if __name__ == "__main__":
    main()