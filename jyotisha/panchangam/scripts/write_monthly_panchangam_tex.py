#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import os.path
import sys

from indic_transliteration import sanscript

from jyotisha.panchangam import scripts
from jyotisha.panchangam.spatio_temporal import City

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)



CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def main():
    [city_name, latitude, longitude, tz] = sys.argv[1:5]
    year = int(sys.argv[5])

    script = sanscript.DEVANAGARI  # Default script is devanagari

    if len(sys.argv) == 7:
        script = sys.argv[6]

    city = City(city_name, latitude, longitude, tz)
    panchangam = scripts.get_panchangam(city=city, year=year, script=script)

    panchangam.computeFestivals()
    panchangam.computeSolarEclipses()
    panchangam.computeLunarEclipses()

    monthly_template_file = open(os.path.join(CODE_ROOT, 'panchangam/data/templates/monthly_cal_template.tex'))
    panchangam.writeMonthlyTeX(monthly_template_file)
    # panchangam.writeDebugLog()


if __name__ == '__main__':
    main()
