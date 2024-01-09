import datetime
import time
from pyjoycon import device
from pyjoycon.joycon import JoyCon
import logging
import paddle

logFormatter = logging.Formatter('%(asctime)s %(message)s')
rootLogger = logging.getLogger()

fileHandler = logging.FileHandler("watch_" + time.strftime("%Y%m%d-%H%M%S") + ".log")
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

rootLogger.setLevel(logging.DEBUG)

def main():
    lid = device.get_L_id()
    rid = device.get_R_id()
    ljoycon = None
    rjoycon = None
    lconnectTime = 0
    rconnectTime = 0
    # (ljoycon, rjoycon) = paddle.setupJoyCon()
    # logging.info(f"setup: {ljoycon}, {rjoycon}")
    while True:
        device_ids = device.get_device_ids()
        logging.info(f"device_ids: {device_ids}")
        if not lid in device_ids:
            logging.info("L JoyCon is disconnected")
            logging.info(f"time: {datetime.timedelta(seconds=time.time() - lconnectTime)}")
            del ljoycon
            ljoycon = None
        elif ljoycon is None:
            logging.info("L JoyCon is connected")
            try:
                ljoycon = JoyCon(*lid)
                lconnectTime = time.time()
            except Exception as e:
                # ignore assertion error on _spi_flash_read and retry in next loop
                logging.error(e)
                del ljoycon
                ljoycon = None

        if not rid in device_ids:
            logging.info("R JoyCon is disconnected")
            logging.info(f"time: {datetime.timedelta(seconds=time.time() - rconnectTime)}")
            del rjoycon
            rjoycon = None
        elif rjoycon is None:
            logging.info("R JoyCon is connected")
            try:
                rjoycon = JoyCon(*rid)
                rconnectTime = time.time()
            except Exception as e:
                logging.error(e)
                del rjoycon
                rjoycon = None
        if not ljoycon is None:
            lAcc = paddle.getAccel(ljoycon)
        if not rjoycon is None:
            rAcc = paddle.getAccel(rjoycon)
        logging.info(f"accel: {lAcc}, {rAcc}")
        time.sleep(1)

if __name__ == "__main__":
    main()