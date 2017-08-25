#!/usr/bin/python3
#  -*- coding: utf-8 -*-

from indic_transliteration.little.transliterator import transliterate as tr
import ast


def init_names_auto(fname='translation_table_HK.tsv'):

    with open(fname) as f:
        lines = f.readlines()

    scripts_list = ['devanagari', 'iast']

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
                    NAMES[var[:-6]][scr][key] = str(tr(NAMES[var[:-6]]['hk'][key],
                                                       'harvardkyoto', scr), 'utf8').title()
        else:
            NAMES[var] = {}
            NAMES[var]['hk'] = value.strip('\'')
            for scr in scripts_list:
                NAMES[var][scr] = str(tr(NAMES[var]['hk'], 'harvardkyoto', scr), 'utf8').title()

    return (NAMES)
