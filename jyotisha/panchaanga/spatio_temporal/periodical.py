import sys

import methodtools
from timebudget import timebudget

from jyotisha.panchaanga import spatio_temporal
from jyotisha.panchaanga.spatio_temporal import daily
from jyotisha.panchaanga.temporal import zodiac, time, set_constants, ComputationSystem
from jyotisha.panchaanga.temporal.festival import applier, FestivalInstance
from jyotisha.panchaanga.temporal.festival.applier import tithi_festival, ecliptic, solar, vaara
from jyotisha.panchaanga.temporal.time import Date
from jyotisha.panchaanga.temporal.tithi import TithiAssigner
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject


timebudget.set_quiet(True)  # don't show measurements as they happen
# timebudget.report_at_exit()  # Generate report when the program exits

set_constants()


class Panchaanga(common.JsonObject):
  """This class enables the construction of a panchaanga for arbitrary periods, with festival_id_to_instance.
    """
  LATEST_VERSION = "0.0.4"

  def __init__(self, city, start_date, end_date, computation_system: ComputationSystem = ComputationSystem.MULTI_NEW_MOON_SOLAR_MONTH_ADHIKA__CHITRA_180):
    """Constructor for the panchaanga.
        """
    super(Panchaanga, self).__init__()
    self.version = Panchaanga.LATEST_VERSION
    self.city = city
    self.start_date = Date(*([int(x) for x in start_date.split('-')])) if isinstance(start_date, str) else start_date
    self.start_date.set_time_to_day_start()
    self.end_date = Date(*([int(x) for x in end_date.split('-')])) if isinstance(end_date, str) else end_date
    self.end_date.set_time_to_day_start()

    self.computation_system = computation_system

    self.jd_start = time.utc_gregorian_to_jd(self.start_date)
    self.jd_end = time.utc_gregorian_to_jd(self.end_date)

    self.duration = int(self.jd_end - self.jd_start) + 1

    # some buffer, for various look-ahead calculations
    # Pushkaram starting on 31 Jan might not get over till 12 days later
    self.duration_to_calculate = int(self.duration + 16)

    self.weekday_start = time.get_weekday(self.jd_start)

    self.festival_id_to_days = {}
    self.compute_angas(compute_lagnas=computation_system.options.lagnas)
    self.update_festival_details()

  @timebudget
  def compute_angas(self, compute_lagnas=True):
    """Compute the entire panchaanga
    """

    nDays = self.duration_to_calculate

    # INITIALISE VARIABLES
    self.date_str_to_panchaanga: dict[str, daily.DailyPanchaanga] = {}

    # Computing solar month details for Dec 31
    # rather than Jan 1, since we have an always increment
    # solar_sidereal_month_day_sunset at the start of the loop across every day in
    # year
    previous_day = time.jd_to_utc_gregorian(self.jd_start - 1)
    daily_panchaanga_start = daily.DailyPanchaanga(city=self.city, date=previous_day, computation_system=self.computation_system)

    solar_month_today_sunset = NakshatraDivision(daily_panchaanga_start.jd_sunset,
                                                 ayanaamsha_id=self.computation_system.ayanaamsha_id).get_anga(
      zodiac.AngaType.SOLAR_MONTH)
    solar_month_tmrw_sunrise = NakshatraDivision(daily_panchaanga_start.jd_sunrise + 1,
                                                 ayanaamsha_id=self.computation_system.ayanaamsha_id).get_anga(
      zodiac.AngaType.SOLAR_MONTH)
    month_start_after_sunset = solar_month_today_sunset != solar_month_tmrw_sunrise

    #############################################################
    # Compute all parameters -- sun/moon latitude/longitude etc #
    #############################################################

    for d in range(-1, nDays - 1):
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

  def get_2_day_interval_boundaries_angas(self, d, get_anga_func, interval_type):
    """Get anga data at various points.
    
    Useful for festival assignments."""
    daily_panchaangas = self.daily_panchaangas_sorted()
    jd_sunrise = daily_panchaangas[d].jd_sunrise
    jd_sunrise_tmrw = daily_panchaangas[d + 1].jd_sunrise
    jd_sunrise_datmrw = daily_panchaangas[d + 2].jd_sunrise
    jd_sunset = daily_panchaangas[d].jd_sunset
    jd_sunset_tmrw = daily_panchaangas[d + 1].jd_sunset
    jd_moonrise = daily_panchaangas[d].jd_moonrise
    jd_moonrise_tmrw = daily_panchaangas[d + 1].jd_moonrise
    if interval_type == 'sunrise':
      angas = [get_anga_func(jd_sunrise),
               get_anga_func(jd_sunrise),
               get_anga_func(jd_sunrise_tmrw),
               get_anga_func(jd_sunrise_tmrw)]
    elif interval_type == 'sunset':
      angas = [get_anga_func(jd_sunset),
               get_anga_func(jd_sunset),
               get_anga_func(jd_sunset_tmrw),
               get_anga_func(jd_sunset_tmrw)]
    elif interval_type == 'praatah':
      angas = [get_anga_func(jd_sunrise),  # praatah1 start
               # praatah1 end
               get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (1.0 / 5.0)),
               get_anga_func(jd_sunrise_tmrw),  # praatah2 start
               # praatah2 end
               get_anga_func(jd_sunrise_tmrw + \
                             (jd_sunset_tmrw - jd_sunrise_tmrw) * (1.0 / 5.0))]
    elif interval_type == 'saangava':
      angas = [
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (1.0 / 5.0)),
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (2.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw +
                      (jd_sunset_tmrw - jd_sunrise_tmrw) * (1.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw +
                      (jd_sunset_tmrw - jd_sunrise_tmrw) * (2.0 / 5.0))]
    elif interval_type == 'madhyaahna':
      angas = [
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (2.0 / 5.0)),
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (3.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw +
                      (jd_sunset_tmrw - jd_sunrise_tmrw) * (2.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw + (jd_sunset_tmrw -
                                         jd_sunrise_tmrw) * (3.0 / 5.0))]
    elif interval_type == 'aparaahna':
      angas = [
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (3.0 / 5.0)),
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (4.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw +
                      (jd_sunset_tmrw - jd_sunrise_tmrw) * (3.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw +
                      (jd_sunset_tmrw - jd_sunrise_tmrw) * (4.0 / 5.0))]
    elif interval_type == 'saayaahna':
      angas = [
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (4.0 / 5.0)),
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (5.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw +
                      (jd_sunset_tmrw - jd_sunrise_tmrw) * (4.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw +
                      (jd_sunset_tmrw - jd_sunrise_tmrw) * (5.0 / 5.0))]
    elif interval_type == 'madhyaraatri':
      angas = [
        get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (2.0 / 5.0)),
        get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (3.0 / 5.0)),
        get_anga_func(jd_sunset_tmrw +
                      (jd_sunrise_datmrw - jd_sunset_tmrw) * (2.0 / 5.0)),
        get_anga_func(jd_sunset_tmrw +
                      (jd_sunrise_datmrw - jd_sunset_tmrw) * (3.0 / 5.0))]
    elif interval_type == 'pradosha':
      # pradOSo.astamayAdUrdhvaM ghaTikAdvayamiShyatE (tithyAdi tattvam, Vrat Parichay panchaanga. 25 Gita Press)
      angas = [get_anga_func(jd_sunset),
               get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (1.0 / 15.0)),
               get_anga_func(jd_sunset_tmrw),
               get_anga_func(jd_sunset_tmrw +
                             (jd_sunrise_datmrw - jd_sunset_tmrw) * (1.0 / 15.0))]
    elif interval_type == 'nishiitha':
      angas = [
        get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (7.0 / 15.0)),
        get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (8.0 / 15.0)),
        get_anga_func(jd_sunset_tmrw +
                      (jd_sunrise_datmrw - jd_sunset_tmrw) * (7.0 / 15.0)),
        get_anga_func(jd_sunset_tmrw +
                      (jd_sunrise_datmrw - jd_sunset_tmrw) * (8.0 / 15.0))]
    elif interval_type == 'dinamaana':
      angas = [
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (0.0 / 5.0)),
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (5.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw +
                      (jd_sunset_tmrw - jd_sunrise_tmrw) * (0.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw + (jd_sunset_tmrw -
                                         jd_sunrise_tmrw) * (5.0 / 5.0))]
    elif interval_type == 'raatrimaana':
      angas = [
        get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (0.0 / 15.0)),
        get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (15.0 / 15.0)),
        get_anga_func(jd_sunset_tmrw +
                      (jd_sunrise_datmrw - jd_sunset_tmrw) * (0.0 / 15.0)),
        get_anga_func(jd_sunset_tmrw +
                      (jd_sunrise_datmrw - jd_sunset_tmrw) * (15.0 / 15.0))]
    elif interval_type == 'arunodaya':
      # deliberately not simplifying expressions involving 15/15
      angas = [
        get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (13.0 / 15.0)),
        get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (15.0 / 15.0)),
        get_anga_func(jd_sunset_tmrw +
                      (jd_sunrise_datmrw - jd_sunset_tmrw) * (13.0 / 15.0)),
        get_anga_func(jd_sunset_tmrw +
                      (jd_sunrise_datmrw - jd_sunset_tmrw) * (15.0 / 15.0))]
    elif interval_type == 'moonrise':
      angas = [get_anga_func(jd_moonrise),
               get_anga_func(jd_moonrise),
               get_anga_func(jd_moonrise_tmrw),
               get_anga_func(jd_moonrise_tmrw)]
    else:
      # Error!
      raise ValueError('Unkown kaala "%s" input!' % interval_type)
    return angas

  @timebudget
  def update_festival_details(self, debug=False):
    """

    Festival data may be updated more frequently and a precomputed panchaanga may go out of sync. Hence we keep this method separate.
    :return:
    """
    self._reset_festivals()
    from jyotisha.panchaanga.temporal.festival import rules
    TithiAssigner(panchaanga=self).assign_shraaddha_tithi()
    applier.MiscFestivalAssigner(panchaanga=self).assign_all(debug=debug)
    ecliptic.EclipticFestivalAssigner(panchaanga=self).assign_all(debug=debug)
    tithi_festival.TithiFestivalAssigner(panchaanga=self).assign_all(debug=debug)
    solar.SolarFestivalAssigner(panchaanga=self).assign_all(debug=debug)
    vaara.VaraFestivalAssigner(panchaanga=self).assign_all(debug=debug)
    applier.MiscFestivalAssigner(panchaanga=self).cleanup_festivals(debug=debug)
    applier.MiscFestivalAssigner(panchaanga=self).assign_relative_festivals()
    self._sync_festivals_dict_and_daily_festivals()
    applier.MiscFestivalAssigner(panchaanga=self).assign_festival_numbers()


  def _sync_festivals_dict_and_daily_festivals(self):
    for festival_id, days in self.festival_id_to_days.items():
      for fest_day in days:
        fest_day_str = fest_day.get_date_str()
        if fest_day_str in self.date_str_to_panchaanga:
          self.date_str_to_panchaanga[fest_day_str].festival_id_to_instance[festival_id] =  FestivalInstance(name=festival_id)

    for dp in self.date_str_to_panchaanga.values():
      for fest in dp.festival_id_to_instance.values():
        days = self.festival_id_to_days.get(fest.name, [])
        if dp.date not in days:
          days.append(dp.date)
        self.festival_id_to_days[fest.name] = days

  def _reset_festivals(self):
    self.festival_id_to_days = {}
    for daily_panchaanga in self.date_str_to_panchaanga.values():
      daily_panchaanga.festival_id_to_instance = {}

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

  @classmethod
  def read_from_file(cls, filename, name_to_json_class_index_extra=None):
    with timebudget("Loading the file"):
      panchaanga = JsonObject.read_from_file(filename=filename,
                                             name_to_json_class_index_extra=name_to_json_class_index_extra)
      panchaanga._refill_daily_panchaangas()
      return panchaanga

  @timebudget
  def dump_to_file(self, filename, floating_point_precision=None, sort_keys=True):
    self._force_non_redundancy_in_daily_panchaangas()
    super(Panchaanga, self).dump_to_file(filename=filename, floating_point_precision=floating_point_precision,
                                         sort_keys=sort_keys)
    self._refill_daily_panchaangas()


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])

if __name__ == '__main__':
  city = spatio_temporal.City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchaanga = Panchaanga(city=city, start_date='2019-04-14', end_date='2020-04-13',
                          ayanaamsha_id=zodiac.Ayanamsha.CHITRA_AT_180)
