import codecs
import functools
import os

import toml

from jyotisha.panchaanga.temporal.festival.rules import DATA_ROOT
_PANCHA_PAXIN_PATH = os.path.join(DATA_ROOT, "pancha-paxin")


@functools.lru_cache()
def get_names_table():
  names_path = os.path.join(_PANCHA_PAXIN_PATH, "names.toml")
  with codecs.open(names_path, "r") as fp:
    pancha_paxin_names = toml.load(fp)
    return pancha_paxin_names


@functools.lru_cache()
def get_activities_table(weekday_id, paxa_id):
  pancha_paxin_names = get_names_table()
  table_path = os.path.join(_PANCHA_PAXIN_PATH, "paxa", pancha_paxin_names["table_ids"][str(paxa_id)][str(weekday_id)])
  import pandas
  activities_table = pandas.read_csv(table_path)
  return activities_table