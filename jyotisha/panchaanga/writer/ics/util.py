from datetime import timedelta

from icalendar import Alarm


def get_4_hr_display_alarm():
  alarm = Alarm()
  alarm.add('action', 'DISPLAY')
  alarm.add('trigger', timedelta(hours=-4))  # default alarm, with a 4 hour reminder
  return alarm