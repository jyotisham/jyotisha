#!/usr/bin/python3
#  -*- coding: utf-8 -*-
import json
from collections import OrderedDict
from init_names_auto import init_names_auto
from transliterator import transliterate as tr

if __name__ == '__main__':
    NAMES = init_names_auto()
    with open('kanchi_aradhana_rules.json') as aradhana_data:
        aradhana_rules = json.load(aradhana_data, object_pairs_hook=OrderedDict)

    for script in ['devanagari', 'iast']:
        with open('../docs/kanchi_aradhana_days_%s.md' % script, 'w') as f:
            f.write('## Sri Kanchi Matham Guru Aaradhana Days\n\n')
            f.write('(obtained from [kamakoti.org](http://kamakoti.org/peeth/origin.html#appendix2), ')
            f.write('and corrected using [@kamakoti twitter feed](https://twitter.com/kamakoti)!)\n\n')
            f.write('| # | Jagadguru | Mukti Year (Kali) | Mukti Year Name | Month | Tithi |\n')
            f.write('| - | --------- | ----------------- | --------------- | ----- | ----- |\n')
            for guru in aradhana_rules.keys():
                if guru[:5] == 'kAJcI':
                    name = str(' '.join(guru.split()[3:-1])).replace('~', ' ')
                    num = int(guru.split()[1])
                    kali_year = str(aradhana_rules[guru]['Start Year'] - 1)
                    year_name = NAMES['YEAR'][script][((int(kali_year) + 12) % 60) + 1]
                else:
                    name = guru[:-9]
                    num = '-'
                    kali_year = '-'
                    year_name = '-'
                tithi = NAMES['TITHI'][script][aradhana_rules[guru]['Angam Number']]
                if aradhana_rules[guru]['Month Type'] == 'lunar_month':
                    month_name = NAMES['CHANDRA_MASA'][script][aradhana_rules[guru]['Month Number']]
                elif aradhana_rules[guru]['Month Type'] == 'solar_month':
                    month_name = NAMES['MASA'][script][aradhana_rules[guru]['Month Number']]
                f.write('| %s | %s | %s | %s | %s | %s |\n' %
                        (num, str(tr(name, 'harvardkyoto', script), 'utf8').title(),
                         kali_year, year_name, month_name, tithi.replace('~', ' ')))
