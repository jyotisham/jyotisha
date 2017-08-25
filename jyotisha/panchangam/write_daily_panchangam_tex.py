#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os.path
import pickle
import sys
from jyotisha.panchangam import panchangam
from jyotisha.panchangam.helper_functions import city


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

    City = city(city_name, latitude, longitude, tz)

    if computeLagnams:
        # Includes lagna etc
        fname = '../precomputed/%s-%s-detailed.pickle' % (city_name, year)
    else:
        fname = '../precomputed/%s-%s.pickle' % (city_name, year)

    if os.path.isfile(fname):
        # Load pickle, do not compute!
        with open(fname, 'rb') as f:
            Panchangam = pickle.load(f)
        sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
    else:
        sys.stderr.write('No precomputed data available. Computing panchangam... ')
        sys.stderr.flush()
        Panchangam = panchangam(city=City, year=year, script=script)
        Panchangam.computeAngams(computeLagnams)
        Panchangam.assignLunarMonths()
        sys.stderr.write('done.\n')
        sys.stderr.write('Writing computed panchangam to %s...' % fname)
        with open(fname, 'wb') as f:
            # Pickle the 'data' dictionary using the highest protocol available.
            pickle.dump(Panchangam, f, pickle.HIGHEST_PROTOCOL)

    Panchangam.computeFestivals()
    Panchangam.computeSolarEclipses()
    Panchangam.computeLunarEclipses()

    daily_template_file = open('../tex/templates/daily_cal_template.tex')
    Panchangam.writeDailyTeX(daily_template_file, computeLagnams)
    # Panchangam.writeDebugLog()


if __name__ == '__main__':
    main()
