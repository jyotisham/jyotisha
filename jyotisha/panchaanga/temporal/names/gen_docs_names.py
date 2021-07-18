#!/usr/bin/python3
#  -*- coding: utf-8 -*-
import logging

from indic_transliteration import sanscript

from jyotisha.panchaanga.temporal.names.init_names_auto import init_names_auto

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

if __name__ == '__main__':
  NAMES = init_names_auto()

  # TODO: Verify the below.
  with open('README.md', 'w') as f:
    for anga in NAMES:
      f.write('## ' + anga + '\n')
      f.write('(as initialised from `init_names_auto.py`)\n\n')
      f.write('| # | ' + ' | '.join(sorted(list(NAMES[anga]['sa'].keys()))) + ' |\n')
      f.write('|---| ' + ' | '.join(['-' * len(scr)
                                     for scr in sorted(list(NAMES[anga]['sa'].keys()))]) + ' |\n')
      if anga == 'VARA_NAMES':
        amin = 0  # min anga for VARA alone is 0, rest 1
      else:
        amin = 1
      for num in range(amin, len(NAMES[anga]['sa'][sanscript.roman.HK_DRAVIDIAN])):
        line = '| %d' % (num)
        for script in sorted(list(NAMES[anga]['sa'].keys())):
          line += ' | ' + sanscript.transliterate(NAMES[anga]['sa'][sanscript.roman.HK_DRAVIDIAN][num], sanscript.roman.HK_DRAVIDIAN, script)
        f.write(line + ' |\n')
      f.write('\n\n')
