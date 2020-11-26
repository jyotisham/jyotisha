import logging
import os
import re
from copy import deepcopy
from datetime import timedelta

from icalendar import Event, Alarm

from jyotisha.panchaanga.temporal.festival import FestivalInstance, rules
from jyotisha.panchaanga.temporal.interval import Interval
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
                    'rAtri-': 'rAtriH',
                    'rAtra-': 'rAtraH',
                    'nakSatra-': 'nakSatram',
                    'pakSa-': 'pakSaH',
                    'puSkara-': 'puSkaram',
                    'dIpa-': 'dIpaH',
                    'snAna-': 'snAnam',
                    'tsava-': 'tsavaH',
                    'vrata-': 'vratam'}
    for _orig, _repl in REPLACEMENTS.items():
      new_fest_id = new_fest_id.replace(_orig, _repl)
    full_festival_instance = FestivalInstance(name=new_fest_id, interval=Interval(jd_start=daily_panchaangas[start_d].julian_day_start, jd_end=festival_instance.interval.jd_start+1))
    return full_festival_instance


def festival_instance_to_event(festival_instance, scripts, panchaanga, all_day=False):
  rules_collection = rules.RulesCollection.get_cached(
    repos_tuple=tuple(panchaanga.computation_system.options.fest_repos))
  fest_details_dict = rules_collection.name_to_rule
  fest_name = festival_instance.get_best_transliterated_name(scripts=scripts, fest_details_dict=rules_collection.name_to_rule)["text"].replace("~", " ")
  event = Event()
  event.add('summary', fest_name)
  desc = get_description(festival_instance=festival_instance, script=scripts[0], fest_details_dict=fest_details_dict)
  event.add('description', desc.strip().replace('\n', '<br/>'))

  if festival_instance.interval is not None and festival_instance.interval.jd_end is not None and festival_instance.interval.jd_start is not None :
    # Starting or ending time is empty, e.g. harivasara, so no ICS entry
    t1 = panchaanga.city.get_timezone_obj().julian_day_to_local_datetime(jd=festival_instance.interval.jd_start)
    t2 = panchaanga.city.get_timezone_obj().julian_day_to_local_datetime(jd=festival_instance.interval.jd_end)
    # we know that t1 is something like 'textsf{hh:mm(+1)}{'
    # so we know the exact positions of min and hour
    event.add('dtstart', t1)
    event.add('dtend', t2)
  if all_day:
    event['X-MICROSOFT-CDO-ALLDAYEVENT'] = 'TRUE'
    event['TRANSP'] = 'TRANSPARENT'
    event['X-MICROSOFT-CDO-BUSYSTATUS'] = 'FREE'
  alarm = Alarm()
  alarm.add('action', 'DISPLAY')
  alarm.add('trigger', timedelta(hours=-4))  # default alarm, with a 4 hour reminder
  event.add_component(alarm)
  return event


def get_description(festival_instance, fest_details_dict, script):
  fest_id = festival_instance.name
  desc = None
  if re.match('aGgArakI.*saGkaTahara-caturthI-vratam', fest_id):
    fest_id = fest_id.replace('aGgArakI~', '')
    if fest_id in fest_details_dict:
      desc = fest_details_dict[fest_id].get_description_string(
        script=script)
      desc += 'When `caturthI` occurs on a Tuesday, it is known as `aGgArakI` and is even more sacred.'
    else:
      logging.warning('No description found for caturthI festival %s!' % fest_id)
  elif re.match('.*-.*-EkAdazI', fest_id) is not None:
    # Handle ekaadashii descriptions differently
    ekad = '-'.join(fest_id.split('-')[1:])  # get rid of sarva etc. prefix!
    ekad_suff_pos = ekad.find(' (')
    if ekad_suff_pos != -1:
      # ekad_suff = ekad[ekad_suff_pos + 1:-1]
      ekad = ekad[:ekad_suff_pos]
    if ekad in fest_details_dict:
      desc = fest_details_dict[ekad].get_description_string(
        script=script, include_url=True, include_shlokas=True, truncate=True)
    else:
      logging.warning('No description found for Ekadashi festival %s (%s)!' % (ekad, fest_id))
  elif fest_id.find('saGkrAntiH') != -1:
    # Handle Sankranti descriptions differently
    planet_trans = fest_id.split('~')[0]  # get rid of ~(rAshi name) etc.
    if planet_trans in fest_details_dict:
      desc = fest_details_dict[planet_trans].get_description_string(
        script=script, include_url=True, include_shlokas=True, truncate=True)
    else:
      logging.warning('No description found for festival %s!' % planet_trans)
  elif fest_id in fest_details_dict:
      desc = fest_details_dict[fest_id].get_description_string(
        script=script, include_url=True, include_shlokas=True, truncate=True, include_images=False)


  if desc is None:
      # Check approx. match
      matched_festivals = []
      for fest_key in fest_details_dict:
        if fest_id.startswith(fest_key):
          matched_festivals += [fest_key]
      if matched_festivals == []:
        logging.warning('No description found for festival %s!' % fest_id)
      elif len(matched_festivals) > 1:
        logging.warning('No exact match found for festival %s! Found more than one approximate match: %s' % (
          fest_id, str(matched_festivals)))
      else:
        desc = fest_details_dict[matched_festivals[0]].get_description_string(script=script,
                                                                              include_url=True, include_shlokas=True,
                                                                              truncate=True)
  return default_if_none(desc, "")


def set_interval(daily_panchaanga, festival_instance):
  if festival_instance.interval is None:
    festival_instance.interval = Interval(jd_start=daily_panchaanga.julian_day_start,
                                          jd_end=daily_panchaanga.julian_day_start + 1)
  if festival_instance.interval.jd_start is None:
    festival_instance.interval.jd_start = daily_panchaanga.julian_day_start
  if festival_instance.interval.jd_end is None:
    festival_instance.interval.jd_end = daily_panchaanga.julian_day_start + 1
  if festival_instance.name == 'kRttikA-maNDala-pArAyaNam':
    festival_instance.interval = Interval(jd_start=daily_panchaanga.julian_day_start,
                                          jd_end=daily_panchaanga.julian_day_start + 2)


def add_festival_events(day_index, ics_calendar, panchaanga, scripts):
  daily_panchaanga = panchaanga.daily_panchaangas_sorted()[day_index]
  for festival_instance_in in sorted(daily_panchaanga.festival_id_to_instance.values()):
    festival_instance = deepcopy(festival_instance_in)
    fest_id = festival_instance.name
    all_day = False
    if festival_instance.interval is None:
      all_day = True

    set_interval(daily_panchaanga, festival_instance)
    if fest_id.find('samApanam') != -1:
      # It's an ending event
      full_festival_instance = get_full_festival_instance(festival_instance=festival_instance,
                                                          daily_panchaangas=panchaanga.daily_panchaangas_sorted(), day_index=day_index)
      if full_festival_instance is not None:
        event = festival_instance_to_event(festival_instance=full_festival_instance, scripts=scripts,
                                           panchaanga=panchaanga, all_day=True)
        ics_calendar.add_component(event)

    event = festival_instance_to_event(festival_instance=festival_instance, scripts=scripts, panchaanga=panchaanga,
                                       all_day=all_day)
    ics_calendar.add_component(event)