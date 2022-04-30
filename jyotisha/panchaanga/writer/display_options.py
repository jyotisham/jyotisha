from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject
import logging
import sys

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class DisplayOptions(JsonObject):
  def __init__(self, scripts=None, languages=None):
    self.scripts = scripts
    self.languages = languages

  def sort_festivals(self, festival_id_to_instance):
    return sorted(festival_id_to_instance.values())


class KarthikDisplayOptions(DisplayOptions):
  def __init__(self, scripts=None, languages=None):
    self.scripts = scripts
    self.languages = languages

  def sort_festivals(self, festival_id_to_instance):
    festivals_list = sorted(festival_id_to_instance.values())
    prioritised_festivals_list = ['saGkramaNa', 'grahaNa', 'amAvAsyA', 'zrAddha',
                                  'mAsaH', 'EkAdazI', 'vijayA/zravaNa', 'saMvatsaraH', 'harivAsaraH', 
                                  'caturthI']
    manually_prioritised_festivals = []

    for f in list(festivals_list):
      if any(match in f.name for match in prioritised_festivals_list):
        festivals_list.remove(f)
        manually_prioritised_festivals.append(f)

    if manually_prioritised_festivals:
      festivals_list = manually_prioritised_festivals + festivals_list

    return festivals_list


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)
