from datetime import timedelta

from icalendar import Calendar, Alarm, Event

from indic_transliteration import sanscript
from jyotisha.panchaanga.temporal import names
from jyotisha.panchaanga.writer.ics import util
from jyotisha.panchaanga.writer.md.day_details import day_summary


def writeDailyICS(panchaanga, script=sanscript.DEVANAGARI):
  """Write out the panchaanga TeX using a specified template
  """
  compute_lagnams=panchaanga.computation_system.festival_options.set_lagnas

  samvatsara_id = (panchaanga.year - 1568) % 60 + 1  # distance from prabhava
  samvatsara_names = (names.NAMES['SAMVATSARA_NAMES']['sa'][script][samvatsara_id],
                      names.NAMES['SAMVATSARA_NAMES']['sa'][script][(samvatsara_id % 60) + 1])

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
  (title, details) = day_summary(d=d, panchaanga=panchaanga, script=script, subsection_md="##")
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