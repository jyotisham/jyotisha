import logging
import os
import sys
from itertools import filterfalse

from jyotisha.panchaanga import temporal
from jyotisha.panchaanga.temporal import festival
from jyotisha.panchaanga.temporal import interval, PanchaangaApplier, tithi
from jyotisha.panchaanga.temporal import time
from jyotisha.panchaanga.temporal import zodiac
from jyotisha.panchaanga.temporal.festival import rules
from jyotisha.panchaanga.temporal.festival.rules import get_festival_rules_dict
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision, AngaSpan
from sanskrit_data.schema import common

DATA_ROOT = os.path.join(os.path.dirname(festival.__file__), "data")


class FestivalAssigner(PanchaangaApplier):
  def filter_festivals(self,
                       incl_tags=['CommonFestivals', 'MonthlyVratam', 'RareDays', 'AmavasyaDays', 'Dashavataram',
                                  'SunSankranti']):

    festival_rules = {**rules.festival_rules_solar, **rules.festival_rules_lunar, **rules.festival_rules_rel, **rules.festival_rules_desc_only}

    for d in range(1, len(self.panchaanga.festivals)):
      if len(self.daily_panchaangas[d].festivals) > 0:
        # Eliminate repeat festivals on the same day, and keep the list arbitrarily sorted
        self.daily_panchaangas[d].festivals = sorted(list(set(self.daily_panchaangas[d].festivals)))

        def chk_fest(fest):
          fest_title = fest.name
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

        self.daily_panchaangas[d].festivals[:] = filterfalse(chk_fest, self.daily_panchaangas[d].festivals)


  def add_festival(self, festival_name, d, debug=False):
    if debug:
      logging.debug('%03d: %s ' % (d, festival_name))
    if festival_name in self.panchaanga.festival_id_to_instance:
      if self.daily_panchaangas[d].date not in self.panchaanga.festival_id_to_instance[festival_name].days:
        # Second occurrence of a festival within a
        # Gregorian calendar year
        if self.daily_panchaangas[d-1].date in self.panchaanga.festival_id_to_instance[festival_name].days:
          # No festival occurs on consecutive days; paraviddha assigned twice
          logging.warning(
            '%s occurring on two consecutive days (%d, %d). Removing! paraviddha assigned twice?' % (
              festival_name, d - 1, d))
          self.panchaanga.festival_id_to_instance[festival_name].days.remove(self.daily_panchaangas[d-1].date)
        self.panchaanga.festival_id_to_instance[festival_name].days.append(self.daily_panchaangas[d].date)
    else:
      self.panchaanga.festival_id_to_instance[festival_name] = festival.FestivalInstance(name=festival_name, days=[self.daily_panchaangas[d].date])

  def assign_festivals_from_rules(self, festival_rules, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

      for festival_name in festival_rules:
        if 'month_type' in festival_rules[festival_name]['timing']:
          month_type = festival_rules[festival_name]['timing']['month_type']
        else:
          # Maybe only description of the festival is given, as computation has been
          # done in computeFestivals(), without using a rule in festival_rules.json!
          if 'description_short' in festival_rules[festival_name]:
            continue
          raise ValueError("No month_type mentioned for %s" % festival_name)
        if 'month_number' in festival_rules[festival_name]['timing']:
          month_num = festival_rules[festival_name]['timing']['month_number']
        else:
          raise ValueError("No month_num mentioned for %s" % festival_name)
        if 'angam_type' in festival_rules[festival_name]['timing']:
          angam_type = festival_rules[festival_name]['timing']['angam_type']
        else:
          raise ValueError("No angam_type mentioned for %s" % festival_name)
        if 'angam_number' in festival_rules[festival_name]['timing']:
          angam_num = festival_rules[festival_name]['timing']['angam_number']
        else:
          raise ValueError("No angam_num mentioned for %s" % festival_name)
        if 'kaala' in festival_rules[festival_name]['timing']:
          kaala = festival_rules[festival_name]['timing']['kaala']
        else:
          kaala = 'sunrise'  # default!
        if 'priority' in festival_rules[festival_name]['timing']:
          priority = festival_rules[festival_name]['timing']['priority']
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
          if self.daily_panchaangas[d].angas.tithi_at_sunrise == 30 and self.daily_panchaangas[d + 1].angas.tithi_at_sunrise == 2 and \
              self.daily_panchaangas[d + 1].lunar_month == month_num:
            # Only in this case, we have a problem
            self.add_festival(festival_name, d, debug_festivals)
            continue

        if angam_type == 'day' and month_type == 'solar_month' and self.daily_panchaangas[d].solar_sidereal_date_sunset.month == month_num:
          if self.daily_panchaangas[d].solar_sidereal_date_sunset.day == angam_num:
            if kaala == 'arunodaya':
              angams = self.panchaanga.get_angas_for_interval_boundaries(d - 1,
                                                                         lambda x: NakshatraDivision(x,
                                                                              ayanaamsha_id=self.ayanaamsha_id).get_solar_raashi(),
                                                                         kaala)
              if angams[1] == month_num:
                self.add_festival(festival_name, d, debug_festivals)
              elif angams[2] == month_num:
                self.add_festival(festival_name, d + 1, debug_festivals)
            else:
              self.add_festival(festival_name, d, debug_festivals)
        elif (month_type == 'lunar_month' and ((self.daily_panchaangas[d].lunar_month == month_num or month_num == 0) or (
            (self.daily_panchaangas[d + 1].lunar_month == month_num and angam_num == 1)))) or \
            (month_type == 'solar_month' and (self.daily_panchaangas[d].solar_sidereal_date_sunset.month == month_num or month_num == 0)):
          # Using 0 as a special tag to denote every month!
          if angam_type == 'tithi':
            angam_sunrise = [d.angas.tithi_at_sunrise for d in self.daily_panchaangas]
            angam_data = [d.angas.tithis_with_ends for d in self.daily_panchaangas]
            get_angam_func = lambda x: temporal.tithi.get_tithi(x)
            num_angams = 30
          elif angam_type == 'nakshatram':
            angam_sunrise = [d.nakshatra_at_sunrise for d in self.daily_panchaangas]
            angam_data = [d.angas.nakshatras_with_ends for d in self.daily_panchaangas]
            get_angam_func = lambda x: NakshatraDivision(x, ayanaamsha_id=self.ayanaamsha_id).get_nakshatra()
            num_angams = 27
          elif angam_type == 'yoga':
            angam_sunrise = [d.angas.yoga_at_sunrise for d in self.daily_panchaangas]
            angam_data = [d.angas.yogas_with_ends for d in self.daily_panchaangas]
            get_angam_func = lambda x: NakshatraDivision(x, ayanaamsha_id=self.ayanaamsha_id).get_yoga()
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
              angams = self.panchaanga.get_angas_for_interval_boundaries(d - 1, get_angam_func, kaala)
            else:
              angams = self.panchaanga.get_angas_for_interval_boundaries(d, get_angam_func, kaala)

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
                  ('%', festival_name, ': ', festival_rules[festival_name]))
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
                if festival_name not in self.panchaanga.festival_id_to_instance and angams[3] > angam_num:
                  logging.debug((angams, angam_num))
                  logging.warning(
                    'Could not assign paraviddha day for %s!  Please check for unusual cases.' % festival_name)
            elif priority == 'puurvaviddha':
              # angams_yest = self.panchaanga.get_angams_for_kaalas(d - 1, get_angam_func, kaala)
              # if debug_festivals:
              #     print("%angams yest & today:", angams_yest)
              if angams[0] == angam_num or angams[1] == angam_num:
                if festival_name in self.panchaanga.festival_id_to_instance:
                  # Check if yesterday was assigned already
                  # to this puurvaviddha festival!
                  if self.panchaanga.festival_id_to_instance[festival_name].days.count(self.daily_panchaangas[d-1].date) == 0:
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
                  if festival_name in self.panchaanga.festival_id_to_instance:
                    offset_date = self.daily_panchaangas[d - 1 + d_offset].date
                    if self.panchaanga.festival_id_to_instance[festival_name].days.count(offset_date) == 0:
                      fday = d + d_offset
                  else:
                    fday = d + d_offset
                else:
                  if festival_name not in self.panchaanga.festival_id_to_instance and angams != [prev_angam] * 4:
                    logging.debug('Special case: %s; angams = %s' % (festival_name, str(angams)))

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
              p, q, r = prev_angam, angam_num, next_angam  # short-hand
              if angams in ([p, p, q, q], [p, q, q, q], [q, q, q, q], [p, p, q, r], [p, p, r, r]):
                fday = d + 1
              elif angams in ([p, q, r, r], [q, q, q, r], [q, q, r, r]):
                fday = d
              elif angams == [p, q, q, r]:
                angam, angam_end = angam_data[d][0]
                vyapti_1 = max(t_end_d - angam_end, 0)
                vyapti_2 = max(angam_end - t_start_d1, 0)
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
            if (month_type == 'lunar_month' and ((self.daily_panchaangas[d].lunar_month == month_num or month_num == 0) or (
                (self.daily_panchaangas[d + 1].lunar_month == month_num and angam_num == 1)))) or \
                (month_type == 'solar_month' and (
                    self.daily_panchaangas[fday].solar_sidereal_date_sunset.month == month_num or month_num == 0)):
              # If month on fday is incorrect, we ignore and move.
              if month_type == 'lunar_month' and angam_num == 1 and self.daily_panchaangas[
                fday + 1].lunar_month != month_num:
                continue
              # if festival_name.find('\\') == -1 and \
              #         'kaala' in festival_rules[festival_name] and \
              #         festival_rules[festival_name]['timing']['kaala'] == 'arunodaya':
              #     fday += 1
              self.add_festival(festival_name, fday, debug_festivals)
            else:
              if debug_festivals:
                if month_type == 'solar_month':
                  logging.warning('Not adding festival %s on %d fday (month = %d instead of %d)' % (
                    festival_name, fday, self.daily_panchaangas[fday].solar_sidereal_date_sunset.month, month_num))
                else:
                  logging.warning('Not adding festival %s on %d fday (month = %d instead of %d)' % (
                    festival_name, fday, self.daily_panchaangas[fday].lunar_month, month_num))

  def assign_festival_numbers(self, festival_rules, debug_festivals=False):
    # Update festival numbers if they exist
    solar_y_start_d = []
    lunar_y_start_d = []
    for d in range(1, self.panchaanga.duration + 1):
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 1 and self.daily_panchaangas[d - 1].solar_sidereal_date_sunset.month != 1:
        solar_y_start_d.append(d)
      if self.daily_panchaangas[d].lunar_month == 1 and self.daily_panchaangas[d - 1].lunar_month != 1:
        lunar_y_start_d.append(d)

    period_start_year = self.panchaanga.start_date.year
    for festival_name in festival_rules:
      if festival_name in self.panchaanga.festival_id_to_instance and 'year_start' in festival_rules[festival_name]['timing']:
        fest_start_year = festival_rules[festival_name]['timing']['year_start']
        month_type = festival_rules[festival_name]['timing']['month_type']
        if len(self.panchaanga.festival_id_to_instance[festival_name].days) > 1:
          if self.panchaanga.festival_id_to_instance[festival_name].days[1] - self.panchaanga.festival_id_to_instance[festival_name].days[0] < 300:
            # Lunar festivals can repeat after 354 days; Solar festivals "can" repeat after 330 days
            # (last day of Dhanur masa Jan and first day of Dhanur masa Dec may have same nakshatra and are about 335 days apart)
            # In fact they will be roughly 354 days apart, again!
            logging.warning('Multiple occurrences of festival %s within year. Check?: %s' % (
              festival_name, str(self.panchaanga.festival_id_to_instance[festival_name].days)))
        for assigned_day in self.panchaanga.festival_id_to_instance[festival_name].days:
          assigned_day_index = int(assigned_day - self.daily_panchaangas[0].date)
          if month_type == 'solar_month':
            fest_num = period_start_year + 3100 - fest_start_year + 1
            for start_day in solar_y_start_d:
              if assigned_day_index >= start_day:
                fest_num += 1
          elif month_type == 'lunar_month':
            if festival_rules[festival_name]['timing']['angam_number'] == 1 and festival_rules[festival_name]['timing'][
              'month_number'] == 1:
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
          else:
            if festival_name not in self.panchaanga.festival_id_to_instance:
              logging.warning(
                'Did not find festival %s to be assigned. Dhanurmasa festival?' % festival_name)
              continue
            festival_name_updated = festival_name + '~\\#{%d}' % fest_num
            # logging.debug('Changing %s to %s' % (festival_name, festival_name_updated))
            if festival_name_updated in self.panchaanga.festival_id_to_instance:
              logging.warning('Overwriting festival day for %s %s with %s.' % (
                festival_name_updated, self.panchaanga.festival_id_to_instance[festival_name_updated].days[0], assigned_day))
              self.panchaanga.festival_id_to_instance[festival_name_updated] = festival.FestivalInstance(name=festival_name_updated, days=[assigned_day])
            else:
              self.panchaanga.festival_id_to_instance[festival_name_updated] = festival.FestivalInstance(name=festival_name_updated, days=[assigned_day])
        del (self.panchaanga.festival_id_to_instance[festival_name])

  def cleanup_festivals(self, debug=False):
    # If tripurotsava coincides with maha kArttikI (kRttikA nakShatram)
    # only then it is mahAkArttikI
    # else it is only tripurotsava
    if 'tripurOtsavaH' not in self.panchaanga.festival_id_to_instance:
      logging.error('tripurOtsavaH not in self.panchaanga.festival_id_to_instance!')
    else:
      if self.panchaanga.festival_id_to_instance['tripurOtsavaH'].days != self.panchaanga.festival_id_to_instance['mahA~kArttikI'].days:
        logging.warning('Removing mahA~kArttikI (%s) since it does not coincide with tripurOtsavaH (%s)' % (
          self.panchaanga.festival_id_to_instance['tripurOtsavaH'].days[0], self.panchaanga.festival_id_to_instance['mahA~kArttikI'].days[0]))
        del self.panchaanga.festival_id_to_instance['mahA~kArttikI']
        # An error here implies the festivals were not assigned: adhika
        # mAsa calc errors??


class MiscFestivalAssigner(FestivalAssigner):
  def __init__(self, panchaanga):
    super(MiscFestivalAssigner, self).__init__(panchaanga=panchaanga)
  
  def assign_all(self, debug=False):
    self.assign_agni_nakshatram(debug_festivals=debug)
    # ASSIGN ALL FESTIVALS FROM adyatithi submodule
    # festival_rules = get_festival_rules_dict(os.path.join(CODE_ROOT, 'panchaanga/data/festival_rules_test.json'))
    festival_rules = {**rules.festival_rules_solar, **rules.festival_rules_lunar}

    assert "tripurOtsavaH" in festival_rules
    self.assign_festivals_from_rules(festival_rules, debug_festivals=debug)
    self.assign_festival_numbers(festival_rules, debug_festivals=debug)
    

  def assign_agni_nakshatram(self, debug_festivals=False):
    agni_jd_start = agni_jd_end = None
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

      # AGNI NAKSHATRAM
      # Arbitrarily checking after Mesha 10! Agni Nakshatram can't start earlier...
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 1 and self.daily_panchaangas[d].solar_sidereal_date_sunset.day == 10:
        agni_jd_start, dummy = AngaSpan.find(
          self.daily_panchaangas[d].jd_sunrise, self.daily_panchaangas[d].jd_sunrise + 30,
          zodiac.AngaType.SOLAR_NAKSH_PADA, 7, ayanaamsha_id=self.ayanaamsha_id).to_tuple()
        dummy, agni_jd_end = AngaSpan.find(
          agni_jd_start, agni_jd_start + 30,
          zodiac.AngaType.SOLAR_NAKSH_PADA, 13, ayanaamsha_id=self.ayanaamsha_id).to_tuple()

      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 1 and self.daily_panchaangas[d].solar_sidereal_date_sunset.day > 10:
        if agni_jd_start is not None:
          if self.daily_panchaangas[d].jd_sunset < agni_jd_start < self.daily_panchaangas[d + 1].jd_sunset:
            self.add_festival('agninakSatra-ArambhaH', d + 1, debug_festivals)
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 2 and self.daily_panchaangas[d].solar_sidereal_date_sunset.day > 10:
        if agni_jd_end is not None:
          if self.daily_panchaangas[d].jd_sunset < agni_jd_end < self.daily_panchaangas[d + 1].jd_sunset:
            self.add_festival('agninakSatra-samApanam', d + 1, debug_festivals)

  def assign_relative_festivals(self):
    # Add "RELATIVE" festivals --- festivals that happen before or
    # after other festivals with an exact timedelta!
    if 'yajurvEda-upAkarma' not in self.panchaanga.festival_id_to_instance:
      logging.error('yajurvEda-upAkarma not in festivals!')
    else:
      # Extended for longer calendars where more than one upAkarma may be there
      self.panchaanga.festival_id_to_instance['varalakSmI-vratam'] = festival.FestivalInstance(name='varalakSmI-vratam', days=[])
      for d in self.panchaanga.festival_id_to_instance['yajurvEda-upAkarma'].days:
        self.panchaanga.festival_id_to_instance['varalakSmI-vratam'].days.append(d - ((d.get_weekday() - 5) % 7))
      # self.panchaanga.festival_id_to_instance['varalakSmI-vratam'].days = [self.panchaanga.festival_id_to_instance['yajurvEda-upAkarma'].days[0] -
      #                                        ((self.panchaanga.weekday_start - 1 + self.panchaanga.festival_id_to_instance['yajurvEda-upAkarma'].days[
      #                                            0] - 5) % 7)]

    relative_festival_rules = rules.festival_rules_rel

    for festival_name in relative_festival_rules:
      offset = int(relative_festival_rules[festival_name]['timing']['offset'])
      rel_festival_name = relative_festival_rules[festival_name]['timing']['anchor_festival_id']
      if rel_festival_name not in self.panchaanga.festival_id_to_instance:
        # Check approx. match
        matched_festivals = []
        for fest_key in self.panchaanga.festival_id_to_instance:
          if fest_key.startswith(rel_festival_name):
            matched_festivals += [fest_key]
        if matched_festivals == []:
          logging.error('Relative festival %s not in festival_id_to_instance!' % rel_festival_name)
        elif len(matched_festivals) > 1:
          logging.error('Relative festival %s not in festival_id_to_instance! Found more than one approximate match: %s' % (
            rel_festival_name, str(matched_festivals)))
        else:
          self.panchaanga.festival_id_to_instance[festival_name] = festival.FestivalInstance(name=festival_name, days=[x + offset for x in self.panchaanga.festival_id_to_instance[matched_festivals[0]].days])
      else:
        self.panchaanga.festival_id_to_instance[festival_name] = festival.FestivalInstance(name=festival_name, days=[x + offset for x in self.panchaanga.festival_id_to_instance[rel_festival_name].days])

    for _, fest in self.panchaanga.festival_id_to_instance.items():
      for fest_day in fest.days:
        self.panchaanga.daily_panchaangas[fest_day.get_date_str()].festivals.append(fest)


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
