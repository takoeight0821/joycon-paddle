import logging
import threading
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

class Button:
    key: str
    isPressed: bool
    
    def __init__(self, key: str) -> None:
        self.key = key
        self.isPressed = False
    
    def press(self) -> bool:
        if not self.isPressed:
            pyautogui.keyDown(self.key)
            self.isPressed = True
            return True
        return False
    
    def release(self) -> bool:
        if self.isPressed:
            pyautogui.keyUp(self.key)
            self.isPressed = False
            return True
        return False

def soundStart():
    try:
        urllib.request.urlopen(serverAddress + "/start").read()
    except Exception as e:
        logging.error(e)
    
def soundStop():
    try:
        urllib.request.urlopen(serverAddress + "/stop").read()
    except Exception as e:
        logging.error(e)

def main():
    dataLength = 60
    threshold = 700

    avgHistory = History(dataLength)
    leftHistory = History(dataLength)
    rightHistory = History(dataLength)

    # (ljoycon, rjoycon) = setupJoyCon()
    lid = device.get_L_id()
    rid = device.get_R_id()
    logging.info(f"setup: {lid}, {rid}")
    ljoycon = None
    rjoycon = None

    is_pressed = False

    leftAccel = 0
    rightAccel = 0
    
    avgFilter = GravityFilter(0.8)
    leftFilter = GravityFilter(0.8)
    rightFilter = GravityFilter(0.8)
    
    avgButton = Button('s')
    leftButton = Button('a')
    rightButton = Button('d')

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
            leftAccel = getAccel(ljoycon)
        
        if not rjoycon is None:
            rightAccel = getAccel(rjoycon)

        avgAccel = addAverage(leftAccel, rightAccel)
        avgAccel = avgFilter.filter(avgAccel)
        logging.info(f"accel: {avgAccel}")
        avgHistory.append(avgAccel)
        avgVelocity = avgHistory.velocity()
        logging.info(f"velocity: {avgVelocity}")
        
        leftAccel = leftFilter.filter(leftAccel)
        leftHistory.append(leftAccel)
        leftVelocity = leftHistory.velocity()

        rightAccel = rightFilter.filter(rightAccel)
        rightHistory.append(rightAccel)
        rightVelocity = rightHistory.velocity()
        
        logging.info(f"left: {leftVelocity}, right: {rightVelocity}")
        
        if leftVelocity > threshold and rightVelocity > threshold:
            logging.info("both: press s")
            leftButton.release()
            rightButton.release()
            avgButton.press()
            threading.Thread(target=soundStart).start()
        elif leftVelocity > threshold and rightVelocity <= threshold:
            logging.info("left: press a")
            avgButton.release()
            rightButton.release()
            leftButton.press()
            threading.Thread(target=soundStart).start()
        elif leftVelocity <= threshold and rightVelocity > threshold:
            logging.info("right: press d")
            avgButton.release()
            leftButton.release()
            rightButton.press()
            threading.Thread(target=soundStart).start()
        else:
            logging.info("release all")
            avgButton.release()
            leftButton.release()
            rightButton.release()
            threading.Thread(target=soundStop).start()

        time.sleep(1/120)

if __name__ == "__main__":
    main()