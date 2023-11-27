import time
from pyjoycon import device
from pyjoycon.joycon import JoyCon
import logging

logFormatter = logging.Formatter('%(asctime)s %(message)s')
rootLogger = logging.getLogger()

fileHandler = logging.FileHandler('watch.log')
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

rootLogger.setLevel(logging.DEBUG)

# Setup
# Send 0x010602 to enable pair mode
#ids = device.get_device_ids()
#for id in ids:
#    joycon = JoyCon(*id)
#    joycon._write_output_report(b'\x01', b'\x06', b'\x02')
#    logging.info("Sent 0x010602 to " + str(id))

joyconTable = {}

while True:
    ids = device.get_device_ids()
    if ids == []:
        logging.warning("No JoyCons found.")
    else:
        logging.info("JoyCons found: " + str(ids))
    removed = []
    for id in joyconTable:
        if id not in ids:
            removed.append(id)
            logging.info("JoyCon disconnected: " + str(id))
    for id in removed:
        del joyconTable[id]
        logging.info("JoyCon removed from table: " + str(id))
    for id in ids:
        if id in joyconTable:
            joycon = joyconTable[id]
        else:
            joycon = JoyCon(*id)
            joyconTable[id] = joycon
        joycon._write_output_report(b'\x01', b'\x06', b'\x01')
        logging.info("Sent 0x010601 to " + str(id))
    time.sleep(5)