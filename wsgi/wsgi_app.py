import logging
import os
import sys

from werkzeug.debug import DebuggedApplication

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

(file_path, fname) = os.path.split(__file__)
app_path = os.path.dirname(file_path)
os.chdir(app_path)
logging.info("My path is " + app_path)
sys.path.insert (0, app_path)
sys.stdout = sys.stderr
from jyotisha.rest_api import run

application = DebuggedApplication(run.app, True)
