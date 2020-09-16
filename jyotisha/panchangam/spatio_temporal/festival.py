import os
from itertools import filterfalse
from math import floor

from jyotisha.panchangam.temporal.body import Graha
from jyotisha.panchangam.temporal.festival import read_old_festival_rules_dict
from pytz import timezone as tz
import logging
from datetime import datetime

from jyotisha import names
from scipy.optimize import brentq

from jyotisha.panchangam import temporal
from jyotisha.panchangam.spatio_temporal import CODE_ROOT
from jyotisha.panchangam.temporal import zodiac
from jyotisha.panchangam.temporal.hour import Hour
from jyotisha.panchangam.temporal.zodiac import NakshatraDivision, AngaSpan
from sanskrit_data.schema.common import JsonObject


class FestivalAssigner(JsonObject):
  def __init__(self, panchaanga):
    self.panchaanga = panchaanga

  def assign_all(self, debug_festivals=False):
    pass

  def filter_festivals(self,
                       incl_tags=['CommonFestivals', 'MonthlyVratam', 'RareDays', 'AmavasyaDays', 'Dashavataram',
                                  'SunSankranti']):
    festival_rules_main = read_old_festival_rules_dict(
      os.path.join(CODE_ROOT, 'panchangam/temporal/festival/data/legacy/festival_rules.json'))
    festival_rules_rel = read_old_festival_rules_dict(
      os.path.join(CODE_ROOT, 'panchangam/temporal/festival/data/legacy/relative_festival_rules.json'))
    festival_rules_desc_only = read_old_festival_rules_dict(
      os.path.join(CODE_ROOT, 'panchangam/temporal/festival/data/legacy/festival_rules_desc_only.json'))

    festival_rules = {**festival_rules_main, **festival_rules_rel, **festival_rules_desc_only}

    for d in range(1, len(self.panchaanga.festivals)):
      if len(self.panchaanga.festivals[d]) > 0:
        # Eliminate repeat festivals on the same day, and keep the list arbitrarily sorted
        self.panchaanga.festivals[d] = sorted(list(set(self.panchaanga.festivals[d])))

        def chk_fest(fest_title):
          fest_num_loc = fest_title.find('~#')
          if fest_num_loc != -1:
            fest_text_itle = fest_title[:fest_num_loc]
          else:
            fest_text_itle = fest_title
          if fest_text_itle in festival_rules:
            tag_list = (festival_rules[fest_text_itle]['tags'].split(','))
            if set(tag_list).isdisjoint(set(incl_tags)):
              return True
            else:
              return False
          else:
            return False

        self.panchaanga.festivals[d][:] = filterfalse(chk_fest, self.panchaanga.festivals[d])


  def add_festival(self, festival_name, d, debug=False):
    if debug:
      logging.debug('%03d: %s ' % (d, festival_name))
    if festival_name in self.panchaanga.fest_days:
      if d not in self.panchaanga.fest_days[festival_name]:
        # Second occurrence of a festival within a
        # Gregorian calendar year
        if (d - 1) in self.panchaanga.fest_days[festival_name]:
          # No festival occurs on consecutive days; paraviddha assigned twice
          logging.warning(
            '%s occurring on two consecutive days (%d, %d). Removing! paraviddha assigned twice?' % (
              festival_name, d - 1, d))
          self.panchaanga.fest_days[festival_name].remove(d - 1)
        self.panchaanga.fest_days[festival_name].append(d)
    else:
      self.panchaanga.fest_days[festival_name] = [d]

  def assign_festivals_from_rules(self, festival_rules, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      for festival_name in festival_rules:
        if 'month_type' in festival_rules[festival_name]:
          month_type = festival_rules[festival_name]['month_type']
        else:
          # Maybe only description of the festival is given, as computation has been
          # done in computeFestivals(), without using a rule in festival_rules.json!
          if 'description_short' in festival_rules[festival_name]:
            continue
          raise (ValueError, "No month_type mentioned for %s" % festival_name)
        if 'month_number' in festival_rules[festival_name]:
          month_num = festival_rules[festival_name]['month_number']
        else:
          raise (ValueError, "No month_num mentioned for %s" % festival_name)
        if 'angam_type' in festival_rules[festival_name]:
          angam_type = festival_rules[festival_name]['angam_type']
        else:
          raise (ValueError, "No angam_type mentioned for %s" % festival_name)
        if 'angam_number' in festival_rules[festival_name]:
          angam_num = festival_rules[festival_name]['angam_number']
        else:
          raise (ValueError, "No angam_num mentioned for %s" % festival_name)
        if 'kaala' in festival_rules[festival_name]:
          kaala = festival_rules[festival_name]['kaala']
        else:
          kaala = 'sunrise'  # default!
        if 'priority' in festival_rules[festival_name]:
          priority = festival_rules[festival_name]['priority']
        else:
          priority = 'puurvaviddha'
        # if 'titles' in festival_rules[festival_name]:
        #     fest_other_names = festival_rules[festival_name]['titles']
        # if 'Nirnaya' in festival_rules[festival_name]:
        #     fest_nirnaya = festival_rules[festival_name]['Nirnaya']
        # if 'references_primary' in festival_rules[festival_name]:
        #     fest_ref1 = festival_rules[festival_name]['references_primary']
        # if 'references_secondary' in festival_rules[festival_name]:
        #     fest_ref2 = festival_rules[festival_name]['references_secondary']
        # if 'comments' in festival_rules[festival_name]:
        #     fest_comments = festival_rules[festival_name]['comments']

        if angam_type == 'tithi' and month_type == 'lunar_month' and angam_num == 1:
          # Shukla prathama tithis need to be dealt carefully, if e.g. the prathama tithi
          # does not touch sunrise on either day (the regular check won't work, because
          # the month itself is different the previous day!)
          if self.panchaanga.tithi_sunrise[d] == 30 and self.panchaanga.tithi_sunrise[d + 1] == 2 and \
              self.panchaanga.lunar_month[d + 1] == month_num:
            # Only in this case, we have a problem
            self.add_festival(festival_name, d, debug_festivals)
            continue

        if angam_type == 'day' and month_type == 'solar_month' and self.panchaanga.solar_month[d] == month_num:
          if self.panchaanga.solar_month_day[d] == angam_num:
            if kaala == 'arunodaya':
              angams = self.panchaanga.get_angams_for_kaalas(d - 1,
                                                  lambda x: NakshatraDivision(x,
                                                                              ayanamsha_id=self.panchaanga.ayanamsha_id).get_solar_rashi(),
                                                  kaala)
              if angams[1] == month_num:
                self.add_festival(festival_name, d, debug_festivals)
              elif angams[2] == month_num:
                self.add_festival(festival_name, d + 1, debug_festivals)
            else:
              self.add_festival(festival_name, d, debug_festivals)
        elif (month_type == 'lunar_month' and ((self.panchaanga.lunar_month[d] == month_num or month_num == 0) or (
            (self.panchaanga.lunar_month[d + 1] == month_num and angam_num == 1)))) or \
            (month_type == 'solar_month' and (self.panchaanga.solar_month[d] == month_num or month_num == 0)):
          # Using 0 as a special tag to denote every month!
          if angam_type == 'tithi':
            angam_sunrise = self.panchaanga.tithi_sunrise
            angam_data = self.panchaanga.tithi_data
            get_angam_func = lambda x: NakshatraDivision(x, ayanamsha_id=self.panchaanga.ayanamsha_id).get_tithi()
            num_angams = 30
          elif angam_type == 'nakshatram':
            angam_sunrise = self.panchaanga.nakshatram_sunrise
            angam_data = self.panchaanga.nakshatram_data
            get_angam_func = lambda x: NakshatraDivision(x, ayanamsha_id=self.panchaanga.ayanamsha_id).get_nakshatram()
            num_angams = 27
          elif angam_type == 'yoga':
            angam_sunrise = self.panchaanga.yoga_sunrise
            angam_data = self.panchaanga.yoga_data
            get_angam_func = lambda x: NakshatraDivision(x, ayanamsha_id=self.panchaanga.ayanamsha_id).get_yoga()
            num_angams = 27
          else:
            raise ValueError('Error; unknown string in rule: "%s"' % (angam_type))

          if angam_num == 1:
            prev_angam = num_angams
          else:
            prev_angam = angam_num - 1
          next_angam = (angam_num % num_angams) + 1
          nnext_angam = (next_angam % 30) + 1

          fday = None

          if angam_sunrise[d] == prev_angam or angam_sunrise[d] == angam_num:
            if kaala == 'arunodaya':
              # We want for arunodaya *preceding* today's sunrise; therefore, use d - 1
              angams = self.panchaanga.get_angams_for_kaalas(d - 1, get_angam_func, kaala)
            else:
              angams = self.panchaanga.get_angams_for_kaalas(d, get_angam_func, kaala)

            if angams is None:
              logging.error('No angams returned! Skipping festival %s' % festival_name)
              continue
              # Some error, e.g. weird kaala, so skip festival
            if debug_festivals:
              try:
                logging.debug(('%', festival_name, ': ', festival_rules[festival_name]))
                logging.debug(("%%angams today & tmrw:", angams))
              except KeyError:
                logging.debug(
                  ('%', festival_name, ': ', festival_rules[festival_name.split('\\')[0][:-1]]))
                logging.debug(("%%angams today & tmrw:", angams))

            if priority == 'paraviddha':
              if (angams[1] == angam_num and angams[3] == angam_num) or (
                  angams[2] == angam_num and angams[3] == angam_num):
                # Incident at kaala on two consecutive days; so take second
                fday = d + 1
              elif angams[0] == angam_num and angams[1] == angam_num:
                # Incident only on day 1, maybe just touching day 2
                fday = d
              elif angams[1] == angam_num:
                fday = d
                if debug_festivals:
                  logging.warning('%s %d did not touch start of %s kaala on d=%d or %d,\
                                        but incident at end of kaala at d=%d. Assigning %d for %s; angams: %s' %
                                  (angam_type, angam_num, kaala, d, d + 1, d, fday, festival_name,
                                   str(angams)))
              elif angams[2] == angam_num:
                fday = d
                if debug_festivals:
                  logging.warning(
                    '%s %d present only at start of %s kaala on d=%d. Assigning %d for %s; angams: %s' %
                    (angam_type, angam_num, kaala, d + 1, d, festival_name, str(angams)))
              elif angams[0] == angam_num and angams[1] == next_angam:
                if kaala == 'aparaahna':
                  fday = d
                else:
                  fday = d - 1
              elif angams[1] == prev_angam and angams[2] == next_angam:
                fday = d
                logging.warning(
                  '%s %d did not touch %s kaala on d=%d or %d. Assigning %d for %s; angams: %s' %
                  (angam_type, angam_num, kaala, d, d + 1, fday, festival_name, str(angams)))
              else:
                if festival_name not in self.panchaanga.fest_days and angams[3] > angam_num:
                  logging.debug((angams, angam_num))
                  logging.warning(
                    'Could not assign paraviddha day for %s!  Please check for unusual cases.' % festival_name)
            elif priority == 'puurvaviddha':
              # angams_yest = self.panchaanga.get_angams_for_kaalas(d - 1, get_angam_func, kaala)
              # if debug_festivals:
              #     print("%angams yest & today:", angams_yest)
              if angams[0] == angam_num or angams[1] == angam_num:
                if festival_name in self.panchaanga.fest_days:
                  # Check if yesterday was assigned already
                  # to this puurvaviddha festival!
                  if self.panchaanga.fest_days[festival_name].count(d - 1) == 0:
                    fday = d
                else:
                  fday = d
              elif angams[2] == angam_num or angams[3] == angam_num:
                fday = d + 1
              else:
                # This means that the correct angam did not
                # touch the kaala on either day!
                if angams == [prev_angam, prev_angam, next_angam, next_angam]:
                  # d_offset = {'sunrise': 0, 'aparaahna': 1, 'moonrise': 1, 'madhyaahna': 1, 'sunset': 1}[kaala]
                  d_offset = 0 if kaala in ['sunrise', 'moonrise'] else 1
                  if debug_festivals:
                    logging.warning(
                      '%d-%02d-%02d> %s: %s %d did not touch %s on either day: %s. Assigning today + %d' %
                      (y, m, dt, festival_name, angam_type, angam_num, kaala, str(angams),
                       d_offset))
                  # Need to assign a day to the festival here
                  # since the angam did not touch kaala on either day
                  # BUT ONLY IF YESTERDAY WASN'T ALREADY ASSIGNED,
                  # THIS BEING PURVAVIDDHA
                  # Perhaps just need better checking of
                  # conditions instead of this fix
                  if festival_name in self.panchaanga.fest_days:
                    if self.panchaanga.fest_days[festival_name].count(d - 1 + d_offset) == 0:
                      fday = d + d_offset
                  else:
                    fday = d + d_offset
                else:
                  if festival_name not in self.panchaanga.fest_days and angams != [prev_angam] * 4:
                    logging.debug('Special case: %s; angams = %s' % (festival_name, str(angams)))

            elif priority == 'vyaapti':
              if kaala == 'aparaahna':
                t_start_d, t_end_d = temporal.get_interval(self.panchaanga.jd_sunrise[d], self.panchaanga.jd_sunset[d], 3, 5).to_tuple()
              else:
                logging.error('Unknown kaala: %s.' % festival_name)

              if kaala == 'aparaahna':
                t_start_d1, t_end_d1 = temporal.get_interval(self.panchaanga.jd_sunrise[d + 1],
                                                             self.panchaanga.jd_sunset[d + 1], 3, 5).to_tuple()
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
              p, q, r = prev_angam, angam_num, next_angam  # short-hand
              if angams in ([p, p, q, q], [p, q, q, q], [q, q, q, q], [p, p, q, r], [p, p, r, r]):
                fday = d + 1
              elif angams in ([p, q, r, r], [q, q, q, r], [q, q, r, r]):
                fday = d
              elif angams == [p, q, q, r]:
                angam, angam_end = angam_data[d][0]
                assert t_start_d < angam_end < t_end_d
                vyapti_1 = t_end_d - angam_end
                angam_d1, angam_end_d1 = angam_data[d + 1][0]
                assert t_start_d1 < angam_end_d1 < t_end_d1
                vyapti_2 = angam_end - t_start_d1
                for [angam, angam_end] in angam_data[d + 1]:
                  if angam_end is None:
                    pass
                  elif t_start_d1 < angam_end < t_end_d1:
                    vyapti_2 = angam_end - t_start_d1

                if vyapti_2 > vyapti_1:
                  fday = d + 1
                else:
                  fday = d
            else:
              logging.error('Unknown priority "%s" for %s! Check the rules!' % (priority, festival_name))

          if fday is not None:
            if (month_type == 'lunar_month' and ((self.panchaanga.lunar_month[d] == month_num or month_num == 0) or (
                (self.panchaanga.lunar_month[d + 1] == month_num and angam_num == 1)))) or \
                (month_type == 'solar_month' and (
                    self.panchaanga.solar_month[fday] == month_num or month_num == 0)):
              # If month on fday is incorrect, we ignore and move.
              if month_type == 'lunar_month' and angam_num == 1 and self.panchaanga.lunar_month[
                fday + 1] != month_num:
                continue
              # if festival_name.find('\\') == -1 and \
              #         'kaala' in festival_rules[festival_name] and \
              #         festival_rules[festival_name]['kaala'] == 'arunodaya':
              #     fday += 1
              self.add_festival(festival_name, fday, debug_festivals)
            else:
              if debug_festivals:
                if month_type == 'solar_month':
                  logging.warning('Not adding festival %s on %d fday (month = %d instead of %d)' % (
                    festival_name, fday, self.panchaanga.solar_month[fday], month_num))
                else:
                  logging.warning('Not adding festival %s on %d fday (month = %d instead of %d)' % (
                    festival_name, fday, self.panchaanga.lunar_month[fday], month_num))

  def assign_festival_numbers(self, festival_rules, debug_festivals=False):
    # Update festival numbers if they exist
    solar_y_start_d = []
    lunar_y_start_d = []
    for d in range(1, self.panchaanga.duration + 1):
      if self.panchaanga.solar_month[d] == 1 and self.panchaanga.solar_month[d - 1] != 1:
        solar_y_start_d.append(d)
      if self.panchaanga.lunar_month[d] == 1 and self.panchaanga.lunar_month[d - 1] != 1:
        lunar_y_start_d.append(d)

    period_start_year = self.panchaanga.start_date[0]
    for festival_name in festival_rules:
      if festival_name in self.panchaanga.fest_days and 'year_start' in festival_rules[festival_name]:
        fest_start_year = festival_rules[festival_name]['year_start']
        month_type = festival_rules[festival_name]['month_type']
        if len(self.panchaanga.fest_days[festival_name]) > 1:
          if self.panchaanga.fest_days[festival_name][1] - self.panchaanga.fest_days[festival_name][0] < 300:
            # Lunar festivals can repeat after 354 days; Solar festivals "can" repeat after 330 days
            # (last day of Dhanur masa Jan and first day of Dhanur masa Dec may have same nakshatra and are about 335 days apart)
            # In fact they will be roughly 354 days apart, again!
            logging.warning('Multiple occurrences of festival %s within year. Check?: %s' % (
              festival_name, str(self.panchaanga.fest_days[festival_name])))
        for assigned_day in self.panchaanga.fest_days[festival_name]:
          if month_type == 'solar_month':
            fest_num = period_start_year + 3100 - fest_start_year + 1
            for start_day in solar_y_start_d:
              if assigned_day >= start_day:
                fest_num += 1
          elif month_type == 'lunar_month':
            if festival_rules[festival_name]['angam_number'] == 1 and festival_rules[festival_name][
              'month_number'] == 1:
              # Assigned day may be less by one, since prathama may have started after sunrise
              # Still assume assigned_day >= lunar_y_start_d!
              fest_num = period_start_year + 3100 - fest_start_year + 1
              for start_day in lunar_y_start_d:
                if assigned_day >= start_day:
                  fest_num += 1
            else:
              fest_num = period_start_year + 3100 - fest_start_year + 1
              for start_day in lunar_y_start_d:
                if assigned_day >= start_day:
                  fest_num += 1

          if fest_num <= 0:
            logging.warning('Festival %s is only in the future!' % festival_name)
          else:
            if festival_name not in self.panchaanga.fest_days:
              logging.warning(
                'Did not find festival %s to be assigned. Dhanurmasa festival?' % festival_name)
              continue
            festival_name_updated = festival_name + '~\\#{%d}' % fest_num
            # logging.debug('Changing %s to %s' % (festival_name, festival_name_updated))
            if festival_name_updated in self.panchaanga.fest_days:
              logging.warning('Overwriting festival day for %s %d with %d.' % (
                festival_name_updated, self.panchaanga.fest_days[festival_name_updated][0], assigned_day))
              self.panchaanga.fest_days[festival_name_updated] = [assigned_day]
            else:
              self.panchaanga.fest_days[festival_name_updated] = [assigned_day]
        del (self.panchaanga.fest_days[festival_name])

  def cleanup_festivals(self, debug_festivals=False):
    # If tripurotsava coincides with maha kArttikI (kRttikA nakShatram)
    # only then it is mahAkArttikI
    # else it is only tripurotsava
    if 'tripurOtsavaH' not in self.panchaanga.fest_days:
      logging.error('tripurOtsavaH not in self.panchaanga.fest_days!')
    else:
      if self.panchaanga.fest_days['tripurOtsavaH'] != self.panchaanga.fest_days['mahA~kArttikI']:
        logging.warning('Removing mahA~kArttikI (%d) since it does not coincide with tripurOtsavaH (%d)' % (
          self.panchaanga.fest_days['tripurOtsavaH'][0], self.panchaanga.fest_days['mahA~kArttikI'][0]))
        del self.panchaanga.fest_days['mahA~kArttikI']
        # An error here implies the festivals were not assigned: adhika
        # mAsa calc errors??


class MiscFestivalAssigner(FestivalAssigner):
  def __init__(self, panchaanga):
    super(MiscFestivalAssigner, self).__init__(panchaanga=panchaanga)
  
  def assign_all(self, debug_festivals=False):
    self.assign_agni_nakshatram(debug_festivals=debug_festivals)
    # ASSIGN ALL FESTIVALS FROM adyatithi submodule
    # festival_rules = read_old_festival_rules_dict(os.path.join(CODE_ROOT, 'panchangam/data/festival_rules_test.json'))
    festival_rules = read_old_festival_rules_dict(
      os.path.join(CODE_ROOT, 'panchangam/temporal/festival/data/legacy/festival_rules.json'))
    assert "tripurOtsavaH" in festival_rules
    self.assign_festivals_from_rules(festival_rules, debug_festivals=debug_festivals)
    self.assign_festival_numbers(festival_rules, debug_festivals=debug_festivals)
    

  def assign_agni_nakshatram(self, debug_festivals=False):
    agni_jd_start = agni_jd_end = None
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # AGNI NAKSHATRAM
      # Arbitrarily checking after Mesha 10! Agni Nakshatram can't start earlier...
      if self.panchaanga.solar_month[d] == 1 and self.panchaanga.solar_month_day[d] == 10:
        agni_jd_start, dummy = AngaSpan.find(
          self.panchaanga.jd_sunrise[d], self.panchaanga.jd_sunrise[d] + 30,
          zodiac.SOLAR_NAKSH_PADA, 7, ayanamsha_id=self.panchaanga.ayanamsha_id).to_tuple()
        dummy, agni_jd_end = AngaSpan.find(
          agni_jd_start, agni_jd_start + 30,
          zodiac.SOLAR_NAKSH_PADA, 13, ayanamsha_id=self.panchaanga.ayanamsha_id).to_tuple()

      if self.panchaanga.solar_month[d] == 1 and self.panchaanga.solar_month_day[d] > 10:
        if agni_jd_start is not None:
          if self.panchaanga.jd_sunset[d] < agni_jd_start < self.panchaanga.jd_sunset[d + 1]:
            self.add_festival('agninakSatra-ArambhaH', d + 1, debug_festivals)
      if self.panchaanga.solar_month[d] == 2 and self.panchaanga.solar_month_day[d] > 10:
        if agni_jd_end is not None:
          if self.panchaanga.jd_sunset[d] < agni_jd_end < self.panchaanga.jd_sunset[d + 1]:
            self.add_festival('agninakSatra-samApanam', d + 1, debug_festivals)

  def assign_relative_festivals(self):
    # Add "RELATIVE" festivals --- festivals that happen before or
    # after other festivals with an exact timedelta!
    if 'yajurvEda-upAkarma' not in self.panchaanga.fest_days:
      logging.error('yajurvEda-upAkarma not in festivals!')
    else:
      # Extended for longer calendars where more than one upAkarma may be there
      self.panchaanga.fest_days['varalakSmI-vratam'] = []
      for d in self.panchaanga.fest_days['yajurvEda-upAkarma']:
        self.panchaanga.fest_days['varalakSmI-vratam'].append(d - ((self.panchaanga.weekday_start - 1 + d - 5) % 7))
      # self.panchaanga.fest_days['varalakSmI-vratam'] = [self.panchaanga.fest_days['yajurvEda-upAkarma'][0] -
      #                                        ((self.panchaanga.weekday_start - 1 + self.panchaanga.fest_days['yajurvEda-upAkarma'][
      #                                            0] - 5) % 7)]

    relative_festival_rules = read_old_festival_rules_dict(
      os.path.join(CODE_ROOT, 'panchangam/temporal/festival/data/legacy/relative_festival_rules.json'))

    for festival_name in relative_festival_rules:
      offset = int(relative_festival_rules[festival_name]['offset'])
      rel_festival_name = relative_festival_rules[festival_name]['anchor_festival_id']
      if rel_festival_name not in self.panchaanga.fest_days:
        # Check approx. match
        matched_festivals = []
        for fest_key in self.panchaanga.fest_days:
          if fest_key.startswith(rel_festival_name):
            matched_festivals += [fest_key]
        if matched_festivals == []:
          logging.error('Relative festival %s not in fest_days!' % rel_festival_name)
        elif len(matched_festivals) > 1:
          logging.error('Relative festival %s not in fest_days! Found more than one approximate match: %s' % (
            rel_festival_name, str(matched_festivals)))
        else:
          self.panchaanga.fest_days[festival_name] = [x + offset for x in self.panchaanga.fest_days[matched_festivals[0]]]
      else:
        self.panchaanga.fest_days[festival_name] = [x + offset for x in self.panchaanga.fest_days[rel_festival_name]]

    for festival_name in self.panchaanga.fest_days:
      for j in range(0, len(self.panchaanga.fest_days[festival_name])):
        self.panchaanga.festivals[self.panchaanga.fest_days[festival_name][j]].append(festival_name)


class TithiFestivalAssigner(FestivalAssigner):
  def assign_all(self, debug_festivals=False):
    self.assign_chandra_darshanam(debug_festivals=debug_festivals)
    self.assign_chaturthi_vratam(debug_festivals=debug_festivals)
    self.assign_shasthi_vratam(debug_festivals=debug_festivals)
    self.assign_vishesha_saptami(debug_festivals=debug_festivals)
    self.assign_ekadashi_vratam(debug_festivals=debug_festivals)
    self.assign_mahadwadashi(debug_festivals=debug_festivals)
    self.assign_pradosha_vratam(debug_festivals=debug_festivals)
    self.assign_vishesha_trayodashi(debug_festivals=debug_festivals)
    self.assign_amavasya_yoga(debug_festivals=debug_festivals)
  
  def assign_chaturthi_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # SANKATAHARA chaturthi
      if self.panchaanga.tithi_sunrise[d] == 18 or self.panchaanga.tithi_sunrise[d] == 19:
        ldiff_moonrise_yest = (Graha(Graha.MOON).get_longitude(self.panchaanga.jd_moonrise[d - 1]) - Graha(
          Graha.SUN).get_longitude(self.panchaanga.jd_moonrise[d - 1])) % 360
        ldiff_moonrise = (Graha(Graha.MOON).get_longitude(self.panchaanga.jd_moonrise[d]) - Graha(Graha.SUN).get_longitude(
          self.panchaanga.jd_moonrise[d])) % 360
        ldiff_moonrise_tmrw = (Graha(Graha.MOON).get_longitude(self.panchaanga.jd_moonrise[d + 1]) - Graha(
          Graha.SUN).get_longitude(self.panchaanga.jd_moonrise[d + 1])) % 360
        tithi_moonrise_yest = int(1 + floor(ldiff_moonrise_yest / 12.0))
        tithi_moonrise = int(1 + floor(ldiff_moonrise / 12.0))
        tithi_moonrise_tmrw = int(1 + floor(ldiff_moonrise_tmrw / 12.0))

        _m = self.panchaanga.lunar_month[d]
        if floor(_m) != _m:
          _m = 13  # Adhika masa
        chaturthi_name = names.NAMES['SANKATAHARA_CHATURTHI_NAMES']['hk'][_m] + '-mahAgaNapati '

        if tithi_moonrise == 19:
          # otherwise yesterday would have already been assigned
          if tithi_moonrise_yest != 19:
            chaturthi_name = '%s%s' % ('aGgArakI~' if self.panchaanga.weekday[d] == 2 else '', chaturthi_name)
            self.panchaanga.festivals[d].append(chaturthi_name + 'saGkaTahara-caturthI-vratam')
            # shravana krishna chaturthi
            if self.panchaanga.lunar_month[d] == 5:
              chaturthi_name = '%s%s' % ('aGgArakI~' if self.panchaanga.weekday[d] == 2 else '', chaturthi_name)
              self.panchaanga.festivals[d][-1] = chaturthi_name + 'mahAsaGkaTahara-caturthI-vratam'
        elif tithi_moonrise_tmrw == 19:
          chaturthi_name = '%s%s' % ('aGgArakI~' if self.panchaanga.weekday[d + 1] == 2 else '', chaturthi_name)
          self.panchaanga.festivals[d + 1].append(chaturthi_name + 'saGkaTahara-caturthI-vratam')
          # self.panchaanga.lunar_month[d] and[d + 1] are same, so checking [d] is enough
          if self.panchaanga.lunar_month[d] == 5:
            chaturthi_name = '%s%s' % ('aGgArakI~' if self.panchaanga.weekday[d] == 2 else '', chaturthi_name)
            self.panchaanga.festivals[d + 1][-1] = chaturthi_name + 'mahAsaGkaTahara-caturthI-vratam'
        else:
          if tithi_moonrise_yest != 19:
            if tithi_moonrise == 18 and tithi_moonrise_tmrw == 20:
              # No vyApti on either day -- pick parA, i.e. next day.
              chaturthi_name = '%s%s' % ('aGgArakI~' if self.panchaanga.weekday[d + 1] == 2 else '', chaturthi_name)
              self.panchaanga.festivals[d + 1].append(chaturthi_name + 'saGkaTahara-caturthI-vratam')
              # shravana krishna chaturthi
              if self.panchaanga.lunar_month[d] == 5:
                chaturthi_name = '%s%s' % (
                  'aGgArakI~' if self.panchaanga.weekday[d + 1] == 2 else '', chaturthi_name)
                self.panchaanga.festivals[d + 1][-1] = chaturthi_name + 'mahAsaGkaTahara-caturthI-vratam'

  def assign_shasthi_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)
      # # SHASHTHI Vratam
      # Check only for Adhika maasa here...
      festival_name = 'SaSThI-vratam'
      if self.panchaanga.lunar_month[d] == 8:
        festival_name = 'skanda' + festival_name
      elif self.panchaanga.lunar_month[d] == 4:
        festival_name = 'kumAra-' + festival_name
      elif self.panchaanga.lunar_month[d] == 6:
        festival_name = 'SaSThIdEvI-' + festival_name
      elif self.panchaanga.lunar_month[d] == 9:
        festival_name = 'subrahmaNya-' + festival_name

      if self.panchaanga.tithi_sunrise[d] == 5 or self.panchaanga.tithi_sunrise[d] == 6:
        angams = self.panchaanga.get_angams_for_kaalas(d, lambda x: NakshatraDivision(x,
                                                                           ayanamsha_id=self.panchaanga.ayanamsha_id).get_tithi(),
                                            'madhyaahna')
        if angams[0] == 6 or angams[1] == 6:
          if festival_name in self.panchaanga.fest_days:
            # Check if yesterday was assigned already
            # to this puurvaviddha festival!
            if self.panchaanga.fest_days[festival_name].count(d - 1) == 0:
              self.add_festival(festival_name, d, debug_festivals)
          else:
            self.add_festival(festival_name, d, debug_festivals)
        elif angams[2] == 6 or angams[3] == 6:
          self.add_festival(festival_name, d + 1, debug_festivals)
        else:
          # This means that the correct angam did not
          # touch the kaala on either day!
          # sys.stderr.write('Could not assign puurvaviddha day for %s!\
          # Please check for unusual cases.\n' % festival_name)
          if angams[2] == 6 + 1 or angams[3] == 6 + 1:
            # Need to assign a day to the festival here
            # since the angam did not touch kaala on either day
            # BUT ONLY IF YESTERDAY WASN'T ALREADY ASSIGNED,
            # THIS BEING PURVAVIDDHA
            # Perhaps just need better checking of
            # conditions instead of this fix
            if festival_name in self.panchaanga.fest_days:
              if self.panchaanga.fest_days[festival_name].count(d - 1) == 0:
                self.add_festival(festival_name, d, debug_festivals)
            else:
              self.add_festival(festival_name, d, debug_festivals)

  def assign_vishesha_saptami(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # SPECIAL SAPTAMIs
      if self.panchaanga.weekday[d] == 0 and (self.panchaanga.tithi_sunrise[d] % 15) == 7:
        festival_name = 'bhAnusaptamI'
        if self.panchaanga.tithi_sunrise[d] == 7:
          festival_name = 'vijayA' + '~' + festival_name
        if self.panchaanga.nakshatram_sunrise[d] == 27:
          # Even more auspicious!
          festival_name += '★'
        self.add_festival(festival_name, d, debug_festivals)

      if NakshatraDivision(self.panchaanga.jd_sunrise[d], ayanamsha_id=self.panchaanga.ayanamsha_id).get_angam(
          zodiac.NAKSHATRA_PADA) == 49 and \
          self.panchaanga.tithi_sunrise[d] == 7:
        self.add_festival('bhadrA~saptamI', d, debug_festivals)

      if self.panchaanga.solar_month_end_time[d] is not None:
        # we have a Sankranti!
        if self.panchaanga.tithi_sunrise[d] == 7:
          self.add_festival('mahAjayA~saptamI', d, debug_festivals)

  def assign_ekadashi_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # checking @ 6am local - can we do any better?
      local_time = tz(self.panchaanga.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
      # compute offset from UTC in hours
      tz_off = (datetime.utcoffset(local_time).days * 86400 +
                datetime.utcoffset(local_time).seconds) / 3600.0

      # EKADASHI Vratam
      # One of two consecutive tithis must appear @ sunrise!

      if (self.panchaanga.tithi_sunrise[d] % 15) == 10 or (self.panchaanga.tithi_sunrise[d] % 15) == 11:
        yati_ekadashi_fday = smaarta_ekadashi_fday = vaishnava_ekadashi_fday = None
        ekadashi_tithi_days = [x % 15 for x in self.panchaanga.tithi_sunrise[d:d + 3]]
        if self.panchaanga.tithi_sunrise[d] > 15:
          ekadashi_paksha = 'krishna'
        else:
          ekadashi_paksha = 'shukla'
        if ekadashi_tithi_days in [[11, 11, 12], [10, 12, 12]]:
          smaarta_ekadashi_fday = d + 1
          tithi_arunodayam = NakshatraDivision(
            self.panchaanga.jd_sunrise[d + 1] - (1 / 15.0) * (self.panchaanga.jd_sunrise[d + 1] - self.panchaanga.jd_sunrise[d]),
            ayanamsha_id=self.panchaanga.ayanamsha_id).get_tithi()
          if tithi_arunodayam % 15 == 10:
            vaishnava_ekadashi_fday = d + 2
          else:
            vaishnava_ekadashi_fday = d + 1
        elif ekadashi_tithi_days in [[10, 12, 13], [11, 12, 13], [11, 12, 12], [11, 12, 14]]:
          smaarta_ekadashi_fday = d
          tithi_arunodayam = NakshatraDivision(
            self.panchaanga.jd_sunrise[d] - (1 / 15.0) * (self.panchaanga.jd_sunrise[d] - self.panchaanga.jd_sunrise[d - 1]),
            ayanamsha_id=self.panchaanga.ayanamsha_id).get_tithi()
          if tithi_arunodayam % 15 == 11 and ekadashi_tithi_days in [[11, 12, 13], [11, 12, 14]]:
            vaishnava_ekadashi_fday = d
          else:
            vaishnava_ekadashi_fday = d + 1
        elif ekadashi_tithi_days in [[10, 11, 13], [11, 11, 13]]:
          smaarta_ekadashi_fday = d
          vaishnava_ekadashi_fday = d + 1
          yati_ekadashi_fday = d + 1
        else:
          pass
          # These combinations are taken care of, either in the past or future.
          # if ekadashi_tithi_days == [10, 11, 12]:
          #     logging.debug('Not assigning. Maybe tomorrow?')
          # else:
          #     logging.debug(('!!', d, ekadashi_tithi_days))

        if yati_ekadashi_fday == smaarta_ekadashi_fday == vaishnava_ekadashi_fday is None:
          # Must have already assigned
          pass
        elif yati_ekadashi_fday is None:
          if smaarta_ekadashi_fday == vaishnava_ekadashi_fday:
            # It's sarva ekadashi
            self.add_festival(
              'sarva-' + names.get_ekadashi_name(ekadashi_paksha, self.panchaanga.lunar_month[d]),
              smaarta_ekadashi_fday, debug_festivals)
            if ekadashi_paksha == 'shukla':
              if self.panchaanga.solar_month[d] == 9:
                self.add_festival('sarva-vaikuNTha-EkAdazI', smaarta_ekadashi_fday, debug_festivals)
          else:
            self.add_festival(
              'smArta-' + names.get_ekadashi_name(ekadashi_paksha, self.panchaanga.lunar_month[d]),
              smaarta_ekadashi_fday, debug_festivals)
            self.add_festival(
              'vaiSNava-' + names.get_ekadashi_name(ekadashi_paksha, self.panchaanga.lunar_month[d]),
              vaishnava_ekadashi_fday, debug_festivals)
            if ekadashi_paksha == 'shukla':
              if self.panchaanga.solar_month[d] == 9:
                self.add_festival('smArta-vaikuNTha-EkAdazI', smaarta_ekadashi_fday, debug_festivals)
                self.add_festival('vaiSNava-vaikuNTha-EkAdazI', vaishnava_ekadashi_fday,
                                  debug_festivals)
        else:
          self.add_festival('smArta-' + names.get_ekadashi_name(ekadashi_paksha,
                                                                self.panchaanga.lunar_month[d]) + ' (gRhastha)',
                            smaarta_ekadashi_fday, debug_festivals)
          self.add_festival('smArta-' + names.get_ekadashi_name(ekadashi_paksha, self.panchaanga.lunar_month[
            d]) + ' (sannyastha)', yati_ekadashi_fday, debug_festivals)
          self.add_festival(
            'vaiSNava-' + names.get_ekadashi_name(ekadashi_paksha, self.panchaanga.lunar_month[d]),
            vaishnava_ekadashi_fday, debug_festivals)
          if self.panchaanga.solar_month[d] == 9:
            if ekadashi_paksha == 'shukla':
              self.add_festival('smArta-vaikuNTha-EkAdazI (gRhastha)', smaarta_ekadashi_fday,
                                debug_festivals)
              self.add_festival('smArta-vaikuNTha-EkAdazI (sannyastha)', yati_ekadashi_fday,
                                debug_festivals)
              self.add_festival('vaiSNava-vaikuNTha-EkAdazI', vaishnava_ekadashi_fday, debug_festivals)

        if yati_ekadashi_fday == smaarta_ekadashi_fday == vaishnava_ekadashi_fday is None:
          # Must have already assigned
          pass
        else:
          if self.panchaanga.solar_month[d] == 8 and ekadashi_paksha == 'shukla':
            # self.add_festival('guruvAyupura-EkAdazI', smaarta_ekadashi_fday, debug_festivals)
            self.add_festival('guruvAyupura-EkAdazI', vaishnava_ekadashi_fday, debug_festivals)
            self.add_festival('kaizika-EkAdazI', vaishnava_ekadashi_fday, debug_festivals)

          # Harivasara Computation
          if ekadashi_paksha == 'shukla':

            harivasara_end = brentq(
              lambda x: NakshatraDivision(x, ayanamsha_id=self.panchaanga.ayanamsha_id).get_angam_float(
                zodiac.TITHI_PADA, -45, False),
              self.panchaanga.jd_sunrise[smaarta_ekadashi_fday] - 2,
              self.panchaanga.jd_sunrise[smaarta_ekadashi_fday] + 2)
          else:
            harivasara_end = brentq(
              lambda x: NakshatraDivision(x, ayanamsha_id=self.panchaanga.ayanamsha_id).get_angam_float(
                angam_type=zodiac.TITHI_PADA, offset_angas=-105, debug=False),
              self.panchaanga.jd_sunrise[smaarta_ekadashi_fday] - 2,
              self.panchaanga.jd_sunrise[smaarta_ekadashi_fday] + 2)
          [_y, _m, _d, _t] = temporal.jd_to_utc_gregorian(harivasara_end + (tz_off / 24.0))
          hariv_end_time = Hour(temporal.jd_to_utc_gregorian(harivasara_end + (tz_off / 24.0))[3]).toString(
            format=self.panchaanga.fmt)
          fday_hv = temporal.utc_gregorian_to_jd(_y, _m, _d, 0) - self.panchaanga.jd_start_utc + 1
          self.panchaanga.festivals[int(fday_hv)].append(
            'harivAsaraH\\textsf{%s}{\\RIGHTarrow}\\textsf{%s}' % ('', hariv_end_time))

  def assign_mahadwadashi(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)
      # 8 MAHA DWADASHIS
      if (self.panchaanga.tithi_sunrise[d] % 15) == 11 and (self.panchaanga.tithi_sunrise[d + 1] % 15) == 11:
        self.add_festival('unmIlanI~mahAdvAdazI', d + 1, debug_festivals)

      if (self.panchaanga.tithi_sunrise[d] % 15) == 12 and (self.panchaanga.tithi_sunrise[d + 1] % 15) == 12:
        self.add_festival('vyaJjulI~mahAdvAdazI', d, debug_festivals)

      if (self.panchaanga.tithi_sunrise[d] % 15) == 11 and (self.panchaanga.tithi_sunrise[d + 1] % 15) == 13:
        self.add_festival('trisparzA~mahAdvAdazI', d, debug_festivals)

      if (self.panchaanga.tithi_sunrise[d] % 15) == 0 and (self.panchaanga.tithi_sunrise[d + 1] % 15) == 0:
        # Might miss out on those parva days right after Dec 31!
        if (d - 3) > 0:
          self.add_festival('pakSavardhinI~mahAdvAdazI', d - 3, debug_festivals)

      if self.panchaanga.nakshatram_sunrise[d] == 4 and (self.panchaanga.tithi_sunrise[d] % 15) == 12:
        self.add_festival('pApanAzinI~mahAdvAdazI', d, debug_festivals)

      if self.panchaanga.nakshatram_sunrise[d] == 7 and (self.panchaanga.tithi_sunrise[d] % 15) == 12:
        self.add_festival('jayantI~mahAdvAdazI', d, debug_festivals)

      if self.panchaanga.nakshatram_sunrise[d] == 8 and (self.panchaanga.tithi_sunrise[d] % 15) == 12:
        self.add_festival('jayA~mahAdvAdazI', d, debug_festivals)

      if self.panchaanga.nakshatram_sunrise[d] == 8 and (self.panchaanga.tithi_sunrise[d] % 15) == 12 and self.panchaanga.lunar_month[d] == 12:
        # Better checking needed (for other than sunrise).
        # Last occurred on 27-02-1961 - pushya nakshatra and phalguna krishna dvadashi (or shukla!?)
        self.add_festival('gOvinda~mahAdvAdazI', d, debug_festivals)

      if (self.panchaanga.tithi_sunrise[d] % 15) == 12:
        if self.panchaanga.nakshatram_sunrise[d] in [21, 22, 23]:
          # We have a dwadashi near shravana, check for Shravana sparsha
          for td in self.panchaanga.tithi_data[d:d + 2]:
            (t12, t12_end) = td[0]
            if t12_end is None:
              continue
            if (t12 % 15) == 11:
              if NakshatraDivision(t12_end, ayanamsha_id=self.panchaanga.ayanamsha_id).get_angam(
                  zodiac.NAKSHATRAM) == 22:
                if (self.panchaanga.tithi_sunrise[d] % 15) == 12 and (self.panchaanga.tithi_sunrise[d + 1] % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d, debug_festivals)
                elif (self.panchaanga.tithi_sunrise[d] % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d, debug_festivals)
                elif (self.panchaanga.tithi_sunrise[d + 1] % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d + 1, debug_festivals)
            if (t12 % 15) == 12:
              if NakshatraDivision(t12_end, ayanamsha_id=self.panchaanga.ayanamsha_id).get_angam(
                  zodiac.NAKSHATRAM) == 22:
                if (self.panchaanga.tithi_sunrise[d] % 15) == 12 and (self.panchaanga.tithi_sunrise[d + 1] % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d, debug_festivals)
                elif (self.panchaanga.tithi_sunrise[d] % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d, debug_festivals)
                elif (self.panchaanga.tithi_sunrise[d + 1] % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d + 1, debug_festivals)

      if self.panchaanga.nakshatram_sunrise[d] == 22 and (self.panchaanga.tithi_sunrise[d] % 15) == 12:
        self.add_festival('vijayA/zravaNa-mahAdvAdazI', d, debug_festivals)

  def assign_pradosha_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)
      # compute offset from UTC in hours
      # PRADOSHA Vratam
      pref = ''
      if self.panchaanga.tithi_sunrise[d] in (12, 13, 27, 28):
        tithi_sunset = NakshatraDivision(self.panchaanga.jd_sunset[d], ayanamsha_id=self.panchaanga.ayanamsha_id).get_tithi() % 15
        tithi_sunset_tmrw = NakshatraDivision(self.panchaanga.jd_sunset[d + 1],
                                              ayanamsha_id=self.panchaanga.ayanamsha_id).get_tithi() % 15
        if tithi_sunset <= 13 and tithi_sunset_tmrw != 13:
          fday = d
        elif tithi_sunset_tmrw == 13:
          fday = d + 1
        if self.panchaanga.weekday[fday] == 1:
          pref = 'sOma-'
        elif self.panchaanga.weekday[fday] == 6:
          pref = 'zani-'
        self.add_festival(pref + 'pradOSa-vratam', fday, debug_festivals)

  def assign_amavasya_yoga(self, debug_festivals=False):
    if 'amAvAsyA' not in self.panchaanga.fest_days:
      logging.error('Must compute amAvAsyA before coming here!')
    else:
      ama_days = self.panchaanga.fest_days['amAvAsyA']
      for d in ama_days:
        # Get Name
        if self.panchaanga.lunar_month[d] == 6:
          pref = '(%s) mahAlaya ' % (
            names.get_chandra_masa(self.panchaanga.lunar_month[d], names.NAMES, 'hk', visarga=False))
        elif self.panchaanga.solar_month[d] == 4:
          pref = '%s (kaTaka) ' % (
            names.get_chandra_masa(self.panchaanga.lunar_month[d], names.NAMES, 'hk', visarga=False))
        elif self.panchaanga.solar_month[d] == 10:
          pref = 'mauni (%s/makara) ' % (
            names.get_chandra_masa(self.panchaanga.lunar_month[d], names.NAMES, 'hk', visarga=False))
        else:
          pref = names.get_chandra_masa(self.panchaanga.lunar_month[d], names.NAMES, 'hk',
                                        visarga=False) + '-'

        ama_nakshatram_today = self.panchaanga.get_angams_for_kaalas(d, lambda x: NakshatraDivision(x,
                                                                                         ayanamsha_id=self.panchaanga.ayanamsha_id).get_nakshatram(),
                                                          'aparaahna')[:2]
        suff = ''
        # Assign
        if 23 in ama_nakshatram_today and self.panchaanga.lunar_month[d] == 10:
          suff = ' (alabhyam–zraviSThA)'
        elif 24 in ama_nakshatram_today and self.panchaanga.lunar_month[d] == 10:
          suff = ' (alabhyam–zatabhiSak)'
        elif ama_nakshatram_today[0] in [15, 16, 17, 6, 7, 8, 23, 24, 25]:
          suff = ' (alabhyam–%s)' % names.NAMES['NAKSHATRAM_NAMES']['hk'][ama_nakshatram_today[0]]
        elif ama_nakshatram_today[1] in [15, 16, 17, 6, 7, 8, 23, 24, 25]:
          suff = ' (alabhyam–%s)' % names.NAMES['NAKSHATRAM_NAMES']['hk'][ama_nakshatram_today[1]]
        if self.panchaanga.weekday[d] in [1, 2, 4]:
          if suff == '':
            suff = ' (alabhyam–puSkalA)'
          else:
            suff = suff.replace(')', ', puSkalA)')
        self.add_festival(pref + 'amAvAsyA' + suff, d, debug_festivals)
    if 'amAvAsyA' in self.panchaanga.fest_days:
      del self.panchaanga.fest_days['amAvAsyA']

    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # SOMAMAVASYA
      if self.panchaanga.tithi_sunrise[d] == 30 and self.panchaanga.weekday[d] == 1:
        self.add_festival('sOmavatI amAvAsyA', d, debug_festivals)

      # AMA-VYATIPATA YOGAH
      # श्रवणाश्विधनिष्ठार्द्रानागदैवतमापतेत् ।
      # रविवारयुतामायां व्यतीपातः स उच्यते ॥
      # व्यतीपाताख्ययोगोऽयं शतार्कग्रहसन्निभः ॥
      # “In Mahabharata, if on a Sunday, Amavasya and one of the stars –
      # Sravanam, Asvini, Avittam, Tiruvadirai or Ayilyam, occurs, then it is called ‘Vyatipatam’.
      # This Vyatipata yoga is equal to a hundred Surya grahanas in merit.”
      tithi_sunset = NakshatraDivision(self.panchaanga.jd_sunset[d], ayanamsha_id=self.panchaanga.ayanamsha_id).get_angam(
        zodiac.TITHI)
      if self.panchaanga.weekday[d] == 0 and (self.panchaanga.tithi_sunrise[d] == 30 or tithi_sunset == 30):
        # AMAVASYA on a Sunday
        if (self.panchaanga.nakshatram_sunrise[d] in [1, 6, 9, 22, 23] and self.panchaanga.tithi_sunrise[d] == 30) or \
            (tithi_sunset == 30 and NakshatraDivision(self.panchaanga.jd_sunset[d],
                                                      ayanamsha_id=self.panchaanga.ayanamsha_id).get_angam(
              zodiac.NAKSHATRAM) in [
               1, 6, 9, 22, 23]):
          festival_name = 'vyatIpAta-yOgaH (alabhyam)'
          self.add_festival(festival_name, d, debug_festivals)
          logging.debug('* %d-%02d-%02d> %s!' % (y, m, dt, festival_name))

  def assign_chandra_darshanam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)
      # Chandra Darshanam
      if self.panchaanga.tithi_sunrise[d] == 1 or self.panchaanga.tithi_sunrise[d] == 2:
        tithi_sunset = NakshatraDivision(self.panchaanga.jd_sunset[d], ayanamsha_id=self.panchaanga.ayanamsha_id).get_tithi()
        tithi_sunset_tmrw = NakshatraDivision(self.panchaanga.jd_sunset[d + 1], ayanamsha_id=self.panchaanga.ayanamsha_id).get_tithi()
        # if tithi_sunset <= 2 and tithi_sunset_tmrw != 2:
        if tithi_sunset <= 2:
          if tithi_sunset == 1:
            self.panchaanga.festivals[d + 1].append('candra-darzanam')
          else:
            self.panchaanga.festivals[d].append('candra-darzanam')
        elif tithi_sunset_tmrw == 2:
          self.panchaanga.festivals[d + 1].append('candra-darzanam')

  def assign_vishesha_trayodashi(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)
      # VARUNI TRAYODASHI
      if self.panchaanga.lunar_month[d] == 12 and self.panchaanga.tithi_sunrise[d] == 28:
        if NakshatraDivision(self.panchaanga.jd_sunrise[d], ayanamsha_id=self.panchaanga.ayanamsha_id).get_angam(
            zodiac.NAKSHATRAM) == 24:
          vtr_name = 'vAruNI~trayOdazI'
          if self.panchaanga.weekday[d] == 6:
            vtr_name = 'mahA' + vtr_name
            if NakshatraDivision(self.panchaanga.jd_sunrise[d], ayanamsha_id=self.panchaanga.ayanamsha_id).get_angam(
                zodiac.YOGA) == 23:
              vtr_name = 'mahA' + vtr_name
          self.add_festival(vtr_name, d, debug_festivals)


class VaraFestivalAssigner(FestivalAssigner):
  def assign_all(self, debug_festivals=False):
    self.assign_bhriguvara_subrahmanya_vratam(debug_festivals=debug_festivals)
    self.assign_masa_vara_yoga_vratam(debug_festivals=debug_festivals)
    self.assign_nakshatra_vara_yoga_vratam(debug_festivals=debug_festivals)
    self.assign_ayushman_bava_saumya_yoga(debug_festivals=debug_festivals)
    self.assign_tithi_vara_yoga(debug_festivals=debug_festivals)


  def assign_bhriguvara_subrahmanya_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # BHRGUVARA SUBRAHMANYA VRATAM
      if self.panchaanga.solar_month[d] == 7 and self.panchaanga.weekday[d] == 5:
        festival_name = 'bhRguvAra-subrahmaNya-vratam'
        if festival_name not in self.panchaanga.fest_days:
          # only the first bhRguvAra of tulA mAsa is considered (skAnda purANam)
          # https://youtu.be/rgXwyo0L3i8?t=222
          self.add_festival(festival_name, d, debug_festivals)

  def assign_masa_vara_yoga_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # KRTTIKA SOMAVASARA
      if self.panchaanga.lunar_month[d] == 8 and self.panchaanga.weekday[d] == 1:
        self.add_festival('kRttikA~sOmavAsaraH', d, debug_festivals)

      # SOLAR MONTH-WEEKDAY FESTIVALS
      for (mwd_fest_m, mwd_fest_wd, mwd_fest_name) in ((5, 0, 'ta:AvaNi~JAyir2r2ukkizhamai'),
                                                       (6, 6, 'ta:puraTTAci~can2ikkizhamai'),
                                                       (8, 0, 'ta:kArttigai~JAyir2r2ukkizhamai'),
                                                       (4, 5, 'ta:ADi~veLLikkizhamai'),
                                                       (10, 5, 'ta:tai~veLLikkizhamai'),
                                                       (11, 2, 'ta:mAci~cevvAy')):
        if self.panchaanga.solar_month[d] == mwd_fest_m and self.panchaanga.weekday[d] == mwd_fest_wd:
          self.add_festival(mwd_fest_name, d, debug_festivals)

  def assign_tithi_vara_yoga(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # MANGALA-CHATURTHI
      if self.panchaanga.weekday[d] == 2 and (self.panchaanga.tithi_sunrise[d] % 15) == 4:
        festival_name = 'aGgAraka-caturthI'
        if self.panchaanga.tithi_sunrise[d] == 4:
          festival_name = 'sukhA' + '~' + festival_name
        self.add_festival(festival_name, d, debug_festivals)

      # KRISHNA ANGARAKA CHATURDASHI
      if self.panchaanga.weekday[d] == 2 and self.panchaanga.tithi_sunrise[d] == 29:
        # Double-check rule. When should the vyApti be?
        self.add_festival('kRSNAGgAraka-caturdazI-puNyakAlaH/yamatarpaNam', d, debug_festivals)

      # BUDHASHTAMI
      if self.panchaanga.weekday[d] == 3 and (self.panchaanga.tithi_sunrise[d] % 15) == 8:
        self.add_festival('budhASTamI', d, debug_festivals)


  def assign_nakshatra_vara_yoga_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # NAKSHATRA-WEEKDAY FESTIVALS
      for (nwd_fest_n, nwd_fest_wd, nwd_fest_name) in ((13, 0, 'Adityahasta-puNyakAlaH'),
                                                       (8, 0, 'ravipuSyayOga-puNyakAlaH'),
                                                       (22, 1, 'sOmazrAvaNI-puNyakAlaH'),
                                                       (5, 1, 'sOmamRgazIrSa-puNyakAlaH'),
                                                       (1, 2, 'bhaumAzvinI-puNyakAlaH'),
                                                       (6, 2, 'bhaumArdrA-puNyakAlaH'),
                                                       (17, 3, 'budhAnurAdhA-puNyakAlaH'),
                                                       (8, 4, 'gurupuSya-puNyakAlaH'),
                                                       (27, 5, 'bhRgurEvatI-puNyakAlaH'),
                                                       (4, 6, 'zanirOhiNI-puNyakAlaH'),
                                                       ):
        n_prev = ((nwd_fest_n - 2) % 27) + 1
        if (self.panchaanga.nakshatram_sunrise[d] == nwd_fest_n or self.panchaanga.nakshatram_sunrise[d] == n_prev) and self.panchaanga.weekday[
          d] == nwd_fest_wd:
          # Is it necessarily only at sunrise?
          angams = self.panchaanga.get_angams_for_kaalas(d, lambda x: NakshatraDivision(x,
                                                                             ayanamsha_id=self.panchaanga.ayanamsha_id).get_nakshatram(),
                                              'dinamaana')
          if any(x == nwd_fest_n for x in [self.panchaanga.nakshatram_sunrise[d], angams[0], angams[1]]):
            self.add_festival(nwd_fest_name, d, debug_festivals)


  def assign_ayushman_bava_saumya_yoga(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # AYUSHMAN BAVA SAUMYA
      if self.panchaanga.weekday[d] == 3 and NakshatraDivision(self.panchaanga.jd_sunrise[d], ayanamsha_id=self.panchaanga.ayanamsha_id).get_angam(
          zodiac.YOGA) == 3:
        if NakshatraDivision(self.panchaanga.jd_sunrise[d], ayanamsha_id=self.panchaanga.ayanamsha_id).get_angam(
            zodiac.KARANAM) in list(range(2, 52, 7)):
          self.add_festival('AyuSmAn-bava-saumya', d, debug_festivals)
      if self.panchaanga.weekday[d] == 3 and NakshatraDivision(self.panchaanga.jd_sunset[d], ayanamsha_id=self.panchaanga.ayanamsha_id).get_angam(
          zodiac.YOGA) == 3:
        if NakshatraDivision(self.panchaanga.jd_sunset[d], ayanamsha_id=self.panchaanga.ayanamsha_id).get_angam(
            zodiac.KARANAM) in list(range(2, 52, 7)):
          self.add_festival('AyuSmAn-bava-saumya', d, debug_festivals)

class SolarFestivalAssigner(FestivalAssigner):
  def assign_all(self, debug_festivals=False):
    self.assign_gajachhaya_yoga(debug_festivals=debug_festivals)
    self.assign_mahodaya_ardhodaya(debug_festivals=debug_festivals)
    self.assign_month_day_festivals(debug_festivals=debug_festivals)
    self.assign_ayanam(debug_festivals=debug_festivals)
    self.assign_vishesha_vyatipata(debug_festivals=debug_festivals)

  def assign_ayanam(self, debug_festivals=False):
    last_d_assigned = 0
    for d in range(1, self.panchaanga.duration + 1):

      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # checking @ 6am local - can we do any better?
      local_time = tz(self.panchaanga.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
      # compute offset from UTC in hours
      tz_off = (datetime.utcoffset(local_time).days * 86400 +
                datetime.utcoffset(local_time).seconds) / 3600.0

      # TROPICAL AYANAMS
      if self.panchaanga.solar_month_day[d] == 1:
        ayana_jd_start = \
          Graha(Graha.SUN).get_next_raashi_transit(jd_start=self.panchaanga.jd_sunrise[d],
                                                   jd_end=self.panchaanga.jd_sunrise[d] + 15,
                                                   ayanamsha_id=zodiac.Ayanamsha.ASHVINI_STARTING_0)[0][0]
        [_y, _m, _d, _t] = temporal.jd_to_utc_gregorian(ayana_jd_start + (tz_off / 24.0))
        # Reduce fday by 1 if ayana time precedes sunrise and change increment _t by 24
        fday_nirayana = int(temporal.utc_gregorian_to_jd(_y, _m, _d, 0) - self.panchaanga.jd_start_utc + 1)
        if fday_nirayana > self.panchaanga.duration:
          continue
        if ayana_jd_start < self.panchaanga.jd_sunrise[fday_nirayana]:
          fday_nirayana -= 1
          _t += 24
        ayana_time = Hour(_t).toString(format=self.panchaanga.fmt)

        self.panchaanga.festivals[fday_nirayana].append('%s\\textsf{%s}{\\RIGHTarrow}\\textsf{%s}' % (
          names.NAMES['RTU_MASA_NAMES'][self.panchaanga.script][self.panchaanga.solar_month[d]], '', ayana_time))
        self.panchaanga.tropical_month_end_time[fday_nirayana] = ayana_jd_start
        for i in range(last_d_assigned + 1, fday_nirayana + 1):
          self.panchaanga.tropical_month[i] = self.panchaanga.solar_month[d]
        last_d_assigned = fday_nirayana
        if self.panchaanga.solar_month[d] == 3:
          if self.panchaanga.jd_sunset[fday_nirayana] < ayana_jd_start < self.panchaanga.jd_sunset[fday_nirayana + 1]:
            self.panchaanga.festivals[fday_nirayana].append('dakSiNAyana-puNyakAlaH')
          else:
            self.panchaanga.festivals[fday_nirayana - 1].append('dakSiNAyana-puNyakAlaH')
        if self.panchaanga.solar_month[d] == 9:
          if self.panchaanga.jd_sunset[fday_nirayana] < ayana_jd_start < self.panchaanga.jd_sunset[fday_nirayana + 1]:
            self.panchaanga.festivals[fday_nirayana + 1].append('uttarAyaNa-puNyakAlaH/mitrOtsavaH')
          else:
            self.panchaanga.festivals[fday_nirayana].append('uttarAyaNa-puNyakAlaH/mitrOtsavaH')
    for i in range(last_d_assigned + 1, self.panchaanga.duration + 1):
      self.panchaanga.tropical_month[i] = (self.panchaanga.solar_month[last_d_assigned] % 12) + 1

  def assign_month_day_festivals(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)
      ####################
      # Festival details #
      ####################

      # KARADAIYAN NOMBU
      if self.panchaanga.solar_month[d] == 12 and self.panchaanga.solar_month_day[d] == 1:
        if NakshatraDivision(self.panchaanga.jd_sunrise[d] - (1 / 15.0) * (self.panchaanga.jd_sunrise[d] - self.panchaanga.jd_sunrise[d - 1]),
                             ayanamsha_id=self.panchaanga.ayanamsha_id).get_solar_rashi() == 12:
          # If kumbha prevails two ghatikAs before sunrise, nombu can be done in the early morning itself, else, previous night.
          self.panchaanga.fest_days['ta:kAraDaiyAn2 nOn2bu'] = [d - 1]
        else:
          self.panchaanga.fest_days['ta:kAraDaiyAn2 nOn2bu'] = [d]

      # KUCHELA DINAM
      if self.panchaanga.solar_month[d] == 9 and self.panchaanga.solar_month_day[d] <= 7 and self.panchaanga.weekday[d] == 3:
        self.panchaanga.fest_days['kucEla-dinam'] = [d]

      # MESHA SANKRANTI
      if self.panchaanga.solar_month[d] == 1 and self.panchaanga.solar_month[d - 1] == 12:
        # distance from prabhava
        samvatsara_id = (y - 1568) % 60 + 1
        new_yr = 'mESa-saGkrAntiH' + '~(' + names.NAMES['SAMVATSARA_NAMES']['hk'][
          (samvatsara_id % 60) + 1] + \
                 '-' + 'saMvatsaraH' + ')'
        # self.panchaanga.fest_days[new_yr] = [d]
        self.add_festival(new_yr, d, debug_festivals)
        self.add_festival('paJcAGga-paThanam', d, debug_festivals)

  def assign_vishesha_vyatipata(self, debug_festivals=False):
    vs_list = self.panchaanga.fest_days['vyatIpAta-zrAddham']
    for d in vs_list:
      if self.panchaanga.solar_month[d] == 9:
        self.panchaanga.fest_days['vyatIpAta-zrAddham'].remove(d)
        festival_name = 'mahAdhanurvyatIpAta-zrAddham'
        self.add_festival(festival_name, d, debug_festivals)
      elif self.panchaanga.solar_month[d] == 6:
        self.panchaanga.fest_days['vyatIpAta-zrAddham'].remove(d)
        festival_name = 'mahAvyatIpAta-zrAddham'
        self.add_festival(festival_name, d, debug_festivals)

  def assign_gajachhaya_yoga(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # checking @ 6am local - can we do any better?
      local_time = tz(self.panchaanga.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
      # compute offset from UTC in hours
      tz_off = (datetime.utcoffset(local_time).days * 86400 +
                datetime.utcoffset(local_time).seconds) / 3600.0
      # GAJACHHAYA YOGA
      if self.panchaanga.solar_month[d] == 6 and self.panchaanga.solar_month_day[d] == 1:
        moon_magha_jd_start = moon_magha_jd_start = t28_start = None
        moon_magha_jd_end = moon_magha_jd_end = t28_end = None
        moon_hasta_jd_start = moon_hasta_jd_start = t30_start = None
        moon_hasta_jd_end = moon_hasta_jd_end = t30_end = None

        sun_hasta_jd_start, sun_hasta_jd_end = AngaSpan.find(
          self.panchaanga.jd_sunrise[d], self.panchaanga.jd_sunrise[d] + 30, zodiac.SOLAR_NAKSH, 13,
          ayanamsha_id=self.panchaanga.ayanamsha_id).to_tuple()

        moon_magha_jd_start, moon_magha_jd_end = AngaSpan.find(
          sun_hasta_jd_start - 2, sun_hasta_jd_end + 2, zodiac.NAKSHATRAM, 10,
          ayanamsha_id=self.panchaanga.ayanamsha_id).to_tuple()
        if all([moon_magha_jd_start, moon_magha_jd_end]):
          t28_start, t28_end = AngaSpan.find(
            moon_magha_jd_start - 3, moon_magha_jd_end + 3, zodiac.TITHI, 28,
            ayanamsha_id=self.panchaanga.ayanamsha_id).to_tuple()

        moon_hasta_jd_start, moon_hasta_jd_end = AngaSpan.find(
          sun_hasta_jd_start - 1, sun_hasta_jd_end + 1, zodiac.NAKSHATRAM, 13,
          ayanamsha_id=self.panchaanga.ayanamsha_id).to_tuple()
        if all([moon_hasta_jd_start, moon_hasta_jd_end]):
          t30_start, t30_end = AngaSpan.find(
            sun_hasta_jd_start - 1, sun_hasta_jd_end + 1, zodiac.TITHI, 30,
            ayanamsha_id=self.panchaanga.ayanamsha_id).to_tuple()

        gc_28 = gc_30 = False

        if all([sun_hasta_jd_start, moon_magha_jd_start, t28_start]):
          # We have a GC yoga
          gc_28_start = max(sun_hasta_jd_start, moon_magha_jd_start, t28_start)
          gc_28_end = min(sun_hasta_jd_end, moon_magha_jd_end, t28_end)

          if gc_28_start < gc_28_end:
            gc_28 = True

        if all([sun_hasta_jd_start, moon_hasta_jd_start, t30_start]):
          # We have a GC yoga
          gc_30_start = max(sun_hasta_jd_start, moon_hasta_jd_start, t30_start)
          gc_30_end = min(sun_hasta_jd_end, moon_hasta_jd_end, t30_end)

          if gc_30_start < gc_30_end:
            gc_30 = True

      if self.panchaanga.solar_month[d] == 6 and (gc_28 or gc_30):
        if gc_28:
          gc_28_start += tz_off / 24.0
          gc_28_end += tz_off / 24.0
          # sys.stderr.write('28: (%f, %f)\n' % (gc_28_start, gc_28_end))
          gc_28_d = 1 + floor(gc_28_start - self.panchaanga.jd_start_utc)
          t1 = Hour(temporal.jd_to_utc_gregorian(gc_28_start)[3]).toString(format=self.panchaanga.fmt)

          if floor(gc_28_end - 0.5) != floor(gc_28_start - 0.5):
            # -0.5 is for the fact that julday is zero at noon always, not midnight!
            offset = 24
          else:
            offset = 0
          t2 = Hour(temporal.jd_to_utc_gregorian(gc_28_end)[3] + offset).toString(format=self.panchaanga.fmt)
          # sys.stderr.write('gajacchhaya %d\n' % gc_28_d)

          self.panchaanga.fest_days['gajacchAyA-yOgaH' +
                         '-\\textsf{' + t1 + '}{\\RIGHTarrow}\\textsf{' +
                         t2 + '}'] = [gc_28_d]
          gc_28 = False
        if gc_30:
          gc_30_start += tz_off / 24.0
          gc_30_end += tz_off / 24.0
          # sys.stderr.write('30: (%f, %f)\n' % (gc_30_start, gc_30_end))
          gc_30_d = 1 + floor(gc_30_start - self.panchaanga.jd_start_utc)
          t1 = Hour(temporal.jd_to_utc_gregorian(gc_30_start)[3]).toString(format=self.panchaanga.fmt)

          if floor(gc_30_end - 0.5) != floor(gc_30_start - 0.5):
            offset = 24
          else:
            offset = 0
          t2 = Hour(temporal.jd_to_utc_gregorian(gc_30_end)[3] + offset).toString(format=self.panchaanga.fmt)
          # sys.stderr.write('gajacchhaya %d\n' % gc_30_d)

          self.panchaanga.fest_days['gajacchAyA-yOgaH' +
                         '-\\textsf{' + t1 + '}{\\RIGHTarrow}\\textsf{' +
                         t2 + '}'] = [gc_30_d]
          gc_30 = False

  def assign_mahodaya_ardhodaya(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # MAHODAYAM
      # Can also refer youtube video https://youtu.be/0DBIwb7iaLE?list=PL_H2LUtMCKPjh63PRk5FA3zdoEhtBjhzj&t=6747
      # 4th pada of vyatipatam, 1st pada of Amavasya, 2nd pada of Shravana, Suryodaya, Bhanuvasara = Ardhodayam
      # 4th pada of vyatipatam, 1st pada of Amavasya, 2nd pada of Shravana, Suryodaya, Somavasara = Mahodayam
      sunrise_zodiac = NakshatraDivision(self.panchaanga.jd_sunrise[d], ayanamsha_id=self.panchaanga.ayanamsha_id)
      sunset_zodiac = NakshatraDivision(self.panchaanga.jd_sunset[d], ayanamsha_id=self.panchaanga.ayanamsha_id)
      if self.panchaanga.lunar_month[d] in [10, 11] and self.panchaanga.tithi_sunrise[d] == 30 or sunrise_zodiac.get_tithi() == 30:
        if sunrise_zodiac.get_angam(zodiac.YOGA) == 17 or \
            sunset_zodiac.get_angam(zodiac.YOGA) == 17 and \
            sunrise_zodiac.get_angam(zodiac.NAKSHATRAM) == 22 or \
            sunset_zodiac.get_angam(zodiac.NAKSHATRAM) == 22:
          if self.panchaanga.weekday[d] == 1:
            festival_name = 'mahOdaya-puNyakAlaH'
            self.add_festival(festival_name, d, debug_festivals)
            # logging.debug('* %d-%02d-%02d> %s!' % (y, m, dt, festival_name))
          elif self.panchaanga.weekday[d] == 0:
            festival_name = 'ardhOdaya-puNyakAlaH'
            self.add_festival(festival_name, d, debug_festivals)
            # logging.debug('* %d-%02d-%02d> %s!' % (y, m, dt, festival_name))



class EclipticFestivalAssigner(FestivalAssigner):
  def assign_all(self, debug_festivals=False):
    self.computeTransits()
    self.compute_solar_eclipses()
    self.compute_lunar_eclipses()

  def compute_solar_eclipses(self):
    jd = self.panchaanga.jd_start_utc
    while 1:
      next_eclipse_sol = self.panchaanga.city.get_solar_eclipse_time(jd_start=jd)
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(next_eclipse_sol[1][0])
      local_time = tz(self.panchaanga.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
      # checking @ 6am local - can we do any better?
      tz_off = (datetime.utcoffset(local_time).days * 86400 +
                datetime.utcoffset(local_time).seconds) / 3600.0
      # compute offset from UTC
      jd = next_eclipse_sol[1][0] + (tz_off / 24.0)
      jd_eclipse_solar_start = next_eclipse_sol[1][1] + (tz_off / 24.0)
      jd_eclipse_solar_end = next_eclipse_sol[1][4] + (tz_off / 24.0)
      # -1 is to not miss an eclipse that occurs after sunset on 31-Dec!
      if jd_eclipse_solar_start > self.panchaanga.jd_end_utc + 1:
        break
      else:
        fday = int(floor(jd) - floor(self.panchaanga.jd_start_utc) + 1)
        if (jd < (self.panchaanga.jd_sunrise[fday] + tz_off / 24.0)):
          fday -= 1
        eclipse_solar_start = temporal.jd_to_utc_gregorian(jd_eclipse_solar_start)[3]
        eclipse_solar_end = temporal.jd_to_utc_gregorian(jd_eclipse_solar_end)[3]
        if (jd_eclipse_solar_start - (tz_off / 24.0)) == 0.0 or \
            (jd_eclipse_solar_end - (tz_off / 24.0)) == 0.0:
          # Move towards the next eclipse... at least the next new
          # moon (>=25 days away)
          jd += temporal.MIN_DAYS_NEXT_ECLIPSE
          continue
        if eclipse_solar_end < eclipse_solar_start:
          eclipse_solar_end += 24
        sunrise_eclipse_day = temporal.jd_to_utc_gregorian(self.panchaanga.jd_sunrise[fday] + (tz_off / 24.0))[3]
        sunset_eclipse_day = temporal.jd_to_utc_gregorian(self.panchaanga.jd_sunset[fday] + (tz_off / 24.0))[3]
        if eclipse_solar_start < sunrise_eclipse_day:
          eclipse_solar_start = sunrise_eclipse_day
        if eclipse_solar_end > sunset_eclipse_day:
          eclipse_solar_end = sunset_eclipse_day
        solar_eclipse_str = 'sUrya-grahaNam' + \
                            '~\\textsf{' + Hour(eclipse_solar_start).toString(format=self.panchaanga.fmt) + \
                            '}{\\RIGHTarrow}\\textsf{' + Hour(eclipse_solar_end).toString(format=self.panchaanga.fmt) + '}'
        if self.panchaanga.weekday[fday] == 0:
          solar_eclipse_str = '★cUDAmaNi-' + solar_eclipse_str
        self.panchaanga.festivals[fday].append(solar_eclipse_str)
      jd = jd + temporal.MIN_DAYS_NEXT_ECLIPSE

  def compute_lunar_eclipses(self):
    # Set location
    jd = self.panchaanga.jd_start_utc
    while 1:
      next_eclipse_lun = self.panchaanga.city.get_lunar_eclipse_time(jd)
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(next_eclipse_lun[1][0])
      local_time = tz(self.panchaanga.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
      # checking @ 6am local - can we do any better? This is crucial,
      # since DST changes before 6 am
      tz_off = (datetime.utcoffset(local_time).days * 86400 +
                datetime.utcoffset(local_time).seconds) / 3600.0
      # compute offset from UTC
      jd = next_eclipse_lun[1][0] + (tz_off / 24.0)
      jd_eclipse_lunar_start = next_eclipse_lun[1][2] + (tz_off / 24.0)
      jd_eclipse_lunar_end = next_eclipse_lun[1][3] + (tz_off / 24.0)
      # -1 is to not miss an eclipse that occurs after sunset on 31-Dec!
      if jd_eclipse_lunar_start > self.panchaanga.jd_end_utc:
        break
      else:
        eclipse_lunar_start = temporal.jd_to_utc_gregorian(jd_eclipse_lunar_start)[3]
        eclipse_lunar_end = temporal.jd_to_utc_gregorian(jd_eclipse_lunar_end)[3]
        if (jd_eclipse_lunar_start - (tz_off / 24.0)) == 0.0 or \
            (jd_eclipse_lunar_end - (tz_off / 24.0)) == 0.0:
          # Move towards the next eclipse... at least the next full
          # moon (>=25 days away)
          jd += temporal.MIN_DAYS_NEXT_ECLIPSE
          continue
        fday = int(floor(jd_eclipse_lunar_start) - floor(self.panchaanga.jd_start_utc) + 1)
        # print '%%', jd, fday, self.panchaanga.jd_sunrise[fday],
        # self.panchaanga.jd_sunrise[fday-1]
        if (jd < (self.panchaanga.jd_sunrise[fday] + tz_off / 24.0)):
          fday -= 1
        if eclipse_lunar_start < temporal.jd_to_utc_gregorian(self.panchaanga.jd_sunrise[fday + 1] + tz_off / 24.0)[3]:
          eclipse_lunar_start += 24
        # print '%%', jd, fday, self.panchaanga.jd_sunrise[fday],
        # self.panchaanga.jd_sunrise[fday-1], eclipse_lunar_start,
        # eclipse_lunar_end
        jd_moonrise_eclipse_day = self.panchaanga.city.get_rising_time(julian_day_start=self.panchaanga.jd_sunrise[fday],
                                                            body=Graha.MOON) + (tz_off / 24.0)

        jd_moonset_eclipse_day = self.panchaanga.city.get_rising_time(julian_day_start=jd_moonrise_eclipse_day,
                                                           body=Graha.MOON) + (tz_off / 24.0)

        if eclipse_lunar_end < eclipse_lunar_start:
          eclipse_lunar_end += 24

        if jd_eclipse_lunar_end < jd_moonrise_eclipse_day or \
            jd_eclipse_lunar_start > jd_moonset_eclipse_day:
          # Move towards the next eclipse... at least the next full
          # moon (>=25 days away)
          jd += temporal.MIN_DAYS_NEXT_ECLIPSE
          continue

        moonrise_eclipse_day = temporal.jd_to_utc_gregorian(jd_moonrise_eclipse_day)[3]
        moonset_eclipse_day = temporal.jd_to_utc_gregorian(jd_moonset_eclipse_day)[3]

        if jd_eclipse_lunar_start < jd_moonrise_eclipse_day:
          eclipse_lunar_start = moonrise_eclipse_day
        if jd_eclipse_lunar_end > jd_moonset_eclipse_day:
          eclipse_lunar_end = moonset_eclipse_day

        if Graha(Graha.MOON).get_longitude(jd_eclipse_lunar_end) < Graha(Graha.SUN).get_longitude(
            jd_eclipse_lunar_end):
          grasta = 'rAhugrasta'
        else:
          grasta = 'kEtugrasta'

        lunar_eclipse_str = 'candra-grahaNam~(' + grasta + ')' + \
                            '~\\textsf{' + Hour(eclipse_lunar_start).toString(format=self.panchaanga.fmt) + \
                            '}{\\RIGHTarrow}\\textsf{' + Hour(eclipse_lunar_end).toString(format=self.panchaanga.fmt) + '}'
        if self.panchaanga.weekday[fday] == 1:
          lunar_eclipse_str = '★cUDAmaNi-' + lunar_eclipse_str

        self.panchaanga.festivals[fday].append(lunar_eclipse_str)
      jd += temporal.MIN_DAYS_NEXT_ECLIPSE

  def computeTransits(self):
    jd_end = self.panchaanga.jd_start_utc + self.panchaanga.duration
    check_window = 400  # Max t between two Jupiter transits is ~396 (checked across 180y)
    # Let's check for transitions in a relatively large window
    # to finalise what is the FINAL transition post retrograde movements
    transits = Graha(Graha.JUPITER).get_next_raashi_transit(self.panchaanga.jd_start_utc, jd_end + check_window,
                                                            ayanamsha_id=self.panchaanga.ayanamsha_id)
    if len(transits) > 0:
      for i, (jd_transit, rashi1, rashi2) in enumerate(transits):
        if self.panchaanga.jd_start_utc < jd_transit < jd_end:
          fday = int(floor(jd_transit) - floor(self.panchaanga.jd_start_utc) + 1)
          self.panchaanga.festivals[fday].append('guru-saGkrAntiH~(%s##\\To{}##%s)' %
                                      (names.NAMES['RASHI_NAMES']['hk'][rashi1],
                                       names.NAMES['RASHI_NAMES']['hk'][rashi2]))
          if rashi1 < rashi2 and transits[i + 1][1] < transits[i + 1][2]:
            # Considering only non-retrograde transits for pushkara computations
            # logging.debug('Non-retrograde transit; we have a pushkaram!')
            (madhyanha_start, madhyaahna_end) = temporal.get_interval(self.panchaanga.jd_sunrise[fday],
                                                                      self.panchaanga.jd_sunset[fday], 2, 5).to_tuple()
            if jd_transit < madhyaahna_end:
              fday_pushkara = fday
            else:
              fday_pushkara = fday + 1
            self.add_festival(
              '%s-Adi-puSkara-ArambhaH' % names.NAMES['PUSHKARA_NAMES']['hk'][rashi2],
              fday_pushkara, debug=False)
            self.add_festival(
              '%s-Adi-puSkara-samApanam' % names.NAMES['PUSHKARA_NAMES']['hk'][rashi2],
              fday_pushkara + 11, debug=False)
            self.add_festival(
              '%s-antya-puSkara-samApanam' % names.NAMES['PUSHKARA_NAMES']['hk'][rashi1],
              fday_pushkara - 1, debug=False)
            self.add_festival(
              '%s-antya-puSkara-ArambhaH' % names.NAMES['PUSHKARA_NAMES']['hk'][rashi1],
              fday_pushkara - 12, debug=False)
  