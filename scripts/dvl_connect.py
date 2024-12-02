from nucleus_driver import NucleusDriver
import time

driver = NucleusDriver()

SERIAL_PORT = "/dev/ttyUSB0"

driver.set_serial_configuration(port=SERIAL_PORT)
driver.connect(connection_type='serial')

PATH = '/home/jdcast/nucleus_driver/logs/'
driver.set_log_path(path=PATH)

driver.start_logging()

time.sleep(5);

driver.stop_logging()

driver.disconnect()
