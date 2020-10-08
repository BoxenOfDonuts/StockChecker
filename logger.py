import logging
import uuid
from pythonjsonlogger import jsonlogger

runID = str(uuid.uuid4())
app = 'StockChecker'


class UUIDFilter(logging.Filter):
    def filter(self, record):
        record.runID = runID
        record.app = app
        return True


LOGFILE = '/mnt/price_check/stock_checker.log'
#LOGFILE = 'checker.log'
logHandler = logging.FileHandler(filename=LOGFILE)
formatter = jsonlogger.JsonFormatter('%(asctime)s %(runID)s %(app)s %(message)s')
logHandler.setFormatter(formatter)
logging.getLogger().addHandler(logHandler)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger()
logger.addFilter(UUIDFilter())