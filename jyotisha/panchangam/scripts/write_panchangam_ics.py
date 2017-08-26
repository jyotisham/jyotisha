#!/usr/bin/python3
import os
import pickle
import sys

from indic_transliteration import sanscript

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

    fname_det = os.path.join(CODE_ROOT, 'data/precomputed/%s-%s-detailed.pickle' % (city_name, year))
    fname = os.path.join(CODE_ROOT, 'data/precomputed/%s-%s.pickle' % (city_name, year))

    if os.path.isfile(fname):
        # Load pickle, do not compute!
        with open(fname, 'rb') as f:
            panchangam = pickle.load(f)
        sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
    elif os.path.isfile(fname_det):
        # Load pickle, do not compute!
        with open(fname_det, 'rb') as f:
            panchangam = pickle.load(f)
        sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
    else:
        sys.stderr.write('No precomputed data available. Computing panchangam... ')
        sys.stderr.flush()
        panchangam = Panchangam(city=city, year=year, script=script)
        panchangam.computeAngams(computeLagnams=False)
        panchangam.assignLunarMonths()
        sys.stderr.write('done.\n')
        sys.stderr.write('Writing computed panchangam to %s...' % fname)
        with open(fname, 'wb') as f:
            # Pickle the 'data' dictionary using the highest protocol available.
            pickle.dump(panchangam, f, pickle.HIGHEST_PROTOCOL)

    Panchangam.computeFestivals()
    Panchangam.computeSolarEclipses()
    Panchangam.computeLunarEclipses()

    Panchangam.computeIcsCalendar()
    Panchangam.writeIcsCalendar('%s-%d-%s.ics' % (city_name, year, script))


if __name__ == '__main__':
    main()
else:
    '''Imported as a module'''
