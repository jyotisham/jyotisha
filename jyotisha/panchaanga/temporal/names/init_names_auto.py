#!/usr/bin/python3
#  -*- coding: utf-8 -*-
import codecs
import logging
import os

from indic_transliteration import xsanscript as xsanscript

logging.basicConfig(level=logging.DEBUG,
                    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s ")

scripts = [xsanscript.HK, xsanscript.IAST, xsanscript.TAMIL, xsanscript.TELUGU]


def init_names_auto(fname=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'festival/data/period_names/translation_table.json')):
  """Read various nakShatra, samvatsara, mAsa and such names from a file return a dict with all of that.

  :returns a dict like { "YEAR_NAMES": {"hk": } ...}
  """
  with open(fname) as f:
    import json
    names_dict = json.load(f)
    new_names_dict = {}
    for dictionary in names_dict:
      if dictionary in ("SHUULAM", "SA_TO_TAMIL", "ARAB_MONTH_NAMES", "TIPU_ABJAD_MONTH_NAMES", "TIPU_ABTATH_MONTH_NAMES"):
        continue
      if dictionary != 'VARA_NAMES':
        # Vara Names follow zero indexing, rest don't
        names_dict[dictionary]['sa'].insert(0, 'अस्पष्टम्')

      names_dict[dictionary]['sa'] = {xsanscript.DEVANAGARI: names_dict[dictionary]['sa']}
      for scr in scripts:
        names_dict[dictionary]['sa'][scr] = [xsanscript.transliterate(name, xsanscript.DEVANAGARI, scr).title() if scr == xsanscript.IAST else xsanscript.transliterate(name, xsanscript.DEVANAGARI, scr) for name in
                                       names_dict[dictionary]['sa'][xsanscript.DEVANAGARI]]
    #   
    #   new_names_dict[dictionary] = {"sa": names_dict[dictionary]['sa'][xsanscript.HK]}
    # with codecs.open(fname + ".new",  "w") as f:
    #   json.dump(new_names_dict, f, ensure_ascii=False, indent=2)
    return names_dict

if __name__ == '__main__':
    init_names_auto()