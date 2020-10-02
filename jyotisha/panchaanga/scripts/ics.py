#!/usr/bin/python3

# import json
import logging
import os
import re
import sys
from datetime import datetime, date, timedelta

from icalendar import Calendar, Event, Alarm
from indic_transliteration import xsanscript as sanscript
from pytz import timezone as tz

import jyotisha.custom_transliteration
import jyotisha.panchaanga.spatio_temporal.annual
import jyotisha.panchaanga.temporal
# from jyotisha.panchaanga import scripts
import jyotisha.panchaanga.temporal.festival.rules
from jyotisha.panchaanga.spatio_temporal import City
from jyotisha.panchaanga.temporal import festival
from jyotisha.panchaanga.temporal import time
from jyotisha.panchaanga.temporal.festival import rules
from jyotisha.panchaanga.temporal.festival.rules import HinduCalendarEvent

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def write_to_file(ics_calendar, fname):
  ics_calendar_file = open(fname, 'wb')
  ics_calendar_file.write(ics_calendar.to_ical())
  ics_calendar_file.close()


def compute_calendar(panchaanga, script=sanscript.DEVANAGARI, all_tags=True, brief=False):
  DATA_ROOT = os.path.join(os.path.dirname(festival.__file__), "data")

  festival_rules = {**rules.festival_rules_solar, **rules.festival_rules_lunar, **rules.festival_rules_rel, **rules.festival_rules_desc_only}

  ics_calendar = Calendar()
  # uid_list = []

  alarm = Alarm()
  alarm.add('action', 'DISPLAY')
  alarm.add('trigger', timedelta(hours=-4))  # default alarm, with a 4 hour reminder

  year_start = time.jd_to_utc_gregorian(panchaanga.jd_start + 1).to_date_fractional_hour_tuple()[0]  # 1 helps ignore local time etc.

  daily_panchaangas = panchaanga.daily_panchaangas_sorted()
  for d in range(1, panchaanga.duration):
    daily_panchaanga = daily_panchaangas[d]
    [y, m, dt, t] = time.jd_to_utc_gregorian(panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

    if len(daily_panchaanga.festivals) > 0:
      # Eliminate repeat festivals on the same day, and keep the list arbitrarily sorted
      daily_panchaanga.festivals = sorted(list(set(daily_panchaanga.festivals)))
      summary_text = [x.name for x in daily_panchaanga.festivals]
      # this will work whether we have one or more events on the same day
      for stext in sorted(summary_text):
        desc = ''
        event = Event()

        if not all_tags:
          fest_num_loc = stext.find('~\\#')
          if fest_num_loc != -1:
            stext_chk = stext[:fest_num_loc]
          else:
            stext_chk = stext
          if stext_chk in festival_rules:
            tag_list = (festival_rules[stext_chk].tags.split(','))
            incl_tags = ['CommonFestivals', 'MonthlyVratam', 'RareDays', 'AmavasyaDays', 'Dashavataram', 'SunSankranti']
            if set(tag_list).isdisjoint(set(incl_tags)):
              continue

        if stext == 'kRttikA-maNDala-pArAyaNam':
          event.add('summary', jyotisha.custom_transliteration.tr(stext.replace('-', ' '), script))
          fest_num_loc = stext.find('~\\#')
          if fest_num_loc != -1:
            stext = stext[:fest_num_loc]
          event.add('dtstart', date(y, m, dt))
          event.add('dtend', (datetime(y, m, dt) + timedelta(48)).date())

          if stext in festival_rules:
            desc = festival_rules[stext].get_description_string(
              script=script, include_url=True, include_shlokas=True, truncate=True)
          else:
            logging.warning('No description found for festival %s!' % stext)

          event.add_component(alarm)
          event.add('description', desc.strip().replace('\n', '<br/>'))
          event['X-MICROSOFT-CDO-ALLDAYEVENT'] = 'TRUE'
          event['TRANSP'] = 'TRANSPARENT'
          event['X-MICROSOFT-CDO-BUSYSTATUS'] = 'FREE'
          ics_calendar.add_component(event)
        elif stext.find('RIGHTarrow') != -1:
          if y != year_start:
            continue
          # It's a grahanam/yoga, with a start and end time
          if stext.find('{}') != -1:
            # Starting or ending time is empty, e.g. harivasara, so no ICS entry
            continue
          [stext, t1, arrow, t2] = stext.split('\\')
          stext = stext.strip('-~')
          event.add('summary', jyotisha.custom_transliteration.tr(stext, script))
          # we know that t1 is something like 'textsf{hh:mm(+1)}{'
          # so we know the exact positions of min and hour
          if t1[12] in '(':  # (+1), next day
            event.add('dtstart', datetime(y, m, dt, int(t1[7:9]), int(t1[10:12]),
                                          tzinfo=tz(panchaanga.city.timezone)) + timedelta(1))
          else:
            if t1[12] == '*':
              event.add('dtstart', datetime(y, m, dt, int(t1[7:9]) - 24, int(t1[10:12]),
                                            tzinfo=tz(panchaanga.city.timezone)) + timedelta(1))
            else:
              event.add('dtstart', datetime(y, m, dt, int(t1[7:9]), int(t1[10:12]),
                                            tzinfo=tz(panchaanga.city.timezone)))

          if t2[12] == '(':  # (+1), next day
            event.add('dtend', datetime(y, m, dt, int(t2[7:9]), int(t2[10:12]),
                                        tzinfo=tz(panchaanga.city.timezone)) + timedelta(1))
          else:
            if t2[12] == '*':
              event.add('dtend', datetime(y, m, dt, int(t2[7:9]) - 24, int(t2[10:12]),
                                          tzinfo=tz(panchaanga.city.timezone)) + timedelta(1))
            else:
              event.add('dtend', datetime(y, m, dt, int(t2[7:9]), int(t2[10:12]),
                                          tzinfo=tz(panchaanga.city.timezone)))

          if stext in festival_rules:
            festival_event = festival_rules[stext]
            desc = festival_event.get_description_string(script=script, include_url=True,
                                                         include_shlokas=True, truncate=True)
          else:
            logging.warning('No description found for festival %s!\n' % stext)
          event.add('description', desc.strip().replace('\n', '<br/>'))
          event.add_component(alarm)
          ics_calendar.add_component(event)
        elif stext.find('samApanam') != -1:
          # It's an ending event
          event.add('summary', jyotisha.custom_transliteration.tr(stext, script))
          event.add('dtstart', date(y, m, dt))
          event.add('dtend', (datetime(y, m, dt) + timedelta(1)).date())

          if stext in festival_rules:
            festival_event = festival_rules[stext]
            desc = festival_event.get_description_string(script=script, include_url=True,
                                                         include_shlokas=True, truncate=True)
          else:
            logging.warning('No description found for festival %s!' % stext)

          event.add_component(alarm)
          event.add('description', desc.strip().replace('\n', '<br/>'))
          event['X-MICROSOFT-CDO-ALLDAYEVENT'] = 'TRUE'
          event['TRANSP'] = 'TRANSPARENT'
          event['X-MICROSOFT-CDO-BUSYSTATUS'] = 'FREE'
          ics_calendar.add_component(event)

          # Find start and add entire event as well
          event = Event()
          check_d = d
          stext_start = stext[:stext.find(
            'samApanam')] + 'ArambhaH'  # This discards any bracketed info after the word ArambhaH
          start_d = None
          while check_d > 1:
            check_d -= 1
            if stext_start in [x.name for x in daily_panchaangas[check_d].festivals]:
              start_d = check_d
              break

          if start_d is None:
            # Look for approx match
            check_d = d
            while check_d > 1:
              check_d -= 1
              for fest_key in [x.name for x in daily_panchaangas[check_d].festivals]:
                if fest_key.startswith(stext_start):
                  logging.debug('Found approx match for %s: %s' % (stext_start, fest_key))
                  start_d = check_d
                  break

          if start_d is None:
            logging.error('Unable to find start date for %s' % stext_start)
          else:
            # logging.debug(stext)
            event_summary_text = stext
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
              event_summary_text = event_summary_text.replace(_orig, _repl)
            event.add('summary', jyotisha.custom_transliteration.tr(event_summary_text, script))
            event.add('dtstart', (datetime(y, m, dt) - timedelta(d - start_d)).date())
            event.add('dtend', (datetime(y, m, dt) + timedelta(1)).date())

            # print(event)
            event.add_component(alarm)
            event.add('description', desc.strip().replace('\n', '<br/>'))
            event['X-MICROSOFT-CDO-ALLDAYEVENT'] = 'TRUE'
            event['TRANSP'] = 'TRANSPARENT'
            event['X-MICROSOFT-CDO-BUSYSTATUS'] = 'FREE'
            ics_calendar.add_component(event)
        else:
          if y != year_start:
            continue
          summary = jyotisha.custom_transliteration.tr(
            stext.replace('~', ' ').replace('\\#', '#').replace('\\To{}', '▶'), script)
          summary = re.sub('.tamil{(.*)}', '\\1', summary)
          summary = re.sub('{(.*)}', '\\1', summary)  # strip braces around numbers
          event.add('summary', summary)
          fest_num_loc = stext.find('~\\#')
          if fest_num_loc != -1:
            stext = stext[:fest_num_loc]
          event.add('dtstart', date(y, m, dt))
          event.add('dtend', (datetime(y, m, dt) + timedelta(1)).date())

          if re.match('.*-.*-EkAdazI', stext) is None and stext.find('saGkrAntiH') == -1:
            if stext in festival_rules:
              desc = festival_rules[stext].get_description_string(
                script=script, include_url=True, include_shlokas=True, truncate=True, include_images=False)
            else:
              if re.match('aGgArakI.*saGkaTahara-caturthI-vratam', stext):
                stext = stext.replace('aGgArakI~', '')
                if stext in festival_rules:
                  desc = festival_rules[stext].get_description_string(
                    script=script)
                  desc += 'When `caturthI` occurs on a Tuesday, it is known as `aGgArakI` and is even more sacred.'
                else:
                  logging.warning('No description found for caturthI festival %s!' % stext)
              else:
                # Check approx. match
                matched_festivals = []
                for fest_key in festival_rules:
                  if stext.startswith(fest_key):
                    matched_festivals += [fest_key]
                if matched_festivals == []:
                  logging.warning('No description found for festival %s!' % stext)
                elif len(matched_festivals) > 1:
                  logging.warning('No exact match found for festival %s! Found more than one approximate match: %s' % (
                  stext, str(matched_festivals)))
                else:
                  desc = festival_rules[matched_festivals[0]].get_description_string(script=script,
                                                                                 include_url=True, include_shlokas=True,
                                                                                 truncate=True)

          elif stext.find('saGkrAntiH') != -1:
            # Handle Sankranti descriptions differently
            planet_trans = stext.split('~')[0]  # get rid of ~(rAshi name) etc.
            if planet_trans in festival_rules:
              desc = festival_rules[planet_trans].get_description_string(
                script=script, include_url=True, include_shlokas=True, truncate=True)
            else:
              logging.warning('No description found for festival %s!' % planet_trans)
          else:
            # logging.debug(stext)
            # Handle ekaadashii descriptions differently
            ekad = '-'.join(stext.split('-')[1:])  # get rid of sarva etc. prefix!
            ekad_suff_pos = ekad.find(' (')
            if ekad_suff_pos != -1:
              # ekad_suff = ekad[ekad_suff_pos + 1:-1]
              ekad = ekad[:ekad_suff_pos]
            if ekad in festival_rules:
              desc = festival_rules[ekad].get_description_string(
                script=script, include_url=True, include_shlokas=True, truncate=True)
            else:
              logging.warning('No description found for Ekadashi festival %s (%s)!' % (ekad, stext))
          event.add_component(alarm)
          event.add('description', desc.strip().replace('\n', '<br/>'))
          event['X-MICROSOFT-CDO-ALLDAYEVENT'] = 'TRUE'
          event['TRANSP'] = 'TRANSPARENT'
          event['X-MICROSOFT-CDO-BUSYSTATUS'] = 'FREE'
          ics_calendar.add_component(event)

    # if m == 12 and dt == 31:
    #     break

  return ics_calendar


def main():
  [city_name, latitude, longitude, tz] = sys.argv[1:5]
  year = int(sys.argv[5])

  if len(sys.argv) == 8:
    all_tags = False
  else:
    all_tags = True  # Default assume detailed ICS with all tags

  if len(sys.argv) >= 7:
    script = sys.argv[6]
  else:
    script = sanscript.IAST  # Default script is IAST for writing calendar

  city = City(city_name, latitude, longitude, tz)

  panchaanga = jyotisha.panchaanga.spatio_temporal.annual.get_panchaanga(city=city, year=year)
  script = script  # Force script
  panchaanga.update_festival_details()

  ics_calendar = compute_calendar(panchaanga, all_tags)
  output_file = os.path.expanduser('%s/%s-%d-%s.ics' % ("~/Documents", city.name, year, script))
  write_to_file(ics_calendar, output_file)


if __name__ == '__main__':
  main()
else:
  '''Imported as a module'''
