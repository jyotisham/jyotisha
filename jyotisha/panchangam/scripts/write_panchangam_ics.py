#!/usr/bin/python3
import os
import pickle
import sys

from indic_transliteration import sanscript
from sanskrit_data.schema.common import JsonObject

from jyotisha.panchangam.panchangam import Panchangam
from jyotisha.panchangam.spatio_temporal import City
import logging

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

    if os.path.isfile(fname):
        # Load pickle, do not compute!
        panchangam = JsonObject.read_from_file(filename=fname)
        sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
    elif os.path.isfile(fname_det):
        # Load pickle, do not compute!
        panchangam = JsonObject.read_from_file(filename=fname_det)
        sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
    else:
        sys.stderr.write('No precomputed data available. Computing panchangam... ')
        sys.stderr.flush()
        panchangam = Panchangam(city=city, year=year, script=script)
        panchangam.computeAngams(computeLagnams=False)
        panchangam.assignLunarMonths()
        sys.stderr.write('done.\n')
        sys.stderr.write('Writing computed panchangam to %s...' % fname)
        try:
            panchangam.dump_to_file(filename=fname)
        except EnvironmentError:
            logging.warning("Not able to save.")

    panchangam.computeFestivals()
    panchangam.computeSolarEclipses()
    panchangam.computeLunarEclipses()

    panchangam.computeIcsCalendar()
    panchangam.writeIcsCalendar('%s-%d-%s.ics' % (city_name, year, script))


if __name__ == '__main__':
    main()
else:
    '''Imported as a module'''
