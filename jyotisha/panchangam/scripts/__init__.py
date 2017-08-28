import os

import sys
import traceback

from sanskrit_data.schema.common import JsonObject

from jyotisha.panchangam.spatio_temporal import Panchangam
import logging

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def get_panchangam(city, year, script):
  fname_det = os.path.expanduser('~/Documents/%s-%s-detailed.json' % (city.name, year))
  fname = os.path.expanduser('~/Documents/%s-%s.json' % (city.name, year))

  if os.path.isfile(fname):
    sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
    return JsonObject.read_from_file(filename=fname)
  elif os.path.isfile(fname_det):
    # Load pickle, do not compute!
    sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
    return JsonObject.read_from_file(filename=fname_det)
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
      logging.error(traceback.format_exc())
    return panchangam