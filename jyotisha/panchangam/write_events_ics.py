#!/usr/bin/python3
import json
import os.path
import pickle
import sys
from datetime import datetime, date, timedelta

from icalendar import Calendar, Event, Alarm
from pytz import timezone as tz
from jyotisha.panchangam import panchangam
from jyotisha.panchangam.helper_functions import swe, MAX_SZ, get_nakshatram, get_tithi, City


def compute_events(P, json_file):
    P.fest_days = {}  # Resetting it
    for d in range(1, MAX_SZ):
        [y, m, dt, t] = swe.revjul(P.jd_start + d - 1)

        debugEvents = True

        with open(json_file) as event_data:
            event_rules = json.load(event_data)

        for event_name in event_rules:
            if 'Month Type' in event_rules[event_name]:
                month_type = event_rules[event_name]['Month Type']
            else:
                raise(ValueError, "No month_type mentioned for %s" % event_name)
            if 'Month Number' in event_rules[event_name]:
                month_num = event_rules[event_name]['Month Number']
            else:
                raise(ValueError, "No month_num mentioned for %s" % event_name)
            if 'Angam Type' in event_rules[event_name]:
                angam_type = event_rules[event_name]['Angam Type']
            else:
                raise(ValueError, "No angam_type mentioned for %s" % event_name)
            if 'Angam Number' in event_rules[event_name]:
                angam_num = event_rules[event_name]['Angam Number']
            else:
                raise(ValueError, "No angam_num mentioned for %s" % event_name)
            if 'kala' in event_rules[event_name]:
                kala = event_rules[event_name]['kala']
            else:
                kala = 'sunrise'
            if 'priority' in event_rules[event_name]:
                priority = event_rules[event_name]['priority']
            else:
                priority = 'purvaviddha'
            if 'Start Year' in event_rules[event_name]:
                event_start_year = event_rules[event_name]['Start Year']
            else:
                event_start_year = None

            if angam_type == 'tithi' and month_type == 'lunar_month' and\
               angam_num == 1:
                # Shukla prathama tithis need to be dealt carefully, if e.g. the prathama tithi
                # does not touch sunrise on either day (the regular check won't work, because
                # the month itself is different the previous day!)
                if P.tithi_sunrise[d] == 30 and P.tithi_sunrise[d + 1] == 2 and\
                   P.lunar_month[d + 1] == month_num:
                    # Only in this case, we have a problem

                    event_num = None
                    if event_start_year is not None:
                        if month_type == 'lunar_month':
                            event_num = P.year + 3100 +\
                                (d >= P.lunar_month.index(1)) - event_start_year + 1

                    if event_num is not None and event_num < 0:
                        print('Festival %s is only in the future!' % event_name)
                        return

                    if event_num is not None:
                        event_name += '~\\#{%d}' % event_num

                    print('%%0 Assigned fday = %d' % d)
                    P.addFestival(event_name, d, debugEvents)
                    continue

            if angam_type == 'day' and month_type == 'solar_month'\
               and P.solar_month[d] == month_num:
                if P.solar_month_day[d] == angam_num:
                    P.fest_days[event_name] = [d]
            elif (month_type == 'lunar_month' and P.lunar_month[d] == month_num) or\
                 (month_type == 'solar_month' and P.solar_month[d] == month_num):
                if angam_type == 'tithi':
                    angam_sunrise = P.tithi_sunrise
                    get_angam_func = get_tithi
                    angam_num_pred = (angam_num - 2) % 30 + 1
                    angam_num_succ = (angam_num % 30) + 1
                elif angam_type == 'nakshatram':
                    angam_sunrise = P.nakshatram_sunrise
                    get_angam_func = get_nakshatram
                    angam_num_pred = (angam_num - 2) % 27 + 1
                    angam_num_succ = (angam_num % 27) + 1
                else:
                    raise ValueError('Error; unknown string in rule: "%s"' % (angam_type))
                    return

                fday = None
                event_num = None
                if event_start_year is not None and month_type is not None:
                    if month_type == 'solar_month':
                        event_num = P.year + 3100 +\
                            (d >= P.solar_month.index(1)) - event_start_year + 1
                    elif month_type == 'lunar_month':
                        event_num = P.year + 3100 +\
                            (d >= P.lunar_month.index(1)) - event_start_year + 1

                if event_num is not None and event_num < 0:
                    print('Festival %s is only in the future!' % event_name)
                    return

                if event_num is not None:
                    event_name += '~\\#{%d}' % event_num

                if angam_sunrise[d] == angam_num_pred or angam_sunrise[d] == angam_num:
                    angams = P.get_angams_for_kalas(d, get_angam_func, kala)
                    if angams is None:
                        sys.stderr.write('No angams returned! Skipping festival %s'
                                         % event_name)
                        continue
                        # Some error, e.g. weird kala, so skip festival
                    if debugEvents:
                        print('%' * 80)
                        try:
                            print('%', event_name, ': ', event_rules[event_name])
                            print("%%angams today & tmrw:", angams)
                        except KeyError:
                            print('%', event_name, ': ', event_rules[event_name.split('\\')[0][:-1]])
                            print("%%angams today & tmrw:", angams)
                    if priority == 'paraviddha':
                        if angams[0] == angam_num or angams[1] == angam_num:
                            print('%%1 Assigned fday = %d' % d)
                            fday = d
                        if angams[2] == angam_num or angams[3] == angam_num:
                            print('%%2 Assigned fday = %d', d + 1)
                            fday = d + 1
                        if fday is None:
                            if debugEvents:
                                print('%', angams, angam_num)
                            sys.stderr.write('Could not assign paraviddha day for %s!' %
                                             event_name +
                                             ' Please check for unusual cases.\n')
                        else:
                            sys.stderr.write('Assigned paraviddha day for %s!' %
                                             event_name + ' Ignore future warnings!\n')
                    elif priority == 'purvaviddha':
                        angams_yest = P.get_angams_for_kalas(d - 1, get_angam_func, kala)
                        if debugEvents:
                            print("%angams yest & today:", angams_yest)
                        if angams[0] == angam_num or angams[1] == angam_num:
                            if event_name in P.fest_days:
                                # Check if yesterday was assigned already
                                # to this purvaviddha festival!
                                if angam_num == 1:
                                    # Need to check if tomorrow is still the same month, unlikely!
                                    if P.lunar_month[d + 1] == month_num:
                                        if P.fest_days[event_name].count(d - 1) == 0:
                                            fday = d
                                            print('%%3B Assigned fday = %d' % d)
                                    else:
                                        continue

                                else:
                                    if P.fest_days[event_name].count(d - 1) == 0:
                                        fday = d
                                        print('%%3B Assigned fday = %d' % d)
                            else:
                                fday = d
                                print('%%4 Assigned fday = %d' % d)
                        elif angams[2] == angam_num or angams[3] == angam_num:
                            if (month_type == 'lunar_month' and P.lunar_month[d + 1] == month_num) or\
                               (month_type == 'solar_month' and P.solar_month[d + 1] == month_num):
                                fday = d + 1
                                print('%%5 Assigned fday = %d' % (d + 1))
                        else:
                            # This means that the correct angam did not
                            # touch the kalam on either day!
                            # sys.stderr.write('Could not assign purvaviddha day for %s!\
                            # Please check for unusual cases.\n' % event_name)
                            if angams[2] == angam_num_succ or angams[3] == angam_num_succ:
                                # Need to assign a day to the festival here
                                # since the angam did not touch kalam on either day
                                # BUT ONLY IF YESTERDAY WASN'T ALREADY ASSIGNED,
                                # THIS BEING PURVAVIDDHA
                                # Perhaps just need better checking of
                                # conditions instead of this fix
                                if event_name in P.fest_days:
                                    if P.fest_days[event_name].count(d - 1) == 0:
                                        fday = d
                                        print('%%6 Assigned fday = %d' % d)
                                else:
                                    fday = d
                                    print('%%7 Assigned fday = %d' % d)
                    else:
                        sys.stderr.write('Unknown priority "%s" for %s! Check the rules!' %
                                         (priority, event_name))
                # print (P.fest_days)
                if fday is not None:
                    P.addFestival(event_name, fday, debugEvents)

    for festival_name in P.fest_days:
        for j in range(0, len(P.fest_days[festival_name])):
            P.festivals[P.fest_days[festival_name][j]].append(festival_name)


def computeIcsCalendar(P, ics_file_name):
    P.ics_calendar = Calendar()
    for d in range(1, MAX_SZ - 1):
        [y, m, dt, t] = swe.revjul(P.jd_start + d - 1)

        if len(P.festivals[d]) > 0:
            # Eliminate repeat festivals on the same day, and keep the list arbitrarily sorted
            P.festivals[d] = sorted(list(set(P.festivals[d])))

            summary_text = P.festivals[d]
            # this will work whether we have one or more events on the same day
            for stext in summary_text:
                if not stext.find('>>') == -1:
                    # It's an event, with a start and end time
                    event = Event()
                    [stext, t1, arrow, t2] = stext.split('|')
                    event.add('summary', stext.split('|')[-1].replace('~', ' ').strip())
                    h1, m1 = t1.split(':')
                    h2, m2 = t2.split(':')
                    event.add('dtstart', datetime(y, m, dt, int(h1), int(m1),
                                                  tzinfo= tz(P.city.timezone)))
                    event.add('dtend', datetime(y, m, dt, int(h2), int(m2),
                                                tzinfo=tz(P.city.timezone)))
                    P.ics_calendar.add_component(event)
                else:
                    event = Event()
                    event.add('summary', stext.replace('~', ' '))
                    event.add('dtstart', date(y, m, dt))
                    event.add('dtend', (datetime(y, m, dt) + timedelta(1)).date())
                    alarm = Alarm()
                    alarm.add('action', 'DISPLAY')
                    alarm.add('trigger', timedelta(hours=-4))
                    event.add_component(alarm)
                    event['X-MICROSOFT-CDO-ALLDAYEVENT'] = 'TRUE'
                    event['TRANSP'] = 'TRANSPARENT'
                    event['X-MICROSOFT-CDO-BUSYSTATUS'] = 'FREE'

                    P.ics_calendar.add_component(event)

        if m == 12 and dt == 31:
            break

    with open(ics_file_name, 'wb') as ics_calendar_file:
        ics_calendar_file.write(P.ics_calendar.to_ical())


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

    fname_det = '../precomputed/%s-%s-detailed.pickle' % (city_name, year)
    fname = '../precomputed/%s-%s.pickle' % (city_name, year)

    if os.path.isfile(fname):
        # Load pickle, do not compute!
        with open(fname, 'rb') as f:
            Panchangam = pickle.load(f)
        sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
    elif os.path.isfile(fname_det):
        # Load pickle, do not compute!
        with open(fname_det, 'rb') as f:
            Panchangam = pickle.load(f)
        sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
    else:
        sys.stderr.write('No precomputed data available. Computing panchangam... ')
        sys.stderr.flush()
        Panchangam = panchangam(city=City, year=year, script=script)
        Panchangam.computeAngams(computeLagnams=False)
        Panchangam.assignLunarMonths()
        sys.stderr.write('done.\n')
        sys.stderr.write('Writing computed panchangam to %s...' % fname)
        with open(fname, 'wb') as f:
            # Pickle the 'data' dictionary using the highest protocol available.
            pickle.dump(Panchangam, f, pickle.HIGHEST_PROTOCOL)

    compute_events(Panchangam, json_file)
    cal_file_name = '../ics/%s-%s-%s' % (city_name, year, json_file.replace('.json', '.ics'))
    computeIcsCalendar(Panchangam, cal_file_name)
    print('Wrote ICS file to %s' % cal_file_name)


if __name__ == '__main__':
    main()
else:
    '''Imported as a module'''
