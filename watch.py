import time
from pyjoycon import device
from pyjoycon.joycon import JoyCon
import logging
import paddle

logFormatter = logging.Formatter('%(asctime)s %(message)s')
rootLogger = logging.getLogger()

fileHandler = logging.FileHandler('watch.log')
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

rootLogger.setLevel(logging.DEBUG)

def main():
    lids = device.get_L_ids()
    rids = device.get_R_ids()
    (ljoycon, rjoycon) = paddle.setupJoyCon()
    logging.info(f"setup: {ljoycon}, {rjoycon}")
    while True:
        device_ids = device.get_device_ids()
        logging.info(f"device_ids: {set(device_ids)}")
        if not set(lids).issubset(set(device_ids)):
            logging.info("L JoyCon is disconnected")
            break
        if not set(rids).issubset(set(device_ids)):
            logging.info("R JoyCon is disconnected")
            break
        lAcc = paddle.getAccel(ljoycon)
        rAcc = paddle.getAccel(rjoycon)
        logging.info(f"accel: {lAcc}, {rAcc}")
        time.sleep(1)

if __name__ == "__main__":
    main()