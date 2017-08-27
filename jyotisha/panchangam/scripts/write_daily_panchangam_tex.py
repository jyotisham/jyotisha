#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import os.path
import sys

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

    computeLagnams = False  # Default
    script = 'deva'  # Default script is devanagari

    if len(sys.argv) == 8:
        computeLagnams = True
        script = sys.argv[6]
    elif len(sys.argv) == 7:
        script = sys.argv[6]
        computeLagnams = False

    city = City(city_name, latitude, longitude, tz)

    panchangam = scripts.get_panchangam()

    panchangam.computeFestivals()
    panchangam.computeSolarEclipses()
    panchangam.computeLunarEclipses()

    daily_template_file = open(os.path.join(CODE_ROOT, 'panchangam/data/templates/daily_cal_template.tex'))
    panchangam.writeDailyTeX(daily_template_file, computeLagnams)
    # panchangam.writeDebugLog()


if __name__ == '__main__':
    main()
