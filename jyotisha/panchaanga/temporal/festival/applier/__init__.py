import copy
import logging
import os
import sys
from math import floor
from numbers import Number

from jyotisha.panchaanga.temporal import PeriodicPanchaangaApplier, era, zodiac
from jyotisha.panchaanga.temporal import festival
from jyotisha.panchaanga.temporal.festival import rules, FestivalInstance
from jyotisha.panchaanga.temporal.festival.rules import RulesRepo
from jyotisha.panchaanga.temporal.interval import Interval, AngaSpan
from jyotisha.panchaanga.temporal.zodiac.angas import AngaType, Anga
from sanskrit_data.schema import common
from timebudget import timebudget

DATA_ROOT = os.path.join(os.path.dirname(festival.__file__), "data")


class FestivalAssigner(PeriodicPanchaangaApplier):
  def __init__(self, panchaanga):
    super(FestivalAssigner, self).__init__(panchaanga=panchaanga)
    self.festival_id_to_days = panchaanga.festival_id_to_days
    self.festival_options = panchaanga.computation_system.festival_options
    self.rules_collection = rules.RulesCollection.get_cached(
      repos_tuple=tuple(panchaanga.computation_system.festival_options.repos), julian_handling=self.festival_options.julian_handling)

  def _find_vara_span(self, jd1, jd2, target_anga_id):
    """ Resolves an AngaType.VARA span the same way every other per-day anga span is bounded elsewhere in this
    codebase (sunrise to next sunrise), rather than via AngaSpanFinder's brentq-based ecliptic longitude search
    (wrong tool for a step function like weekday, and liable to drift from the timezone-correct
    daily_panchaanga.date.get_weekday() used everywhere else). Scans self.daily_panchaangas (already computed for
    this run) for the day whose weekday matches target_anga_id, so results are byte-identical to date.get_weekday().
    """
    if isinstance(target_anga_id, Number):
      target_anga = Anga.get_cached(index=target_anga_id, anga_type_id=AngaType.VARA.name)
    else:
      target_anga = target_anga_id
    for daily_panchaanga in self.daily_panchaangas:
      if daily_panchaanga.jd_next_sunrise is None or daily_panchaanga.jd_next_sunrise <= jd1:
        continue
      if daily_panchaanga.jd_sunrise is None or daily_panchaanga.jd_sunrise >= jd2:
        break
      if daily_panchaanga.date.get_weekday() + 1 == target_anga.index:
        return AngaSpan(jd_start=daily_panchaanga.jd_sunrise, jd_end=daily_panchaanga.jd_next_sunrise, anga=target_anga)
    return None

  def _assign_anga_intersection(self, yoga_name, intersect_list, jd_start=None, jd_end=None, show_debug_info=True):
    """ Assign a festival wherever every (anga_type, target_anga_id) pair in intersect_list simultaneously holds
    within [jd_start, jd_end]. target_anga_id may be a single index or a list of indices (any-of / OR semantics
    for that anga -- eg. karana in {2, 9, 16, ...}); list-valued entries are expanded by trying each candidate
    value independently (so multiple list-valued angas in the same call are tried combinatorially).

    anga_type may be AngaType.VARA (weekday), resolved via _find_vara_span rather than ecliptic search.
    """
    if jd_start is None:
      jd_start = self.panchaanga.jd_start
    if jd_end is None:
      jd_end = self.panchaanga.jd_end

    for i, (anga_type, target_anga_id) in enumerate(intersect_list):
      if isinstance(target_anga_id, (list, tuple)):
        any_happened = False
        for candidate in target_anga_id:
          expanded = list(intersect_list)
          expanded[i] = (anga_type, candidate)
          any_happened = self._assign_anga_intersection(
            yoga_name, expanded, jd_start=jd_start, jd_end=jd_end, show_debug_info=show_debug_info) or any_happened
        return any_happened

    jd_start_in = jd_start
    jd_end_in = jd_end
    anga_list = []
    yoga_happens = True
    for anga_type, target_anga_id in intersect_list:
      if anga_type == AngaType.VARA:
        anga = self._find_vara_span(jd1=jd_start, jd2=jd_end, target_anga_id=target_anga_id)
      else:
        finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.ayanaamsha_id, anga_type=anga_type)
        anga = finder.find(jd1=jd_start, jd2=jd_end, target_anga_id=target_anga_id)
      if anga is None:
        if show_debug_info:
          msg = ' + '.join(['%s %s' % (intersect_list[i][0], intersect_list[i][1]) for i in range(len(intersect_list))])
          logging.debug('No %s involving %s in span %s!' % (yoga_name, msg, Interval(jd_start=jd_start_in, jd_end=jd_end_in)))
        yoga_happens = False
        break
      else:
        if anga.jd_start is None:
          anga.jd_start = jd_start
        if anga.jd_end is None:
          anga.jd_end = jd_end

      if anga.jd_start is not None:
        jd_start = anga.jd_start
      if anga.jd_end is not None:
        jd_end = anga.jd_end
      anga_list.append(anga)

    if yoga_happens:
      jd_start, jd_end = max([x.jd_start for x in anga_list]), min([x.jd_end for x in anga_list])
      if jd_start > jd_end or jd_start > self.panchaanga.jd_end:
        if show_debug_info:
          msg = ' + '.join(['%s %s' % (intersect_list[i][0], intersect_list[i][1]) for i in range(len(intersect_list))])
          logging.debug('No %s involving %s in span %s!' % (msg, yoga_name, Interval(jd_start=jd_start_in, jd_end=jd_end_in)))
      elif (jd_end - jd_start) < 1/1800:  # Less than 1 Kalā
        if show_debug_info:
          msg = ' + '.join(['%s %s' % (intersect_list[i][0], intersect_list[i][1]) for i in range(len(intersect_list))])
          logging.debug('Not assigning %s involving %s in span %s due to extremely short duration (%s seconds)!' % (msg, yoga_name, Interval(jd_start=jd_start_in, jd_end=jd_end_in), (jd_end - jd_start) * 24 * 60 * 60))
      else:
        fday = int(floor(jd_start) - floor(self.daily_panchaangas[0].julian_day_start))
        if jd_start < self.daily_panchaangas[fday].jd_sunrise:
          fday -= 1
        jd_midnight_local = self.daily_panchaangas[fday + 1].julian_day_start
        if jd_start > jd_midnight_local and jd_end > self.daily_panchaangas[fday + 1].jd_sunrise:
          fday += 1
        if show_debug_info:
          logging.debug(f'Adding {yoga_name} from {Interval(jd_start=jd_start, jd_end=jd_end)} on {self.daily_panchaangas[fday].date}')
        self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=yoga_name, interval=Interval(jd_start=jd_start, jd_end=jd_end)), date=self.daily_panchaangas[fday].date)

    return yoga_happens

  @timebudget
  def assign_festival_numbers(self):
    # Update festival numbers if they exist
    solar_y_start_d = []
    lunar_y_start_d = []
    if self.daily_panchaangas[0].lunar_date.month.index == 1:
      lunar_y_start_d.append(0)
    for d in range(1, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 1 and self.daily_panchaangas[d - 1].solar_sidereal_date_sunset.month != 1:
        solar_y_start_d.append(d)
      if self.daily_panchaangas[d].lunar_date.month.index == 1 and self.daily_panchaangas[d - 1].lunar_date.month.index != 1:
        lunar_y_start_d.append(d)

    period_start_year = self.panchaanga.start_date.year
    for festival_name in copy.copy(self.panchaanga.festival_id_to_days):
      festival_rule = self.rules_collection.name_to_rule.get(festival_name, None)
      if festival_rule is None:
        continue
      if festival_rule.timing.year_start is not None:
        fest_start_year = festival_rule.timing.year_start
        fest_start_year_era = festival_rule.timing.year_start_era
        year_offset = era.get_year_0_offset(fest_start_year_era)
        month_type = festival_rule.timing.month_type
        for assigned_day in copy.copy(self.panchaanga.festival_id_to_days[festival_name]):
          assigned_day_index = int(assigned_day - self.daily_panchaangas[0].date)
          if month_type == RulesRepo.SIDEREAL_SOLAR_MONTH_DIR:
            fest_num = period_start_year + year_offset - fest_start_year
            for start_day in solar_y_start_d:
              if assigned_day_index >= start_day:
                fest_num += 1
          elif month_type == RulesRepo.LUNAR_MONTH_DIR:
            if festival_rule.timing.anga_number == 1 and festival_rule.timing.month_number == 1:
              # Assigned day may be less by one, since prathama may have started after sunrise
              # Still assume assigned_day >= lunar_y_start_d!
              fest_num = period_start_year + year_offset - fest_start_year
              for start_day in lunar_y_start_d:
                if assigned_day_index >= start_day:
                  fest_num += 1
            else:
              fest_num = period_start_year + year_offset - fest_start_year
              for start_day in lunar_y_start_d:
                if assigned_day_index >= start_day:
                  fest_num += 1
          elif month_type == RulesRepo.GREGORIAN_MONTH_DIR:
            fest_num = period_start_year + year_offset - fest_start_year

          if fest_num <= 0:
            # logging.debug('Festival %s is only in the future!' % festival_name)
            self.panchaanga.delete_festival_date(fest_id=festival_name, date=assigned_day)
          else:
            self.panchaanga.date_str_to_panchaanga[assigned_day.get_date_str()].festival_id_to_instance[festival_name].ordinal = fest_num

  def cleanup_anadhyayana_festivals(self):
    # Cleanup Anadhyayana Festivals
    if 'anadhyAyaH~1' in self.rules_collection.name_to_rule:
      ANADHYAYANA_FEST_GROUPS = [('anadhyAyaH~14', 'anadhyAyaH~15', 'anadhyAyaH~16'), ('anadhyAyaH~15', 'anadhyAyaH~16', 'anadhyAyaH~16'), ('anadhyAyaH~29', 'anadhyAyaH~30', 'anadhyAyaH~1'), ('anadhyAyaH~30', 'anadhyAyaH~1', 'anadhyAyaH~1')]
      for prev_f, next_f, nnext_f in ANADHYAYANA_FEST_GROUPS:
        for d in list(self.panchaanga.festival_id_to_days[prev_f]):
          if self.panchaanga.daily_panchaanga_for_date(d + 1) is None:
            # We are past the end of the year
            continue
          today_festivals = self.panchaanga.daily_panchaanga_for_date(d).festival_id_to_instance.keys()
          next_day_festivals = self.panchaanga.daily_panchaanga_for_date(d + 1).festival_id_to_instance.keys()
          if next_f not in today_festivals and next_f not in next_day_festivals and nnext_f not in next_day_festivals:
              # This occurs because there is no anadhyayana today, possibly because the anadhyayana was assigned
              # in paraviddha fashion to the day after
              if 'anadhyAyaH~pUrvarAtrau' in next_day_festivals:
                self.panchaanga.delete_festival_date(fest_id='anadhyAyaH~pUrvarAtrau', date=d + 1)
                logging.warning(f'Deleted anadhyAyaH~pUrvarAtrau on {str(d+1)}')
              self.panchaanga.add_festival(fest_id=next_f, date=d + 1)
              logging.warning(f'Added {next_f} on {str(d+1)}')

  def cleanup_festivals(self):
    # If tripurotsava coincides with maha kArttikI (kRttikA nakShatram)
    # only then it is mahAkArttikI
    # else it is only tripurotsava
    if 'tripurOtsavaH' in self.panchaanga.festival_id_to_days:
      if self.panchaanga.festival_id_to_days['tripurOtsavaH'] != self.panchaanga.festival_id_to_days['mahA~kArttikI']:
        logging.warning('Removing mahA~kArttikI (%s) since it does not coincide with tripurOtsavaH (%s)' % (
          str(self.panchaanga.festival_id_to_days['tripurOtsavaH']), set(self.panchaanga.festival_id_to_days['mahA~kArttikI'])))
      self.panchaanga.delete_festival(fest_id='mahA~kArttikI')
      # An error here implies the festival_id_to_instance were not assigned: adhika
      # mAsa calc errors??
    
    # Check if Mahalaya Paksha does not go beyond prathamA
    if len(self.panchaanga.festival_id_to_days.get('mahAlaya-pakSa-tarpaNa-pUrtiH', [])) > 0 and len(self.panchaanga.festival_id_to_days.get('mahAlaya-pakSa-ArambhaH', [])) > 0:
      mahalaya_end_date = list(self.panchaanga.festival_id_to_days['mahAlaya-pakSa-tarpaNa-pUrtiH'])[0]
      mahalaya_start_date = list(self.panchaanga.festival_id_to_days['mahAlaya-pakSa-ArambhaH'])[0]
      len_mahalaya = int(mahalaya_end_date - mahalaya_start_date + 1)
      if len_mahalaya < 16:
        # Can move at most to prathamA, by one day
        logging.warning(f'Moving end of mahAlaya-pakSa since it is {len_mahalaya}<16 days long')
        self.panchaanga.delete_festival_date(fest_id='mahAlaya-pakSa-tarpaNa-pUrtiH', date=mahalaya_end_date)
        # Adding to next day instead
        self.panchaanga.add_festival(fest_id='mahAlaya-pakSa-tarpaNa-pUrtiH', date=mahalaya_end_date + 1)

    # Remove paraviddha assigned on consecutive days
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      for f in [fest.name for fest in self.daily_panchaangas[d].festival_id_to_instance.values()]:
        if f in [fest.name for fest in self.daily_panchaangas[d + 1].festival_id_to_instance.values()]:
          if 'sAyana' not in f and 'anadhyAyaH' not in f:
            self.panchaanga.delete_festival_date(fest_id=f, date=self.daily_panchaangas[d].date)
            logging.warning('%s on both days %d and %d! Deleted %d' % (f, d, d + 1, d))

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
