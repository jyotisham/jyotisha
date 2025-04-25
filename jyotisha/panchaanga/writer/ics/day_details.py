import logging

from icalendar import Calendar, Event
from datetime import datetime
from indic_transliteration import sanscript
from jyotisha.panchaanga.writer.ics import util
from jyotisha.panchaanga.writer.md.day_details import day_summary


def writeDailyICS(panchaanga, script=sanscript.DEVANAGARI):
  """Write out the panchaanga TeX using a specified template
  """
  ics_calendar = Calendar()

  daily_panchaangas = panchaanga.daily_panchaangas_sorted()
  for d, daily_panchaanga in enumerate(daily_panchaangas):
    if daily_panchaanga.date < panchaanga.start_date or daily_panchaanga.date > panchaanga.end_date:
      continue

    event = get_day_summary_event(d, panchaanga, script)

    ics_calendar.add_component(event)

  return ics_calendar


def get_day_summary_event(d, panchaanga, script):
  daily_panchaanga = panchaanga.daily_panchaangas_sorted()[d]
  event = Event()
  (title, details) = day_summary(d=d, panchaanga=panchaanga, script=script, subsection_md="##")
  event.add('summary', title)
  event.add('description', details)
  tz = daily_panchaanga.city.get_timezone_obj()
  dt_start = tz.julian_day_to_local_datetime(jd=daily_panchaanga.jd_sunrise)
  event.add('dtstamp', datetime.now())
  # logging.debug(daily_panchaanga.date)
  event.add('dtstart', dt_start)
  event.add('dtend', tz.julian_day_to_local_datetime(jd=daily_panchaanga.jd_next_sunrise))
  uid = f"{dt_start.strftime('%Y%m%d')}_day_summary"
  event.add('uid', uid)
  alarm_4h =  util.get_4_hr_display_alarm()
  alarm_4h.add('description', 'Reminder')
  event.add_component(alarm_4h)
  event['X-MICROSOFT-CDO-ALLDAYEVENT'] = 'TRUE'
  event['TRANSP'] = 'TRANSPARENT'
  event['X-MICROSOFT-CDO-BUSYSTATUS'] = 'FREE'
  return event