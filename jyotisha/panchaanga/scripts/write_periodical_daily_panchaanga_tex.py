#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import os
import os.path
import sys
from math import ceil

from indic_transliteration import xsanscript as sanscript

import jyotisha
import jyotisha.custom_transliteration
import jyotisha.names
from jyotisha.panchaanga.spatio_temporal import City
from jyotisha.panchaanga.temporal import zodiac
from jyotisha.panchaanga.temporal.nakshatra import NakshatraAssigner

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

CODE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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

  kali_year_start = panchaanga.start_date[0] + 3100 + (panchaanga.solar_month[1] == 1)
  kali_year_end = panchaanga.end_date[0] + 3100 + (panchaanga.solar_month[panchaanga.duration] == 1)
  # Aligning to prabhava cycle from Kali start (+12 below)
  samvatsara_names = [jyotisha.names.NAMES['SAMVATSARA_NAMES'][panchaanga.script][(_x + 12) % 60 + 1] for _x in
                      list(range(kali_year_start, kali_year_end + 1))]
  yname = samvatsara_names[0]  # Assign year name until Mesha Sankranti

  print('\\mbox{}', file=output_stream)
  print('\\renewcommand{\\yearname}{%d}' % panchaanga.start_date[0], file=output_stream)
  print('\\begin{center}', file=output_stream)
  print('{\\sffamily \\fontsize{20}{20}\\selectfont  %4d-%02d-%02d–%4d-%02d-%02d\\\\[0.5cm]}'
        % (panchaanga.start_date[0], panchaanga.start_date[1], panchaanga.start_date[2], panchaanga.end_date[0],
           panchaanga.end_date[1], panchaanga.end_date[2]), file=output_stream)

  print('\\mbox{\\fontsize{48}{48}\\selectfont %s}\\\\'
        % ('–'.join(list(set(samvatsara_names[:2])))), file=output_stream)
  print('\\mbox{\\fontsize{32}{32}\\selectfont %s } %%'
        % jyotisha.custom_transliteration.tr('kali', panchaanga.script), file=output_stream)
  print('{\\sffamily \\fontsize{43}{43}\\selectfont  %s\\\\[0.5cm]}\n\\hrule\n\\vspace{0.2cm}'
        % '–'.join([str(_y) for _y in set([kali_year_start, kali_year_end])]), file=output_stream)
  print('{\\sffamily \\fontsize{50}{50}\\selectfont  \\uppercase{%s}\\\\[0.2cm]}' % panchaanga.city.name,
        file=output_stream)
  print('{\\sffamily \\fontsize{23}{23}\\selectfont  {%s}\\\\[0.2cm]}'
        % jyotisha.custom_transliteration.print_lat_lon(panchaanga.city.latitude, panchaanga.city.longitude),
        file=output_stream)
  print('\\hrule', file=output_stream)
  print('\\end{center}', file=output_stream)
  print('\\clearpage\\pagestyle{fancy}', file=output_stream)

  nakshatra_assigner = NakshatraAssigner(panchaanga)
  nakshatra_assigner.calc_nakshatra_tyaajya(False)
  nakshatra_assigner.calc_nakshatra_amrta(False)

  for d in range(1, panchaanga.duration + 1):

    [y, m, dt, t] = time.jd_to_utc_gregorian(panchaanga.jd_start + d - 1)

    if m == 1 and dt == 1:
      print('\\renewcommand{\\yearname}{%d}' % y, file=output_stream)

    # What is the jd at 00:00 local time today?
    jd = panchaanga.daily_panchaangas[d].julian_day_start

    tithi_data_str = ''
    for tithi_ID, tithi_end_jd in panchaanga.daily_panchaangas[d].tithi_data:
      if tithi_data_str != '':
        tithi_data_str += '\\hspace{1ex}'
      tithi = '\\raisebox{-1pt}{\moon[scale=0.8]{%d}}\\hspace{2pt}' % (tithi_ID) + \
              jyotisha.names.NAMES['TITHI_NAMES'][panchaanga.script][tithi_ID]
      if tithi_end_jd is None:
        tithi_data_str = '%s\\mbox{%s\\To{}%s\\tridina}' % \
                         (tithi_data_str, tithi, jyotisha.custom_transliteration.tr('ahOrAtram', panchaanga.script))
      else:
        tithi_data_str = '%s\\mbox{%s\\To{}\\textsf{%s (%s)}}' % \
                         (tithi_data_str, tithi,
                          jyotisha.panchaanga.temporal.hour.Hour(
                            24 * (tithi_end_jd - panchaanga.daily_panchaangas[d].jd_sunrise)).toString(format='gg-pp'),
                          jyotisha.panchaanga.temporal.hour.Hour(24 * (tithi_end_jd - jd)).toString(
                            format=panchaanga.fmt))
    if len(panchaanga.daily_panchaangas[d].tithi_data) == 2:
      tithi_data_str += '\\avamA{}'

    nakshatram_data_str = ''
    amritadi_yoga_list = []
    for nakshatram_ID, nakshatram_end_jd in panchaanga.daily_panchaangas[d].nakshatra_data:
      if nakshatram_data_str != '':
        nakshatram_data_str += '\\hspace{1ex}'
      nakshatram = jyotisha.names.NAMES['NAKSHATRAM_NAMES'][panchaanga.script][nakshatram_ID]
      if len(amritadi_yoga_list) == 0:  # Otherwise, we would have already added in the previous run of this for loop
        amritadi_yoga_list.append(
          jyotisha.panchaanga.temporal.nakshatra.AMRITADI_YOGA[panchaanga.weekday[d]][nakshatram_ID])
      if nakshatram_end_jd is None:
        nakshatram_data_str = '%s\\mbox{%s\\To{}%s}' % \
                              (nakshatram_data_str, nakshatram,
                               jyotisha.custom_transliteration.tr('ahOrAtram', panchaanga.script))
      else:
        next_yoga = jyotisha.panchaanga.temporal.nakshatra.AMRITADI_YOGA[panchaanga.weekday[d]][(nakshatram_ID % 27) + 1]
        if amritadi_yoga_list[-1] != next_yoga:
          amritadi_yoga_list.append(next_yoga)
        nakshatram_data_str = '%s\\mbox{%s\\To{}\\textsf{%s (%s)}}' % \
                              (nakshatram_data_str, nakshatram,
                               jyotisha.panchaanga.temporal.hour.Hour(
                                 24 * (nakshatram_end_jd - panchaanga.daily_panchaangas[d].jd_sunrise)).toString(format='gg-pp'),
                               jyotisha.panchaanga.temporal.hour.Hour(24 * (nakshatram_end_jd - jd)).toString(
                                 format=panchaanga.fmt))
    amritadi_yoga_str = '/'.join(
      [jyotisha.custom_transliteration.tr(_x, panchaanga.script) for _x in amritadi_yoga_list])
    if len(panchaanga.daily_panchaangas[d].nakshatra_data) == 2:
      nakshatram_data_str += '\\avamA{}'

    if panchaanga.tyajyam_data[d] == []:
      tyajyam_data_str = '---'
    else:
      tyajyam_data_str = ''
      for td in panchaanga.tyajyam_data[d]:
        tyajyam_data_str += '%s--%s\\hspace{2ex}' % (
          jyotisha.panchaanga.temporal.hour.Hour(24 * (td[0] - jd)).toString(format=panchaanga.fmt),
          jyotisha.panchaanga.temporal.hour.Hour(24 * (td[1] - jd)).toString(format=panchaanga.fmt))

    if panchaanga.amrita_data[d] == []:
      amrita_data_str = '---'
    else:
      amrita_data_str = ''
      for td in panchaanga.amrita_data[d]:
        amrita_data_str += '%s--%s\\hspace{2ex}' % (
          jyotisha.panchaanga.temporal.hour.Hour(24 * (td[0] - jd)).toString(format=panchaanga.fmt),
          jyotisha.panchaanga.temporal.hour.Hour(24 * (td[1] - jd)).toString(format=panchaanga.fmt))

    rashi_data_str = 'चन्द्रराशिः—'
    for rashi_ID, rashi_end_jd in panchaanga.daily_panchaangas[d].raashi_data:
      # if rashi_data_str != '':
      #     rashi_data_str += '\\hspace{1ex}'
      rashi = jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][rashi_ID]
      if rashi_end_jd is None:
        rashi_data_str = '%s\\mbox{%s}' % (rashi_data_str, rashi)
      else:
        rashi_data_str = '%s\\mbox{%s\\RIGHTarrow\\textsf{%s}}' % \
                         (rashi_data_str, rashi,
                          jyotisha.panchaanga.temporal.hour.Hour(24 * (rashi_end_jd - jd)).toString(
                            format=panchaanga.fmt))

    chandrashtama_rashi_data_str = 'चन्द्राष्टम-राशिः—'
    for rashi_ID, rashi_end_jd in panchaanga.daily_panchaangas[d].raashi_data:
      rashi = jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][rashi_ID]
      if rashi_end_jd is None:
        chandrashtama_rashi_data_str = '\\mbox{%s%s}' % (
        chandrashtama_rashi_data_str, jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][((rashi_ID - 8) % 12) + 1])
      else:
        chandrashtama_rashi_data_str = '\\mbox{%s%s\To{}\\textsf{%s}}' % (
        chandrashtama_rashi_data_str, jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][((rashi_ID - 8) % 12) + 1],
        jyotisha.panchaanga.temporal.hour.Hour(24 * (rashi_end_jd - jd)).toString(format=panchaanga.fmt))

    SHULAM = [('pratIcyAm', 12, 'guDam'), ('prAcyAm', 8, 'dadhi'), ('udIcyAm', 12, 'kSIram'),
              ('udIcyAm', 16, 'kSIram'), ('dakSiNAyAm', 20, 'tailam'), ('pratIcyAm', 12, 'guDam'),
              ('prAcyAm', 8, 'dadhi')]
    shulam_end_jd = panchaanga.daily_panchaangas[d].jd_sunrise + (panchaanga.daily_panchaangas[d].jd_sunset - panchaanga.daily_panchaangas[d].jd_sunrise) * (
          SHULAM[panchaanga.weekday[d]][1] / 30)
    shulam_data_str = '%s—%s (\\RIGHTarrow\\textsf{%s})  %s–%s' % (
    jyotisha.custom_transliteration.tr('zUlam', panchaanga.script),
    jyotisha.custom_transliteration.tr(SHULAM[panchaanga.weekday[d]][0], panchaanga.script),
    jyotisha.panchaanga.temporal.hour.Hour(24 * (shulam_end_jd - jd)).toString(format=panchaanga.fmt),
    jyotisha.custom_transliteration.tr('parihAraH', panchaanga.script),
    jyotisha.custom_transliteration.tr(SHULAM[panchaanga.weekday[d]][2], panchaanga.script))

    if compute_lagnams:
      lagna_data_str = 'लग्नानि–'
      for lagna_ID, lagna_end_jd in panchaanga.lagna_data[d]:
        lagna = jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][lagna_ID]
        lagna_data_str = '%s\\mbox{%s\\RIGHTarrow\\textsf{%s}} ' % \
                         (lagna_data_str, lagna,
                          jyotisha.panchaanga.temporal.hour.Hour(24 * (lagna_end_jd - jd)).toString(
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
                         jyotisha.panchaanga.temporal.hour.Hour(24 * (yoga_end_jd - panchaanga.daily_panchaangas[d].jd_sunrise)).toString(
                           format='gg-pp'),
                         jyotisha.panchaanga.temporal.hour.Hour(24 * (yoga_end_jd - jd)).toString(
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
                            jyotisha.panchaanga.temporal.hour.Hour(
                              24 * (karanam_end_jd - panchaanga.daily_panchaangas[d].jd_sunrise)).toString(format='gg-pp'),
                            jyotisha.panchaanga.temporal.hour.Hour(24 * (karanam_end_jd - jd)).toString(
                              format=panchaanga.fmt))
    if karanam_end_jd is not None:
      karanam_data_str += '\\mbox{%s\\Too{}}' % (
        jyotisha.names.NAMES['KARANAM_NAMES'][panchaanga.script][(karanam_ID % 60) + 1])

    if panchaanga.daily_panchaangas[d].shraaddha_tithi == [None]:
      stithi_data_str = '---'
    else:
      if panchaanga.daily_panchaangas[d].shraaddha_tithi[0] == 0:
        stithi_data_str = jyotisha.custom_transliteration.tr('zUnyatithiH', panchaanga.script)
      else:
        t1 = jyotisha.names.NAMES['TITHI_NAMES'][panchaanga.script][panchaanga.daily_panchaangas[d].shraaddha_tithi[0]]
        if len(panchaanga.daily_panchaangas[d].shraaddha_tithi) == 2:
          t2 = jyotisha.names.NAMES['TITHI_NAMES'][panchaanga.script][panchaanga.daily_panchaangas[d].shraaddha_tithi[1]]
          stithi_data_str = '%s/%s (%s)' % \
                            (t1.split('-')[-1], t2.split('-')[-1],
                             jyotisha.custom_transliteration.tr('tithidvayam', panchaanga.script))
        else:
          stithi_data_str = '%s' % (t1.split('-')[-1])

    sunrise = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].jd_sunrise - jd)).toString(
      format=panchaanga.fmt)
    sunset = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].jd_sunset - jd)).toString(format=panchaanga.fmt)
    moonrise = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].jd_moonrise - jd)).toString(
      format=panchaanga.fmt)
    moonset = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].jd_moonset - jd)).toString(
      format=panchaanga.fmt)

    braahma_start = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.kaalas[d]['braahma'][0] - jd)).toString(
      format=panchaanga.fmt)
    pratahsandhya_start = jyotisha.panchaanga.temporal.hour.Hour(
      24 * (panchaanga.kaalas[d]['prAtaH sandhyA'][0] - jd)).toString(format=panchaanga.fmt)
    pratahsandhya_end = jyotisha.panchaanga.temporal.hour.Hour(
      24 * (panchaanga.kaalas[d]['prAtaH sandhyA end'][0] - jd)).toString(format=panchaanga.fmt)
    sangava = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.kaalas[d]['saGgava'][0] - jd)).toString(
      format=panchaanga.fmt)
    madhyaahna = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.kaalas[d]['madhyAhna'][0] - jd)).toString(
      format=panchaanga.fmt)
    madhyahnika_sandhya_start = jyotisha.panchaanga.temporal.hour.Hour(
      24 * (panchaanga.kaalas[d]['mAdhyAhnika sandhyA'][0] - jd)).toString(format=panchaanga.fmt)
    madhyahnika_sandhya_end = jyotisha.panchaanga.temporal.hour.Hour(
      24 * (panchaanga.kaalas[d]['mAdhyAhnika sandhyA end'][0] - jd)).toString(format=panchaanga.fmt)
    aparahna = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.kaalas[d]['aparAhna'][0] - jd)).toString(
      format=panchaanga.fmt)
    sayahna = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.kaalas[d]['sAyAhna'][0] - jd)).toString(
      format=panchaanga.fmt)
    sayamsandhya_start = jyotisha.panchaanga.temporal.hour.Hour(
      24 * (panchaanga.kaalas[d]['sAyaM sandhyA'][0] - jd)).toString(format=panchaanga.fmt)
    sayamsandhya_end = jyotisha.panchaanga.temporal.hour.Hour(
      24 * (panchaanga.kaalas[d]['sAyaM sandhyA end'][0] - jd)).toString(format=panchaanga.fmt)
    ratriyama1 = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.kaalas[d]['rAtri yAma 1'][0] - jd)).toString(
      format=panchaanga.fmt)
    shayana_time_end = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.kaalas[d]['zayana'][0] - jd)).toString(
      format=panchaanga.fmt)
    dinanta = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.kaalas[d]['dinAnta'][0] - jd)).toString(
      format=panchaanga.fmt)

    rahu = '%s--%s' % (
      jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.kaalas[d]['rahu'][0] - jd)).toString(
        format=panchaanga.fmt),
      jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.kaalas[d]['rahu'][1] - jd)).toString(
        format=panchaanga.fmt))
    yama = '%s--%s' % (
      jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.kaalas[d]['yama'][0] - jd)).toString(
        format=panchaanga.fmt),
      jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.kaalas[d]['yama'][1] - jd)).toString(
        format=panchaanga.fmt))
    gulika = '%s--%s' % (
      jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.kaalas[d]['gulika'][0] - jd)).toString(
        format=panchaanga.fmt),
      jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.kaalas[d]['gulika'][1] - jd)).toString(
        format=panchaanga.fmt))

    if panchaanga.solar_month[d] == 1 and panchaanga.solar_month[d - 1] == 12 and d > 1:
      # Move to next year
      yname = samvatsara_names[samvatsara_names.index(yname) + 1]

    # Assign samvatsara, ayana, rtu #
    sar_data = '{%s}{%s}{%s}' % (yname,
                                 jyotisha.names.NAMES['AYANA_NAMES'][panchaanga.script][panchaanga.tropical_month[d]],
                                 jyotisha.names.NAMES['RTU_NAMES'][panchaanga.script][panchaanga.tropical_month[d]])

    if panchaanga.solar_month_end_time[d] is None:
      month_end_str = ''
    else:
      _m = panchaanga.solar_month[d - 1]
      if panchaanga.solar_month_end_time[d] >= panchaanga.daily_panchaangas[d + 1].jd_sunrise:
        month_end_str = '\\mbox{%s{\\tiny\\RIGHTarrow}\\textsf{%s}}' % (
          jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][_m], jyotisha.panchaanga.temporal.hour.Hour(
            24 * (panchaanga.solar_month_end_time[d] - panchaanga.daily_panchaangas[d + 1].julian_day_start)).toString(format=panchaanga.fmt))
      else:
        month_end_str = '\\mbox{%s{\\tiny\\RIGHTarrow}\\textsf{%s}}' % (
          jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][_m], jyotisha.panchaanga.temporal.hour.Hour(
            24 * (panchaanga.solar_month_end_time[d] - panchaanga.daily_panchaangas[d].julian_day_start)).toString(format=panchaanga.fmt))

    month_data = '\\sunmonth{%s}{%d}{%s}' % (
      jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][panchaanga.solar_month[d]], panchaanga.solar_month_day[d],
      month_end_str)

    print('\\caldata{%s}{%s}{%s{%s}{%s}{%s}%s}' %
          (month[m], dt, month_data,
           jyotisha.names.get_chandra_masa(panchaanga.lunar_month[d],
                                           jyotisha.names.NAMES, panchaanga.script),
           jyotisha.names.NAMES['RTU_NAMES'][panchaanga.script][int(ceil(panchaanga.lunar_month[d]))],
           jyotisha.names.NAMES['VARA_NAMES'][panchaanga.script][panchaanga.weekday[d]], sar_data), file=output_stream)

    if panchaanga.daily_panchaangas[d].jd_moonrise > panchaanga.daily_panchaangas[d + 1].jd_sunrise:
      moonrise = '---'
    if panchaanga.daily_panchaangas[d].jd_moonset > panchaanga.daily_panchaangas[d + 1].jd_sunrise:
      moonset = '---'

    if panchaanga.daily_panchaangas[d].jd_moonrise < panchaanga.daily_panchaangas[d].jd_moonset:
      print('{\\sunmoonrsdata{%s}{%s}{%s}{%s}' % (sunrise, sunset, moonrise, moonset), file=output_stream)
    else:
      print('{\\sunmoonsrdata{%s}{%s}{%s}{%s}' % (sunrise, sunset, moonrise, moonset), file=output_stream)

    print(
      '{\kalas{%s %s %s %s %s %s %s %s %s %s %s %s %s %s}}}' % (braahma_start, pratahsandhya_start, pratahsandhya_end,
                                                                sangava,
                                                                madhyahnika_sandhya_start, madhyahnika_sandhya_end,
                                                                madhyaahna, aparahna, sayahna,
                                                                sayamsandhya_start, sayamsandhya_end,
                                                                ratriyama1, shayana_time_end, dinanta),
      file=output_stream)
    if compute_lagnams:
      print('{\\tnykdata{%s}%%\n{%s}%%\n{%s}%%\n{%s}{%s}\n}'
            % (tithi_data_str, nakshatram_data_str, yoga_data_str,
               karanam_data_str, lagna_data_str), file=output_stream)
    else:
      print('{\\tnykdata{%s}%%\n{%s}%%\n{%s}%%\n{%s}{\\scriptsize %s}\n}'
            % (tithi_data_str, nakshatram_data_str, yoga_data_str,
               karanam_data_str, ''), file=output_stream)

    # Using set as an ugly workaround since we may have sometimes assigned the same
    # festival to the same day again!
    print('{%s}' % '\\eventsep '.join(
      [jyotisha.custom_transliteration.tr(f, panchaanga.script).replace('★', '$^\\star$') for f in
       sorted(set(panchaanga.festivals[d]))]), file=output_stream)

    print('{%s} ' % WDAY[panchaanga.weekday[d]], file=output_stream)
    print('\\cfoot{\\rygdata{%s,%s,%s,%s,%s,%s,%s,%s,%s,%s}}' % (
    stithi_data_str, amritadi_yoga_str, rahu, yama, gulika, tyajyam_data_str, amrita_data_str, rashi_data_str,
    chandrashtama_rashi_data_str, shulam_data_str), file=output_stream)

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

  panchaanga = jyotisha.panchaanga.spatio_temporal.periodical.get_panchaanga(city=city, start_date=start_date,
                                                                             end_date=end_date, script=script, fmt=fmt,
                                                                             compute_lagnams=compute_lagnams,
                                                                             ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180)
  panchaanga.script = script  # Force script irrespective of what was obtained from saved file
  panchaanga.fmt = fmt  # Force fmt

  panchaanga.update_festival_details()

  daily_template_file = open(os.path.join(CODE_ROOT, 'data/templates/daily_cal_template.tex'))
  writeDailyTeX(panchaanga, daily_template_file, compute_lagnams)


if __name__ == '__main__':
  main()
