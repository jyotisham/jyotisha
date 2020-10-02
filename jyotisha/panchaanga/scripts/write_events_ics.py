#!/usr/bin/python3
import json
import logging
import os.path
import sys
from datetime import datetime, date, timedelta

from icalendar import Calendar, Event, Alarm
from pytz import timezone as tz

import jyotisha.panchaanga.spatio_temporal.annual
from jyotisha.panchaanga.temporal import time, festival
from jyotisha.panchaanga import temporal
from jyotisha.panchaanga.spatio_temporal import City
from jyotisha.panchaanga.temporal import MAX_SZ, tithi
from jyotisha.panchaanga.temporal.festival import FestivalInstance
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision, Ayanamsha

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def compute_events(panchaanga, json_file):
  panchaanga.festival_id_to_instance = {}  # Resetting it
  daily_panchaangas = panchaanga.daily_panchaangas_sorted()
  for d in range(1, MAX_SZ):

    debugEvents = False

    with open(json_file) as event_data:
      event_rules = json.load(event_data)

    for event_name in event_rules:
      if 'month_type' in event_rules[event_name]:
        month_type = event_rules[event_name]['timing']['month_type']
      else:
        raise ValueError("No month_type mentioned for %s" % event_name)
      if 'month_number' in event_rules[event_name]:
        month_num = event_rules[event_name]['timing']['month_number']
      else:
        raise ValueError("No month_num mentioned for %s" % event_name)
      if 'anga_type' in event_rules[event_name]:
        anga_type = event_rules[event_name]['timing']['anga_type']
      else:
        raise ValueError("No anga_type mentioned for %s" % event_name)
      if 'anga_number' in event_rules[event_name]:
        angam_num = event_rules[event_name]['timing']['anga_number']
      else:
        raise ValueError("No angam_num mentioned for %s" % event_name)
      if 'kaala' in event_rules[event_name]:
        kaala = event_rules[event_name]['timing']['kaala']
      else:
        kaala = 'sunrise'
      if 'priority' in event_rules[event_name]:
        priority = event_rules[event_name]['timing']['priority']
      else:
        priority = 'puurvaviddha'
      if 'year_start' in event_rules[event_name]:
        event_start_year = event_rules[event_name]['timing']['year_start']
      else:
        event_start_year = None

      daily_panchaanga = daily_panchaangas[d]
      if anga_type == 'tithi' and month_type == 'lunar_month' and \
          angam_num == 1:
        # Shukla prathama tithis need to be dealt carefully, if e.g. the prathama tithi
        # does not touch sunrise on either day (the regular check won't work, because
        # the month itself is different the previous day!)
        if daily_panchaanga.angas.tithi_at_sunrise == 30 and daily_panchaangas[d + 1].angas.tithi_at_sunrise == 2 and \
            daily_panchaangas[d + 1].lunar_month == month_num:
          # Only in this case, we have a problem

          event_num = None
          if event_start_year is not None:
            if month_type == 'lunar_month':
              event_num = panchaanga.year + 3100 + (d >= panchaanga.lunar_month.index(1)) - event_start_year + 1

          if event_num is not None and event_num < 0:
            logging.debug('Festival %s is only in the future!' % event_name)
            return

          if event_num is not None:
            event_name += '-#%d' % event_num

          logging.debug('Assigned fday = %d' % d)
          panchaanga.add_festival(event_name, d, debugEvents)
          continue

      if anga_type == 'day' and month_type == 'sidereal_solar_month' \
          and daily_panchaanga.solar_sidereal_date_sunset.month == month_num:
        if daily_panchaanga.solar_sidereal_date_sunset.day == angam_num:
          panchaanga.festival_id_to_instance[event_name] = festival.FestivalInstance(name=event_name, days=[daily_panchaangas[d].date])
      elif (month_type == 'lunar_month' and daily_panchaanga.lunar_month == month_num) or \
          (month_type == 'sidereal_solar_month' and daily_panchaanga.solar_sidereal_date_sunset.month == month_num):
        if anga_type == 'tithi':
          angam_sunrise = daily_panchaanga.angas.tithi_at_sunrise
          get_angam_func = lambda x: tithi.get_tithi(x)
          angam_num_pred = (angam_num - 2) % 30 + 1
          angam_num_succ = (angam_num % 30) + 1
        elif anga_type == 'nakshatra':
          angam_sunrise = daily_panchaanga.angas.nakshatra_at_sunrise
          get_angam_func = lambda x: NakshatraDivision(x, ayanaamsha_id=Ayanamsha.CHITRA_AT_180).get_nakshatra()
          angam_num_pred = (angam_num - 2) % 27 + 1
          angam_num_succ = (angam_num % 27) + 1
        else:
          raise ValueError('Error; unknown string in rule: "%s"' % (anga_type))
          return

        fday = None
        event_num = None
        if event_start_year is not None and month_type is not None:
          if month_type == 'sidereal_solar_month':
            event_num = panchaanga.year + 3100 + (d >= daily_panchaangas.index(1).solar_month) - event_start_year + 1
          elif month_type == 'lunar_month':
            event_num = panchaanga.year + 3100 + (d >= panchaanga.lunar_month.index(1)) - event_start_year + 1

        if event_num is not None and event_num < 0:
          logging.debug('Festival %s is only in the future!' % event_name)
          return

        if event_num is not None:
          event_name += '-#%d' % event_num

        if angam_sunrise[d] == angam_num_pred or angam_sunrise[d] == angam_num:
          angams = panchaanga.get_angas_for_interval_boundaries(d, get_angam_func, kaala)
          if angams is None:
            sys.stderr.write('No angams returned! Skipping festival %s'
                             % event_name)
            continue
            # Some error, e.g. weird kaala, so skip festival
          if debugEvents:
            logging.debug('%' * 80)
            try:
              logging.debug('%s: %s' % (event_name, event_rules[event_name]))
              logging.debug("%%angams today & tmrw: %s" % angams)
            except KeyError:
              logging.debug('%s: %s' % (event_name, event_rules[event_name.split('\\')[0][:-1]]))
              logging.debug("%%angams today & tmrw: %s" % angams)
          if priority == 'paraviddha':
            if angams[0] == angam_num or angams[1] == angam_num:
              logging.debug('Assigned fday = %d' % d)
              fday = d
            if angams[2] == angam_num or angams[3] == angam_num:
              logging.debug('Assigned fday = %d' % d + 1)
              fday = d + 1
            if fday is None:
              if debugEvents:
                logging.debug('%s: %s' % (angams, angam_num))
              sys.stderr.write('Could not assign paraviddha day for %s!' %
                               event_name +
                               ' Please check for unusual cases.\n')
            else:
              sys.stderr.write('Assigned paraviddha day for %s!' %
                               event_name + ' Ignore future warnings!\n')
          elif priority == 'puurvaviddha':
            angams_yest = panchaanga.get_angas_for_interval_boundaries(d - 1, get_angam_func, kaala)
            if debugEvents:
              logging.debug("Angams yest & today: %s" % angams_yest)
            if angams[0] == angam_num or angams[1] == angam_num:
              if event_name in panchaanga.festival_id_to_instance:
                # Check if yesterday was assigned already
                # to this puurvaviddha festival!
                if angam_num == 1:
                  # Need to check if tomorrow is still the same month, unlikely!
                  if daily_panchaangas[d + 1].lunar_month == month_num:
                    if panchaanga.festival_id_to_instance[event_name].days.count(daily_panchaangas[d - 1].date) == 0:
                      fday = d
                      if debugEvents:
                        logging.debug('Assigned fday = %d' % d)
                  else:
                    continue

                else:
                  if panchaanga.festival_id_to_instance[event_name].days.count(daily_panchaangas[d - 1].date) == 0:
                    fday = d
                    if debugEvents:
                      logging.debug('Assigned fday = %d' % d)
              else:
                fday = d
                logging.debug('Assigned fday = %d' % d)
            elif angams[2] == angam_num or angams[3] == angam_num:
              if (month_type == 'lunar_month' and daily_panchaangas[d + 1].lunar_month == month_num) or \
                  (month_type == 'sidereal_solar_month' and daily_panchaangas[d + 1].solar_sidereal_date_sunset.month == month_num):
                fday = d + 1
                logging.debug('Assigned fday = %d' % (d + 1))
            else:
              # This means that the correct anga did not
              # touch the kaala on either day!
              # sys.stderr.write('Could not assign puurvaviddha day for %s!\
              # Please check for unusual cases.\n' % event_name)
              if angams[2] == angam_num_succ or angams[3] == angam_num_succ:
                # Need to assign a day to the festival here
                # since the anga did not touch kaala on either day
                # BUT ONLY IF YESTERDAY WASN'T ALREADY ASSIGNED,
                # THIS BEING PURVAVIDDHA
                # Perhaps just need better checking of
                # conditions instead of this fix
                if event_name in panchaanga.festival_id_to_instance:
                  if panchaanga.festival_id_to_instance[event_name].days.count(daily_panchaangas[d - 1].date) == 0:
                    fday = d
                    logging.debug('Assigned fday = %d' % d)
                else:
                  fday = d
                  logging.debug('Assigned fday = %d' % d)
          else:
            sys.stderr.write('Unknown priority "%s" for %s! Check the rules!' %
                             (priority, event_name))
        # logging.debug (panchaanga.festival_id_to_instance.days)
        if fday is not None:
          panchaanga.add_festival(event_name, fday, debugEvents)

  for festival_name in panchaanga.festival_id_to_instance:
    for j in range(0, len(panchaanga.festival_id_to_instance[festival_name])):
      panchaanga.date_str_to_panchaanga[panchaanga.festival_id_to_instance[festival_name].days[j].get_date_str()].festivals.append(FestivalInstance(name=festival_name))


def computeIcsCalendar(panchaanga, ics_file_name):
  panchaanga.ics_calendar = Calendar()
  daily_panchaangas = panchaanga.daily_panchaangas_sorted()
  for d in range(1, MAX_SZ - 1):
    daily_panchaanga = daily_panchaangas[d]
    [y, m, dt, t] = time.jd_to_utc_gregorian(panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

    if len(daily_panchaanga.festivals) > 0:
      # Eliminate repeat festivals on the same day, and keep the list arbitrarily sorted
      daily_panchaanga.festivals = sorted(list(set(daily_panchaanga.festivals)))

      summary_text = daily_panchaanga.festivals
      # this will work whether we have one or more events on the same day
      for stext in summary_text:
        if not stext.find('>>') == -1:
          # It's an event, with a start and end time
          event = Event()
          [stext, t1, arrow, t2] = stext.split('|')
          event.add('summary', stext.split('|')[-1].replace('-', ' ').strip())
          h1, m1 = t1.split(':')
          h2, m2 = t2.split(':')
          event.add('dtstart', datetime(y, m, dt, int(h1), int(m1), tzinfo=tz(panchaanga.city.timezone)))
          event.add('dtend', datetime(y, m, dt, int(h2), int(m2), tzinfo=tz(panchaanga.city.timezone)))
          panchaanga.ics_calendar.add_component(event)
        else:
          event = Event()
          # summary = re.sub('{(.*)}','\\1', )  # strip braces around numbers
          event.add('summary', stext.replace('-', ' '))
          event.add('dtstart', date(y, m, dt))
          event.add('dtend', (datetime(y, m, dt) + timedelta(1)).date())
          alarm = Alarm()
          alarm.add('action', 'DISPLAY')
          alarm.add('trigger', timedelta(hours=-4))
          event.add_component(alarm)
          event['X-MICROSOFT-CDO-ALLDAYEVENT'] = 'TRUE'
          event['TRANSP'] = 'TRANSPARENT'
          event['X-MICROSOFT-CDO-BUSYSTATUS'] = 'FREE'

          panchaanga.ics_calendar.add_component(event)

    if m == 12 and dt == 31:
      break

  with open(ics_file_name, 'wb') as ics_calendar_file:
    ics_calendar_file.write(panchaanga.ics_calendar.to_ical())


def main():
  [json_file, city_name, latitude, longitude, tz] = sys.argv[1:6]
  if not os.path.isfile(json_file):
    raise IOError('File %s not found!' % json_file)

  year = int(sys.argv[6])

  if len(sys.argv) == 8:
    script = sys.argv[7]
  else:
    script = 'iast'  # Default script is IAST for writing calendar

  city = City(city_name, latitude, longitude, tz)

  panchaanga = jyotisha.panchaanga.spatio_temporal.annual.get_panchaanga(city=city, year=year)
  # panchaanga.add_details()

  compute_events(panchaanga, json_file)
  cal_file_name = '%s-%s-%s' % (city_name, year, os.path.basename(json_file).replace('.json', '.ics'))
  computeIcsCalendar(panchaanga, cal_file_name)
  print('Wrote ICS file to %s' % cal_file_name)


if __name__ == '__main__':
  main()
else:
  '''Imported as a module'''
