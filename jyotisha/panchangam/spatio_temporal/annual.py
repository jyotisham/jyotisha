import logging
import os
import sys
import traceback

from indic_transliteration import xsanscript as sanscript

from jyotisha.panchangam import spatio_temporal
from jyotisha.panchangam.spatio_temporal import periodical
from jyotisha.panchangam.temporal import zodiac
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject

common.update_json_class_index(sys.modules[__name__])


def get_panchaanga(city, year, script, fmt='hh:mm', compute_lagnams=False, precomputed_json_dir="~/Documents",
                   ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180, allow_precomputed=True):
  fname_det = os.path.expanduser('%s/%s-%s-detailed.json' % (precomputed_json_dir, city.name, year))
  fname = os.path.expanduser('%s/%s-%s.json' % (precomputed_json_dir, city.name, year))

  if os.path.isfile(fname) and not compute_lagnams and allow_precomputed:
    sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
    return JsonObject.read_from_file(filename=fname)
  elif os.path.isfile(fname_det) and allow_precomputed:
    # Load pickle, do not compute!
    sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
    return JsonObject.read_from_file(filename=fname_det)
  else:
    sys.stderr.write('No precomputed data available. Computing panchangam...\n')
    panchangam = periodical.Panchangam(city=city, start_date='%d-01-01' % year, end_date='%d-12-31' % year,
                                       script=script, fmt=fmt, compute_lagnams=compute_lagnams,
                                       ayanamsha_id=ayanamsha_id)
    panchangam.year = year
    sys.stderr.write('Writing computed panchangam to %s...\n' % fname)

    try:
      if compute_lagnams:
        panchangam.dump_to_file(filename=fname_det)
      else:
        panchangam.dump_to_file(filename=fname)
    except EnvironmentError:
      logging.warning("Not able to save.")
      logging.error(traceback.format_exc())
    # Save without festival details
    # Festival data may be updated more frequently and a precomputed panchangam may go out of sync. Hence we keep this method separate.
    panchangam.update_festival_details()
    return panchangam


if __name__ == '__main__':
  city = spatio_temporal.City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchangam = periodical.Panchangam(city=city, start_date='2019-01-01', end_date='2019-12-31',
                                     script=sanscript.DEVANAGARI, ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180,
                                     fmt='hh:mm', compute_lagnams=False)
