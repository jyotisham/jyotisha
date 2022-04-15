from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject
import logging

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class DisplayOptions(JsonObject):
  def __init__(self, scripts=None, languages=None):
    self.scripts = scripts
    self.languages = languages

  def sort_festivals(self, festival_id_to_instance):
    pass


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)
