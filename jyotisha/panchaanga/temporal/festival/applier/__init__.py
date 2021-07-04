import copy
import logging
import os
import sys

from jyotisha.panchaanga.temporal import PeriodicPanchaangaApplier, era
from jyotisha.panchaanga.temporal import festival
from jyotisha.panchaanga.temporal.festival import rules
from jyotisha.panchaanga.temporal.festival.rules import RulesRepo
from sanskrit_data.schema import common
from timebudget import timebudget

DATA_ROOT = os.path.join(os.path.dirname(festival.__file__), "data")


class FestivalAssigner(PeriodicPanchaangaApplier):
  def __init__(self, panchaanga):
    super(FestivalAssigner, self).__init__(panchaanga=panchaanga)
    self.festival_id_to_days = panchaanga.festival_id_to_days
    self.rules_collection = rules.RulesCollection.get_cached(
      repos_tuple=tuple(panchaanga.computation_system.festival_options.repos), julian_handling=panchaanga.computation_system.festival_options.julian_handling)

  @timebudget
  def assign_festival_numbers(self):
    # Update festival numbers if they exist
    solar_y_start_d = []
    lunar_y_start_d = []
    if self.daily_panchaangas[0].lunar_month_sunrise.index == 1:
      lunar_y_start_d.append(0)
    for d in range(1, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 1 and self.daily_panchaangas[d - 1].solar_sidereal_date_sunset.month != 1:
        solar_y_start_d.append(d)
      if self.daily_panchaangas[d].lunar_month_sunrise.index == 1 and self.daily_panchaangas[d - 1].lunar_month_sunrise.index != 1:
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
            logging.debug('Festival %s is only in the future!' % festival_name)
            self.panchaanga.delete_festival_date(fest_id=festival_name, date=assigned_day)
          else:
            self.panchaanga.date_str_to_panchaanga[assigned_day.get_date_str()].festival_id_to_instance[festival_name].ordinal = fest_num

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

    # Remove paraviddha assigned on consecutive days
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      for f in [fest.name for fest in self.daily_panchaangas[d].festival_id_to_instance.values()]:
        if f in [fest.name for fest in self.daily_panchaangas[d + 1].festival_id_to_instance.values()]:
          self.panchaanga.delete_festival_date(fest_id=f, date=self.daily_panchaangas[d].date)
          logging.warning('%s on both days %d and %d! Deleted %d' % (f, d, d + 1, d))

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
