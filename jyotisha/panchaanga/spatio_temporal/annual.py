import logging
import os
import sys
import traceback

from indic_transliteration import xsanscript as sanscript

from jyotisha.panchaanga import spatio_temporal
from jyotisha.panchaanga.spatio_temporal import periodical
from jyotisha.panchaanga.spatio_temporal.periodical import Panchaanga
from jyotisha.panchaanga.temporal import zodiac
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject

common.update_json_class_index(sys.modules[__name__])


def get_panchaanga(city, year, compute_lagnas=False, precomputed_json_dir="~/Documents",
                   ayanaamsha_id=zodiac.Ayanamsha.CHITRA_AT_180, allow_precomputed=True):
  fname_det = os.path.expanduser('%s/%s-%s-detailed.json' % (precomputed_json_dir, city.name, year))
  fname = os.path.expanduser('%s/%s-%s.json' % (precomputed_json_dir, city.name, year))

  panchaanga = None
  if os.path.isfile(fname) and allow_precomputed:
    sys.stderr.write('Loaded pre-computed panchaanga from %s.\n' % fname)
    panchaanga = Panchaanga.read_from_file(filename=fname, name_to_json_class_index_extra={"Panchangam": periodical.Panchaanga})
    if not hasattr(panchaanga, 'version') or panchaanga.version != periodical.Panchaanga.LATEST_VERSION:
      logging.warning("Precomputed Panchanga obsolete.")
      return get_panchaanga(city=city, year=year, compute_lagnas=compute_lagnas, precomputed_json_dir=precomputed_json_dir,
                                  ayanaamsha_id=ayanaamsha_id, allow_precomputed=False)
    else:
      return panchaanga
  else:
    sys.stderr.write('No precomputed data available. Computing panchaanga...\n')
    panchaanga = periodical.Panchaanga(city=city, start_date='%d-01-01' % year, end_date='%d-12-31' % year, compute_lagnas=compute_lagnas,
                                       ayanaamsha_id=ayanaamsha_id)
    panchaanga.year = year
    sys.stderr.write('Writing computed panchaanga to %s...\n' % fname)

    try:
      if compute_lagnas:
        panchaanga.dump_to_file(filename=fname_det)
      else:
        panchaanga.dump_to_file(filename=fname)
    except EnvironmentError:
      logging.warning("Not able to save.")
      logging.error(traceback.format_exc())
    # Save without festival details
    # Festival data may be updated more frequently and a precomputed panchaanga may go out of sync. Hence we keep this method separate.
    panchaanga.update_festival_details()
    return panchaanga


if __name__ == '__main__':
  city = spatio_temporal.City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchaanga = periodical.Panchaanga(city=city, start_date='2019-01-01', end_date='2019-12-31', ayanaamsha_id=zodiac.Ayanamsha.CHITRA_AT_180,
                                     compute_lagnas=False)
