#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import os
import os.path
import sys
from datetime import datetime
from math import ceil

from indic_transliteration import xsanscript as sanscript
from pytz import timezone as tz

import jyotisha
import jyotisha.custom_transliteration
import jyotisha.names
import jyotisha.panchaanga.spatio_temporal.annual
import jyotisha.panchaanga.temporal

from jyotisha.panchaanga.spatio_temporal import City
from jyotisha.panchaanga.temporal import zodiac, time

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def writeDailyTeX(panchaanga, template_file, compute_lagnams=True, output_stream=None):
  """Write out the panchaanga TeX using a specified template
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

  year = panchaanga.start_date[0]
  logging.debug(year)

  samvatsara_id = (year - 1568) % 60 + 1  # distance from prabhava
  samvatsara_names = (jyotisha.names.NAMES['SAMVATSARA_NAMES'][panchaanga.script][samvatsara_id],
                      jyotisha.names.NAMES['SAMVATSARA_NAMES'][panchaanga.script][(samvatsara_id % 60) + 1])

  yname = samvatsara_names[0]  # Assign year name until Mesha Sankranti

  print('\\mbox{}', file=output_stream)
  print('\\renewcommand{\\yearname}{%d}' % year, file=output_stream)
  print('\\begin{center}', file=output_stream)
  print('{\\sffamily \\fontsize{80}{80}\\selectfont  %d\\\\[0.5cm]}' % year, file=output_stream)
  print('\\mbox{\\fontsize{48}{48}\\selectfont %s–%s}\\\\'
        % samvatsara_names, file=output_stream)
  print('\\mbox{\\fontsize{32}{32}\\selectfont %s } %%'
        % jyotisha.custom_transliteration.tr('kali', panchaanga.script), file=output_stream)
  print('{\\sffamily \\fontsize{43}{43}\\selectfont  %d–%d\\\\[0.5cm]}\n\\hrule\n\\vspace{0.2cm}'
        % (year + 3100, year + 3101), file=output_stream)
  print('{\\sffamily \\fontsize{50}{50}\\selectfont  \\uppercase{%s}\\\\[0.2cm]}' % panchaanga.city.name,
        file=output_stream)
  print('{\\sffamily \\fontsize{23}{23}\\selectfont  {%s}\\\\[0.2cm]}'
        % jyotisha.custom_transliteration.print_lat_lon(panchaanga.city.latitude, panchaanga.city.longitude),
        file=output_stream)
  print('\\hrule', file=output_stream)
  print('\\end{center}', file=output_stream)
  print('\\clearpage\\pagestyle{fancy}', file=output_stream)

  for d in range(1, jyotisha.panchaanga.temporal.MAX_SZ - 1):

    [y, m, dt, t] = time.jd_to_utc_gregorian(panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

    # checking @ 6am local - can we do any better?
    local_time = tz(panchaanga.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
    # compute offset from UTC in hours
    tz_off = (datetime.utcoffset(local_time).days * 86400 +
              datetime.utcoffset(local_time).seconds) / 3600.0

    # What is the jd at 00:00 local time today?
    jd = panchaanga.daily_panchaangas[d].julian_day_start

    tithi_data_str = ''
    for tithi_ID, tithi_end_jd in panchaanga.daily_panchaangas[d].tithi_data:
      # if tithi_data_str != '':
      #     tithi_data_str += '\\hspace{1ex}'
      tithi = '\\raisebox{-1pt}{\\moon[scale=0.8]{%d}}\\hspace{2pt}' % (tithi_ID) + \
              jyotisha.names.NAMES['TITHI_NAMES'][panchaanga.script][tithi_ID]
      if tithi_end_jd is None:
        tithi_data_str = '%s\\mbox{%s\\To{}%s}' % \
                         (tithi_data_str, tithi,
                          jyotisha.custom_transliteration.tr('ahOrAtram (tridinaspRk)', panchaanga.script))
      else:
        tithi_data_str = '%s\\mbox{%s\\To{}\\textsf{%s (%s)}}\\hspace{1ex}' % \
                         (tithi_data_str, tithi,
                          time.Hour(
                            24 * (tithi_end_jd - panchaanga.daily_panchaangas[d].jd_sunrise)).toString(format='gg-pp'),
                          time.Hour(24 * (tithi_end_jd - jd)).toString(
                            format=panchaanga.fmt))

    nakshatram_data_str = ''
    for nakshatram_ID, nakshatram_end_jd in panchaanga.daily_panchaangas[d].nakshatra_data:
      if nakshatram_data_str != '':
        nakshatram_data_str += '\\hspace{1ex}'
      nakshatram = jyotisha.names.NAMES['NAKSHATRAM_NAMES'][panchaanga.script][nakshatram_ID]
      if nakshatram_end_jd is None:
        nakshatram_data_str = '%s\\mbox{%s\\To{}%s}' % \
                              (nakshatram_data_str, nakshatram,
                               jyotisha.custom_transliteration.tr('ahOrAtram', panchaanga.script))
      else:
        nakshatram_data_str = '%s\\mbox{%s\\To{}\\textsf{%s (%s)}}' % \
                              (nakshatram_data_str, nakshatram,
                               time.Hour(
                                 24 * (nakshatram_end_jd - panchaanga.daily_panchaangas[d].jd_sunrise)).toString(format='gg-pp'),
                               time.Hour(24 * (nakshatram_end_jd - jd)).toString(
                                 format=panchaanga.fmt))

    rashi_data_str = ''
    for rashi_ID, rashi_end_jd in panchaanga.daily_panchaangas[d].raashi_data:
      # if rashi_data_str != '':
      #     rashi_data_str += '\\hspace{1ex}'
      rashi = jyotisha.names.NAMES['RASHI_SUFFIXED_NAMES'][panchaanga.script][rashi_ID]
      if rashi_end_jd is None:
        rashi_data_str = '%s\\mbox{%s}' % (rashi_data_str, rashi)
      else:
        rashi_data_str = '%s\\mbox{%s \\RIGHTarrow \\textsf{%s}}' % \
                         (rashi_data_str, rashi,
                          time.Hour(24 * (rashi_end_jd - jd)).toString(
                            format=panchaanga.fmt))
    if compute_lagnams:
      lagna_data_str = 'लग्नम्–'
      for lagna_ID, lagna_end_jd in panchaanga.daily_panchaangas[d].lagna_data:
        lagna = jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][lagna_ID]
        lagna_data_str = '%s\\mbox{%s\\RIGHTarrow\\textsf{%s}} ' % \
                         (lagna_data_str, lagna,
                          time.Hour(24 * (lagna_end_jd - jd)).toString(
                            format=panchaanga.fmt))

    yoga_data_str = ''
    for yoga_ID, yoga_end_jd in panchaanga.daily_panchaangas[d].yoga_data:
      # if yoga_data_str != '':
      #     yoga_data_str += '\\hspace{1ex}'
      yoga = jyotisha.names.NAMES['YOGA_NAMES'][panchaanga.script][yoga_ID]
      if yoga_end_jd is None:
        yoga_data_str = '%s\\mbox{%s\\To{}%s}' % \
                        (yoga_data_str, yoga, jyotisha.custom_transliteration.tr('ahOrAtram', panchaanga.script))
      else:
        yoga_data_str = '%s\\mbox{%s\\To{}\\textsf{%s (%s)}}\\hspace{1ex}' % \
                        (yoga_data_str, yoga,
                         time.Hour(24 * (yoga_end_jd - panchaanga.daily_panchaangas[d].jd_sunrise)).toString(
                           format='gg-pp'),
                         time.Hour(24 * (yoga_end_jd - jd)).toString(
                           format=panchaanga.fmt))
    if yoga_end_jd is not None:
      yoga_data_str += '\\mbox{%s\\Too{}}' % (
        jyotisha.names.NAMES['YOGA_NAMES'][panchaanga.script][(yoga_ID % 27) + 1])

    karanam_data_str = ''
    for numKaranam, (karanam_ID, karanam_end_jd) in enumerate(panchaanga.daily_panchaangas[d].karana_data):
      # if numKaranam == 1:
      #     karanam_data_str += '\\hspace{1ex}'
      karanam = jyotisha.names.NAMES['KARANAM_NAMES'][panchaanga.script][karanam_ID]
      if karanam_end_jd is None:
        karanam_data_str = '%s\\mbox{%s\\To{}%s}' % \
                           (karanam_data_str, karanam,
                            jyotisha.custom_transliteration.tr('ahOrAtram', panchaanga.script))
      else:
        karanam_data_str = '%s\\mbox{%s\\To{}\\textsf{%s (%s)}}\\hspace{1ex}' % \
                           (karanam_data_str, karanam,
                            time.Hour(
                              24 * (karanam_end_jd - panchaanga.daily_panchaangas[d].jd_sunrise)).toString(format='gg-pp'),
                            time.Hour(24 * (karanam_end_jd - jd)).toString(
                              format=panchaanga.fmt))
    if karanam_end_jd is not None:
      karanam_data_str += '\\mbox{%s\\Too{}}' % (
        jyotisha.names.NAMES['KARANAM_NAMES'][panchaanga.script][(karanam_ID % 60) + 1])

    sunrise = time.Hour(24 * (panchaanga.daily_panchaangas[d].jd_sunrise - jd)).toString(
      format=panchaanga.fmt)
    sunset = time.Hour(24 * (panchaanga.daily_panchaangas[d].jd_sunset - jd)).toString(format=panchaanga.fmt)
    moonrise = time.Hour(24 * (panchaanga.daily_panchaangas[d].jd_moonrise - jd)).toString(
      format=panchaanga.fmt)
    moonset = time.Hour(24 * (panchaanga.daily_panchaangas[d].jd_moonset - jd)).toString(
      format=panchaanga.fmt)

    braahma_start = time.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['braahma'][0] - jd)).toString(
      format=panchaanga.fmt)
    pratahsandhya_start = time.Hour(
      24 * (panchaanga.daily_panchaangas[d].kaalas['prAtaH sandhyA'][0] - jd)).toString(format=panchaanga.fmt)
    pratahsandhya_end = time.Hour(
      24 * (panchaanga.daily_panchaangas[d].kaalas['prAtaH sandhyA end'][0] - jd)).toString(format=panchaanga.fmt)
    sangava = time.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['saGgava'][0] - jd)).toString(
      format=panchaanga.fmt)
    madhyaahna = time.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['madhyAhna'][0] - jd)).toString(
      format=panchaanga.fmt)
    madhyahnika_sandhya_start = time.Hour(
      24 * (panchaanga.daily_panchaangas[d].kaalas['mAdhyAhnika sandhyA'][0] - jd)).toString(format=panchaanga.fmt)
    madhyahnika_sandhya_end = time.Hour(
      24 * (panchaanga.daily_panchaangas[d].kaalas['mAdhyAhnika sandhyA end'][0] - jd)).toString(format=panchaanga.fmt)
    aparahna = time.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['aparAhna'][0] - jd)).toString(
      format=panchaanga.fmt)
    sayahna = time.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['sAyAhna'][0] - jd)).toString(
      format=panchaanga.fmt)
    sayamsandhya_start = time.Hour(
      24 * (panchaanga.daily_panchaangas[d].kaalas['sAyaM sandhyA'][0] - jd)).toString(format=panchaanga.fmt)
    sayamsandhya_end = time.Hour(
      24 * (panchaanga.daily_panchaangas[d].kaalas['sAyaM sandhyA end'][0] - jd)).toString(format=panchaanga.fmt)
    ratriyama1 = time.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['rAtri yAma 1'][0] - jd)).toString(
      format=panchaanga.fmt)
    shayana_time_end = time.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['zayana'][0] - jd)).toString(
      format=panchaanga.fmt)
    dinanta = time.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['dinAnta'][0] - jd)).toString(
      format=panchaanga.fmt)

    rahu = '%s--%s' % (
      time.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['rahu'][0] - jd)).toString(
        format=panchaanga.fmt),
      time.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['rahu'][1] - jd)).toString(
        format=panchaanga.fmt))
    yama = '%s--%s' % (
      time.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['yama'][0] - jd)).toString(
        format=panchaanga.fmt),
      time.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['yama'][1] - jd)).toString(
        format=panchaanga.fmt))
    gulika = '%s--%s' % (
      time.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['gulika'][0] - jd)).toString(
        format=panchaanga.fmt),
      time.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['gulika'][1] - jd)).toString(
        format=panchaanga.fmt))

    if panchaanga.solar_month[d] == 1:
      # Flip the year name for the remaining days
      yname = samvatsara_names[1]

    # Assign samvatsara, ayana, rtu #
    sar_data = '{%s}{%s}{%s}' % (yname,
                                 jyotisha.names.NAMES['AYANA_NAMES'][panchaanga.script][panchaanga.solar_month[d]],
                                 jyotisha.names.NAMES['RTU_NAMES'][panchaanga.script][panchaanga.solar_month[d]])

    if panchaanga.solar_month_end_time[d] is None:
      month_end_str = ''
    else:
      _m = panchaanga.solar_month[d - 1]
      if panchaanga.solar_month_end_time[d] >= panchaanga.daily_panchaangas[d + 1].jd_sunrise:
        month_end_str = '\\mbox{%s{\\tiny\\RIGHTarrow}\\textsf{%s}}' % (
          jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][_m], time.Hour(
            24 * (panchaanga.solar_month_end_time[d] - panchaanga.daily_panchaangas[d + 1].julian_day_start)).toString(format=panchaanga.fmt))
      else:
        month_end_str = '\\mbox{%s{\\tiny\\RIGHTarrow}\\textsf{%s}}' % (
          jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][_m], time.Hour(
            24 * (panchaanga.solar_month_end_time[d] - panchaanga.daily_panchaangas[d].julian_day_start)).toString(format=panchaanga.fmt))

    month_data = '\\sunmonth{%s}{%d}{%s}' % (
      jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][panchaanga.solar_month[d]], panchaanga.solar_month_day[d],
      month_end_str)

    print('\\caldata{%s}{%s}{%s{%s}{%s}{%s}%s}' %
          (month[m], dt, month_data,
           jyotisha.names.get_chandra_masa(panchaanga.lunar_month[d],
                                           jyotisha.names.NAMES, panchaanga.script),
           jyotisha.names.NAMES['RTU_NAMES'][panchaanga.script][int(ceil(panchaanga.lunar_month[d]))],
           jyotisha.names.NAMES['VARA_NAMES'][panchaanga.script][panchaanga.daily_panchaangas[d].date.get_weekday()], sar_data), file=output_stream)

    if panchaanga.daily_panchaangas[d].jd_moonrise > panchaanga.daily_panchaangas[d + 1].jd_sunrise:
      moonrise = '---'
    if panchaanga.daily_panchaangas[d].jd_moonset > panchaanga.daily_panchaangas[d + 1].jd_sunrise:
      moonset = '---'

    if panchaanga.daily_panchaangas[d].jd_moonrise < panchaanga.daily_panchaangas[d].jd_moonset:
      print('{\\sunmoonrsdata{%s}{%s}{%s}{%s}' % (sunrise, sunset, moonrise, moonset), file=output_stream)
    else:
      print('{\\sunmoonsrdata{%s}{%s}{%s}{%s}' % (sunrise, sunset, moonrise, moonset), file=output_stream)

    print(
      '{\\kalas{%s %s %s %s %s %s %s %s %s %s %s %s %s %s}}}' % (braahma_start, pratahsandhya_start, pratahsandhya_end,
                                                                sangava,
                                                                madhyahnika_sandhya_start, madhyahnika_sandhya_end,
                                                                madhyaahna, aparahna, sayahna,
                                                                sayamsandhya_start, sayamsandhya_end,
                                                                ratriyama1, shayana_time_end, dinanta),
      file=output_stream)
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
      [jyotisha.custom_transliteration.tr(f, panchaanga.script).replace('★', '$^\\star$') for f in
       sorted(set(panchaanga.daily_panchaangas[d].festivals))]), file=output_stream)

    print('{%s} ' % WDAY[panchaanga.daily_panchaangas[d].date.get_weekday()], file=output_stream)
    print('\\cfoot{\\rygdata{%s}{%s}{%s}}' % (rahu, yama, gulika), file=output_stream)

    if m == 12 and dt == 31:
      break

  print('\\end{document}', file=output_stream)


def main():
  [city_name, latitude, longitude, tz] = sys.argv[1:5]
  year = int(sys.argv[5])

  compute_lagnams = False  # Default
  script = sanscript.DEVANAGARI  # Default script is devanagari
  fmt = 'hh:mm'

  if len(sys.argv) == 9:
    compute_lagnams = True
    fmt = sys.argv[7]
    script = sys.argv[6]
  elif len(sys.argv) == 8:
    script = sys.argv[6]
    fmt = sys.argv[7]
    compute_lagnams = False
  elif len(sys.argv) == 7:
    script = sys.argv[6]
    compute_lagnams = False

  city = City(city_name, latitude, longitude, tz)

  panchaanga = jyotisha.panchaanga.spatio_temporal.annual.get_panchaanga(city=city, year=year, script=script, fmt=fmt,
                                                                         compute_lagnas=compute_lagnams,
                                                                         ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180)
  panchaanga.script = script  # Force script irrespective of what was obtained from saved file
  panchaanga.fmt = fmt  # Force fmt

  panchaanga.update_festival_details()

  daily_template_file = open(os.path.join(CODE_ROOT, 'panchaanga/data/templates/daily_cal_template.tex'))
  writeDailyTeX(panchaanga, daily_template_file, compute_lagnams)
  # panchaanga.writeDebugLog()


if __name__ == '__main__':
  main()
