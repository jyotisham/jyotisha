#!/usr/bin/python3

import json
import logging
import os
import re
import swisseph as swe
import sys
from datetime import datetime, date, timedelta

from icalendar import Calendar, Event, Alarm
from indic_transliteration import xsanscript as sanscript
from pytz import timezone as tz

import jyotisha.custom_transliteration
import jyotisha.panchangam.temporal
from jyotisha.panchangam import scripts
from jyotisha.panchangam.spatio_temporal import City

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def write_to_file(ics_calendar, fname):
    ics_calendar_file = open(fname, 'wb')
    ics_calendar_file.write(ics_calendar.to_ical())
    ics_calendar_file.close()


def compute_calendar(panchangam):
    with open(os.path.join(CODE_ROOT, 'panchangam/data/festival_rules.json')) as festivals_data:
        festival_rules_main = json.load(festivals_data)

    with open(os.path.join(CODE_ROOT, 'panchangam/data/relative_festival_rules.json')) as relative_festivals_data:
        festival_rules_rel = json.load(relative_festivals_data)

    with open(os.path.join(CODE_ROOT, 'panchangam/data/festival_rules_desc_only.json')) as festivals_desc_data:
        festival_rules_desc_only = json.load(festivals_desc_data)

    festival_rules = {**festival_rules_main, **festival_rules_rel, **festival_rules_desc_only}

    ics_calendar = Calendar()
    uid_list = []

    alarm = Alarm()
    alarm.add('action', 'DISPLAY')
    alarm.add('trigger', timedelta(hours=-4))  # default alarm, with a 4 hour reminder

    # BASE_URL = "http://adyatithih.wordpress.com/"
    BASE_URL = "http://karthikraman.github.io/adyatithih/posts/"

    for d in range(1, jyotisha.panchangam.temporal.MAX_SZ - 1):
        [y, m, dt, t] = swe.revjul(panchangam.jd_start + d - 1)

        if len(panchangam.festivals[d]) > 0:
            # Eliminate repeat festivals on the same day, and keep the list arbitrarily sorted
            panchangam.festivals[d] = sorted(list(set(panchangam.festivals[d])))
            summary_text = panchangam.festivals[d]
            # this will work whether we have one or more events on the same day
            for stext in sorted(summary_text):
                desc = ''
                page_id = ''
                event = Event()
                if stext == 'kRttikA-maNDala-pArAyaNam':
                    event.add('summary', jyotisha.custom_transliteration.tr(stext.replace('-', ' '), panchangam.script))
                    fest_num_loc = stext.find('~\#')
                    if fest_num_loc != -1:
                        stext = stext[:fest_num_loc]
                    event.add('dtstart', date(y, m, dt))
                    event.add('dtend', (datetime(y, m, dt) + timedelta(48)).date())

                    if stext in festival_rules:
                        desc = festival_rules[stext]['description_short'] + '\n\n' + \
                            jyotisha.custom_transliteration.tr(festival_rules[stext]['Shloka'],
                                                               panchangam.script, False) + '\n\n'
                        if 'URL' in festival_rules[stext]:
                            page_id = festival_rules[stext]['URL']
                        else:
                            sys.stderr.write('No URL found for festival %s!\n' % stext)
                    else:
                        sys.stderr.write('No description found for festival %s!\n' % stext)
                    desc += BASE_URL + page_id.rstrip('-1234567890').rstrip('0123456789{}\\#')
                    uid = '%s-%d' % (page_id, y)

                    event.add_component(alarm)
                    event.add('description', desc.strip())
                    uid_list.append(uid)
                    event.add('uid', uid)
                    event['X-MICROSOFT-CDO-ALLDAYEVENT'] = 'TRUE'
                    event['TRANSP'] = 'TRANSPARENT'
                    event['X-MICROSOFT-CDO-BUSYSTATUS'] = 'FREE'
                    ics_calendar.add_component(event)
                elif stext.find('RIGHTarrow') != -1:
                    # It's a grahanam/yogam, with a start and end time
                    if stext.find('{}') != -1:
                        # Starting or ending time is empty, e.g. harivasara, so no ICS entry
                        continue
                    [stext, t1, arrow, t2] = stext.split('\\')
                    stext = stext.strip('-')
                    event.add('summary', jyotisha.custom_transliteration.tr(stext, panchangam.script))
                    # we know that t1 is something like 'textsf{hh:mm(+1)}{'
                    # so we know the exact positions of min and hour
                    if t1[12] == '(':  # (+1), next day
                        event.add('dtstart', datetime(y, m, dt, int(t1[7:9]), int(t1[10:12]),
                                                      tzinfo=tz(panchangam.city.timezone)) + timedelta(1))
                    else:
                        event.add('dtstart', datetime(y, m, dt, int(t1[7:9]), int(t1[10:12]),
                                                      tzinfo=tz(panchangam.city.timezone)))
                    if t2[12] == '(':  # (+1), next day
                        event.add('dtend', datetime(y, m, dt, int(t2[7:9]), int(t2[10:12]),
                                                    tzinfo=tz(panchangam.city.timezone)) + timedelta(1))
                    else:
                        event.add('dtend', datetime(y, m, dt, int(t2[7:9]), int(t2[10:12]),
                                                    tzinfo=tz(panchangam.city.timezone)))

                    if stext in festival_rules:
                        desc = festival_rules[stext]['description_short'] + '\n\n' + \
                            jyotisha.custom_transliteration.tr(festival_rules[stext]['Shloka'], panchangam.script, False) + '\n\n'
                        if 'URL' in festival_rules[stext]:
                            page_id = festival_rules[stext]['URL']
                        else:
                            sys.stderr.write('No URL found for festival %s!\n' % stext)
                    else:
                        sys.stderr.write('No description found for festival %s!\n' % stext)

                    desc += BASE_URL + page_id
                    event.add('description', desc.strip())
                    uid = '%s-%d-%02d' % (page_id, y, m)
                    if uid not in uid_list:
                        uid_list.append(uid)
                    else:
                        uid = '%s-%d-%02d-%02d' % (page_id, y, m, dt)
                        uid_list.append(uid)
                    event.add('uid', uid)
                    event.add_component(alarm)
                    ics_calendar.add_component(event)
                elif stext.find('samApanam') != -1:
                    # It's an ending event
                    event.add('summary', jyotisha.custom_transliteration.tr(stext, panchangam.script))
                    event.add('dtstart', date(y, m, dt))
                    event.add('dtend', (datetime(y, m, dt) + timedelta(1)).date())

                    if stext in festival_rules:
                        desc = festival_rules[stext]['description_short'] + '\n\n' + \
                            jyotisha.custom_transliteration.tr(festival_rules[stext]['Shloka'], panchangam.script, False) + '\n\n'
                        if 'URL' in festival_rules[stext]:
                            page_id = festival_rules[stext]['URL']
                        else:
                            sys.stderr.write('No URL found for festival %s!\n' % stext)
                    else:
                        sys.stderr.write('No description found for festival %s!\n' % stext)

                    desc += BASE_URL + page_id.rstrip('-1234567890').rstrip('0123456789{}\\#')
                    # print(event)
                    event.add_component(alarm)
                    event.add('description', desc.strip())
                    uid = '%s-%d-%02d' % (page_id, y, m)
                    if uid not in uid_list:
                        uid_list.append(uid)
                    else:
                        uid = '%s-%d-%02d-%02d' % (page_id, y, m, dt)
                        uid_list.append(uid)
                    event.add('uid', uid)
                    event['X-MICROSOFT-CDO-ALLDAYEVENT'] = 'TRUE'
                    event['TRANSP'] = 'TRANSPARENT'
                    event['X-MICROSOFT-CDO-BUSYSTATUS'] = 'FREE'
                    ics_calendar.add_component(event)

                    # Find start and add entire event as well
                    desc = ''
                    page_id = page_id.replace('-samapanam', '')
                    event = Event()
                    check_d = d
                    stext_start = stext.replace('samApanam', 'ArambhaH')
                    # print(stext_start)
                    while check_d > 1:
                        check_d -= 1
                        if stext_start in panchangam.festivals[check_d]:
                            # print(panchangam.festivals[check_d])
                            start_d = check_d
                            break

                    event.add('summary', jyotisha.custom_transliteration.tr(stext.replace('samApanam', '').replace('rAtri-', 'rAtriH').replace('nakSatra-', 'nakSatram').replace('pakSa-', 'pakSaH').replace('kara-', 'karam').replace('tsava-', 'tsavaH'), panchangam.script))
                    event.add('dtstart', (datetime(y, m, dt) - timedelta(d - start_d)).date())
                    event.add('dtend', (datetime(y, m, dt) + timedelta(1)).date())

                    desc += BASE_URL + page_id.rstrip('-1234567890').rstrip('0123456789{}\\#')
                    # print(event)
                    event.add_component(alarm)
                    event.add('description', desc.strip())
                    uid = '%s-%d-%02d' % (page_id, y, m)
                    if uid not in uid_list:
                        uid_list.append(uid)
                    else:
                        suff = 0
                        while uid in uid_list:
                            uid = '%s-%d-%02d-%02d-%d' % (page_id, y, m, dt, suff)
                            suff += 1
                        uid_list.append(uid)
                    event.add('uid', uid)
                    event['X-MICROSOFT-CDO-ALLDAYEVENT'] = 'TRUE'
                    event['TRANSP'] = 'TRANSPARENT'
                    event['X-MICROSOFT-CDO-BUSYSTATUS'] = 'FREE'
                    ics_calendar.add_component(event)

                else:
                    summary = jyotisha.custom_transliteration.tr(stext.replace('~', ' ').replace('\#', '#').replace('\\To{}', '▶'), panchangam.script)
                    summary = re.sub('.tamil{(.*)}', '\\1', summary)
                    summary = re.sub('{(.*)}', '\\1', summary)  # strip braces around numbers
                    event.add('summary', summary)
                    fest_num_loc = stext.find('~\#')
                    if fest_num_loc != -1:
                        stext = stext[:fest_num_loc]
                    event.add('dtstart', date(y, m, dt))
                    event.add('dtend', (datetime(y, m, dt) + timedelta(1)).date())

                    if stext.find('EkAdazI') == -1 and stext.find('saGkrAntiH') == -1:
                        if stext in festival_rules:
                            desc = festival_rules[stext]['description_short'] + '\n\n' + \
                                jyotisha.custom_transliteration.tr(festival_rules[stext]['Shloka'], panchangam.script, False) + '\n\n'
                            if 'URL' in festival_rules[stext]:
                                page_id = festival_rules[stext]['URL']
                            else:
                                sys.stderr.write('No URL found for festival %s!\n' % stext)
                        else:
                            sys.stderr.write('No description found for festival %s!\n' % stext)
                        desc += BASE_URL + page_id.rstrip('-1234567890').rstrip('0123456789{}\\#')
                        uid = '%s-%d-%02d' % (page_id, y, m)
                    elif stext.find('saGkrAntiH') != -1:
                        # Handle Sankranti descriptions differently
                        planet_trans = stext.split('~')[0]  # get rid of ~(rAshi name) etc.
                        if planet_trans in festival_rules:
                            desc = festival_rules[planet_trans]['description_short'] + '\n\n' + \
                                jyotisha.custom_transliteration.tr(festival_rules[planet_trans]['Shloka'], panchangam.script) + '\n\n'
                            if 'URL' in festival_rules[planet_trans]:
                                page_id = festival_rules[planet_trans]['URL']
                            else:
                                sys.stderr.write('No URL found for festival %s!\n' % stext)
                        else:
                            sys.stderr.write('No description found for festival %s!\n' % planet_trans)
                        desc += '\n' + BASE_URL + page_id
                        uid = '%s-%d-%02d' % (page_id, y, m)
                    else:
                        # Handle ekadashi descriptions differently
                        ekad = '-'.join(stext.split('-')[1:])  # get rid of sarva etc. prefix!
                        if ekad in festival_rules:
                            desc = festival_rules[ekad]['description_short'] + '\n\n' + \
                                jyotisha.custom_transliteration.tr(festival_rules[ekad]['Shloka'], panchangam.script) + '\n\n'
                            if 'URL' in festival_rules[ekad]:
                                page_id = festival_rules[ekad]['URL']
                            else:
                                sys.stderr.write('No URL found for festival %s!\n' % stext)
                        else:
                            sys.stderr.write('No description found for festival %s!\n' % ekad)
                        desc += '\n' + BASE_URL + page_id
                        pref = jyotisha.custom_transliteration.romanise(sanscript.transliterate(
                            stext.split('-')[0],
                            sanscript.HK, sanscript.IAST)) + "-"
                        uid = '%s-%d-%02d' % (pref + page_id, y, m)
                    # print(page_id)
                    event.add_component(alarm)
                    event.add('description', desc.strip())
                    if uid not in uid_list:
                        uid_list.append(uid)
                    else:
                        suff = 0
                        while uid in uid_list:
                            uid = '%s-%d-%02d-%02d-%d' % (page_id, y, m, dt, suff)
                            suff += 1
                        uid_list.append(uid)
                    event.add('uid', uid)
                    event['X-MICROSOFT-CDO-ALLDAYEVENT'] = 'TRUE'
                    event['TRANSP'] = 'TRANSPARENT'
                    event['X-MICROSOFT-CDO-BUSYSTATUS'] = 'FREE'
                    ics_calendar.add_component(event)

        if m == 12 and dt == 31:
            break

    return ics_calendar


def main():
    [city_name, latitude, longitude, tz] = sys.argv[1:5]
    year = int(sys.argv[5])

    if len(sys.argv) == 7:
        script = sys.argv[6]
    else:
        script = sanscript.IAST  # Default script is IAST for writing calendar

    city = City(city_name, latitude, longitude, tz)

    panchangam = scripts.get_panchangam(city=city, year=year, script=script)
    panchangam.add_details()

    ics_calendar = compute_calendar(panchangam)
    write_to_file(ics_calendar, '%s-%d-%s.ics' % (city_name, year, script))


if __name__ == '__main__':
    main()
else:
    '''Imported as a module'''
