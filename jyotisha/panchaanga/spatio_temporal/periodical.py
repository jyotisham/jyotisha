import copy
import logging
import sys
from collections import defaultdict
from typing import Dict

import methodtools
from timebudget import timebudget

from jyotisha.panchaanga.spatio_temporal import daily
from jyotisha.panchaanga.temporal import time, set_constants, ComputationSystem, AngaType, era
from jyotisha.panchaanga.temporal.festival import FestivalInstance
from jyotisha.panchaanga.temporal.festival.applier import tithi_festival, ecliptic, solar, vaara, rule_repo_based, \
  FestivalAssigner
from jyotisha.panchaanga.temporal.time import Date
from jyotisha.panchaanga.temporal.tithi import ShraddhaTithiAssigner
from jyotisha.panchaanga.temporal.zodiac.angas import Tithi
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

  def __init__(self, city, start_date, end_date, year_type = None, computation_system: ComputationSystem = None):
    """Constructor for the panchaanga.
        """
    super(Panchaanga, self).__init__()
    self.version = Panchaanga.LATEST_VERSION
    self.city = city
    self.start_date = Date(*([int(x) for x in start_date.split('-')])) if isinstance(start_date, str) else start_date
    self.start_date.set_time_to_day_start()
    self.end_date = Date(*([int(x) for x in end_date.split('-')])) if isinstance(end_date, str) else end_date
    self.end_date.set_time_to_day_start()
    self.year_type = year_type

    self.computation_system = default_if_none(computation_system, ComputationSystem.DEFAULT)

    self.jd_start = time.utc_gregorian_to_jd(self.start_date)
    self.jd_end = time.utc_gregorian_to_jd(self.end_date)

    self.duration = int(self.jd_end - self.jd_start) + 1

    # For accurate festival assignment, we sometimes need panchaanga information about succeeding or preceding days. 
    # For example, consider a festival to be selebrated during naxatra 27 in solar sideral month 9. If naxatra 27 occurs twice in sidereal_solar_month 9 (gap of 27+ daus), the latter occurence is to be selected - the former day will not get a festival. 
    self.duration_posterior_padding = int(self.duration + 30)
    self.duration_prior_padding = 2

    self.weekday_start = time.get_weekday(self.jd_start)

    self.festival_id_to_days = defaultdict(set, {})
    self.compute_angas(compute_lagnas=self.computation_system.festival_options.lagnas)
    if not self.computation_system.festival_options.no_fests:
      self.update_festival_details()

  @timebudget
  def compute_angas(self, compute_lagnas=True):
    """Compute the entire panchaanga
    """

    # INITIALISE VARIABLES
    self.date_str_to_panchaanga: Dict[str, daily.DailyPanchaanga] = {}


    #############################################################
    # Compute all parameters -- sun/moon latitude/longitude etc #
    #############################################################

    for d in range(-self.duration_prior_padding, self.duration_posterior_padding - 1):
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
  def daily_panchaangas_sorted(self, skip_padding_days=False):
    if not skip_padding_days:
      return sorted(self.date_str_to_panchaanga.values())
    else:
      full_list = sorted(self.date_str_to_panchaanga.values())
      return [x for x in full_list if self.start_date <= x.date and x.date <= self.end_date]

  def daily_panchaanga_for_jd(self, jd):
    date = self.city.get_timezone_obj().julian_day_to_local_time(julian_day=jd)
    return self.daily_panchaanga_for_date(date=date)

  def daily_panchaanga_for_date(self, date):
    return self.date_str_to_panchaanga.get(date.get_date_str(), None)

  def pre_sunset_daily_panchaanga_for_jd(self, jd):
    panchaanga = self.daily_panchaanga_for_jd(jd=jd)
    if panchaanga is None:
      return None
    elif panchaanga.jd_sunset >= jd:
      return panchaanga
    else:
      return self.daily_panchaanga_for_date(date=panchaanga.date + 1)

  def post_sunrise_daily_panchaanga_for_jd(self, jd):
    panchaanga = self.daily_panchaanga_for_jd(jd=jd)
    if panchaanga is None:
      return None
    elif panchaanga.jd_sunrise <= jd:
      return panchaanga
    else:
      return self.daily_panchaanga_for_date(date=panchaanga.date - 1)

  def get_interval_anga_spans(self, date, interval_id, anga_type):
    dp = self.daily_panchaanga_for_date(date)
    (anga_spans, _) = dp.get_interval_anga_spans(interval_id=interval_id, anga_type=anga_type)
    anga_spans = copy.deepcopy(anga_spans)

    if anga_type == AngaType.TITHI:
      for span in anga_spans:
        if span.anga.index in (1, 2):
          # The below is necessary because tithi 1 or 2 may start after sunrise.
          dp_next = self.daily_panchaanga_for_date(date + 1)
          # Lunar month below may be incorrect (adhika mAsa complication) if dp_next is not available (eg when the next day is beyond this panchaanga duration). Downstream code should be aware of that case.
          month = dp_next.lunar_month_sunrise if dp_next is not None else dp.lunar_month_sunrise + 1
          span.anga = Tithi.from_anga(anga=span.anga, month=month)
        else:
          span.anga = Tithi.from_anga(anga=span.anga, month=dp.lunar_month_sunrise)

    return anga_spans

  def clear_padding_day_festivals(self):
    """Festival assignments for padding days are not trustworthy - since one would need to look-ahead or before into further days for accurate festival assignment. They were computed only to ensure accurate computation of the core days in this panchaanga. To avoid misleading, we ought to clear festivals provisionally assigned to the padding days."""
    daily_panchaangas = self.daily_panchaangas_sorted()
    for dp in daily_panchaangas[:self.duration_prior_padding]:
      self.delete_festivals_on_date(date=dp.date)
    for dp in daily_panchaangas[self.duration_prior_padding + self.duration:]:
      self.delete_festivals_on_date(date=dp.date)

  @timebudget
  def update_festival_details(self):
    """

    Festival data may be updated more frequently and a precomputed panchaanga may go out of sync. Hence we keep this method separate.
    :return:
    """
    self._reset_festivals()
    rule_lookup_assigner = rule_repo_based.RuleLookupAssigner(panchaanga=self)
    rule_lookup_assigner.apply_festival_from_rules_repos()
    ShraddhaTithiAssigner(panchaanga=self).assign_shraaddha_tithi()
    ecliptic.EclipticFestivalAssigner(panchaanga=self).assign_all()
    tithi_festival.TithiFestivalAssigner(panchaanga=self).assign_all()
    solar.SolarFestivalAssigner(panchaanga=self).assign_all()
    vaara.VaraFestivalAssigner(panchaanga=self).assign_all()
    generic_assigner = FestivalAssigner(panchaanga=self)
    generic_assigner.cleanup_festivals()
    rule_lookup_assigner.assign_relative_festivals()
    # self._sync_festivals_dict_and_daily_festivals(here_to_daily=True, daily_to_here=True)
    generic_assigner.assign_festival_numbers()
    self.clear_padding_day_festivals()


  def _sync_festivals_dict_and_daily_festivals(self, here_to_daily=False, daily_to_here=True):
    if here_to_daily:
      for festival_id, days in self.festival_id_to_days.items():
        for fest_day in days:
          if not isinstance(fest_day, Date):
            logging.fatal(festival_id + " " + str(days))
          fest_day_str = fest_day.get_date_str()
          if fest_day_str in self.date_str_to_panchaanga and festival_id not in self.date_str_to_panchaanga[fest_day_str].festival_id_to_instance:
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

  def add_festival(self, fest_id, date, interval_id="full_day"):
    if date.get_date_str() not in self.date_str_to_panchaanga:
      return 
    interval = self.date_str_to_panchaanga[date.get_date_str()].get_interval(interval_id=interval_id)
    self.add_festival_instance(date=date, festival_instance=FestivalInstance(name=fest_id, interval=interval))

  def add_festival_instance(self, festival_instance, date):
    from jyotisha.panchaanga.temporal.festival import rules
    festival_instance.name = rules.clean_id(id=festival_instance.name)
    p_fday = self.date_str_to_panchaanga.get(date.get_date_str(), None)
    if p_fday is not None:
      p_fday.festival_id_to_instance[festival_instance.name] = festival_instance
    self.festival_id_to_days[festival_instance.name].add(date)

  def delete_festival_date(self, fest_id, date):
    self.festival_id_to_days[fest_id].discard(date)
    if len(self.festival_id_to_days[fest_id]) == 0:
      # Avoid empty items (when serializing).
      self.delete_festival(fest_id=fest_id)
    self.date_str_to_panchaanga[date.get_date_str()].festival_id_to_instance.pop(fest_id, None)

  def delete_festivals_on_date(self, date):
    # Reason for casting to list below: Avoid RuntimeError: dictionary changed size during iteration
    dp = self.date_str_to_panchaanga[date.get_date_str()]
    for fest_id in list(dp.festival_id_to_instance.keys()):
      self.delete_festival_date(fest_id=fest_id, date=dp.date)


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
