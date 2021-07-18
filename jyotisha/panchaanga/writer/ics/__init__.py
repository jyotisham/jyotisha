#!/usr/bin/python3

# import json
import logging
import os
import sys

from icalendar import Calendar, Timezone

import jyotisha
from indic_transliteration import sanscript

import jyotisha.panchaanga.spatio_temporal.annual
import jyotisha.panchaanga.temporal
# from jyotisha.panchaanga import scripts
import jyotisha.panchaanga.temporal.festival.rules
from jyotisha.panchaanga.spatio_temporal import City
from jyotisha.panchaanga.temporal.time import ist_timezone
from jyotisha.panchaanga.writer.ics import util
from jyotisha.panchaanga.writer.ics.day_details import get_day_summary_event
from jyotisha.panchaanga.writer.ics.festival_event import write_to_file, get_full_festival_instance, \
  festival_instance_to_event, set_interval, add_festival_events

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def compute_calendar(panchaanga, languages=None, scripts=None, set_sequence=True, festivals_only=False):

  if scripts is None:
    scripts = [sanscript.DEVANAGARI]
  if languages is None:
    languages = ["sa"]
  ics_calendar = Calendar()

  set_calendar_metadata(ics_calendar, panchaanga=panchaanga, set_sequence=set_sequence)

  daily_panchaangas = panchaanga.daily_panchaangas_sorted()
  for day_index, daily_panchaanga in enumerate(daily_panchaangas):
    if daily_panchaanga.date < panchaanga.start_date or daily_panchaanga.date > panchaanga.end_date:
      continue
    if not festivals_only:
      event = get_day_summary_event(d=day_index, panchaanga=panchaanga, script=scripts[0])
      ics_calendar.add_component(event)
    add_festival_events(day_index=day_index, ics_calendar=ics_calendar, panchaanga=panchaanga, scripts=scripts, languages=languages)

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
    scripts = [sanscript.ISO]  # Default language is ISO for writing calendar

  city = City(city_name, latitude, longitude, tz)

  panchaanga = jyotisha.panchaanga.spatio_temporal.annual.get_panchaanga_for_civil_year(city=city, year=year)

  ics_calendar = compute_calendar(panchaanga)
  output_file = os.path.expanduser('%s/%s-%d-%s.ics' % ("~/Documents/jyotisha", city.name, year, scripts))
  write_to_file(ics_calendar, output_file)


if __name__ == '__main__':
  main()
else:
  '''Imported as a module'''


