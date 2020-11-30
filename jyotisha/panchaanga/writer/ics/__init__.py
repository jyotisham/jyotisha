#!/usr/bin/python3

# import json
import logging
import os
import sys
from datetime import timedelta

from icalendar import Calendar, Timezone, Alarm, Event

import jyotisha
from indic_transliteration import xsanscript as sanscript

import jyotisha.panchaanga.spatio_temporal.annual
import jyotisha.panchaanga.temporal
# from jyotisha.panchaanga import scripts
import jyotisha.panchaanga.temporal.festival.rules
from jyotisha.panchaanga.spatio_temporal import City
from jyotisha.panchaanga.temporal.time import ist_timezone
from jyotisha.panchaanga.writer.ics import util
from jyotisha.panchaanga.writer.ics.festival_event import write_to_file, get_full_festival_instance, \
  festival_instance_to_event, set_interval, add_festival_events
from jyotisha.panchaanga.writer.md import day_details
from jyotisha.panchaanga.writer.md.day_details import day_summary

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def compute_calendar(panchaanga, scripts=None, set_sequence=True):

  if scripts is None:
    scripts = [sanscript.DEVANAGARI]
  ics_calendar = Calendar()

  set_calendar_metadata(ics_calendar, panchaanga=panchaanga, set_sequence=set_sequence)

  daily_panchaangas = panchaanga.daily_panchaangas_sorted()
  for day_index, daily_panchaanga in enumerate(daily_panchaangas):
    if daily_panchaanga.date < panchaanga.start_date or daily_panchaanga.date > panchaanga.end_date:
      continue
    event = get_day_summary_event(d=day_index, panchaanga=panchaanga, script=scripts[0])
    ics_calendar.add_component(event)
    add_festival_events(day_index, ics_calendar, panchaanga, scripts)

    # if m == 12 and dt == 31:
    #     break

  return ics_calendar


def set_calendar_metadata(ics_calendar, panchaanga, set_sequence):
  timezone = Timezone()
  timezone.add('TZID', panchaanga.city.timezone)
  ics_calendar.add_component(timezone)
  if set_sequence:
    # Calendar programs such as Google Calendar might not update events if they don't recognize that the ics data has changed. https://support.google.com/calendar/thread/17012350?hl=en
    # https://icalendar.org/iCalendar-RFC-5545/3-8-7-4-sequence-number.html
    ics_calendar.add("SEQUENCE", ist_timezone.current_time_as_int())
    # uid_list = []


def main():
  [city_name, latitude, longitude, tz] = sys.argv[1:5]
  year = int(sys.argv[5])
  if len(sys.argv) >= 7:
    scripts = sys.argv[6].split(",")
  else:
    scripts = [sanscript.IAST]  # Default language is IAST for writing calendar

  city = City(city_name, latitude, longitude, tz)

  panchaanga = jyotisha.panchaanga.spatio_temporal.annual.get_panchaanga_for_civil_year(city=city, year=year)

  ics_calendar = compute_calendar(panchaanga)
  output_file = os.path.expanduser('%s/%s-%d-%s.ics' % ("~/Documents/jyotisha", city.name, year, scripts))
  write_to_file(ics_calendar, output_file)


if __name__ == '__main__':
  main()
else:
  '''Imported as a module'''


def writeDailyICS(panchaanga, script=sanscript.DEVANAGARI):
  """Write out the panchaanga TeX using a specified template
  """
  compute_lagnams=panchaanga.computation_system.options.set_lagnas

  samvatsara_id = (panchaanga.year - 1568) % 60 + 1  # distance from prabhava
  samvatsara_names = (jyotisha.names.NAMES['SAMVATSARA_NAMES'][script][samvatsara_id],
                      jyotisha.names.NAMES['SAMVATSARA_NAMES'][script][(samvatsara_id % 60) + 1])

  yname_solar = samvatsara_names[0]  # Assign year name until Mesha Sankranti
  yname_lunar = samvatsara_names[0]  # Assign year name until Mesha Sankranti


  ics_calendar = Calendar()

  alarm = Alarm()
  alarm.add('action', 'DISPLAY')
  alarm.add('trigger', timedelta(hours=-4))  # default alarm, with a 4 hour reminder

  daily_panchaangas = panchaanga.daily_panchaangas_sorted()
  for d, daily_panchaanga in enumerate(daily_panchaangas):
    if daily_panchaanga.date < panchaanga.start_date or daily_panchaanga.date > panchaanga.end_date:
      continue

    if daily_panchaanga.solar_sidereal_date_sunset.month == 1:
      # Flip the year name for the remaining days
      yname_solar = samvatsara_names[1]
    if daily_panchaanga.lunar_month_sunrise.index == 1:
      # Flip the year name for the remaining days
      yname_lunar = samvatsara_names[1]

    event = get_day_summary_event(d, panchaanga, script)

    ics_calendar.add_component(event)

  return ics_calendar


def get_day_summary_event(d, panchaanga, script):
  daily_panchaanga = panchaanga.daily_panchaangas_sorted()[d]
  event = Event()
  (title, details) = day_summary(d=d, panchaanga=panchaanga, script=script)
  event.add('summary', title)
  event.add('description', details)
  tz = daily_panchaanga.city.get_timezone_obj()
  dt_start = tz.julian_day_to_local_datetime(jd=daily_panchaanga.jd_sunrise)
  event.add('dtstart', dt_start)
  event.add('dtend', tz.julian_day_to_local_datetime(jd=daily_panchaanga.jd_next_sunrise))
  event.add_component(util.get_4_hr_display_alarm())
  event['X-MICROSOFT-CDO-ALLDAYEVENT'] = 'TRUE'
  event['TRANSP'] = 'TRANSPARENT'
  event['X-MICROSOFT-CDO-BUSYSTATUS'] = 'FREE'
  return event