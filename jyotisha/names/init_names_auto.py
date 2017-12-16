#!/usr/bin/python3
#  -*- coding: utf-8 -*-

import ast

import os
import logging

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

CODE_ROOT = os.path.dirname(os.path.dirname(__file__))


def init_names_auto(fname=os.path.join(CODE_ROOT, 'names/data/translation_table_HK.json')):
  """Read various nakShatra, samvatsara, mAsa and such names from a file return a dict with all of that.

  :returns a dict like { "YEAR_NAMES": {"hk": } ...}
  """
  with open(fname) as f:
    import json
    names_dict = json.load(f)
    logging.debug(json.dumps(names_dict, sort_keys=True, indent=2))
    return names_dict
