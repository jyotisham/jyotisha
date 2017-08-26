#!/usr/bin/python3
#  -*- coding: utf-8 -*-

import ast

import os
from indic_transliteration import sanscript
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

    NAMES = {}
    for line in lines:
        var, value = line.strip().split('\t')

        if var[-5:] == 'NAMES':
            # This will be a dictionary itself, like MASA_NAMES
            NAMES[var[:-6]] = {}
            NAMES[var[:-6]]['hk'] = ast.literal_eval(value)

            for scr in scripts_list:
                NAMES[var[:-6]][scr] = {}
                for key in NAMES[var[:-6]]['hk']:
                    NAMES[var[:-6]][scr][key] = sanscript.transliterate(NAMES[var[:-6]]['hk'][key],
                                                       sanscript.HK, scr).title()
        else:
            NAMES[var] = {}
            NAMES[var]['hk'] = value.strip('\'')
            for scr in scripts_list:
                NAMES[var][scr] = sanscript.transliterate(NAMES[var]['hk'], sanscript.HK, scr).title()

    return (NAMES)
