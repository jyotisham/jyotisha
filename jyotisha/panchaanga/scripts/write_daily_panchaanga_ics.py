#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import os
import os.path
import re
import sys
from datetime import datetime, date, timedelta
from io import StringIO
from math import ceil

from icalendar import Calendar, Event, Alarm
from indic_transliteration import xsanscript as sanscript

import jyotisha
import jyotisha.custom_transliteration
import jyotisha.names
import jyotisha.panchaanga.spatio_temporal.annual
import jyotisha.panchaanga.temporal

from jyotisha.panchaanga.temporal import time
from jyotisha.panchaanga import temporal
from jyotisha.panchaanga.spatio_temporal import City

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s  %(filename)s:%(lineno)d : %(message)s "
)

CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def cleanTamilNa(text):
  output_text = re.sub('([^ ])ந', '\\1ன', text)
  output_text = re.sub('([-—*])ன', '\\1ந', output_text)
  output_text = re.sub('ன்த', 'ந்த', output_text)
  return output_text


def getName(text, script):
  LOC = {'tamil': 'குறிப்பிட்ட ஊருக்கான தகவல்கள்', 'devanagari': 'क्षेत्रविशेषस्य विवरणानि',
         'iast': 'Location-specific data'}
  if text == 'LOC':
    return LOC[script]
  translation = {'candrAstamayaH': 'சந்த்ராஸ்தமனம்',
                 'candrOdayaH': 'சந்த்ரோதயம்',
                 'cAndramAnam': 'சாந்த்ரமானம்',
                 'ahOrAtram': 'நாள் முழுவதும்',
                 'tithiH': 'திதி',
                 'dinaM': 'தேதி',
                 'pakSaH': 'பக்ஷம்',
                 'nakSatram': 'நக்ஷத்ரம்',
                 'yOgaH': 'யோகம்',
                 'mAsaH': 'மாஸம்',
                 'RtuH': 'ருதுஃ',
                 'ayanam': 'அயனம்',
                 'karaNam': 'கரணம்',
                 'rAziH': 'ராஶிஃ',
                 'lagnam': 'லக்னம்',
                 'candrASTama-rAziH': 'சந்த்ராஷ்டம-ராஶிஃ',
                 'zUlam': 'ஶூலம்',
                 'vAsaraH': 'வாஸரம்',
                 'dina-vizESAH': 'தின-விஶேஷங்கள்',
                 'saMvatsaraH': 'ஸம்வத்ஸரம்',
                 'sUryAstamayaH': 'ஸூர்யாஸ்தமனம்',
                 'sUryOdayaH': 'ஸூர்யோதயம்',
                 'sauramAnam': 'ஸௌரமானம்',
                 'dinAntaH': 'தினாந்தம்',
                 'aparAhNa-kAlaH': 'அபராஹ்ண-காலம்',
                 'rAhukAlaH': 'ராஹுகாலம்',
                 'yamaghaNTaH': 'யமகண்டம்',
                 'gulikakAlaH': 'குலிககாலம்',
                 'parihAraH': 'பரிஹாரம்',
                 'guDam': 'வெல்லம்',
                 'dadhi': 'தயிர்',
                 'kSIram': 'பால்',
                 'tailam': 'எண்ணெய்',
                 'prAcI dik': 'கிழக்கு',
                 'udIcI dik': 'வடக்கு',
                 'dakSiNA dik': 'தெற்கு ',
                 'pratIcI dik': 'மேற்கு'
                 }
  if script == 'tamil':
    if text in translation:
      return translation[text]
    else:
      logging.warning('%s not found in translation table. Transliterating to %s' % (
      text, jyotisha.custom_transliteration.tr(text, script)))
      return jyotisha.custom_transliteration.tr(text, script)
  else:
    return jyotisha.custom_transliteration.tr(text, script)


def write_to_file(ics_calendar, fname):
  ics_calendar_file = open(fname, 'wb')
  ics_calendar_file.write(ics_calendar.to_ical())
  ics_calendar_file.close()


def writeDailyICS(panchaanga, compute_lagnams=True):
  """Write out the panchaanga TeX using a specified template
  """
  output_stream = StringIO()
  month = {1: 'January', 2: 'February', 3: 'March', 4: 'April',
           5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September',
           10: 'October', 11: 'November', 12: 'December'}
  WDAY = {0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
  SHULAM = [('pratIcI dik', 12, 'guDam'), ('prAcI dik', 8, 'dadhi'), ('udIcI dik', 12, 'kSIram'),
            ('udIcI dik', 16, 'kSIram'), ('dakSiNA dik', 20, 'tailam'), ('pratIcI dik', 12, 'guDam'),
            ('prAcI dik', 8, 'dadhi')]

  samvatsara_id = (panchaanga.year - 1568) % 60 + 1  # distance from prabhava
  samvatsara_names = (jyotisha.names.NAMES['SAMVATSARA_NAMES'][panchaanga.script][samvatsara_id],
                      jyotisha.names.NAMES['SAMVATSARA_NAMES'][panchaanga.script][(samvatsara_id % 60) + 1])

  yname_solar = samvatsara_names[0]  # Assign year name until Mesha Sankranti
  yname_lunar = samvatsara_names[0]  # Assign year name until Mesha Sankranti

  # print(' \\sffamily \\fontsize 43  43 \\selectfont  %d–%d\\\\[0.5cm] \n\\hrule\n\\vspace 0.2cm '
  #       % (panchaanga.year + 3100, panchaanga.year + 3101), file=output_stream)
  # print(' \\sffamily \\fontsize 23  23 \\selectfont   %s \\\\[0.2cm] '
  #       % jyotisha.custom_transliteration.print_lat_lon(panchaanga.city.latitude, panchaanga.city.longitude), file=output_stream)

  ics_calendar = Calendar()

  alarm = Alarm()
  alarm.add('action', 'DISPLAY')
  alarm.add('trigger', timedelta(hours=-4))  # default alarm, with a 4 hour reminder

  for d in range(1, jyotisha.panchaanga.temporal.MAX_SZ - 1):

    [y, m, dt, t] = time.jd_to_utc_gregorian(panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

    print('*%02d-%s-%4d*' % (dt, month[m], y), file=output_stream)
    event = Event()
    event.add('summary', '%02d-%s-%4d (%s)' % (
    dt, month[m], y, cleanTamilNa(jyotisha.custom_transliteration.tr(panchaanga.city.name, panchaanga.script))))

    jd = panchaanga.daily_panchaangas[d].julian_day_start

    paksha_data_str = ''
    tithi_data_str = ''
    for tithi_ID, tithi_end_jd in panchaanga.daily_panchaangas[d].tithi_data:
      tithi = jyotisha.names.NAMES['TITHI_NAMES'][panchaanga.script][tithi_ID].split('-')[-1]
      paksha = jyotisha.custom_transliteration.tr('zuklapakSaH' if tithi_ID <= 15 else 'kRSNapakSaH', panchaanga.script)
      if tithi_end_jd is None:
        tithi_data_str = '%s; %s►%s' % \
                         (tithi_data_str, tithi,
                          jyotisha.custom_transliteration.tr('ahOrAtram (tridinaspRk)', panchaanga.script))
      else:
        tithi_data_str = '%s; %s►%s%s' % \
                         (tithi_data_str, tithi,
                          jyotisha.panchaanga.temporal.hour.Hour(24 * (tithi_end_jd - jd)).toString(
                            format=panchaanga.fmt),
                          ' ')
    tithi_data_str = '*' + getName('tithiH', panchaanga.script) + '*—' + tithi_data_str[2:]
    paksha_data_str = '*' + getName('pakSaH', panchaanga.script) + '*—' + paksha

    nakshatram_data_str = ''
    for nakshatram_ID, nakshatram_end_jd in panchaanga.daily_panchaangas[d].nakshatra_data:
      nakshatram = jyotisha.names.NAMES['NAKSHATRAM_NAMES'][panchaanga.script][nakshatram_ID]
      if nakshatram_end_jd is None:
        nakshatram_data_str = '%s; %s►%s' % \
                              (nakshatram_data_str, nakshatram,
                               jyotisha.custom_transliteration.tr('ahOrAtram', panchaanga.script))
      else:
        nakshatram_data_str = '%s; %s►%s' % \
                              (nakshatram_data_str, nakshatram,
                               jyotisha.panchaanga.temporal.hour.Hour(24 * (nakshatram_end_jd -
                                                                            jd)).toString(format=panchaanga.fmt))
    nakshatram_data_str = '*' + getName('nakSatram', panchaanga.script) + '*—' + nakshatram_data_str[2:]

    chandrashtama_rashi_data_str = ''
    for rashi_ID, rashi_end_jd in panchaanga.daily_panchaangas[d].raashi_data:
      rashi = jyotisha.names.NAMES['RASHI_SUFFIXED_NAMES'][panchaanga.script][rashi_ID]
      if rashi_end_jd is None:
        rashi_data_str = '%s' % (rashi)
        chandrashtama_rashi_data_str = '*' + getName('candrASTama-rAziH', panchaanga.script) + '*—%s' % (
          jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][((rashi_ID - 8) % 12) + 1])
      else:
        rashi_data_str = '%s►%s' % (
        rashi, jyotisha.panchaanga.temporal.hour.Hour(24 * (rashi_end_jd - jd)).toString(format=panchaanga.fmt))
        chandrashtama_rashi_data_str = '*' + getName('candrASTama-rAziH', panchaanga.script) + '*—%s►%s; %s ➥' % (
          jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][((rashi_ID - 8) % 12) + 1],
          jyotisha.panchaanga.temporal.hour.Hour(24 * (rashi_end_jd - jd)).toString(format=panchaanga.fmt),
          jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][((rashi_ID - 7) % 12) + 1])

    if compute_lagnams:
      lagna_data_str = ''
      for lagna_ID, lagna_end_jd in panchaanga.daily_panchaangas[d].lagna_data:
        lagna = jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][lagna_ID]
        lagna_data_str = '%s; %s►%s' % \
                         (lagna_data_str, lagna,
                          jyotisha.panchaanga.temporal.hour.Hour(24 * (lagna_end_jd - jd)).toString(
                            format=panchaanga.fmt))
      lagna_data_str = '*' + getName('lagnam', panchaanga.script) + '*—' + lagna_data_str[2:]

    yoga_data_str = ''
    for yoga_ID, yoga_end_jd in panchaanga.daily_panchaangas[d].yoga_data:
      # if yoga_data_str != '':
      #     yoga_data_str += ' '
      yoga = jyotisha.names.NAMES['YOGA_NAMES'][panchaanga.script][yoga_ID]
      if yoga_end_jd is None:
        yoga_data_str = '%s; %s►%s' % (
        yoga_data_str, yoga, jyotisha.custom_transliteration.tr('ahOrAtram', panchaanga.script))
      else:
        yoga_data_str = '%s; %s►%s' % (yoga_data_str, yoga,
                                       jyotisha.panchaanga.temporal.hour.Hour(24 * (yoga_end_jd - jd)).toString(
                                         format=panchaanga.fmt))
    if yoga_end_jd is not None:
      yoga_data_str += '; %s ➥' % (jyotisha.names.NAMES['YOGA_NAMES'][panchaanga.script][(yoga_ID % 27) + 1])
    yoga_data_str = '*' + getName('yOgaH', panchaanga.script) + '*—' + yoga_data_str[2:]

    karanam_data_str = ''
    for numKaranam, (karanam_ID, karanam_end_jd) in enumerate(panchaanga.daily_panchaangas[d].karana_data):
      # if numKaranam == 1:
      #     karanam_data_str += ' '
      karanam = jyotisha.names.NAMES['KARANAM_NAMES'][panchaanga.script][karanam_ID]
      if karanam_end_jd is None:
        karanam_data_str = '%s; %s►%s' % \
                           (karanam_data_str, karanam,
                            jyotisha.custom_transliteration.tr('ahOrAtram', panchaanga.script))
      else:
        karanam_data_str = '%s; %s►%s' % \
                           (karanam_data_str, karanam,
                            jyotisha.panchaanga.temporal.hour.Hour(24 * (karanam_end_jd - jd)).toString(
                              format=panchaanga.fmt))
    if karanam_end_jd is not None:
      karanam_data_str += '; %s ➥' % (
        jyotisha.names.NAMES['KARANAM_NAMES'][panchaanga.script][(karanam_ID % 60) + 1])
    karanam_data_str = '*' + getName('karaNam', panchaanga.script) + '*—' + karanam_data_str[2:]

    sunrise = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].jd_sunrise - jd)).toString(
      format=panchaanga.fmt)
    sunset = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].jd_sunset - jd)).toString(format=panchaanga.fmt)
    moonrise = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].jd_moonrise - jd)).toString(
      format=panchaanga.fmt)
    moonset = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].jd_moonset - jd)).toString(
      format=panchaanga.fmt)

    # braahma = jyotisha.panchaanga.temporal.Time(24 * (panchaanga.daily_panchaangas[d].kaalas['braahma'][0] - jd)).toString(format=panchaanga.fmt)
    # pratahsandhya = jyotisha.panchaanga.temporal.Time(24 * (panchaanga.daily_panchaangas[d].kaalas['prAtaH sandhyA'][0] - jd)).toString(format=panchaanga.fmt)
    # pratahsandhya_end = jyotisha.panchaanga.temporal.Time(24 * (panchaanga.daily_panchaangas[d].kaalas['prAtaH sandhyA end'][0] - jd)).toString(format=panchaanga.fmt)
    # sangava = jyotisha.panchaanga.temporal.Time(24 * (panchaanga.daily_panchaangas[d].kaalas['saGgava'][0] - jd)).toString(format=panchaanga.fmt)
    # madhyaahna = jyotisha.panchaanga.temporal.Time(24 * (panchaanga.daily_panchaangas[d].kaalas['madhyAhna'][0] - jd)).toString(format=panchaanga.fmt)
    # madhyahnika_sandhya = jyotisha.panchaanga.temporal.Time(24 * (panchaanga.daily_panchaangas[d].kaalas['mAdhyAhnika sandhyA'][0] - jd)).toString(format=panchaanga.fmt)
    # madhyahnika_sandhya_end = jyotisha.panchaanga.temporal.Time(24 * (panchaanga.daily_panchaangas[d].kaalas['mAdhyAhnika sandhyA end'][0] - jd)).toString(format=panchaanga.fmt)
    aparahna = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['aparAhna'][0] - jd)).toString(
      format=panchaanga.fmt)
    sayahna = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['sAyAhna'][0] - jd)).toString(
      format=panchaanga.fmt)
    # sayamsandhya = jyotisha.panchaanga.temporal.Time(24 * (panchaanga.daily_panchaangas[d].kaalas['sAyaM sandhyA'][0] - jd)).toString(format=panchaanga.fmt)
    # sayamsandhya_end = jyotisha.panchaanga.temporal.Time(24 * (panchaanga.daily_panchaangas[d].kaalas['sAyaM sandhyA end'][0] - jd)).toString(format=panchaanga.fmt)
    # ratriyama1 = jyotisha.panchaanga.temporal.Time(24 * (panchaanga.daily_panchaangas[d].kaalas['rAtri yAma 1'][0] - jd)).toString(format=panchaanga.fmt)
    # sayana_time = jyotisha.panchaanga.temporal.Time(24 * (panchaanga.daily_panchaangas[d].kaalas['zayana'][0] - jd)).toString(format=panchaanga.fmt)
    dinanta = jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['dinAnta'][0] - jd)).toString(
      format=panchaanga.fmt)

    rahu = '%s–%s' % (
      jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['rahu'][0] - jd)).toString(
        format=panchaanga.fmt),
      jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['rahu'][1] - jd)).toString(
        format=panchaanga.fmt))
    yama = '%s–%s' % (
      jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['yama'][0] - jd)).toString(
        format=panchaanga.fmt),
      jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['yama'][1] - jd)).toString(
        format=panchaanga.fmt))
    gulika = '%s–%s' % (
      jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['gulika'][0] - jd)).toString(
        format=panchaanga.fmt),
      jyotisha.panchaanga.temporal.hour.Hour(24 * (panchaanga.daily_panchaangas[d].kaalas['gulika'][1] - jd)).toString(
        format=panchaanga.fmt))

    if panchaanga.solar_month[d] == 1:
      # Flip the year name for the remaining days
      yname_solar = samvatsara_names[1]
    if panchaanga.lunar_month[d] == 1:
      # Flip the year name for the remaining days
      yname_lunar = samvatsara_names[1]

    # Assign samvatsara, ayana, rtu #
    ayanam = jyotisha.names.NAMES['AYANA_NAMES'][panchaanga.script][panchaanga.solar_month[d]]
    rtu_solar = jyotisha.names.NAMES['RTU_NAMES'][panchaanga.script][panchaanga.solar_month[d]]
    rtu_lunar = jyotisha.names.NAMES['RTU_NAMES'][panchaanga.script][int(ceil(panchaanga.lunar_month[d]))]

    if panchaanga.solar_month_end_time[d] is None:
      month_end_str = ''
    else:
      _m = panchaanga.solar_month[d - 1]
      if panchaanga.solar_month_end_time[d] >= panchaanga.daily_panchaangas[d + 1].jd_sunrise:
        month_end_str = '%s►%s' % (jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][_m],
                                   jyotisha.panchaanga.temporal.hour.Hour(24 * (
                                         panchaanga.solar_month_end_time[d] - panchaanga.daily_panchaangas[d + 1].julian_day_start)).toString(
                                     format=panchaanga.fmt))
      else:
        month_end_str = '%s►%s' % (jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][_m],
                                   jyotisha.panchaanga.temporal.hour.Hour(
                                     24 * (panchaanga.solar_month_end_time[d] - panchaanga.daily_panchaangas[d].julian_day_start)).toString(
                                     format=panchaanga.fmt))
    if month_end_str == '':
      month_data = '%s (%s %d)' % (jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][panchaanga.solar_month[d]],
                                   getName('dinaM', panchaanga.script), panchaanga.solar_month_day[d])
    else:
      month_data = '%s (%s %d); %s' % (
        jyotisha.names.NAMES['RASHI_NAMES'][panchaanga.script][panchaanga.solar_month[d]],
        getName('dinaM', panchaanga.script), panchaanga.solar_month_day[d], month_end_str)

    vara = jyotisha.names.NAMES['VARA_NAMES'][panchaanga.script][panchaanga.daily_panchaangas[d].date.get_weekday()]

    if yname_lunar == yname_solar:
      print('*' + getName('saMvatsaraH', panchaanga.script) + '*—%s' % yname_lunar, file=output_stream)
      print('*' + getName('ayanam', panchaanga.script) + '*—%s' % ayanam, file=output_stream)
    if rtu_lunar == rtu_solar:
      print('*' + getName('RtuH', panchaanga.script) + '*—%s' % rtu_lunar, file=output_stream)

    print('°' * 25, file=output_stream)
    print('☀ ' + getName('sauramAnam', panchaanga.script), file=output_stream)
    if yname_lunar != yname_solar:
      print('*' + getName('saMvatsaraH', panchaanga.script) + '*—%s' % yname_solar, file=output_stream)
      print('*' + getName('ayanam', panchaanga.script) + '*—%s' % ayanam, file=output_stream)
    if rtu_lunar != rtu_solar:
      print('*' + getName('RtuH', panchaanga.script) + '*—%s' % rtu_solar, file=output_stream)
    print('*' + getName('mAsaH', panchaanga.script) + '*—%s' % month_data, file=output_stream)
    print('°' * 25, file=output_stream)

    print('⚪ ' + getName('cAndramAnam', panchaanga.script), file=output_stream)
    if yname_lunar != yname_solar:
      print('*' + getName('saMvatsaraH', panchaanga.script) + '*—%s' % yname_lunar, file=output_stream)
      print('*' + getName('ayanam', panchaanga.script) + '*—%s' % ayanam, file=output_stream)
    if rtu_lunar != rtu_solar:
      print('*' + getName('RtuH', panchaanga.script) + '*—%s' % rtu_lunar, file=output_stream)
    print(
      '*' + getName('mAsaH', panchaanga.script) + '*—%s' % jyotisha.names.get_chandra_masa(panchaanga.lunar_month[d],
                                                                                           jyotisha.names.NAMES,
                                                                                           panchaanga.script),
      file=output_stream)
    print('°' * 25, file=output_stream)
    # braahma
    # pratahsandhya, pratahsandhya_end
    # sangava
    # madhyahnika_sandhya, madhyahnika_sandhya_end
    # madhyaahna
    # aparahna
    # sayahna
    # sayamsandhya, sayamsandhya_end
    # dinanta
    print('%s' % (paksha_data_str), file=output_stream)
    print('%s' % (tithi_data_str), file=output_stream)
    print('*%s*—%s' % (getName('vAsaraH', panchaanga.script), vara), file=output_stream)
    print('%s (%s)' % (nakshatram_data_str, rashi_data_str), file=output_stream)
    print('%s' % (yoga_data_str), file=output_stream)
    print('%s' % (karanam_data_str), file=output_stream)
    print('%s' % (chandrashtama_rashi_data_str), file=output_stream)

    if panchaanga.daily_panchaangas[d].jd_moonrise > panchaanga.daily_panchaangas[d + 1].jd_sunrise:
      moonrise = '---'
    if panchaanga.daily_panchaangas[d].jd_moonset > panchaanga.daily_panchaangas[d + 1].jd_sunrise:
      moonset = '---'

    print('**%s (%s)**' % (
    getName('LOC', panchaanga.script), jyotisha.custom_transliteration.tr(panchaanga.city.name, panchaanga.script)),
          file=output_stream)

    if compute_lagnams:
      print('%s' % (lagna_data_str), file=output_stream)

    if panchaanga.daily_panchaangas[d].jd_moonrise < panchaanga.daily_panchaangas[d].jd_moonset:
      print('*%s*—%s; *%s*—%s' % (
      getName('sUryOdayaH', panchaanga.script), sunrise, getName('sUryAstamayaH', panchaanga.script), sunset),
            file=output_stream)
      print('*%s*—%s; *%s*—%s' % (
      getName('candrOdayaH', panchaanga.script), moonrise, getName('candrAstamayaH', panchaanga.script), moonset),
            file=output_stream)
    else:
      print('*%s*—%s; *%s*—%s' % (
      getName('sUryOdayaH', panchaanga.script), sunrise, getName('sUryAstamayaH', panchaanga.script), sunset),
            file=output_stream)
      print('*%s*—%s; *%s*—%s' % (
      getName('candrAstamayaH', panchaanga.script), moonset, getName('candrOdayaH', panchaanga.script), moonrise),
            file=output_stream)

    print('*%s*—%s►%s' % (getName('aparAhNa-kAlaH', panchaanga.script), aparahna, sayahna), file=output_stream)
    print('*%s*—%s' % (getName('dinAntaH', panchaanga.script), dinanta), file=output_stream)
    print('*%s*—%s;\n*%s*—%s;\n*%s*—%s' % (getName('rAhukAlaH', panchaanga.script), rahu,
                                           getName('yamaghaNTaH', panchaanga.script), yama,
                                           getName('gulikakAlaH', panchaanga.script), gulika), file=output_stream)

    shulam_end_jd = panchaanga.daily_panchaangas[d].jd_sunrise + (panchaanga.daily_panchaangas[d].jd_sunset - panchaanga.daily_panchaangas[d].jd_sunrise) * (
          SHULAM[panchaanga.daily_panchaangas[d].date.get_weekday()][1] / 30)
    print('*%s*—%s (►%s); *%s*–%s' % (
    getName('zUlam', panchaanga.script), getName(SHULAM[panchaanga.daily_panchaangas[d].date.get_weekday()][0], panchaanga.script),
    jyotisha.panchaanga.temporal.hour.Hour(24 * (shulam_end_jd - jd)).toString(format=panchaanga.fmt),
    getName('parihAraH', panchaanga.script), getName(SHULAM[panchaanga.daily_panchaangas[d].date.get_weekday()][2], panchaanga.script)),
          file=output_stream)
    # Using set as an ugly workaround since we may have sometimes assigned the same
    # festival to the same day again!
    fest_list = []
    for f in sorted(set(panchaanga.daily_panchaangas[d].festivals)):
      fest_name_cleaned = jyotisha.custom_transliteration.tr(f, panchaanga.script).replace('~', ' ').replace('tamil',
                                                                                                             '')
      fest_name_cleaned = re.sub('[{}]', '', fest_name_cleaned).replace('\\', '').replace('textsf', '').replace('To',
                                                                                                                '►').replace(
        'RIGHTarrow', '►')
      fest_list.append(fest_name_cleaned)

    if len(fest_list):
      print('*%s*\n%s\n' % (getName('dina-vizESAH', panchaanga.script), '; '.join(fest_list)), file=output_stream)
    else:
      print('', file=output_stream)

    if panchaanga.fmt == 'hh:mm*':
      dinanta_hh, dinanta_mm = dinanta.split(':')
      dinanta_hh = int(dinanta_hh) - 24
      dinanta_mm = int(dinanta_mm[:-1])
      footer_text = 'Note: All times are shown in 24h format. Times beyond midnight are shown as %s, meaning %02d:%02d am tomorrow.' % (
      dinanta, dinanta_hh, dinanta_mm)
      output_text = cleanTamilNa(output_stream.getvalue()) + '\n\n%s' % footer_text
    else:
      output_text = cleanTamilNa(output_stream.getvalue())

    event.add('dtstart', date(y, m, dt))
    event.add('dtend', (datetime(y, m, dt) + timedelta(1)).date())
    event.add_component(alarm)
    event.add('description', output_text)
    event['X-MICROSOFT-CDO-ALLDAYEVENT'] = 'TRUE'
    event['TRANSP'] = 'TRANSPARENT'
    event['X-MICROSOFT-CDO-BUSYSTATUS'] = 'FREE'

    ics_calendar.add_component(event)

    output_stream = StringIO()

    if m == 12 and dt == 31:
      break

  return ics_calendar


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
                                                                         compute_lagnas=compute_lagnams)
  panchaanga.script = script  # Force script irrespective of what was obtained from saved file
  panchaanga.fmt = fmt  # Force fmt

  panchaanga.update_festival_details()

  ics_calendar = writeDailyICS(panchaanga, compute_lagnams)
  city_name_en = jyotisha.custom_transliteration.romanise(
    jyotisha.custom_transliteration.tr(city.name, sanscript.IAST)).title()
  output_file = os.path.expanduser('%s/%s-%d-%s-daily.ics' % ("../ics/daily", city_name_en, year, script))
  write_to_file(ics_calendar, output_file)
  print('Output ICS written to %s' % output_file, file=sys.stderr)


if __name__ == '__main__':
  main()
