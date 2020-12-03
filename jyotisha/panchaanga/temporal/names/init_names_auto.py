#!/usr/bin/python3
#  -*- coding: utf-8 -*-

import logging
import os

from indic_transliteration import xsanscript as sanscript

logging.basicConfig(level=logging.DEBUG,
                    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s ")

scripts = [sanscript.DEVANAGARI, sanscript.IAST, sanscript.TAMIL, sanscript.TELUGU]


def init_names_auto(fname=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'festival/data/period_names/translation_table_HK.json')):
  """Read various nakShatra, samvatsara, mAsa and such names from a file return a dict with all of that.

  :returns a dict like { "YEAR_NAMES": {"hk": } ...}
  """
  with open(fname) as f:
    import json
    names_dict = json.load(f)
    for dictionary in names_dict:
      if dictionary == "SHUULAM":
        continue
      if dictionary != 'VARA_NAMES':
        # Vara Names follow zero indexing, rest don't
        names_dict[dictionary]['sa'].insert(0, 'aspaShTam')

      names_dict[dictionary]['sa'] = {'hk': names_dict[dictionary]['sa']}
      for scr in scripts:
        names_dict[dictionary]['sa'][scr] = [sanscript.transliterate(name, 'hk', scr).title() for name in
                                       names_dict[dictionary]['sa']['hk']]
    return names_dict
