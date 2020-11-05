import logging
import sys
from collections import defaultdict
from typing import Dict

import methodtools
from timebudget import timebudget

from jyotisha.panchaanga.spatio_temporal import daily
from jyotisha.panchaanga.temporal import time, set_constants, ComputationSystem
from jyotisha.panchaanga.temporal.festival import applier, FestivalInstance
from jyotisha.panchaanga.temporal.festival.applier import tithi_festival, ecliptic, solar, vaara
from jyotisha.panchaanga.temporal.time import Date
from jyotisha.panchaanga.temporal.tithi import TithiAssigner
from jyotisha.util import default_if_none
from sanskrit_data import collection_helper
from sanskrit_data.schema import common

timebudget.set_quiet(True)  # don't show measurements as they happen
# timebudget.report_at_exit()  # Generate report when the program exits

set_constants()


class Panchaanga(common.JsonObject):
  """This class enables the construction of a panchaanga for arbitrary periods, with festival_id_to_instance.
  
    Generally, which days is a given festival associated with (esp pre-sunrise events)? We follow the same conventions as the adyatithi repo.
    """
  LATEST_VERSION = "0.0.4"

  def __init__(self, city, start_date, end_date, computation_system: ComputationSystem = None):
    """Constructor for the panchaanga.
        """
    super(Panchaanga, self).__init__()
    self.version = Panchaanga.LATEST_VERSION
    self.city = city
    self.start_date = Date(*([int(x) for x in start_date.split('-')])) if isinstance(start_date, str) else start_date
    self.start_date.set_time_to_day_start()
    self.end_date = Date(*([int(x) for x in end_date.split('-')])) if isinstance(end_date, str) else end_date
    self.end_date.set_time_to_day_start()

    self.computation_system = default_if_none(computation_system, ComputationSystem.DEFAULT)

    self.jd_start = time.utc_gregorian_to_jd(self.start_date)
    self.jd_end = time.utc_gregorian_to_jd(self.end_date)

    self.duration = int(self.jd_end - self.jd_start) + 1

    # For accurate festival assignment, we sometimes need panchaanga information about succeeding or preceeding days. 
    # For example, consider a festival to be selebrated during naxatra 27 in solar sideral month 9. If naxatra 27 occurs twice in sidereal_solar_month 9 (gap of 27+ daus), the latter occurence is to be selected - the former day will not get a festival. 
    self.duration_posterior_padding = int(self.duration + 30)
    self.duration_prior_padding = 2

    self.weekday_start = time.get_weekday(self.jd_start)

    self.festival_id_to_days = defaultdict(set, {})
    self.compute_angas(compute_lagnas=self.computation_system.options.lagnas)
    if not self.computation_system.options.no_fests:
      self.update_festival_details()

  @timebudget
  def compute_angas(self, compute_lagnas=True):
    """Compute the entire panchaanga
    """

    nDays = self.duration_posterior_padding

    # INITIALISE VARIABLES
    self.date_str_to_panchaanga: Dict[str, daily.DailyPanchaanga] = {}


    #############################################################
    # Compute all parameters -- sun/moon latitude/longitude etc #
    #############################################################

    for d in range(-self.duration_prior_padding, nDays - 1):
      # TODO: Eventually, we are shifting to an array of daily panchangas. Reason: Better modularity.
      # The below block is temporary code to make the transition seamless.
      date_d = time.jd_to_utc_gregorian(self.jd_start + d)
      date_d.set_time_to_day_start()
      previous_daily_panchaanga = self.date_str_to_panchaanga.get(date_d.offset_date(days=-1).get_date_str(), None)
      daily_panchaanga = daily.DailyPanchaanga(city=self.city, date=date_d,
                                               computation_system=self.computation_system,
                                               previous_day_panchaanga=previous_daily_panchaanga)
      if compute_lagnas:
        daily_panchaanga.get_lagna_data()
      self.date_str_to_panchaanga[date_d.get_date_str()] = daily_panchaanga

  @methodtools.lru_cache(maxsize=10)
  def daily_panchaangas_sorted(self):
    return sorted(self.date_str_to_panchaanga.values())

  def daily_panchaanga_for_jd(self, jd):
    date = self.city.timezone.julian_day_to_local_time(julian_day=jd)
    return self.daily_panchaanga_for_date(date=date)

  def daily_panchaanga_for_date(self, date):
    from copy import deepcopy
    date_alt = deepcopy(date)
    date_alt.set_time_to_day_start()
    return self.date_str_to_panchaanga.get(date_alt.get_date_str(), None)

  def pre_sunset_daily_panchaanga_for_jd(self, jd):
    panchaanga = self.daily_panchaanga_for_jd(jd=jd)
    if panchaanga.jd_sunset >= jd:
      return panchaanga
    else:
      return self.daily_panchaanga_for_date(date=panchaanga.date + 1)

  def post_sunrise_daily_panchaanga_for_jd(self, jd):
    panchaanga = self.daily_panchaanga_for_jd(jd=jd)
    if panchaanga.jd_sunrise <= jd:
      return panchaanga
    else:
      return self.daily_panchaanga_for_date(date=panchaanga.date - 1)

  def clear_padding_day_festivals(self):
    """Festival assignments for padding days are not trustworthy - since one would need to look-ahead or before into further days for accurate festival assignment. They were computed only to ensure accurate computation of the core days in this panchaanga. To avoid misleading, we ought to clear festivals provisionally assigned to the padding days."""
    daily_panchaangas = self.daily_panchaangas_sorted()
    for dp in daily_panchaangas[:self.duration_prior_padding]:
      for fest_id in dp.festival_id_to_instance.keys():
        self.festival_id_to_days[fest_id].discard(dp.date)
      dp.festival_id_to_instance = {}
    for dp in daily_panchaangas[self.duration_prior_padding + self.duration:]:
      for fest_id in dp.festival_id_to_instance.keys():
        self.festival_id_to_days[fest_id].discard(dp.date)
      dp.festival_id_to_instance = {}

  @timebudget
  def update_festival_details(self, debug=False):
    """

    Festival data may be updated more frequently and a precomputed panchaanga may go out of sync. Hence we keep this method separate.
    :return:
    """
    self._reset_festivals()
    daily_panchaangas = self.daily_panchaangas_sorted()
    misc_fest_assigner = applier.MiscFestivalAssigner(panchaanga=self)
    for index, dp in enumerate(daily_panchaangas):
      dp.assign_festivals(applier=misc_fest_assigner)
    TithiAssigner(panchaanga=self).assign_shraaddha_tithi()
    applier.FestivalsTimesDaysAssigner(panchaanga=self).assign_festivals_from_rules()
    misc_fest_assigner.assign_all()
    ecliptic.EclipticFestivalAssigner(panchaanga=self).assign_all()
    tithi_festival.TithiFestivalAssigner(panchaanga=self).assign_all()
    solar.SolarFestivalAssigner(panchaanga=self).assign_all()
    vaara.VaraFestivalAssigner(panchaanga=self).assign_all()
    misc_fest_assigner.cleanup_festivals(debug=debug)
    misc_fest_assigner.assign_relative_festivals()
    self._sync_festivals_dict_and_daily_festivals(here_to_daily=True, daily_to_here=True)
    misc_fest_assigner.assign_festival_numbers()
    self.clear_padding_day_festivals()


  def _sync_festivals_dict_and_daily_festivals(self, here_to_daily=False, daily_to_here=True):
    if here_to_daily:
      for festival_id, days in self.festival_id_to_days.items():
        for fest_day in days:
          if not isinstance(fest_day, Date):
            logging.fatal(festival_id + " " + str(days))
          fest_day_str = fest_day.get_date_str()
          if fest_day_str in self.date_str_to_panchaanga:
            self.date_str_to_panchaanga[fest_day_str].festival_id_to_instance[festival_id] =  FestivalInstance(name=festival_id)

    if daily_to_here:
      for dp in self.date_str_to_panchaanga.values():
        for fest in dp.festival_id_to_instance.values():
          days = self.festival_id_to_days.get(fest.name, set())
          if dp.date not in days:
            days.add(dp.date)
          self.festival_id_to_days[fest.name] = days

  def _reset_festivals(self):
    self.festival_id_to_days = defaultdict(set, {})
    for daily_panchaanga in self.date_str_to_panchaanga.values():
      daily_panchaanga.festival_id_to_instance = {}

  def delete_festival(self, fest_id):
    for date in self.festival_id_to_days.pop(fest_id, []):
      self.date_str_to_panchaanga[date.get_date_str()].festival_id_to_instance.pop(fest_id, None)
    

  def _refill_daily_panchaangas(self):
    """Avoids duplication for memory efficiency.
    
    Inverse of _force_non_redundancy_in_daily_panchaangas
    """
    for daily_panchaanga in self.date_str_to_panchaanga.values():
      daily_panchaanga.city = self.city
      daily_panchaanga.computation_system = self.computation_system

  def _force_non_redundancy_in_daily_panchaangas(self):
    """Avoids duplication for memory efficiency."""
    for daily_panchaanga in self.date_str_to_panchaanga.values():
      daily_panchaanga.city = None
      daily_panchaanga.computation_system = None

  def post_load_ops(self):
    self._refill_daily_panchaangas()
    self.festival_id_to_days = collection_helper.lists_to_sets(self.festival_id_to_days)

  @timebudget
  def dump_to_file(self, filename, floating_point_precision=None, sort_keys=True):
    self._force_non_redundancy_in_daily_panchaangas()
    self.festival_id_to_days = collection_helper.sets_to_lists(self.festival_id_to_days)
    super(Panchaanga, self).dump_to_file(filename=filename, floating_point_precision=floating_point_precision,
                                         sort_keys=sort_keys)
    self.festival_id_to_days = collection_helper.lists_to_sets(self.festival_id_to_days)
    self._refill_daily_panchaangas()


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
