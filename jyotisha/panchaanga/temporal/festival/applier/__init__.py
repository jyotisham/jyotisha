import logging
import os
import sys

from jyotisha.panchaanga.temporal import PeriodicPanchaangaApplier
from jyotisha.panchaanga.temporal import festival
from jyotisha.panchaanga.temporal.festival import rules
from sanskrit_data.schema import common
from timebudget import timebudget

DATA_ROOT = os.path.join(os.path.dirname(festival.__file__), "data")


class FestivalAssigner(PeriodicPanchaangaApplier):
  def __init__(self, panchaanga):
    super(FestivalAssigner, self).__init__(panchaanga=panchaanga)
    self.festival_id_to_days = panchaanga.festival_id_to_days
    self.rules_collection = rules.RulesCollection.get_cached(
      repos_tuple=tuple(panchaanga.computation_system.options.fest_repos))


  @timebudget
  def assign_festival_numbers(self):
    # Update festival numbers if they exist
    solar_y_start_d = []
    lunar_y_start_d = []
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + 1):
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 1 and self.daily_panchaangas[d - 1].solar_sidereal_date_sunset.month != 1:
        solar_y_start_d.append(d)
      if self.daily_panchaangas[d].lunar_month_sunrise.index == 1 and self.daily_panchaangas[d - 1].lunar_month_sunrise.index != 1:
        lunar_y_start_d.append(d)

    period_start_year = self.panchaanga.start_date.year
    festival_rules_all = self.rules_collection.name_to_rule
    for festival_name in festival_rules_all:
      if festival_name in self.panchaanga.festival_id_to_days and festival_rules_all[festival_name].timing.year_start is not None:
        fest_start_year = festival_rules_all[festival_name].timing.year_start
        month_type = festival_rules_all[festival_name].timing.month_type
        if len(self.panchaanga.festival_id_to_days[festival_name]) > 1:
          days = list(self.panchaanga.festival_id_to_days[festival_name])
          days.sort()
          if days[1] - days[0] < 300:
            # Lunar festival_id_to_instance can repeat after 354 days; Solar festival_id_to_instance "can" repeat after 330 days
            # (last day of Dhanur masa Jan and first day of Dhanur masa Dec may have same nakshatra and are about 335 days apart)
            # In fact they will be roughly 354 days apart, again!
            logging.warning('Multiple occurrences of festival %s within year. Check?: %s' % (
              festival_name, str(self.panchaanga.festival_id_to_days[festival_name])))
        for assigned_day in self.panchaanga.festival_id_to_days[festival_name]:
          assigned_day_index = int(assigned_day - self.daily_panchaangas[0].date)
          if month_type == 'sidereal_solar_month':
            fest_num = period_start_year + 3100 - fest_start_year + 1
            for start_day in solar_y_start_d:
              if assigned_day_index >= start_day:
                fest_num += 1
          elif month_type == 'lunar_month':
            if festival_rules_all[festival_name].timing.anga_number == 1 and festival_rules_all[festival_name].timing.month_number == 1:
              # Assigned day may be less by one, since prathama may have started after sunrise
              # Still assume assigned_day >= lunar_y_start_d!
              fest_num = period_start_year + 3100 - fest_start_year + 1
              for start_day in lunar_y_start_d:
                if assigned_day_index >= start_day:
                  fest_num += 1
            else:
              fest_num = period_start_year + 3100 - fest_start_year + 1
              for start_day in lunar_y_start_d:
                if assigned_day_index >= start_day:
                  fest_num += 1

          if fest_num <= 0:
            logging.warning('Festival %s is only in the future!' % festival_name)
          self.panchaanga.date_str_to_panchaanga[assigned_day.get_date_str()].festival_id_to_instance[festival_name].ordinal = fest_num

  def cleanup_festivals(self):
    # If tripurotsava coincides with maha kArttikI (kRttikA nakShatram)
    # only then it is mahAkArttikI
    # else it is only tripurotsava
    if 'tripurOtsavaH' not in self.panchaanga.festival_id_to_days:
      logging.error('tripurOtsavaH not in self.panchaanga.festival_id_to_days!')
    else:
      if self.panchaanga.festival_id_to_days['tripurOtsavaH'] != self.panchaanga.festival_id_to_days['mahA~kArttikI']:
        logging.warning('Removing mahA~kArttikI (%s) since it does not coincide with tripurOtsavaH (%s)' % (
          str(self.panchaanga.festival_id_to_days['tripurOtsavaH']), set(self.panchaanga.festival_id_to_days['mahA~kArttikI'])))
      self.panchaanga.delete_festival(fest_id='mahA~kArttikI')
      # An error here implies the festival_id_to_instance were not assigned: adhika
      # mAsa calc errors??


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
