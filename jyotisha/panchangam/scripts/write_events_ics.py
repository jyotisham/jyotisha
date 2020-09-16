#!/usr/bin/python3
import json
import logging
import os.path
import sys
from datetime import datetime, date, timedelta

from icalendar import Calendar, Event, Alarm
from pytz import timezone as tz

import jyotisha.panchangam.spatio_temporal.annual
from jyotisha.panchangam import temporal
from jyotisha.panchangam.spatio_temporal import City
from jyotisha.panchangam.temporal import MAX_SZ
from jyotisha.panchangam.temporal.zodiac import NakshatraDivision, Ayanamsha

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def compute_events(p, json_file):
  p.fest_days = {}  # Resetting it
  for d in range(1, MAX_SZ):
    [y, m, dt, t] = temporal.jd_to_utc_gregorian(p.jd_start + d - 1)

    debugEvents = False

    with open(json_file) as event_data:
      event_rules = json.load(event_data)

    for event_name in event_rules:
      if 'month_type' in event_rules[event_name]:
        month_type = event_rules[event_name]['month_type']
      else:
        raise (ValueError, "No month_type mentioned for %s" % event_name)
      if 'month_number' in event_rules[event_name]:
        month_num = event_rules[event_name]['month_number']
      else:
        raise (ValueError, "No month_num mentioned for %s" % event_name)
      if 'angam_type' in event_rules[event_name]:
        angam_type = event_rules[event_name]['angam_type']
      else:
        raise (ValueError, "No angam_type mentioned for %s" % event_name)
      if 'angam_number' in event_rules[event_name]:
        angam_num = event_rules[event_name]['angam_number']
      else:
        raise (ValueError, "No angam_num mentioned for %s" % event_name)
      if 'kaala' in event_rules[event_name]:
        kaala = event_rules[event_name]['kaala']
      else:
        kaala = 'sunrise'
      if 'priority' in event_rules[event_name]:
        priority = event_rules[event_name]['priority']
      else:
        priority = 'puurvaviddha'
      if 'year_start' in event_rules[event_name]:
        event_start_year = event_rules[event_name]['year_start']
      else:
        event_start_year = None

      if angam_type == 'tithi' and month_type == 'lunar_month' and \
          angam_num == 1:
        # Shukla prathama tithis need to be dealt carefully, if e.g. the prathama tithi
        # does not touch sunrise on either day (the regular check won't work, because
        # the month itself is different the previous day!)
        if p.tithi_sunrise[d] == 30 and p.tithi_sunrise[d + 1] == 2 and \
            p.lunar_month[d + 1] == month_num:
          # Only in this case, we have a problem

          event_num = None
          if event_start_year is not None:
            if month_type == 'lunar_month':
              event_num = p.year + 3100 + (d >= p.lunar_month.index(1)) - event_start_year + 1

          if event_num is not None and event_num < 0:
            logging.debug('Festival %s is only in the future!' % event_name)
            return

          if event_num is not None:
            event_name += '-#%d' % event_num

          logging.debug('Assigned fday = %d' % d)
          p.add_festival(event_name, d, debugEvents)
          continue

      if angam_type == 'day' and month_type == 'solar_month' \
          and p.solar_month[d] == month_num:
        if p.solar_month_day[d] == angam_num:
          p.fest_days[event_name] = [d]
      elif (month_type == 'lunar_month' and p.lunar_month[d] == month_num) or \
          (month_type == 'solar_month' and p.solar_month[d] == month_num):
        if angam_type == 'tithi':
          angam_sunrise = p.tithi_sunrise
          get_angam_func = lambda x: NakshatraDivision(x, ayanamsha_id=Ayanamsha.CHITRA_AT_180).get_tithi()
          angam_num_pred = (angam_num - 2) % 30 + 1
          angam_num_succ = (angam_num % 30) + 1
        elif angam_type == 'nakshatram':
          angam_sunrise = p.nakshatram_sunrise
          get_angam_func = lambda x: NakshatraDivision(x, ayanamsha_id=Ayanamsha.CHITRA_AT_180).get_nakshatram()
          angam_num_pred = (angam_num - 2) % 27 + 1
          angam_num_succ = (angam_num % 27) + 1
        else:
          raise ValueError('Error; unknown string in rule: "%s"' % (angam_type))
          return

        fday = None
        event_num = None
        if event_start_year is not None and month_type is not None:
          if month_type == 'solar_month':
            event_num = p.year + 3100 + (d >= p.solar_month.index(1)) - event_start_year + 1
          elif month_type == 'lunar_month':
            event_num = p.year + 3100 + (d >= p.lunar_month.index(1)) - event_start_year + 1

        if event_num is not None and event_num < 0:
          logging.debug('Festival %s is only in the future!' % event_name)
          return

        if event_num is not None:
          event_name += '-#%d' % event_num

        if angam_sunrise[d] == angam_num_pred or angam_sunrise[d] == angam_num:
          angams = p.get_angams_for_kaalas(d, get_angam_func, kaala)
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
            angams_yest = p.get_angams_for_kaalas(d - 1, get_angam_func, kaala)
            if debugEvents:
              logging.debug("Angams yest & today: %s" % angams_yest)
            if angams[0] == angam_num or angams[1] == angam_num:
              if event_name in p.fest_days:
                # Check if yesterday was assigned already
                # to this puurvaviddha festival!
                if angam_num == 1:
                  # Need to check if tomorrow is still the same month, unlikely!
                  if p.lunar_month[d + 1] == month_num:
                    if p.fest_days[event_name].count(d - 1) == 0:
                      fday = d
                      if debugEvents:
                        logging.debug('Assigned fday = %d' % d)
                  else:
                    continue

                else:
                  if p.fest_days[event_name].count(d - 1) == 0:
                    fday = d
                    if debugEvents:
                      logging.debug('Assigned fday = %d' % d)
              else:
                fday = d
                logging.debug('Assigned fday = %d' % d)
            elif angams[2] == angam_num or angams[3] == angam_num:
              if (month_type == 'lunar_month' and p.lunar_month[d + 1] == month_num) or \
                  (month_type == 'solar_month' and p.solar_month[d + 1] == month_num):
                fday = d + 1
                logging.debug('Assigned fday = %d' % (d + 1))
            else:
              # This means that the correct angam did not
              # touch the kaala on either day!
              # sys.stderr.write('Could not assign puurvaviddha day for %s!\
              # Please check for unusual cases.\n' % event_name)
              if angams[2] == angam_num_succ or angams[3] == angam_num_succ:
                # Need to assign a day to the festival here
                # since the angam did not touch kaala on either day
                # BUT ONLY IF YESTERDAY WASN'T ALREADY ASSIGNED,
                # THIS BEING PURVAVIDDHA
                # Perhaps just need better checking of
                # conditions instead of this fix
                if event_name in p.fest_days:
                  if p.fest_days[event_name].count(d - 1) == 0:
                    fday = d
                    logging.debug('Assigned fday = %d' % d)
                else:
                  fday = d
                  logging.debug('Assigned fday = %d' % d)
          else:
            sys.stderr.write('Unknown priority "%s" for %s! Check the rules!' %
                             (priority, event_name))
        # logging.debug (P.fest_days)
        if fday is not None:
          p.add_festival(event_name, fday, debugEvents)

  for festival_name in p.fest_days:
    for j in range(0, len(p.fest_days[festival_name])):
      p.festivals[p.fest_days[festival_name][j]].append(festival_name)


def computeIcsCalendar(P, ics_file_name):
  P.ics_calendar = Calendar()
  for d in range(1, MAX_SZ - 1):
    [y, m, dt, t] = temporal.jd_to_utc_gregorian(P.jd_start + d - 1)

    if len(P.festivals[d]) > 0:
      # Eliminate repeat festivals on the same day, and keep the list arbitrarily sorted
      P.festivals[d] = sorted(list(set(P.festivals[d])))

      summary_text = P.festivals[d]
      # this will work whether we have one or more events on the same day
      for stext in summary_text:
        if not stext.find('>>') == -1:
          # It's an event, with a start and end time
          event = Event()
          [stext, t1, arrow, t2] = stext.split('|')
          event.add('summary', stext.split('|')[-1].replace('-', ' ').strip())
          h1, m1 = t1.split(':')
          h2, m2 = t2.split(':')
          event.add('dtstart', datetime(y, m, dt, int(h1), int(m1), tzinfo=tz(P.city.timezone)))
          event.add('dtend', datetime(y, m, dt, int(h2), int(m2), tzinfo=tz(P.city.timezone)))
          P.ics_calendar.add_component(event)
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

          P.ics_calendar.add_component(event)

    if m == 12 and dt == 31:
      break

  with open(ics_file_name, 'wb') as ics_calendar_file:
    ics_calendar_file.write(P.ics_calendar.to_ical())


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

  panchangam = jyotisha.panchangam.spatio_temporal.annual.get_panchangam(city=city, year=year, script=script)
  # panchangam.add_details()

  compute_events(panchangam, json_file)
  cal_file_name = '%s-%s-%s' % (city_name, year, os.path.basename(json_file).replace('.json', '.ics'))
  computeIcsCalendar(panchangam, cal_file_name)
  print('Wrote ICS file to %s' % cal_file_name)


if __name__ == '__main__':
  main()
else:
  '''Imported as a module'''
