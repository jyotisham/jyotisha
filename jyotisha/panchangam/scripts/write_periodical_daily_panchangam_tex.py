#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import os
import os.path
import swisseph as swe
import sys
from datetime import datetime

from indic_transliteration import xsanscript as sanscript
from pytz import timezone as tz

import jyotisha
import jyotisha.custom_transliteration
import jyotisha.panchangam.spatio_temporal.periodical
import jyotisha.panchangam.temporal
from jyotisha.panchangam.spatio_temporal import City
from math import ceil

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def writeDailyTeX(panchangam, template_file, compute_lagnams=True, output_stream=None):
    """Write out the panchangam TeX using a specified template
    """
    # day_colours = {0: 'blue', 1: 'blue', 2: 'blue',
    #                3: 'blue', 4: 'blue', 5: 'blue', 6: 'blue'}
    month = {1: 'JANUARY', 2: 'FEBRUARY', 3: 'MARCH', 4: 'APRIL',
             5: 'MAY', 6: 'JUNE', 7: 'JULY', 8: 'AUGUST', 9: 'SEPTEMBER',
             10: 'OCTOBER', 11: 'NOVEMBER', 12: 'DECEMBER'}
    WDAY = {0: 'Sun', 1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat'}

    template_lines = template_file.readlines()
    for i in range(len(template_lines)):
        print(template_lines[i][:-1], file=output_stream)

    samvatsara_id_1 = (panchangam.start_date[0] - 1568) % 60 + 1  # distance from prabhava
    samvatsara_id_2 = (panchangam.end_date[0] - 1568) % 60 + 2  # distance from prabhava
    samvatsara_names = (jyotisha.panchangam.temporal.NAMES['SAMVATSARA_NAMES'][panchangam.script][samvatsara_id_1:samvatsara_id_2 + 1])

    yname = samvatsara_names[0]  # Assign year name until Mesha Sankranti

    print('\\mbox{}', file=output_stream)
    print('\\renewcommand{\\yearname}{%d}' % panchangam.start_date[0], file=output_stream)
    print('\\begin{center}', file=output_stream)
    print('{\\sffamily \\fontsize{60}{60}\\selectfont  %4d-%02d-%02d–%4d-%02d-%02d\\\\[0.5cm]}' % (panchangam.start_date[0], panchangam.start_date[1], panchangam.start_date[2], panchangam.end_date[0], panchangam.end_date[1], panchangam.end_date[2]), file=output_stream)
    print('\\mbox{\\fontsize{48}{48}\\selectfont %s–%s}\\\\'
          % (samvatsara_names[0], samvatsara_names[-1]), file=output_stream)
    print('\\mbox{\\fontsize{32}{32}\\selectfont %s } %%'
          % jyotisha.custom_transliteration.tr('kali', panchangam.script), file=output_stream)
    print('{\\sffamily \\fontsize{43}{43}\\selectfont  %d–%d\\\\[0.5cm]}\n\\hrule\n\\vspace{0.2cm}'
          % (panchangam.start_date[0] + 3100, panchangam.end_date[0] + 3101), file=output_stream)
    print('{\\sffamily \\fontsize{50}{50}\\selectfont  \\uppercase{%s}\\\\[0.2cm]}' % panchangam.city.name, file=output_stream)
    print('{\\sffamily \\fontsize{23}{23}\\selectfont  {%s}\\\\[0.2cm]}'
          % jyotisha.custom_transliteration.print_lat_lon(panchangam.city.latitude, panchangam.city.longitude), file=output_stream)
    print('\\hrule', file=output_stream)
    print('\\end{center}', file=output_stream)
    print('\\clearpage\\pagestyle{fancy}', file=output_stream)

    for d in range(1, panchangam.duration + 1):

        [y, m, dt, t] = swe.revjul(panchangam.jd_start_utc + d - 1)

        if m == 1 and dt == 1:
            print('\\renewcommand{\\yearname}{%d}' % y, file=output_stream)

        # What is the jd at 00:00 local time today?
        jd = panchangam.jd_midnight[d]

        tithi_data_str = ''
        for tithi_ID, tithi_end_jd in panchangam.tithi_data[d]:
            # if tithi_data_str != '':
            #     tithi_data_str += '\\hspace{1ex}'
            tithi = '\\raisebox{-1pt}{\moon[scale=0.8]{%d}}\\hspace{2pt}' % (tithi_ID) + \
                    jyotisha.panchangam.temporal.NAMES['TITHI_NAMES'][panchangam.script][tithi_ID]
            if tithi_end_jd is None:
                tithi_data_str = '%s\\mbox{%s\\To{}%s}' % \
                                 (tithi_data_str, tithi, jyotisha.custom_transliteration.tr('ahOrAtram (tridinaspRk)', panchangam.script))
            else:
                tithi_data_str = '%s\\mbox{%s\\To{}\\textsf{%s (%s)}}\\hspace{1ex}' % \
                                 (tithi_data_str, tithi,
                                  jyotisha.panchangam.temporal.Time(24 * (tithi_end_jd - panchangam.jd_sunrise[d])).toString(format='gg-pp'),
                                  jyotisha.panchangam.temporal.Time(24 * (tithi_end_jd - jd)).toString(format=panchangam.fmt))

        nakshatram_data_str = ''
        for nakshatram_ID, nakshatram_end_jd in panchangam.nakshatram_data[d]:
            if nakshatram_data_str != '':
                nakshatram_data_str += '\\hspace{1ex}'
            nakshatram = jyotisha.panchangam.temporal.NAMES['NAKSHATRAM_NAMES'][panchangam.script][nakshatram_ID]
            if nakshatram_end_jd is None:
                nakshatram_data_str = '%s\\mbox{%s\\To{}%s}' % \
                                      (nakshatram_data_str, nakshatram,
                                       jyotisha.custom_transliteration.tr('ahOrAtram', panchangam.script))
            else:
                nakshatram_data_str = '%s\\mbox{%s\\To{}\\textsf{%s (%s)}}' % \
                                      (nakshatram_data_str, nakshatram,
                                       jyotisha.panchangam.temporal.Time(24 * (nakshatram_end_jd - panchangam.jd_sunrise[d])).toString(format='gg-pp'),
                                       jyotisha.panchangam.temporal.Time(24 * (nakshatram_end_jd - jd)).toString(format=panchangam.fmt))

        rashi_data_str = ''
        for rashi_ID, rashi_end_jd in panchangam.rashi_data[d]:
            # if rashi_data_str != '':
            #     rashi_data_str += '\\hspace{1ex}'
            rashi = jyotisha.panchangam.temporal.NAMES['RASHI_SUFFIXED_NAMES'][panchangam.script][rashi_ID]
            if rashi_end_jd is None:
                rashi_data_str = '%s\\mbox{%s}' % (rashi_data_str, rashi)
            else:
                rashi_data_str = '%s\\mbox{%s \\RIGHTarrow \\textsf{%s}}' % \
                                 (rashi_data_str, rashi,
                                  jyotisha.panchangam.temporal.Time(24 * (rashi_end_jd - jd)).toString(format=panchangam.fmt))
        if compute_lagnams:
            lagna_data_str = 'लग्नम्–'
            for lagna_ID, lagna_end_jd in panchangam.lagna_data[d]:
                lagna = jyotisha.panchangam.temporal.NAMES['RASHI_NAMES'][panchangam.script][lagna_ID]
                lagna_data_str = '%s\\mbox{%s\\RIGHTarrow\\textsf{%s}} ' % \
                                 (lagna_data_str, lagna,
                                  jyotisha.panchangam.temporal.Time(24 * (lagna_end_jd - jd)).toString(format=panchangam.fmt))

        yoga_data_str = ''
        for yoga_ID, yoga_end_jd in panchangam.yoga_data[d]:
            # if yoga_data_str != '':
            #     yoga_data_str += '\\hspace{1ex}'
            yoga = jyotisha.panchangam.temporal.NAMES['YOGA_NAMES'][panchangam.script][yoga_ID]
            if yoga_end_jd is None:
                yoga_data_str = '%s\\mbox{%s\\To{}%s}' % \
                                 (yoga_data_str, yoga, jyotisha.custom_transliteration.tr('ahOrAtram', panchangam.script))
            else:
                yoga_data_str = '%s\\mbox{%s\\To{}\\textsf{%s (%s)}}\\hspace{1ex}' % \
                                 (yoga_data_str, yoga,
                                  jyotisha.panchangam.temporal.Time(24 * (yoga_end_jd - panchangam.jd_sunrise[d])).toString(format='gg-pp'),
                                  jyotisha.panchangam.temporal.Time(24 * (yoga_end_jd - jd)).toString(format=panchangam.fmt))
        if yoga_end_jd is not None:
            yoga_data_str += '\\mbox{%s\\Too{}}' % (jyotisha.panchangam.temporal.NAMES['YOGA_NAMES'][panchangam.script][(yoga_ID % 27) + 1])

        karanam_data_str = ''
        for numKaranam, (karanam_ID, karanam_end_jd) in enumerate(panchangam.karanam_data[d]):
            # if numKaranam == 1:
            #     karanam_data_str += '\\hspace{1ex}'
            karanam = jyotisha.panchangam.temporal.NAMES['KARANAM_NAMES'][panchangam.script][karanam_ID]
            if karanam_end_jd is None:
                karanam_data_str = '%s\\mbox{%s\\To{}%s}' % \
                                   (karanam_data_str, karanam, jyotisha.custom_transliteration.tr('ahOrAtram', panchangam.script))
            else:
                karanam_data_str = '%s\\mbox{%s\\To{}\\textsf{%s (%s)}}\\hspace{1ex}' % \
                                   (karanam_data_str, karanam,
                                    jyotisha.panchangam.temporal.Time(24 * (karanam_end_jd - panchangam.jd_sunrise[d])).toString(format='gg-pp'),
                                    jyotisha.panchangam.temporal.Time(24 * (karanam_end_jd - jd)).toString(format=panchangam.fmt))
        if karanam_end_jd is not None:
            karanam_data_str += '\\mbox{%s\\Too{}}' % (jyotisha.panchangam.temporal.NAMES['KARANAM_NAMES'][panchangam.script][(karanam_ID % 60) + 1])

        sunrise = jyotisha.panchangam.temporal.Time(24 * (panchangam.jd_sunrise[d] - jd)).toString(format=panchangam.fmt)
        sunset = jyotisha.panchangam.temporal.Time(24 * (panchangam.jd_sunset[d] - jd)).toString(format=panchangam.fmt)
        moonrise = jyotisha.panchangam.temporal.Time(24 * (panchangam.jd_moonrise[d] - jd)).toString(format=panchangam.fmt)
        moonset = jyotisha.panchangam.temporal.Time(24 * (panchangam.jd_moonset[d] - jd)).toString(format=panchangam.fmt)


        braahma = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['braahma'][0] - jd)).toString(format=panchangam.fmt)
        pratahsandhya = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['prAtaH sandhyA'][0] - jd)).toString(format=panchangam.fmt)
        pratahsandhya_end = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['prAtaH sandhyA end'][0] - jd)).toString(format=panchangam.fmt)
        sangava = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['saGgava'][0] - jd)).toString(format=panchangam.fmt)
        madhyaahna = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['madhyAhna'][0] - jd)).toString(format=panchangam.fmt)
        madhyahnika_sandhya = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['mAdhyAhnika sandhyA'][0] - jd)).toString(format=panchangam.fmt)
        madhyahnika_sandhya_end = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['mAdhyAhnika sandhyA end'][0] - jd)).toString(format=panchangam.fmt)
        aparahna = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['aparAhna'][0] - jd)).toString(format=panchangam.fmt)
        sayahna = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['sAyAhna'][0] - jd)).toString(format=panchangam.fmt)
        sayamsandhya = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['sAyaM sandhyA'][0] - jd)).toString(format=panchangam.fmt)
        sayamsandhya_end = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['sAyaM sandhyA end'][0] - jd)).toString(format=panchangam.fmt)
        ratriyama1 = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['rAtri yAma 1'][0] - jd)).toString(format=panchangam.fmt)
        sayana_time = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['zayana'][0] - jd)).toString(format=panchangam.fmt)
        dinanta = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['dinAnta'][0] - jd)).toString(format=panchangam.fmt)

        rahu = '%s--%s' % (
            jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['rahu'][0] - jd)).toString(format=panchangam.fmt),
            jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['rahu'][1] - jd)).toString(format=panchangam.fmt))
        yama = '%s--%s' % (
            jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['yama'][0] - jd)).toString(format=panchangam.fmt),
            jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['yama'][1] - jd)).toString(format=panchangam.fmt))
        gulika = '%s--%s' % (
            jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['gulika'][0] - jd)).toString(format=panchangam.fmt),
            jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['gulika'][1] - jd)).toString(format=panchangam.fmt))

        if panchangam.solar_month[d] == 1 and panchangam.solar_month[d - 1] == 12:
            # Move to next year
            yname = samvatsara_names[samvatsara_names.index(yname) + 1]

        # Assign samvatsara, ayana, rtu #
        sar_data = '{%s}{%s}{%s}' % (yname,
                                     jyotisha.panchangam.temporal.NAMES['AYANA_NAMES'][panchangam.script][panchangam.solar_month[d]],
                                     jyotisha.panchangam.temporal.NAMES['RTU_NAMES'][panchangam.script][panchangam.solar_month[d]])

        if panchangam.solar_month_end_time[d] is None:
            month_end_str = ''
        else:
            _m = panchangam.solar_month[d - 1]
            if panchangam.solar_month_end_time[d] >= panchangam.jd_sunrise[d + 1]:
                month_end_str = '\\mbox{%s{\\tiny\\RIGHTarrow}\\textsf{%s}}' % (jyotisha.panchangam.temporal.NAMES['RASHI_NAMES'][panchangam.script][_m], jyotisha.panchangam.temporal.Time(24 * (panchangam.solar_month_end_time[d] - panchangam.jd_midnight[d + 1])).toString(format=panchangam.fmt))
            else:
                month_end_str = '\\mbox{%s{\\tiny\\RIGHTarrow}\\textsf{%s}}' % (jyotisha.panchangam.temporal.NAMES['RASHI_NAMES'][panchangam.script][_m], jyotisha.panchangam.temporal.Time(24 * (panchangam.solar_month_end_time[d] - panchangam.jd_midnight[d])).toString(format=panchangam.fmt))

        month_data = '\\sunmonth{%s}{%d}{%s}' % (jyotisha.panchangam.temporal.NAMES['RASHI_NAMES'][panchangam.script][panchangam.solar_month[d]], panchangam.solar_month_day[d], month_end_str)

        print('\\caldata{%s}{%s}{%s{%s}{%s}{%s}%s}' %
              (month[m], dt, month_data,
               jyotisha.panchangam.temporal.get_chandra_masa(panchangam.lunar_month[d],
                                                             jyotisha.panchangam.temporal.NAMES, panchangam.script),
               jyotisha.panchangam.temporal.NAMES['RTU_NAMES'][panchangam.script][int(ceil(panchangam.lunar_month[d]))],
               jyotisha.panchangam.temporal.NAMES['VARA_NAMES'][panchangam.script][panchangam.weekday[d]], sar_data), file=output_stream)

        if panchangam.jd_moonrise[d] > panchangam.jd_sunrise[d + 1]:
          moonrise = '---'
        if panchangam.jd_moonset[d] > panchangam.jd_sunrise[d + 1]:
          moonset = '---'

        if panchangam.jd_moonrise[d] < panchangam.jd_moonset[d]:
          print('{\\sunmoonrsdata{%s}{%s}{%s}{%s}' % (sunrise, sunset, moonrise, moonset), file=output_stream)
        else:
          print('{\\sunmoonsrdata{%s}{%s}{%s}{%s}' % (sunrise, sunset, moonrise, moonset), file=output_stream)


        print('{\kalas{%s %s %s %s %s %s %s %s %s %s %s %s %s %s}}}' % (braahma, pratahsandhya, pratahsandhya_end,
                                                                     sangava,
                                                                     madhyahnika_sandhya, madhyahnika_sandhya_end,
                                                                     madhyaahna, aparahna, sayahna,
                                                                     sayamsandhya, sayamsandhya_end,
                                                                     ratriyama1, sayana_time, dinanta), file=output_stream)
        if compute_lagnams:
            print('{\\tnykdata{%s}%%\n{%s}{%s}%%\n{%s}%%\n{%s}{%s}\n}'
                  % (tithi_data_str, nakshatram_data_str, rashi_data_str, yoga_data_str,
                     karanam_data_str, lagna_data_str), file=output_stream)
        else:
            print('{\\tnykdata{%s}%%\n{%s}{%s}%%\n{%s}%%\n{%s}{\\scriptsize %s}\n}'
                  % (tithi_data_str, nakshatram_data_str, rashi_data_str, yoga_data_str,
                     karanam_data_str, ''), file=output_stream)

        # Using set as an ugly workaround since we may have sometimes assigned the same
        # festival to the same day again!
        print('{%s}' % '\\eventsep '.join(
            [jyotisha.custom_transliteration.tr(f, panchangam.script).replace('★', '$^\\star$') for f in sorted(set(panchangam.festivals[d]))]), file=output_stream)

        print('{%s} ' % WDAY[panchangam.weekday[d]], file=output_stream)
        print('\\cfoot{\\rygdata{%s}{%s}{%s}}' % (rahu, yama, gulika), file=output_stream)

    print('\\end{document}', file=output_stream)


def main():
    [city_name, latitude, longitude, tz] = sys.argv[1:5]
    start_date = sys.argv[5]
    end_date = sys.argv[6]

    compute_lagnams = False  # Default
    script = sanscript.DEVANAGARI  # Default script is devanagari
    fmt = 'hh:mm'

    if len(sys.argv) == 10:
        compute_lagnams = True
        fmt = sys.argv[8]
        script = sys.argv[7]
    elif len(sys.argv) == 9:
        script = sys.argv[7]
        fmt = sys.argv[8]
        compute_lagnams = False
    elif len(sys.argv) == 8:
        script = sys.argv[7]
        compute_lagnams = False

    city = City(city_name, latitude, longitude, tz)

    panchangam = jyotisha.panchangam.spatio_temporal.periodical.get_panchangam(city=city, start_date=start_date, end_date=end_date, script=script, fmt=fmt, compute_lagnams=compute_lagnams, ayanamsha_id=swe.SIDM_TRUE_CITRA)
    panchangam.script = script  # Force script irrespective of what was obtained from saved file
    panchangam.fmt = fmt  # Force fmt

    panchangam.update_festival_details()

    daily_template_file = open(os.path.join(CODE_ROOT, 'panchangam/data/templates/daily_cal_template.tex'))
    writeDailyTeX(panchangam, daily_template_file, compute_lagnams)
    # panchangam.writeDebugLog()


if __name__ == '__main__':
    main()
