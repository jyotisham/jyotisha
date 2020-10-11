import logging
import os
import sys
import traceback

from jyotisha.panchaanga.spatio_temporal import periodical
from jyotisha.panchaanga.spatio_temporal.periodical import Panchaanga
from jyotisha.panchaanga.temporal import ComputationSystem, set_constants, time
from jyotisha.panchaanga.temporal.time import Date, Timezone
from jyotisha.panchaanga.temporal.zodiac import AngaSpanFinder, Ayanamsha
from sanskrit_data.schema import common
from jyotisha.panchaanga.temporal.zodiac.angas import AngaType

common.update_json_class_index(sys.modules[__name__])

set_constants()


def load_panchaanga(fname, fallback_fn):
  logging.info('Loaded pre-computed panchaanga from %s.\n' % fname)
  panchaanga = Panchaanga.read_from_file(filename=fname, name_to_json_class_index_extra={"Panchangam": periodical.Panchaanga})
  if getattr(panchaanga, 'version', None) is None or panchaanga.version != periodical.Panchaanga.LATEST_VERSION:
    logging.warning("Precomputed Panchanga obsolete.")
    return fallback_fn()
  else:
    # Festival data may be updated more frequently and a precomputed panchaanga may go out of sync. Hence we keep this method separate.
    panchaanga.update_festival_details()
    panchaanga.dump_to_file(filename=fname)
    return panchaanga
  


def get_panchaanga_for_shaka_year(city, year, precomputed_json_dir="~/Documents/jyotisha", computation_system: ComputationSystem = None, allow_precomputed=True):
  fname = os.path.expanduser('%s/%s__shaka_%s__%s.json' % (precomputed_json_dir, city.name, year, computation_system))
  if os.path.isfile(fname) and allow_precomputed:
    fn = lambda: get_panchaanga_for_shaka_year(city=city, year=year, precomputed_json_dir=precomputed_json_dir,
                                               computation_system=computation_system, allow_precomputed=False)
    return load_panchaanga(fname=fname, fallback_fn=fn)
  else:
    logging.info('No precomputed data available. Computing panchaanga...\n')
    SHAKA_CIVIL_ERA_DIFF = 78
    start_year_civil = year + SHAKA_CIVIL_ERA_DIFF
    anga_span_finder = AngaSpanFinder.get_cached(ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0, anga_type=AngaType.SIDEREAL_MONTH)
    start_equinox = anga_span_finder.find(jd1=time.utc_gregorian_to_jd(Date(year=start_year_civil, month=3, day=1)), jd2=time.utc_gregorian_to_jd(Date(year=start_year_civil, month=5, day=1)), target_anga_id=1)
    end_equinox = anga_span_finder.find(jd1=time.utc_gregorian_to_jd(Date(year=start_year_civil  + 1, month=3, day=1)), jd2=time.utc_gregorian_to_jd(Date(year=start_year_civil + 1, month=5, day=1)), target_anga_id=1)
    tz = Timezone(city.timezone)
    panchaanga = periodical.Panchaanga(city=city, start_date=tz.julian_day_to_local_time(julian_day=start_equinox.jd_start), end_date=tz.julian_day_to_local_time(julian_day=end_equinox.jd_start), computation_system=computation_system)
    panchaanga.year = year
    # Festival data may be updated more frequently and a precomputed panchaanga may go out of sync. Hence we keep this method separate.
    panchaanga.update_festival_details()
    logging.info('Writing computed panchaanga to %s...\n' % fname)

    try:
      panchaanga.dump_to_file(filename=fname)
    except EnvironmentError:
      logging.warning("Not able to save.")
      logging.error(traceback.format_exc())
    return panchaanga


def get_panchaanga_for_civil_year(city, year, precomputed_json_dir="~/Documents/jyotisha",
                                  computation_system: ComputationSystem = None, allow_precomputed=True):
  fname = os.path.expanduser('%s/%s-%s.json' % (precomputed_json_dir, city.name, year))

  if os.path.isfile(fname) and allow_precomputed:
    fn = lambda: get_panchaanga_for_civil_year(city=city, year=year, precomputed_json_dir=precomputed_json_dir,
                                            computation_system=computation_system, allow_precomputed=False)
    return load_panchaanga(fname=fname, fallback_fn=fn) 
  else:
    logging.info('No precomputed data available. Computing panchaanga...\n')
    panchaanga = periodical.Panchaanga(city=city, start_date='%d-01-01' % year, end_date='%d-12-31' % year, computation_system=computation_system)
    panchaanga.year = year
    logging.info('Writing computed panchaanga to %s...\n' % fname)

    panchaanga.dump_to_file(filename=fname)
    # Save without festival details
    # Festival data may be updated more frequently and a precomputed panchaanga may go out of sync. Hence we keep this method separate.
    panchaanga.update_festival_details()
    return panchaanga

