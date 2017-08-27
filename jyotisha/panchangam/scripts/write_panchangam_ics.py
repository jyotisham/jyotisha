#!/usr/bin/python3
import logging
import os
import sys

from indic_transliteration import sanscript

from jyotisha.panchangam import scripts
from jyotisha.panchangam.panchangam import Panchangam
from jyotisha.panchangam.spatio_temporal import City

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)



CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))



def main():
    [city_name, latitude, longitude, tz] = sys.argv[1:5]
    year = int(sys.argv[5])

    if len(sys.argv) == 7:
        script = sys.argv[6]
    else:
        script = sanscript.IAST  # Default script is IAST for writing calendar

    city = City(city_name, latitude, longitude, tz)

    panchangam = Panchangam(city=city, year=year, script=script)

    fname_det = os.path.expanduser('~/Documents/%s-%s-detailed.json' % (city_name, year))
    fname = os.path.expanduser('~/Documents/%s-%s.json' % (city_name, year))

    panchangam = scripts.get_panchangam(city=city, year=year, script=script)


    panchangam.computeFestivals()
    panchangam.computeSolarEclipses()
    panchangam.computeLunarEclipses()

    panchangam.computeIcsCalendar()
    panchangam.writeIcsCalendar('%s-%d-%s.ics' % (city_name, year, script))


if __name__ == '__main__':
    main()
else:
    '''Imported as a module'''
