#!/usr/bin/python3
import logging
import os.path
import sys
from datetime import datetime, date, timedelta

from icalendar import Calendar, Event, Alarm
from pytz import timezone as tz

import jyotisha.panchaanga.spatio_temporal.annual
from jyotisha.panchaanga.spatio_temporal import City

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def emit_ics_calendar(panchaanga, ics_file_name):
  ics_calendar = Calendar()
  daily_panchaangas = panchaanga.daily_panchaangas_sorted()
  for d, daily_panchaanga in enumerate(daily_panchaangas):
    if daily_panchaanga.date < panchaanga.start_date or daily_panchaanga.date > panchaanga.end_date:
      continue
    [y, m, dt] = [daily_panchaanga.date.year, daily_panchaanga.date.month, daily_panchaanga.date.day]

    if len(daily_panchaanga.festival_id_to_instance) > 0:

      summary_text = daily_panchaanga.festival_id_to_instance.keys()
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
          ics_calendar.add_component(event)
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

          ics_calendar.add_component(event)

    if m == 12 and dt == 31:
      break

  with open(ics_file_name, 'wb') as ics_calendar_file:
    ics_calendar_file.write(ics_calendar.to_ical())


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

  panchaanga = jyotisha.panchaanga.spatio_temporal.annual.get_panchaanga_for_civil_year(city=city, year=year)
  panchaanga.update_festival_details()

  cal_file_name = '%s-%s-%s' % (city_name, year, os.path.basename(json_file).replace('.json', '.ics'))
  emit_ics_calendar(panchaanga, cal_file_name)
  print('Wrote ICS file to %s' % cal_file_name)


if __name__ == '__main__':
  main()
else:
  '''Imported as a module'''
