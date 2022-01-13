#!/usr/bin/python3
#  -*- coding: utf-8 -*-
import codecs
import logging
import os

from indic_transliteration import sanscript

logging.basicConfig(level=logging.DEBUG,
                    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s ")

scripts = [sanscript.roman.HK_DRAVIDIAN, sanscript.ISO, sanscript.TAMIL, sanscript.TELUGU, sanscript.GRANTHA, sanscript.MALAYALAM]


def init_names_auto(fname=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'festival/data/period_names/misc_names.toml')):
  """Read various nakShatra, samvatsara, mAsa and such names from a file return a dict with all of that.

  :returns a dict like { "YEAR_NAMES": {"hk": } ...}
  """
  with open(fname) as f:
    import toml
    names_dict = toml.load(f)
    for dictionary in names_dict:
      if dictionary in ("SHUULAM", "SA_TO_TAMIL", "ARAB_MONTH_NAMES", "TIPU_ABJAD_MONTH_NAMES", "TIPU_ABTATH_MONTH_NAMES", "SIDEREAL_SOLAR_MONTH_NAMES", "GRAHA_NAMES"):
        continue
      if not dictionary.startswith('VARA_NAMES'):
        # Vara Names follow zero indexing, rest don't
        names_dict[dictionary]['sa'].insert(0, 'अस्पष्टम्')

      names_dict[dictionary]['sa'] = {sanscript.DEVANAGARI: names_dict[dictionary]['sa']}
      def _title(string):
        return '-'.join([(x[:1].upper() + x[1:]) for x in string.split('-')])
      for scr in scripts:
        if scr == sanscript.ISO:
          names_dict[dictionary]['sa'][scr] = [_title(sanscript.transliterate(name, sanscript.DEVANAGARI, scr)) for name in names_dict[dictionary]['sa'][sanscript.DEVANAGARI]]
        else:
          names_dict[dictionary]['sa'][scr] = [sanscript.transliterate(name, sanscript.DEVANAGARI, scr) for name in names_dict[dictionary]['sa'][sanscript.DEVANAGARI]]

    return names_dict

if __name__ == '__main__':
    init_names_auto()