#!/usr/bin/python3 -u

# This web app may be run in two modes. See bottom of the file.
import json
import logging
import os.path
import sys

from jyotisha.rest_api import api_v1
from jyotisha.rest_api.flask_helper import app

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

# Add parent directory to PYTHONPATH, so that jyotisha module can be found.
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
logging.debug(sys.path)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config_local.json')
config = {'port': 9000, }
with open(CONFIG_PATH) as config_file:
  # noinspection PyRedeclaration
  config.update(json.loads(config_file.read()))


def setup_app():
  app.register_blueprint(api_v1.api_blueprint)


def main():
  setup_app()
  app.run(
    host="0.0.0.0",
    debug=False,
    port=config["port"],
    use_reloader=False
  )


if __name__ == "__main__":
  logging.info("Running in stand-alone mode.")
  main()
else:
  logging.info("Likely running as a WSGI app.")
  setup_app()
