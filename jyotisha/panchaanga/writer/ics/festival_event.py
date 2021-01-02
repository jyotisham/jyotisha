import logging
import os
from copy import deepcopy

from icalendar import Event

from jyotisha import custom_transliteration
from jyotisha.panchaanga.temporal.festival import FestivalInstance, rules, get_description
from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.writer.ics.util import get_4_hr_display_alarm
from datetime import datetime, date, timedelta

from jyotisha.util import default_if_none


def write_to_file(ics_calendar, fname):
  os.makedirs(os.path.dirname(fname), exist_ok=True)
  ics_calendar_file = open(fname, 'wb')
  ics_calendar_file.write(ics_calendar.to_ical())
  ics_calendar_file.close()


def get_full_festival_instance(festival_instance, daily_panchaangas, day_index):
  # Find start and add entire event as well
  fest_id = festival_instance.name
  check_d = day_index
  stext_start = fest_id[:fest_id.find(
    'samApanam')] + 'ArambhaH'  # This discards any bracketed info after the word ArambhaH
  start_d = None
  while check_d > 1:
    check_d -= 1
    if stext_start in daily_panchaangas[check_d].festival_id_to_instance.keys():
      start_d = check_d
      break

  if start_d is None:
    # Look for approx match
    check_d = day_index
    while check_d > 1:
      check_d -= 1
      for fest_key in daily_panchaangas[check_d].festival_id_to_instance.keys():
        if fest_key.startswith(stext_start):
          logging.debug('Found approx match for %s: %s' % (stext_start, fest_key))
          start_d = check_d
          break
  

  if start_d is None:
    logging.error('Unable to find start date for %s' % stext_start)
    return None
  else:
    # logging.debug(stext)
    # TODO: Reimplement the below in another way if needed.
    new_fest_id = fest_id
    REPLACEMENTS = {'samApanam': '',
                    'rAtra-': 'rAtraH',
                    'nakSatra-': 'nakSatram',
                    'pakSa-': 'pakSaH',
                    'puSkara-': 'puSkaram',
                    'dIpa-': 'dIpaH',
                    'pArAyaNa-': 'pArAyaNam',
                    'mAsa-': 'mAsaH',
                    'snAna-': 'snAnam',
                    'tsava-': 'tsavaH',
                    'vrata-': 'vratam'}
    for _orig, _repl in REPLACEMENTS.items():
      new_fest_id = new_fest_id.replace(_orig, _repl)
    full_festival_instance = FestivalInstance(name=new_fest_id, interval=Interval(jd_start=daily_panchaangas[start_d].julian_day_start, jd_end=festival_instance.interval.jd_start+1))
    return full_festival_instance


def festival_instance_to_event(festival_instance, languages, scripts, panchaanga, all_day=False):
  rules_collection = rules.RulesCollection.get_cached(
    repos_tuple=tuple(panchaanga.computation_system.festival_options.repos), julian_handling=panchaanga.computation_system.festival_options.julian_handling)
  fest_details_dict = rules_collection.name_to_rule
  fest_name = festival_instance.get_best_transliterated_name(languages=languages, scripts=scripts, fest_details_dict=rules_collection.name_to_rule)["text"].replace("~", " ")
  if festival_instance.ordinal is not None:
    fest_name += ' #%s' % custom_transliteration.tr(str(festival_instance.ordinal), scripts[0])
  event = Event()
  event.add('summary', fest_name)
  desc = get_description(festival_instance=festival_instance, script=scripts[0], fest_details_dict=fest_details_dict, header_md="##")
  event.add('description', desc.strip().replace('\n', '<br/>'))

  if all_day or not festival_instance._show_interval():
    t1 = panchaanga.city.get_timezone_obj().julian_day_to_local_datetime(jd=festival_instance.interval.jd_start)
    t2 = panchaanga.city.get_timezone_obj().julian_day_to_local_datetime(jd=festival_instance.interval.jd_end)
    event.add('dtstart', t1.date())
    event.add('dtend', t2.date())
    event['X-MICROSOFT-CDO-ALLDAYEVENT'] = 'TRUE'
    event['TRANSP'] = 'TRANSPARENT'
    event['X-MICROSOFT-CDO-BUSYSTATUS'] = 'FREE'
  elif festival_instance.interval is not None and festival_instance.interval.jd_end is not None and festival_instance.interval.jd_start is not None:
    # Starting or ending time is empty, e.g. harivasara, so no ICS entry
    t1 = panchaanga.city.get_timezone_obj().julian_day_to_local_datetime(jd=festival_instance.interval.jd_start)
    t2 = panchaanga.city.get_timezone_obj().julian_day_to_local_datetime(jd=festival_instance.interval.jd_end)
    event.add('dtstart', t1)
    event.add('dtend', t2)

  alarm = get_4_hr_display_alarm()
  event.add_component(alarm)
  return event


def set_interval(daily_panchaanga, festival_instance):
  if festival_instance.interval is None:
    festival_instance.interval = Interval(jd_start=daily_panchaanga.julian_day_start,
                                          jd_end=daily_panchaanga.julian_day_start + 1)
  if festival_instance.interval.jd_start is None:
    festival_instance.interval.jd_start = daily_panchaanga.julian_day_start
  if festival_instance.interval.jd_end is None:
    festival_instance.interval.jd_end = daily_panchaanga.julian_day_start + 1


def add_festival_events(day_index, ics_calendar, panchaanga, languages, scripts):
  daily_panchaanga = panchaanga.daily_panchaangas_sorted()[day_index]
  for festival_instance_in in sorted(daily_panchaanga.festival_id_to_instance.values()):
    festival_instance = deepcopy(festival_instance_in)
    fest_id = festival_instance.name
    all_day = False
    if festival_instance.interval is None:
      all_day = True
    elif default_if_none(festival_instance.interval.get_jd_length(), 0) > 0.75:
      all_day = True
      

    set_interval(daily_panchaanga, festival_instance)
    if fest_id.find('samApanam') != -1:
      # It's an ending event
      full_festival_instance = get_full_festival_instance(festival_instance=festival_instance,
                                                          daily_panchaangas=panchaanga.daily_panchaangas_sorted(), day_index=day_index)
      if full_festival_instance is not None:
        event = festival_instance_to_event(festival_instance=full_festival_instance, languages=languages, scripts=scripts,
                                           panchaanga=panchaanga, all_day=True)
        ics_calendar.add_component(event)

    event = festival_instance_to_event(festival_instance=festival_instance, languages=languages, scripts=scripts, panchaanga=panchaanga,
                                       all_day=all_day)
    ics_calendar.add_component(event)