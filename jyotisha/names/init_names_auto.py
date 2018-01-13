#!/usr/bin/python3
#  -*- coding: utf-8 -*-

import os
import logging
from indic_transliteration import xsanscript as sanscript

logging.basicConfig(level=logging.DEBUG,
                    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s ")

CODE_ROOT = os.path.dirname(os.path.dirname(__file__))

scripts = [sanscript.DEVANAGARI, sanscript.IAST]


def init_names_auto(fname=os.path.join(CODE_ROOT, 'names/data/translation_table_HK.json')):
  """Read various nakShatra, samvatsara, mAsa and such names from a file return a dict with all of that.

  :returns a dict like { "YEAR_NAMES": {"hk": } ...}
  """
  with open(fname) as f:
    import json
    names_dict = json.load(f)
    for dictionary in names_dict:
      if dictionary != 'VARA_NAMES':
        # Vara Names follow zero indexing, rest don't
        names_dict[dictionary]['hk'].insert(0, 'aspaShTam')

      for scr in scripts:
        names_dict[dictionary][scr] = [sanscript.transliterate(name, 'hk', scr).title() for name in names_dict[dictionary]['hk']]
    return names_dict
