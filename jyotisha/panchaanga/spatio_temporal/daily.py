#!/usr/bin/python3
#  -*- coding: utf-8 -*-
import logging
import sys
from math import floor, modf

from jyotisha.panchaanga.temporal.festival.rules import pancha_paxi
from indic_transliteration import sanscript

import methodtools
from scipy.optimize import brentq
from timebudget import timebudget

from jyotisha.panchaanga.spatio_temporal import City
from jyotisha.panchaanga.temporal import time, ComputationSystem, set_constants, names, era, body
from jyotisha.panchaanga.temporal import zodiac
from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal.festival.rules import RulesRepo
from jyotisha.panchaanga.temporal.interval import DayLengthBasedPeriods, Interval, get_interval
from jyotisha.panchaanga.temporal.month import LunarMonthAssigner
from jyotisha.panchaanga.temporal.names import translate_or_transliterate
from jyotisha.panchaanga.temporal.time import Timezone, Date, BasicDate, Hour
from jyotisha.panchaanga.temporal.zodiac import Ayanamsha, NakshatraDivision, AngaSpanFinder
from jyotisha.panchaanga.temporal.zodiac.angas import AngaType, Anga
from jyotisha.util import default_if_none
from sanskrit_data.schema import common

timebudget.set_quiet(True)  # don't show measurements as they happen

logging.basicConfig(level=logging.DEBUG,
                    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s ")


set_constants()



class DayAngas(common.JsonObject):
  def __init__(self):
    super().__init__()
    self.tithis_with_ends = None
    self.tithi_at_sunrise = None
    self.nakshatras_with_ends = None
    self.nakshatra_at_sunrise = None
    self.yogas_with_ends = None
    self.yoga_at_sunrise = None
    self.karanas_with_ends = None
    self.solar_nakshatras_with_ends = None
    self.raashis_with_ends = None
    self.solar_raashis_with_ends = None

  def get_angas_with_ends(self, anga_type):
    anga_spans = []
    if anga_type == AngaType.NAKSHATRA:
      anga_spans = self.nakshatras_with_ends
    elif anga_type == AngaType.TITHI:
      anga_spans = self.tithis_with_ends
    elif anga_type == AngaType.YOGA:
      anga_spans = self.yogas_with_ends
    elif anga_type == AngaType.RASHI:
      anga_spans = self.rashis_with_ends
    elif anga_type == AngaType.KARANA:
      anga_spans = self.karanas_with_ends
    elif anga_type == AngaType.SOLAR_NAKSH:
      anga_spans = self.solar_nakshatras_with_ends
    elif anga_type == AngaType.SIDEREAL_MONTH:
      anga_spans = self.solar_raashis_with_ends
    return anga_spans

  def find_anga_span(self, anga):
    for anga_span in self.get_angas_with_ends(anga_type=anga.get_type()):
      if anga_span.anga == anga:
        return anga_span
    return None

  def get_anga_spans_in_interval(self, anga_type, interval):
    """

    Assumptions: interval ends are not None. Anga spans in self could be None.
    Raison d'etre: efficiency.
    :param anga_type: 
    :param interval: 
    :return: 
    """
    all_spans = self.get_angas_with_ends(anga_type=anga_type)
    spans = []
    for span in all_spans:
      if span.jd_end is not None and span.jd_end < interval.jd_start:
        continue
      # Does the anga start within the interval?
      elif span.jd_start is not None and span.jd_start >= interval.jd_start and span.jd_start <= interval.jd_end:
        spans.append(span)
      # Does the anga end within the interval?
      elif span.jd_end is not None and span.jd_end >= interval.jd_start and span.jd_end <= interval.jd_end:
        spans.append(span)
      # Does the anga end fully contain the interval?
      elif (span.jd_start is None or span.jd_start <= interval.jd_start) and (span.jd_end is None or span.jd_end >= interval.jd_end):
        spans.append(span)
      elif span.jd_start is not None and span.jd_start > interval.jd_end:
        break
    return spans

  def get_anga_at_jd(self, jd, anga_type):
    anga_spans = self.get_anga_spans_in_interval(anga_type=anga_type, interval=Interval(jd_start=jd, jd_end=jd))
    for anga_span in anga_spans:
      return anga_span.anga
    return None

  def get_anga_data_str(self, anga_type, script, reference_jd):
    anga_data_str = ''
    angas_with_ends = self.get_angas_with_ends(anga_type=anga_type)
    for anga_span in angas_with_ends:
      (anga_ID, anga_end_jd) = (anga_span.anga.index, anga_span.jd_end)
      anga = anga_type.names_dict[script][anga_ID]
      if anga_end_jd is None:
        anga_end_str = ""
      else:
        anga_end_str = Hour(24 * (anga_end_jd - reference_jd)).to_string()
      anga_data_str = '%s; %s►%s' % \
                       (anga_data_str, anga,
                        anga_end_str)
    anga_data_str = '**%s** — %s' % (translate_or_transliterate(anga_type.name_hk, script), anga_data_str[2:])
    return anga_data_str


class PaxiActivities(common.JsonObject):
  def __init__(self):
    super().__init__()
    self.cock = []
    self.crow = []
    self.owl = []
    self.peacock = []
    self.vulture = []

  def add_activity_interval(self, bird, activity_interval):
    activity_intervals = getattr(self, bird)
    if len(activity_intervals) > 0 and activity_intervals[-1].name == activity_interval.name:
      activity_intervals[-1].jd_end = activity_interval.jd_end
    else:
      activity_intervals.append(activity_interval)


# This class is not named Panchangam in order to be able to disambiguate from annual.Panchangam in serialized objects.
class DailyPanchaanga(common.JsonObject):
  """This class enables the construction of a panchaanga.
  
  For comments on matching pre-sunrise festivals with days, see periodic panchaanga.
  """

  @classmethod
  def from_city_and_julian_day(cls, city, julian_day, computation_system: ComputationSystem = None):
    date = Timezone(city.timezone).julian_day_to_local_time(julian_day)
    return DailyPanchaanga(city=city, date=date, computation_system=computation_system)

  def __init__(self, city: City, date: Date, computation_system = None,
               previous_day_panchaanga=None) -> None:
    """Constructor for the panchaanga.
    """
    super(DailyPanchaanga, self).__init__()
    self.city = city
    self.date = date
    date.set_time_to_day_start()
    self.julian_day_start = Timezone(self.city.timezone).local_time_to_julian_day(date=self.date)
    self.computation_system = default_if_none(computation_system, ComputationSystem.DEFAULT)

    self.jd_sunrise = None
    self.jd_sunset = None
    self.jd_previous_sunset = None
    self.jd_next_sunrise = None
    self.jd_moonrise = None
    self.jd_moonset = None

    self.lagna_data = None
    self.sunrise_day_angas = None
    self.paxi_activities = None

    self.solar_sidereal_date_sunset = None

    self.tropical_date_sunset = None

    self.lunar_month_sunrise = None
    
    self.shraaddha_tithi = []
    self.festival_id_to_instance = {}
    self.mauDhyas = None
    self.amauDhyas = None

    self.compute_sun_moon_transitions(previous_day_panchaanga=previous_day_panchaanga)
    self.compute_solar_day_sunset(previous_day_panchaanga=previous_day_panchaanga)
    self.set_tropical_date_sunset(previous_day_panchaanga=previous_day_panchaanga)
    self.day_length_based_periods = DayLengthBasedPeriods(jd_previous_sunset=self.jd_previous_sunset, jd_sunrise=self.jd_sunrise, jd_sunset=self.jd_sunset, jd_next_sunrise=self.jd_next_sunrise, weekday=self.date.get_weekday())

    if self.computation_system.lunar_month_assigner_type is not None:
      lunar_month_assigner = LunarMonthAssigner.get_assigner(computation_system=self.computation_system)
      self.set_lunar_month_sunrise(month_assigner=lunar_month_assigner, previous_day_panchaanga=previous_day_panchaanga)
      self.set_mauDhyas()

    if self.computation_system.festival_options.set_pancha_paxi_activities:
      self.get_pancha_paxi_activities()

  def __repr__(self):
    return "%s %s" % (repr(self.date), repr(self.city))

  def __hash__(self):
    return repr(self)

  def __lt__(self, other):
    return self.date.get_date_str() < self.date.get_date_str()

  def compute_sun_moon_transitions(self, previous_day_panchaanga=None, force_recomputation=False):
    """

    :param previous_day_panchaanga: Panchangam for previous day, to avoid unnecessary calculations. (rise_trans calculations can be time consuming.)
    :param force_recomputation: Boolean indicating if the transitions should be recomputed. (rise_trans calculations can be time consuming.)
    :return:
    """
    if force_recomputation or self.jd_sunrise is None:
      if previous_day_panchaanga is not None and previous_day_panchaanga.jd_next_sunrise is not None:
        self.jd_sunrise = previous_day_panchaanga.jd_next_sunrise
      else:
        self.jd_sunrise = self.city.get_rising_time(julian_day_start=self.julian_day_start, body=Graha.SUN)
    if force_recomputation or self.jd_sunset is None:
      self.jd_sunset = self.city.get_setting_time(julian_day_start=self.jd_sunrise, body=Graha.SUN)
    if force_recomputation or self.jd_previous_sunset is None:
      if previous_day_panchaanga is not None and previous_day_panchaanga.jd_sunset is not None:
        self.jd_previous_sunset = previous_day_panchaanga.jd_sunset
      else:
        self.jd_previous_sunset = self.city.get_setting_time(julian_day_start=self.jd_sunrise - 1,
                                                             body=Graha.SUN)
    if force_recomputation or self.jd_next_sunrise is None:
      self.jd_next_sunrise = self.city.get_rising_time(julian_day_start=self.jd_sunset, body=Graha.SUN)
    if self.jd_sunset == 0.0:
      logging.error('No sunset was computed!')
      raise (ValueError(
        'No sunset was computed. Perhaps the co-ordinates are beyond the polar circle (most likely a LAT-LONG swap! Please check your inputs.'))

    if force_recomputation or self.jd_moonrise is None:
      self.jd_moonrise = self.city.get_rising_time(julian_day_start=self.jd_sunrise, body=Graha.MOON)
    if force_recomputation or self.jd_moonset is None:
      self.jd_moonset = self.city.get_setting_time(julian_day_start=self.jd_sunrise, body=Graha.MOON)

    if force_recomputation or self.sunrise_day_angas is None:
      self.sunrise_day_angas = DayAngas()
      # Deliberately passing ASHVINI_STARTING_0 below since it is cheapest. Tithi is independent of ayanAmsha. 
      self.sunrise_day_angas.tithis_with_ends = AngaSpanFinder.get_cached(ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0, anga_type=zodiac.AngaType.TITHI).get_all_angas_in_period(jd1=self.jd_sunrise, jd2=self.jd_next_sunrise)
      self.sunrise_day_angas.tithi_at_sunrise = self.sunrise_day_angas.tithis_with_ends[0].anga
      
      self.sunrise_day_angas.nakshatras_with_ends = AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=zodiac.AngaType.NAKSHATRA).get_all_angas_in_period(jd1=self.jd_sunrise, jd2=self.jd_next_sunrise)
      self.sunrise_day_angas.nakshatra_at_sunrise = self.sunrise_day_angas.nakshatras_with_ends[0].anga
      
      self.sunrise_day_angas.yogas_with_ends = AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=zodiac.AngaType.YOGA).get_all_angas_in_period(jd1=self.jd_sunrise, jd2=self.jd_next_sunrise)
      self.sunrise_day_angas.yoga_at_sunrise = self.sunrise_day_angas.yogas_with_ends[0].anga
      
      self.sunrise_day_angas.karanas_with_ends = AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=zodiac.AngaType.KARANA).get_all_angas_in_period(jd1=self.jd_sunrise, jd2=self.jd_next_sunrise)
      
      self.sunrise_day_angas.raashis_with_ends = AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=zodiac.AngaType.RASHI).get_all_angas_in_period(jd1=self.jd_sunrise, jd2=self.jd_next_sunrise)
      self.sunrise_day_angas.solar_raashis_with_ends = AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=zodiac.AngaType.SIDEREAL_MONTH).get_all_angas_in_period(jd1=self.jd_sunrise, jd2=self.jd_next_sunrise)
      
      self.sunrise_day_angas.solar_nakshatras_with_ends = AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=zodiac.AngaType.SOLAR_NAKSH).get_all_angas_in_period(jd1=self.jd_sunrise, jd2=self.jd_next_sunrise)

  def get_interval(self, interval_id):
    interval_id = names.devanaagarii_to_python.get(interval_id, interval_id)
    if interval_id == "moonrise":
      return Interval(name=interval_id, jd_start=self.jd_moonrise, jd_end=self.jd_moonrise)
    elif interval_id == "sunrise":
      return Interval(jd_start=self.jd_sunrise, jd_end=self.jd_sunrise, name=interval_id)
    elif interval_id == "sunset":
      return Interval(jd_start=self.jd_sunset, jd_end=self.jd_sunset, name=interval_id)
    elif interval_id == "full_day":
      return Interval(jd_start=self.jd_sunrise, jd_end=self.jd_next_sunrise, name=interval_id)
    elif interval_id == "aparaahna":
      if self.computation_system.festival_options.aparaahna_as_second_half:
        return getattr(self.day_length_based_periods, interval_id)
      else:
        return getattr(self.day_length_based_periods.fifteen_fold_division, interval_id)
    elif interval_id == "julian_day":
      return Interval(jd_start=self.julian_day_start, jd_end=self.julian_day_start + 1, name=interval_id)
    else:
      if self.computation_system.festival_options.prefer_eight_fold_day_division:
        search_locations = [self.day_length_based_periods, self.day_length_based_periods.eight_fold_division, self.day_length_based_periods.fifteen_fold_division]
      else:
        search_locations = [self.day_length_based_periods, self.day_length_based_periods.fifteen_fold_division, self.day_length_based_periods.eight_fold_division]
      for location in search_locations:
        value = getattr(location, interval_id)
        if value is not None:
          return value
      return None

  def get_interval_anga_spans(self, interval_id, anga_type):
    interval = self.get_interval(interval_id=interval_id)
    return (self.sunrise_day_angas.get_anga_spans_in_interval(interval=interval, anga_type=anga_type), interval)

  def compute_solar_day_sunset(self, previous_day_panchaanga=None):
    """Compute the solar month and day for a given Julian day at sunset.
    """
    # If solar transition happens before the current sunset but after the previous sunset, then that is taken to be solar day 1.
    self.compute_sun_moon_transitions(previous_day_panchaanga=previous_day_panchaanga)
    solar_month_sunset = NakshatraDivision(jd=self.jd_sunset, ayanaamsha_id=self.computation_system.ayanaamsha_id).get_anga(
      anga_type=AngaType.SIDEREAL_MONTH)

    solar_sidereal_month_end_jd = None
    # Some months are really short, like Dhanurmasa ending 1970-Jan-14. So >=28 is used...
    if previous_day_panchaanga is None or previous_day_panchaanga.solar_sidereal_date_sunset.day >= 28 :
      anga_finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=AngaType.SIDEREAL_MONTH)
      solar_month_sunset_span = anga_finder.find(jd1=self.jd_sunset - 32, jd2=self.jd_sunset + 5, target_anga_id=solar_month_sunset)
      solar_sidereal_month_day_sunset = len(self.city.get_sunsets_in_period(jd_start=solar_month_sunset_span.jd_start, jd_end=self.jd_sunset + 1/48.0))
      if solar_sidereal_month_day_sunset == 1 and solar_month_sunset_span.jd_start > self.jd_sunrise:
        solar_sidereal_month_end_jd = solar_month_sunset_span.jd_start
      elif solar_sidereal_month_day_sunset >= 29 and solar_month_sunset_span.jd_end < self.jd_next_sunrise:
        solar_sidereal_month_end_jd = solar_month_sunset_span.jd_end
    else:
      solar_sidereal_month_day_sunset = previous_day_panchaanga.solar_sidereal_date_sunset.day + 1
    from jyotisha.panchaanga.temporal import time
    self.solar_sidereal_date_sunset = time.BasicDateWithTransitions(month=solar_month_sunset.index, day=solar_sidereal_month_day_sunset, month_transition=solar_sidereal_month_end_jd)

  def set_tropical_date_sunset(self, previous_day_panchaanga=None):
    month_transition_jd = None
    if previous_day_panchaanga is not None:
      tropical_date_sunset_day = previous_day_panchaanga.tropical_date_sunset.day + 1
      tropical_date_sunset_month = previous_day_panchaanga.tropical_date_sunset.month
    
    if previous_day_panchaanga is None or previous_day_panchaanga.tropical_date_sunset.day > 28 :
      nd = zodiac.NakshatraDivision(jd=self.jd_sunset, ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0)
      fractional_month = nd.get_fractional_division_for_body(body=Graha.singleton(Graha.SUN), anga_type=AngaType.RASHI)
      (month_fraction, _) = modf(fractional_month)
      approx_day = month_fraction*30
      month_transitions = Graha.singleton(Graha.SUN).get_transits(jd_start=self.jd_sunset-approx_day-5, jd_end=self.jd_sunset + 4, anga_type=AngaType.RASHI, ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0)
      if month_transitions[-1].jd > self.jd_previous_sunset and month_transitions[-1].jd <= self.jd_sunset:
        tropical_date_sunset_day = 1
        tropical_date_sunset_month = month_transitions[-1].value_2
        month_transition_jd = month_transitions[-1].jd
      else:
        tropical_date_sunset_day = len(self.city.get_sunsets_in_period(jd_start=month_transitions[0].jd, jd_end=self.jd_sunset + 1/48.0))
        tropical_date_sunset_month = month_transitions[0].value_2
    self.tropical_date_sunset = time.BasicDateWithTransitions(month=tropical_date_sunset_month, day=tropical_date_sunset_day, month_transition=month_transition_jd)

  def set_lunar_month_sunrise(self, month_assigner, previous_day_panchaanga=None):
    if previous_day_panchaanga is not None:
      span = previous_day_panchaanga.sunrise_day_angas.find_anga_span(Anga.get_cached(anga_type_id=AngaType.TITHI.name, index=1))

      # If a prathamA tithi has started post-sunrise yesterday (and has potentially ended before today's sunrise), or if today we have a prathamA at sunrise
      if (span is not None and span.jd_start is not None) or self.sunrise_day_angas.tithi_at_sunrise.index == 1:
        self.lunar_month_sunrise = month_assigner.get_month_sunrise(daily_panchaanga=self)
      else:
        self.lunar_month_sunrise = previous_day_panchaanga.lunar_month_sunrise
    else:
      if  month_assigner is not None:
        self.lunar_month_sunrise = month_assigner.get_month_sunrise(daily_panchaanga=self)

  def get_date(self, month_type):
    if month_type == RulesRepo.SIDEREAL_SOLAR_MONTH_DIR:
      return self.solar_sidereal_date_sunset
    elif month_type == RulesRepo.LUNAR_MONTH_DIR:
      return BasicDate(month=self.lunar_month_sunrise.index,
                       day=self.sunrise_day_angas.tithi_at_sunrise.index)
    elif month_type == RulesRepo.TROPICAL_MONTH_DIR:
      return self.tropical_date_sunset
    elif month_type == RulesRepo.GREGORIAN_MONTH_DIR:
      return self.date

  @methodtools.lru_cache(maxsize=None)
  def get_month_str(self, month_type, script, language=None):
    if month_type == RulesRepo.SIDEREAL_SOLAR_MONTH_DIR:
      if language is None:
        return names.NAMES['RASHI_NAMES']['sa'][script][self.solar_sidereal_date_sunset.month]
      else:
        return translate_or_transliterate(names.NAMES['SIDEREAL_SOLAR_MONTH_NAMES'][language][self.solar_sidereal_date_sunset.month - 1], source_script=sanscript.DEVANAGARI, script=script)
    elif month_type == RulesRepo.LUNAR_MONTH_DIR:
      return names.get_chandra_masa(month=self.lunar_month_sunrise.index, script=script)
    elif month_type == RulesRepo.TROPICAL_MONTH_DIR:
      return names.NAMES['RTU_MASA_NAMES_SHORT']['sa'][script][self.tropical_date_sunset.month]
    elif month_type == RulesRepo.ISLAMIC_MONTH_DIR:
      islamic_date = self.date.to_islamic_date()
      return names.NAMES["ARAB_MONTH_NAMES"]["ar"][islamic_date.month-1]
    elif month_type == RulesRepo.GREGORIAN_MONTH_DIR:
      return names.month_map[self.date.month]

  def get_samvatsara_offset_1987(self, month_type):
    # The below is a crude variable name: sidereal lunar month could be only approximately equinox-referrent. 
    equinox_referrent_date = self.get_date(month_type=month_type)
    # For a few millennia around 1987, it is safe to assume that lunar year starts wihtin the first 5 months of the Gregorian year. This means that only the tail end of the lunar year occurs within the first few months of the year. And only in that case, would we need to offset relative to 1988 rather than 1987.  
    # TODO: Implement samvatsara skipping logic.  https://github.com/jyotisham/jyotisha/issues/83
    if equinox_referrent_date.month >= 7 and self.date.month <= 5:
      samvatsara_offset_1987_lunar = (self.date.year - 1988) % 60
    else:
      samvatsara_offset_1987_lunar = (self.date.year - 1987) % 60 
    return samvatsara_offset_1987_lunar

  def get_samvatsara(self, month_type, samvatsara_1987=Anga(index=1, anga_type_id=AngaType.SAMVATSARA.name)):
    if isinstance(samvatsara_1987, int):
      samvatsara_1987 = Anga(index=samvatsara_1987, anga_type_id=AngaType.SAMVATSARA.name)
    samvatsara = samvatsara_1987 + self.get_samvatsara_offset_1987(month_type=month_type)
    return samvatsara


  def get_year_number(self, month_type, era_id):
    # The below is a crude variable name: sidereal lunar month could be only approximately equinox-referrent. 
    equinox_referrent_date = self.get_date(month_type=month_type)
    year_0_offset = era.get_year_0_offset(era_id=era_id)
    # For a few millennia around 1987, it is safe to assume that lunar year starts wihtin the first 5 months of the Gregorian year. This means that only the tail end of the lunar year occurs within the first few months of the year. And only in that case, would we need to offset relative to 1988 rather than 1987.  
    if equinox_referrent_date.month >= 7 and self.date.month <= 5:
      year_index = (self.date.year - 1 + year_0_offset)
    else:
      year_index = (self.date.year + year_0_offset)
    return year_index


  def get_hora_data(self, debug=False):
    """Returns the hora data

        Args:
          debug

        Returns:
          tuples detailing the end time of each hora, beginning with the one
          prevailing at sunrise
        """
    if self.hora_data is not None:
      return self.hora_data

    self.hora_data = []
    if getattr(self, "jd_sunrise", None) is None or self.jd_sunrise is None:
      self.compute_sun_moon_transitions()
    
    HORA_SUNRISE = [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY, Graha.JUPITER, Graha.VENUS, Graha.SATURN]
    # HORA_GRAHAS = [Graha.SUN, Graha.VENUS, Graha.MERCURY, Graha.MOON, Graha.SATURN, Graha.JUPITER, Graha.MARS]
    HORA_GRAHAS = (HORA_SUNRISE * 5)[0::5]

    hora_sunrise = HORA_SUNRISE[self.date.get_weekday()]

    hora_list = [(x + HORA_GRAHAS.index(hora_sunrise)) % 7 for x in range(24)]

    for i, hora in enumerate(hora_list[:12]):
      hora_end_time = get_interval(start_jd=self.jd_sunrise, end_jd=self.jd_sunset, part_index=i, num_parts=12).jd_end
      self.hora_data.append((hora, HORA_GRAHAS[hora], hora_end_time))

    for i, hora in enumerate(hora_list[12:]):
      hora_end_time = get_interval(start_jd=self.jd_sunset, end_jd=self.jd_next_sunrise, part_index=i, num_parts=12).jd_end
      self.hora_data.append((hora, HORA_GRAHAS[hora], hora_end_time))

    return self.hora_data


  def get_lagna_data(self, ayanaamsha_id=zodiac.Ayanamsha.CHITRA_AT_180, debug=False):
    """Returns the lagna data

        Args:
          debug

        Returns:
          tuples detailing the end time of each lagna, beginning with the one
          prevailing at sunrise
        """
    if self.lagna_data is not None:
      return self.lagna_data

    self.lagna_data = []
    if getattr(self, "jd_sunrise", None) is None or self.jd_sunrise is None:
      self.compute_sun_moon_transitions()
    lagna_sunrise = 1 + floor(self.city.get_lagna_float(self.jd_sunrise, ayanaamsha_id=ayanaamsha_id))

    lagna_list = [(x + lagna_sunrise - 1) % 12 + 1 for x in range(13)]

    lbrack = self.jd_sunrise - 3 / 24
    rbrack = self.jd_sunrise + 3 / 24

    for lagna in lagna_list:
      # print('---\n', lagna)
      if debug:
        logging.debug(('lagna sunrise', self.city.get_lagna_float(self.jd_sunrise, ayanaamsha_id=ayanaamsha_id)))
        logging.debug(('lbrack', self.city.get_lagna_float(lbrack, int(-lagna), ayanaamsha_id=ayanaamsha_id)))
        logging.debug(('rbrack', self.city.get_lagna_float(rbrack, int(-lagna), ayanaamsha_id=ayanaamsha_id)))

      lagna_end_time = brentq(self.city.get_lagna_float, lbrack, rbrack,
                              args=(-lagna, ayanaamsha_id, debug))
      lbrack = lagna_end_time + 1 / 24
      rbrack = lagna_end_time + 3 / 24
      if lagna_end_time < self.jd_next_sunrise:
        self.lagna_data.append((lagna, lagna_end_time))
    return self.lagna_data


  def get_pancha_paxi_activities(self):
    if self.paxi_activities is not None:
      return self.paxi_activities
    self.paxi_activities = PaxiActivities()
    from jyotisha.panchaanga.temporal.festival import rules
    paxa_id = int((self.sunrise_day_angas.tithi_at_sunrise.index - 1) / 15) + 1
    activities_table = pancha_paxi.get_activities_table(weekday_id=self.date.get_weekday(), paxa_id=paxa_id)

    from jyotisha.panchaanga.temporal import interval   
    for bird in ["cock", "crow", "owl", "peacock", "vulture"]:
      activities = activities_table[bird]
      
      for i in range(0, 120):
        activity_interval = interval.get_interval(start_jd=self.jd_sunrise, end_jd=self.jd_sunset, num_parts=120, part_index=i, name=activities[i])
        self.paxi_activities.add_activity_interval(bird=bird, activity_interval=activity_interval)
      
      for i in range(120, 240):
        activity_interval = interval.get_interval(start_jd=self.jd_sunset, end_jd=self.jd_next_sunrise, num_parts=120, part_index=i - 120, name=activities[i])
        self.paxi_activities.add_activity_interval(bird=bird, activity_interval=activity_interval)
    
    return self.paxi_activities

  def day_has_conjunction(self, body1, body2, gap=None):
    if gap is None:
      gap = (Graha.BODY_TO_ANGULAR_DIA_DEGREES[body1.body_name] + Graha.BODY_TO_ANGULAR_DIA_DEGREES[body2.body_name])/ 2.0

    def has_collision(jd):
      return abs(body.longitude_difference(jd=jd, body1=body1, body2=body2)) < gap

    sign = lambda x: -1 if x < 0 else (1 if x > 0 else (0 if x == 0 else None))
    return has_collision(jd=self.jd_sunrise) or has_collision(jd=self.jd_next_sunrise) or sign(body.longitude_difference(jd=self.jd_sunrise, body1=body1, body2=body2)) != sign(body.longitude_difference(jd=self.jd_next_sunrise, body1=body1, body2=body2))

  def set_mauDhyas(self):
    sun = Graha.singleton(body_name=Graha.SUN)
    mauDhyas = {}
    amauDhyas = {}

    for graha_id in [Graha.MERCURY, Graha.VENUS, Graha.MARS, Graha.JUPITER, Graha.SATURN]:
      graha = Graha.singleton(body_name=graha_id)
      gap = self.computation_system.graha_lopa_measures.graha_id_to_lopa_measure.get(graha_id, None)

      if self.day_has_conjunction(body1=sun, body2=graha, gap=gap):
        mauDhyas[graha_id] = [body.longitude_difference(jd=self.jd_sunrise, body1=sun, body2=graha), body.longitude_difference(jd=self.jd_next_sunrise, body1=sun, body2=graha)]
      else:
        amauDhyas[graha_id] = [body.longitude_difference(jd=self.jd_sunrise, body1=sun, body2=graha), body.longitude_difference(jd=self.jd_next_sunrise, body1=sun, body2=graha)]

    if len(mauDhyas) > 0:
      self.mauDhyas = mauDhyas
    if len(amauDhyas) > 0:
      self.amauDhyas = amauDhyas


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)


if __name__ == '__main__':
  panchaanga = DailyPanchaanga.from_city_and_julian_day(city=City('Chennai', '13:05:24', '80:16:12', 'Asia/Calcutta'),
                                                        julian_day=2457023.27)
  panchaanga.compute_tb_muhuurtas()
  logging.debug(str(panchaanga))
