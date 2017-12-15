#!/usr/bin/python3
#  -*- coding: utf-8 -*-

import ast

import os
from indic_transliteration import xsanscript as sanscript
import logging

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

CODE_ROOT = os.path.dirname(os.path.dirname(__file__))


def init_names_auto(fname=os.path.join(CODE_ROOT, 'names/data/translation_table_HK.tsv')):
  with open(fname) as f:
    lines = f.readlines()

  scripts_list = [sanscript.DEVANAGARI, sanscript.IAST]

  names_dict = {}
  for line in lines:
    var, value = line.strip().split('\t')

    if var[-5:] == 'names_dict':
      # This will be a dictionary itself, like MASA_NAMES
      names_dict[var[:-6]] = {}
      names_dict[var[:-6]]['hk'] = ast.literal_eval(value)

      for scr in scripts_list:
        names_dict[var[:-6]][scr] = {}
        for key in names_dict[var[:-6]]['hk']:
          names_dict[var[:-6]][scr][key] = sanscript.transliterate(names_dict[var[:-6]]['hk'][key],
                                                              sanscript.HK, scr).title()
    else:
      names_dict[var] = {}
      names_dict[var]['hk'] = value.strip('\'')
      for scr in scripts_list:
        names_dict[var][scr] = sanscript.transliterate(names_dict[var]['hk'], sanscript.HK, scr).title()

  return names_dict
