#!/usr/bin/python3
import os
import pickle
import sys
from jyotisha.panchangam import panchangam
from jyotisha.panchangam.helper_functions import city


def main():
    [city_name, latitude, longitude, tz] = sys.argv[1:5]
    year = int(sys.argv[5])

    if len(sys.argv) == 7:
        script = sys.argv[6]
    else:
        script = 'iast'  # Default script is IAST for writing calendar

    City = city(city_name, latitude, longitude, tz)

    Panchangam = panchangam(city=City, year=year, script=script)

    fname_det = '../precomputed/%s-%s-detailed.pickle' % (city_name, year)
    fname = '../precomputed/%s-%s.pickle' % (city_name, year)

    if os.path.isfile(fname):
        # Load pickle, do not compute!
        with open(fname, 'rb') as f:
            Panchangam = pickle.load(f)
        sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
    elif os.path.isfile(fname_det):
        # Load pickle, do not compute!
        with open(fname_det, 'rb') as f:
            Panchangam = pickle.load(f)
        sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
    else:
        sys.stderr.write('No precomputed data available. Computing panchangam... ')
        sys.stderr.flush()
        Panchangam = panchangam(city=City, year=year, script=script)
        Panchangam.computeAngams(computeLagnams=False)
        Panchangam.assignLunarMonths()
        sys.stderr.write('done.\n')
        sys.stderr.write('Writing computed panchangam to %s...' % fname)
        with open(fname, 'wb') as f:
            # Pickle the 'data' dictionary using the highest protocol available.
            pickle.dump(Panchangam, f, pickle.HIGHEST_PROTOCOL)

    Panchangam.computeFestivals()
    Panchangam.computeSolarEclipses()
    Panchangam.computeLunarEclipses()

    Panchangam.computeIcsCalendar()
    Panchangam.writeIcsCalendar('%s-%d-%s.ics' % (city_name, year, script))


if __name__ == '__main__':
    main()
else:
    '''Imported as a module'''
