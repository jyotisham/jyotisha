import logging
import os
import sys

from jyotisha.panchaanga import temporal
from jyotisha.panchaanga.temporal import festival
from jyotisha.panchaanga.temporal import interval, PeriodicPanchaangaApplier, tithi
from jyotisha.panchaanga.temporal import time
from jyotisha.panchaanga.temporal import zodiac
from jyotisha.panchaanga.temporal.festival import rules
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision
from sanskrit_data.schema import common
from timebudget import timebudget
from jyotisha.panchaanga.temporal.zodiac.angas import AngaType, Anga

DATA_ROOT = os.path.join(os.path.dirname(festival.__file__), "data")


class FestivalAssigner(PeriodicPanchaangaApplier):
  def __init__(self, panchaanga):
    super(FestivalAssigner, self).__init__(panchaanga=panchaanga)
    self.rules_collection = rules.RulesCollection.get_cached(repos=tuple(panchaanga.computation_system.options.fest_repos))

  def add_festival(self, festival_name, d):
    if festival_name in self.panchaanga.festival_id_to_days:
      if self.daily_panchaangas[d].date not in self.panchaanga.festival_id_to_days[festival_name]:
        # Second occurrence of a festival within a
        # Gregorian calendar year
        if self.daily_panchaangas[d-1].date in self.panchaanga.festival_id_to_days[festival_name]:
          # No festival occurs on consecutive days; paraviddha assigned twice
          logging.warning(
            '%s occurring on two consecutive days (%d, %d). Removing! paraviddha assigned twice?' % (
              festival_name, d - 1, d))
          self.panchaanga.festival_id_to_days[festival_name].remove(self.daily_panchaangas[d-1].date)
        self.panchaanga.festival_id_to_days[festival_name].append(self.daily_panchaangas[d].date)
    else:
      self.panchaanga.festival_id_to_days[festival_name] = [self.daily_panchaangas[d].date]

  @timebudget
  def assign_festivals_from_rules(self, festival_rules):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

      for rule in festival_rules:
        assert isinstance(rule, rules.HinduCalendarEvent), rule
        if rule.timing.month_type is None and rule.description_short is not None:
          # Maybe only description of the festival is given, as computation has been
          # done in computeFestivals(), without using a rule in festival_rules.json!
            continue
        else:
          self.assign_festival(fest_rule=rule, d=d)

  def assign_sidereal_solar_day_fest(self, fest_rule, d):
    festival_name = fest_rule.id
    month_type = fest_rule.timing.month_type
    month_num = fest_rule.timing.month_number
    anga_type = fest_rule.timing.anga_type
    anga_num = fest_rule.timing.anga_number
    kaala = fest_rule.timing.kaala
    if month_type is None or month_num is None or anga_type is None or anga_num is None:
      raise ValueError(str(fest_rule))
    if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == month_num:
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.day == anga_num:
        if kaala == 'arunodaya':
          prev_angas = self.daily_panchaangas[d-1].day_length_based_periods.arunodaya.get_boundary_angas(anga_type=AngaType.SIDEREAL_MONTH, ayanaamsha_id=self.ayanaamsha_id).to_tuple()
          current_angas = self.daily_panchaangas[d].day_length_based_periods.arunodaya.get_boundary_angas(anga_type=AngaType.SIDEREAL_MONTH, ayanaamsha_id=self.ayanaamsha_id).to_tuple()
          if prev_angas[1] == month_num:
            self.add_festival(festival_name, d)
          elif current_angas[0] == month_num:
            self.add_festival(festival_name, d + 1)
        else:
          self.add_festival(festival_name, d)

  @timebudget
  def assign_festival(self, fest_rule, d):
    festival_name = fest_rule.id
    month_type = fest_rule.timing.month_type
    month_num = fest_rule.timing.month_number
    anga_type = fest_rule.timing.anga_type
    anga_num = fest_rule.timing.anga_number
    if month_type is None or month_num is None or anga_type is None or anga_num is None:
      raise ValueError(str(fest_rule))

    if anga_type == 'tithi' and month_type == 'lunar_month' and anga_num == 1:
      # Shukla prathama tithis need to be dealt carefully, if e.g. the prathama tithi
      # does not touch sunrise on either day (the regular check won't work, because
      # the month itself is different the previous day!)
      if self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise.index == 30 and self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise.index == 2 and \
          self.daily_panchaangas[d + 1].lunar_month_sunrise.index == month_num:
        # Only in this case, we have a problem
        self.add_festival(festival_name, d)
        return 

    if anga_type == 'day' and month_type == 'sidereal_solar_month': 
      self.assign_sidereal_solar_day_fest(fest_rule=fest_rule, d=d)
    elif (month_type == 'lunar_month' and ((self.daily_panchaangas[d].lunar_month_sunrise.index == month_num or month_num == 0) or (
        (self.daily_panchaangas[d + 1].lunar_month_sunrise.index == month_num and anga_num == 1)))) or \
        (month_type == 'sidereal_solar_month' and (self.daily_panchaangas[d].solar_sidereal_date_sunset.month == month_num or month_num == 0)):
      self.assign_tithi_yoga_nakshatra_fest(fest_rule=fest_rule, d=d)

  def assign_tithi_yoga_nakshatra_fest(self, fest_rule, d):
    festival_name = fest_rule.id
    month_type = fest_rule.timing.month_type
    month_num = fest_rule.timing.month_number
    anga_type_str = fest_rule.timing.anga_type
    target_anga = Anga.get_cached(index=fest_rule.timing.anga_number, anga_type_id=anga_type_str.upper())
    if month_type is None or month_num is None or anga_type_str is None or target_anga is None:
      raise ValueError(str(fest_rule))
    kaala = fest_rule.timing.kaala
    if kaala is None:
      kaala = 'sunrise'  # default!
    priority = fest_rule.timing.priority
    if priority is None:
      priority = 'puurvaviddha'
    # Using 0 as a special tag to denote every month!
    if anga_type_str == 'tithi':
      anga_data = [d.sunrise_day_angas.tithis_with_ends for d in self.daily_panchaangas]
      get_anga_func = lambda x: temporal.tithi.get_tithi(x)
    elif anga_type_str == 'nakshatra':
      anga_data = [d.sunrise_day_angas.nakshatras_with_ends for d in self.daily_panchaangas]
      get_anga_func = lambda x: NakshatraDivision(x, ayanaamsha_id=self.ayanaamsha_id).get_nakshatra()
    elif anga_type_str == 'yoga':
      anga_data = [d.sunrise_day_angas.yogas_with_ends for d in self.daily_panchaangas]
      get_anga_func = lambda x: NakshatraDivision(x, ayanaamsha_id=self.ayanaamsha_id).get_yoga()
    else:
      raise ValueError('Error; unknown string in rule: "%s"' % (anga_type_str))

    anga_type = target_anga.get_type()
    prev_anga = target_anga - 1
    next_anga = target_anga + 1
    anga_sunrise = self.daily_panchaangas[d].sunrise_day_angas.get_angas_with_ends(anga_type=anga_type)[0].anga

    fday = None

    if anga_sunrise == prev_anga or anga_sunrise == target_anga:
      if kaala == 'arunodaya':
        # We want for arunodaya *preceding* today's sunrise; therefore, use d - 1
        angas = self.panchaanga.get_2_day_interval_boundaries_angas(d - 1, get_anga_func, kaala)
      else:
        angas = self.panchaanga.get_2_day_interval_boundaries_angas(d, get_anga_func, kaala)

      if angas is None:
        logging.error('No angas returned! Skipping festival %s' % festival_name)
        return 
        # Some error, e.g. weird kaala, so skip festival
      if priority == 'paraviddha':
        if (angas[1] == target_anga and angas[3] == target_anga) or (
            angas[2] == target_anga and angas[3] == target_anga):
          # Incident at kaala on two consecutive days; so take second
          fday = d + 1
        elif angas[0] == target_anga and angas[1] == target_anga:
          # Incident only on day 1, maybe just touching day 2
          fday = d
        elif angas[1] == target_anga:
          fday = d
        elif angas[2] == target_anga:
          fday = d
        elif angas[0] == target_anga and angas[1] == next_anga:
          if kaala == 'aparaahna':
            fday = d
          else:
            fday = d - 1
        elif angas[1] == prev_anga and angas[2] == next_anga:
          fday = d
          logging.warning(
            '%s %d did not touch %s kaala on d=%d or %d. Assigning %d for %s; angas: %s' %
            (anga_type_str, target_anga.index, kaala, d, d + 1, fday, festival_name, str(angas)))
        else:
          if festival_name not in self.panchaanga.festival_id_to_days and angas[3] > target_anga:
            logging.debug((angas, target_anga))
            logging.warning(
              'Could not assign paraviddha day for %s!  Please check for unusual cases.' % festival_name)
      elif priority == 'puurvaviddha':
        if angas[0] == target_anga or angas[1] == target_anga:
          if festival_name in self.panchaanga.festival_id_to_days:
            # Check if yesterday was assigned already
            # to this puurvaviddha festival!
            if self.panchaanga.festival_id_to_days[festival_name].count(self.daily_panchaangas[d-1].date) == 0:
              fday = d
          else:
            fday = d
        elif angas[2] == target_anga or angas[3] == target_anga:
          fday = d + 1
        else:
          # This means that the correct anga did not
          # touch the kaala on either day!
          if angas == [prev_anga, prev_anga, next_anga, next_anga]:
            # d_offset = {'sunrise': 0, 'aparaahna': 1, 'moonrise': 1, 'madhyaahna': 1, 'sunset': 1}[kaala]
            d_offset = 0 if kaala in ['sunrise', 'moonrise'] else 1
            # Need to assign a day to the festival here
            # since the anga did not touch kaala on either day
            # BUT ONLY IF YESTERDAY WASN'T ALREADY ASSIGNED,
            # THIS BEING PURVAVIDDHA
            # Perhaps just need better checking of
            # conditions instead of this fix
            if festival_name in self.panchaanga.festival_id_to_days:
              offset_date = self.daily_panchaangas[d - 1 + d_offset].date
              if self.panchaanga.festival_id_to_days[festival_name].count(offset_date) == 0:
                fday = d + d_offset
            else:
              fday = d + d_offset
          else:
            if festival_name not in self.panchaanga.festival_id_to_days and angas != [prev_anga] * 4:
              logging.debug('Special case: %s; angas = %s' % (festival_name, str(angas)))

      elif priority == 'vyaapti':
        if kaala == 'aparaahna':
          t_start_d, t_end_d = interval.get_interval(self.daily_panchaangas[d].jd_sunrise, self.daily_panchaangas[d].jd_sunset, 3, 5).to_tuple()
        else:
          logging.error('Unknown kaala: %s.' % festival_name)

        if kaala == 'aparaahna':
          t_start_d1, t_end_d1 = interval.get_interval(self.daily_panchaangas[d + 1].jd_sunrise,
                                                                                    self.daily_panchaangas[d + 1].jd_sunset, 3, 5).to_tuple()
        else:
          logging.error('Unknown kaala: %s.' % festival_name)

        # Combinations
        # <a> 0 0 1 1: d + 1
        # <d> 0 1 1 1: d + 1
        # <g> 1 1 1 1: d + 1
        # <b> 0 0 1 2: d + 1
        # <c> 0 0 2 2: d + 1
        # <e> 0 1 1 2: vyApti
        # <f> 0 1 2 2: d
        # <h> 1 1 1 2: d
        # <i> 1 1 2 2: d
        p, q, r = prev_anga, target_anga, next_anga  # short-hand
        if angas in ([p, p, q, q], [p, q, q, q], [q, q, q, q], [p, p, q, r], [p, p, r, r]):
          fday = d + 1
        elif angas in ([p, q, r, r], [q, q, q, r], [q, q, r, r]):
          fday = d
        elif angas == [p, q, q, r]:
          anga_span = anga_data[d][0]
          (anga, anga_end) = (anga_span.anga, anga_span.jd_end)
          vyapti_1 = max(t_end_d - anga_end, 0)
          vyapti_2 = max(anga_end - t_start_d1, 0)
          for anga_span in anga_data[d + 1]:
            anga_end = anga_span.jd_end
            if anga_end is None:
              pass
            elif t_start_d1 < anga_end < t_end_d1:
              vyapti_2 = anga_end - t_start_d1

          if vyapti_2 > vyapti_1:
            fday = d + 1
          else:
            fday = d
      else:
        logging.error('Unknown priority "%s" for %s! Check the rules!' % (priority, festival_name))

    if fday is not None:
      if (month_type == 'lunar_month' and ((self.daily_panchaangas[d].lunar_month_sunrise.index == month_num or month_num == 0) or (
          (self.daily_panchaangas[d + 1].lunar_month_sunrise.index == month_num and target_anga.index == 1)))) or \
          (month_type == 'sidereal_solar_month' and (
              self.daily_panchaangas[fday].solar_sidereal_date_sunset.month == month_num or month_num == 0)):
        # If month on fday is incorrect, we ignore and move.
        if month_type == 'lunar_month' and target_anga.index == 1 and self.daily_panchaangas[
          fday + 1].lunar_month_sunrise.index != month_num:
          return 
        # if festival_name.find('\\') == -1 and \
        #         'kaala' in fest_rule and \
        #         festival_rules[festival_name].timing.kaala == 'arunodaya':
        #     fday += 1
        self.add_festival(festival_name, fday)

  @timebudget
  def assign_festival_numbers(self):
    # Update festival numbers if they exist
    solar_y_start_d = []
    lunar_y_start_d = []
    for d in range(1, self.panchaanga.duration + 1):
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
          if self.panchaanga.festival_id_to_days[festival_name][1] - self.panchaanga.festival_id_to_days[festival_name][0] < 300:
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

  def cleanup_festivals(self, debug=False):
    # If tripurotsava coincides with maha kArttikI (kRttikA nakShatram)
    # only then it is mahAkArttikI
    # else it is only tripurotsava
    if 'tripurOtsavaH' not in self.panchaanga.festival_id_to_days:
      logging.error('tripurOtsavaH not in self.panchaanga.festival_id_to_days!')
    else:
      if self.panchaanga.festival_id_to_days['tripurOtsavaH'] != self.panchaanga.festival_id_to_days['mahA~kArttikI']:
        logging.warning('Removing mahA~kArttikI (%s) since it does not coincide with tripurOtsavaH (%s)' % (
          self.panchaanga.festival_id_to_days['tripurOtsavaH'][0], self.panchaanga.festival_id_to_days['mahA~kArttikI'][0]))
        del self.panchaanga.festival_id_to_days['mahA~kArttikI']
        # An error here implies the festival_id_to_instance were not assigned: adhika
        # mAsa calc errors??


class MiscFestivalAssigner(FestivalAssigner):
  def __init__(self, panchaanga):
    super(MiscFestivalAssigner, self).__init__(panchaanga=panchaanga)


  def assign_all(self, debug=False):
    self.assign_agni_nakshatra()
    # ASSIGN ALL FESTIVALS FROM adyatithi submodule
    # festival_rules = get_festival_rules_dict(os.path.join(CODE_ROOT, 'panchaanga/data/festival_rules_test.json'))
    festival_rules = [x for x in self.rules_collection.name_to_rule.values() if x.timing is not None and x.timing.month_type is not None]

    # assert "tripurOtsavaH" in festival_rules
    self.assign_festivals_from_rules(festival_rules)
    

  def assign_agni_nakshatra(self):
    agni_jd_start = agni_jd_end = None
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

      # AGNI nakshatra
      # Arbitrarily checking after Mesha 10! Agni Nakshatram can't start earlier...
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 1 and self.daily_panchaangas[d].solar_sidereal_date_sunset.day == 10:
        anga_finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.ayanaamsha_id, anga_type=zodiac.AngaType.SOLAR_NAKSH_PADA)
        agni_jd_start, dummy = anga_finder.find(
          jd1=self.daily_panchaangas[d].jd_sunrise, jd2=self.daily_panchaangas[d].jd_sunrise + 30,
          target_anga_id=7).to_tuple()
        dummy, agni_jd_end = anga_finder.find(
          jd1=agni_jd_start, jd2=agni_jd_start + 30,
          target_anga_id=13).to_tuple()

      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 1 and self.daily_panchaangas[d].solar_sidereal_date_sunset.day > 10:
        if agni_jd_start is not None:
          if self.daily_panchaangas[d].jd_sunset < agni_jd_start < self.daily_panchaangas[d + 1].jd_sunset:
            self.add_festival('agninakSatra-ArambhaH', d + 1)
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 2 and self.daily_panchaangas[d].solar_sidereal_date_sunset.day > 10:
        if agni_jd_end is not None:
          if self.daily_panchaangas[d].jd_sunset < agni_jd_end < self.daily_panchaangas[d + 1].jd_sunset:
            self.add_festival('agninakSatra-samApanam', d + 1)

  def assign_relative_festivals(self):
    # Add "RELATIVE" festival_id_to_instance --- festival_id_to_instance that happen before or
    # after other festival_id_to_instance with an exact timedelta!
    if 'yajurvEda-upAkarma' not in self.panchaanga.festival_id_to_days:
      logging.error('yajurvEda-upAkarma not in festival_id_to_instance!')
    else:
      # Extended for longer calendars where more than one upAkarma may be there
      self.panchaanga.festival_id_to_days['varalakSmI-vratam'] = []
      for d in self.panchaanga.festival_id_to_days['yajurvEda-upAkarma']:
        self.panchaanga.festival_id_to_days['varalakSmI-vratam'].append(d - ((d.get_weekday() - 5) % 7))
      # self.panchaanga.festival_id_to_days['varalakSmI-vratam'] = [self.panchaanga.festival_id_to_days['yajurvEda-upAkarma'][0] -
      #                                        ((self.panchaanga.weekday_start - 1 + self.panchaanga.festival_id_to_days['yajurvEda-upAkarma'][
      #                                            0] - 5) % 7)]

    name_to_rule = self.rules_collection.name_to_rule

    for festival_name in name_to_rule:
      if name_to_rule[festival_name].timing is None or name_to_rule[festival_name].timing.offset is None:
        continue
      offset = int(name_to_rule[festival_name].timing.offset)
      rel_festival_name = name_to_rule[festival_name].timing.anchor_festival_id
      if rel_festival_name not in self.panchaanga.festival_id_to_days:
        # Check approx. match
        matched_festivals = []
        for fest_key in self.panchaanga.festival_id_to_days:
          if fest_key.startswith(rel_festival_name):
            matched_festivals += [fest_key]
        if matched_festivals == []:
          logging.error('Relative festival %s not in festival_id_to_days!' % rel_festival_name)
        elif len(matched_festivals) > 1:
          logging.error('Relative festival %s not in festival_id_to_days! Found more than one approximate match: %s' % (
            rel_festival_name, str(matched_festivals)))
        else:
          self.panchaanga.festival_id_to_days[festival_name] = [x + offset for x in self.panchaanga.festival_id_to_days[matched_festivals[0]]]
      else:
        self.panchaanga.festival_id_to_days[festival_name] = [x + offset for x in self.panchaanga.festival_id_to_days[rel_festival_name]]


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
