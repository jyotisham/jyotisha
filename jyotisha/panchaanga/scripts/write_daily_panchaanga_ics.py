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
from jyotisha.panchaanga.temporal.time import Hour

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


def writeDailyICS(panchaanga, script=sanscript.DEVANAGARI, compute_lagnams=True):
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
  samvatsara_names = (jyotisha.names.NAMES['SAMVATSARA_NAMES'][script][samvatsara_id],
                      jyotisha.names.NAMES['SAMVATSARA_NAMES'][script][(samvatsara_id % 60) + 1])

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

  daily_panchaangas = panchaanga.daily_panchaangas_sorted()
  for d in range(1, jyotisha.panchaanga.temporal.MAX_SZ - 1):
    daily_panchaanga = daily_panchaangas[d]
    [y, m, dt, t] = time.jd_to_utc_gregorian(panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

    print('*%02d-%s-%4d*' % (dt, month[m], y), file=output_stream)
    event = Event()
    event.add('summary', '%02d-%s-%4d (%s)' % (
    dt, month[m], y, cleanTamilNa(jyotisha.custom_transliteration.tr(panchaanga.city.name, script))))

    jd = daily_panchaanga.julian_day_start

    paksha_data_str = ''
    tithi_data_str = ''
    for tithi_span in daily_panchaanga.angas.tithis_with_ends:
      (tithi_ID, tithi_end_jd) = (tithi_span.name, tithi_span.jd_end)
      tithi = jyotisha.names.NAMES['TITHI_NAMES'][script][tithi_ID].split('-')[-1]
      paksha = jyotisha.custom_transliteration.tr('zuklapakSaH' if tithi_ID <= 15 else 'kRSNapakSaH', script)
      if tithi_end_jd is None:
        tithi_data_str = '%s; %s►%s' % \
                         (tithi_data_str, tithi,
                          jyotisha.custom_transliteration.tr('ahOrAtram (tridinaspRk)', script))
      else:
        tithi_data_str = '%s; %s►%s%s' % \
                         (tithi_data_str, tithi,
                          Hour(24 * (tithi_end_jd - jd)).toString(
                            format=panchaanga.fmt),
                          ' ')
    tithi_data_str = '*' + getName('tithiH', script) + '*—' + tithi_data_str[2:]
    paksha_data_str = '*' + getName('pakSaH', script) + '*—' + paksha

    nakshatra_data_str = ''
    for nakshatra_span in daily_panchaanga.angas.nakshatras_with_ends:
      (nakshatra_ID, nakshatra_end_jd) = (nakshatra_span.name, nakshatra_span.jd_end)
      nakshatra = jyotisha.names.NAMES['NAKSHATRA_NAMES'][script][nakshatra_ID]
      if nakshatra_end_jd is None:
        nakshatra_data_str = '%s; %s►%s' % \
                              (nakshatra_data_str, nakshatra,
                               jyotisha.custom_transliteration.tr('ahOrAtram', script))
      else:
        nakshatra_data_str = '%s; %s►%s' % \
                              (nakshatra_data_str, nakshatra,
                               Hour(24 * (nakshatra_end_jd -
                                                                            jd)).toString(format=panchaanga.fmt))
    nakshatra_data_str = '*' + getName('nakSatram', script) + '*—' + nakshatra_data_str[2:]

    chandrashtama_rashi_data_str = ''
    for raashi_span in daily_panchaanga.angas.raashis_with_ends:
      (rashi_ID, rashi_end_jd) = (raashi_span.name, raashi_span.jd_end)
      rashi = jyotisha.names.NAMES['RASHI_SUFFIXED_NAMES'][script][rashi_ID]
      if rashi_end_jd is None:
        rashi_data_str = '%s' % (rashi)
        chandrashtama_rashi_data_str = '*' + getName('candrASTama-rAziH', script) + '*—%s' % (
          jyotisha.names.NAMES['RASHI_NAMES'][script][((rashi_ID - 8) % 12) + 1])
      else:
        rashi_data_str = '%s►%s' % (
        rashi, Hour(24 * (rashi_end_jd - jd)).toString(format=panchaanga.fmt))
        chandrashtama_rashi_data_str = '*' + getName('candrASTama-rAziH', script) + '*—%s►%s; %s ➥' % (
          jyotisha.names.NAMES['RASHI_NAMES'][script][((rashi_ID - 8) % 12) + 1],
          Hour(24 * (rashi_end_jd - jd)).toString(format=panchaanga.fmt),
          jyotisha.names.NAMES['RASHI_NAMES'][script][((rashi_ID - 7) % 12) + 1])

    if compute_lagnams:
      lagna_data_str = ''
      for lagna_ID, lagna_end_jd in daily_panchaanga.lagna_data:
        lagna = jyotisha.names.NAMES['RASHI_NAMES'][script][lagna_ID]
        lagna_data_str = '%s; %s►%s' % \
                         (lagna_data_str, lagna,
                          Hour(24 * (lagna_end_jd - jd)).toString(
                            format=panchaanga.fmt))
      lagna_data_str = '*' + getName('lagnam', script) + '*—' + lagna_data_str[2:]

    yoga_data_str = ''
    for yoga_span in daily_panchaanga.angas.yogas_with_ends:
      (yoga_ID, yoga_end_jd) = (yoga_span.name, yoga_span.jd_end)
      # if yoga_data_str != '':
      #     yoga_data_str += ' '
      yoga = jyotisha.names.NAMES['YOGA_NAMES'][script][yoga_ID]
      if yoga_end_jd is None:
        yoga_data_str = '%s; %s►%s' % (
        yoga_data_str, yoga, jyotisha.custom_transliteration.tr('ahOrAtram', script))
      else:
        yoga_data_str = '%s; %s►%s' % (yoga_data_str, yoga,
                                       Hour(24 * (yoga_end_jd - jd)).toString(
                                         format=panchaanga.fmt))
    if yoga_end_jd is not None:
      yoga_data_str += '; %s ➥' % (jyotisha.names.NAMES['YOGA_NAMES'][script][(yoga_ID % 27) + 1])
    yoga_data_str = '*' + getName('yOgaH', script) + '*—' + yoga_data_str[2:]

    karana_data_str = ''
    for numKaranam, karaNa_span in enumerate(daily_panchaanga.angas.karanas_with_ends):
      (karana_ID, karana_end_jd) = (karaNa_span.name, karaNa_span.jd_end)
      # if numKaranam == 1:
      #     karana_data_str += ' '
      karana = jyotisha.names.NAMES['KARANA_NAMES'][script][karana_ID]
      if karana_end_jd is None:
        karana_data_str = '%s; %s►%s' % \
                           (karana_data_str, karana,
                            jyotisha.custom_transliteration.tr('ahOrAtram', script))
      else:
        karana_data_str = '%s; %s►%s' % \
                           (karana_data_str, karana,
                            Hour(24 * (karana_end_jd - jd)).toString(
                              format=panchaanga.fmt))
    if karana_end_jd is not None:
      karana_data_str += '; %s ➥' % (
        jyotisha.names.NAMES['KARANA_NAMES'][script][(karana_ID % 60) + 1])
    karana_data_str = '*' + getName('karaNam', script) + '*—' + karana_data_str[2:]

    sunrise = Hour(24 * (daily_panchaanga.jd_sunrise - jd)).toString(
      format=panchaanga.fmt)
    sunset = Hour(24 * (daily_panchaanga.jd_sunset - jd)).toString(format=panchaanga.fmt)
    moonrise = Hour(24 * (daily_panchaanga.jd_moonrise - jd)).toString(
      format=panchaanga.fmt)
    moonset = Hour(24 * (daily_panchaanga.jd_moonset - jd)).toString(
      format=panchaanga.fmt)

    # braahma = jyotisha.panchaanga.temporal.Time(24 * (daily_panchaanga.day_length_based_periods.braahma.jd_start - jd)).toString(format=panchaanga.fmt)
    # pratahsandhya = jyotisha.panchaanga.temporal.Time(24 * (daily_panchaanga.day_length_based_periods.praatas_sandhyaa.jd_start - jd)).toString(format=panchaanga.fmt)
    # pratahsandhya_end = jyotisha.panchaanga.temporal.Time(24 * (daily_panchaanga.day_length_based_periods.praatas_sandhyaa_end.jd_start - jd)).toString(format=panchaanga.fmt)
    # sangava = jyotisha.panchaanga.temporal.Time(24 * (daily_panchaanga.day_length_based_periods.saangava.jd_start - jd)).toString(format=panchaanga.fmt)
    # madhyaahna = jyotisha.panchaanga.temporal.Time(24 * (daily_panchaanga.day_length_based_periods.madhyaahna.jd_start - jd)).toString(format=panchaanga.fmt)
    # madhyahnika_sandhya = jyotisha.panchaanga.temporal.Time(24 * (daily_panchaanga.day_length_based_periods.maadhyaahnika_sandhyaa.jd_start - jd)).toString(format=panchaanga.fmt)
    # madhyahnika_sandhya_end = jyotisha.panchaanga.temporal.Time(24 * (daily_panchaanga.day_length_based_periods.maadhyaahnika_sandhyaa_end.jd_start - jd)).toString(format=panchaanga.fmt)
    aparahna = Hour(24 * (daily_panchaanga.day_length_based_periods.aparaahnNa.jd_start - jd)).toString(
      format=panchaanga.fmt)
    sayahna = Hour(24 * (daily_panchaanga.day_length_based_periods.saayaahna.jd_start - jd)).toString(
      format=panchaanga.fmt)
    # sayamsandhya = jyotisha.panchaanga.temporal.Time(24 * (daily_panchaanga.day_length_based_periods.saayaM_sandhyaa.jd_start - jd)).toString(format=panchaanga.fmt)
    # sayamsandhya_end = jyotisha.panchaanga.temporal.Time(24 * (daily_panchaanga.day_length_based_periods.saayaM_sandhyaa_end.jd_start - jd)).toString(format=panchaanga.fmt)
    # ratriyama1 = jyotisha.panchaanga.temporal.Time(24 * (daily_panchaanga.day_length_based_periods.raatri_yaama_1.jd_start - jd)).toString(format=panchaanga.fmt)
    # sayana_time = jyotisha.panchaanga.temporal.Time(24 * (daily_panchaanga.day_length_based_periods.shayana.jd_start - jd)).toString(format=panchaanga.fmt)
    dinanta = Hour(24 * (daily_panchaanga.day_length_based_periods.dinaanta.jd_start - jd)).toString(
      format=panchaanga.fmt)

    rahu = '%s–%s' % (
      Hour(24 * (daily_panchaanga.day_length_based_periods.raahu.jd_start - jd)).toString(
        format=panchaanga.fmt),
      Hour(24 * (daily_panchaanga.day_length_based_periods.raahu.jd_end - jd)).toString(
        format=panchaanga.fmt))
    yama = '%s–%s' % (
      Hour(24 * (daily_panchaanga.day_length_based_periods.yama.jd_start - jd)).toString(
        format=panchaanga.fmt),
      Hour(24 * (daily_panchaanga.day_length_based_periods.yama.jd_end - jd)).toString(
        format=panchaanga.fmt))
    gulika = '%s–%s' % (
      Hour(24 * (daily_panchaanga.day_length_based_periods.gulika.jd_start - jd)).toString(
        format=panchaanga.fmt),
      Hour(24 * (daily_panchaanga.day_length_based_periods.gulika.jd_end - jd)).toString(
        format=panchaanga.fmt))

    if daily_panchaanga.solar_sidereal_date_sunset.month == 1:
      # Flip the year name for the remaining days
      yname_solar = samvatsara_names[1]
    if daily_panchaanga.lunar_month_sunrise == 1:
      # Flip the year name for the remaining days
      yname_lunar = samvatsara_names[1]

    # Assign samvatsara, ayana, rtu #
    ayanam = jyotisha.names.NAMES['AYANA_NAMES'][script][daily_panchaanga.solar_sidereal_date_sunset.month]
    rtu_solar = jyotisha.names.NAMES['RTU_NAMES'][script][daily_panchaanga.solar_sidereal_date_sunset.month]
    rtu_lunar = jyotisha.names.NAMES['RTU_NAMES'][script][int(ceil(daily_panchaanga.lunar_month_sunrise))]

    if daily_panchaanga.solar_sidereal_date_sunset.month_transition is None:
      month_end_str = ''
    else:
      _m = daily_panchaangas[d - 1].solar_sidereal_date_sunset.month
      if daily_panchaanga.solar_sidereal_date_sunset.month_transition >= daily_panchaangas[d + 1].jd_sunrise:
        month_end_str = '%s►%s' % (jyotisha.names.NAMES['RASHI_NAMES'][script][_m],
                                   Hour(24 * (
                                         daily_panchaanga.solar_sidereal_date_sunset.month_transition - daily_panchaangas[d + 1].julian_day_start)).toString(
                                     format=panchaanga.fmt))
      else:
        month_end_str = '%s►%s' % (jyotisha.names.NAMES['RASHI_NAMES'][script][_m],
                                   Hour(
                                     24 * (daily_panchaanga.solar_sidereal_date_sunset.month_transition - daily_panchaanga.julian_day_start)).toString(
                                     format=panchaanga.fmt))
    if month_end_str == '':
      month_data = '%s (%s %d)' % (jyotisha.names.NAMES['RASHI_NAMES'][script][daily_panchaanga.solar_sidereal_date_sunset.month],
                                   getName('dinaM', script), daily_panchaanga.solar_sidereal_date_sunset.day)
    else:
      month_data = '%s (%s %d); %s' % (
        jyotisha.names.NAMES['RASHI_NAMES'][script][daily_panchaanga.solar_sidereal_date_sunset.month],
        getName('dinaM', script), daily_panchaanga.solar_sidereal_date_sunset.day, month_end_str)

    vara = jyotisha.names.NAMES['VARA_NAMES'][script][daily_panchaanga.date.get_weekday()]

    if yname_lunar == yname_solar:
      print('*' + getName('saMvatsaraH', script) + '*—%s' % yname_lunar, file=output_stream)
      print('*' + getName('ayanam', script) + '*—%s' % ayanam, file=output_stream)
    if rtu_lunar == rtu_solar:
      print('*' + getName('RtuH', script) + '*—%s' % rtu_lunar, file=output_stream)

    print('°' * 25, file=output_stream)
    print('☀ ' + getName('sauramAnam', script), file=output_stream)
    if yname_lunar != yname_solar:
      print('*' + getName('saMvatsaraH', script) + '*—%s' % yname_solar, file=output_stream)
      print('*' + getName('ayanam', script) + '*—%s' % ayanam, file=output_stream)
    if rtu_lunar != rtu_solar:
      print('*' + getName('RtuH', script) + '*—%s' % rtu_solar, file=output_stream)
    print('*' + getName('mAsaH', script) + '*—%s' % month_data, file=output_stream)
    print('°' * 25, file=output_stream)

    print('⚪ ' + getName('cAndramAnam', script), file=output_stream)
    if yname_lunar != yname_solar:
      print('*' + getName('saMvatsaraH', script) + '*—%s' % yname_lunar, file=output_stream)
      print('*' + getName('ayanam', script) + '*—%s' % ayanam, file=output_stream)
    if rtu_lunar != rtu_solar:
      print('*' + getName('RtuH', script) + '*—%s' % rtu_lunar, file=output_stream)
    print(
      '*' + getName('mAsaH', script) + '*—%s' % jyotisha.names.get_chandra_masa(daily_panchaanga.lunar_month_sunrise,
                                                                                jyotisha.names.NAMES,
                                                                                script),
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
    print('*%s*—%s' % (getName('vAsaraH', script), vara), file=output_stream)
    print('%s (%s)' % (nakshatra_data_str, rashi_data_str), file=output_stream)
    print('%s' % (yoga_data_str), file=output_stream)
    print('%s' % (karana_data_str), file=output_stream)
    print('%s' % (chandrashtama_rashi_data_str), file=output_stream)

    if daily_panchaanga.jd_moonrise > daily_panchaangas[d + 1].jd_sunrise:
      moonrise = '---'
    if daily_panchaanga.jd_moonset > daily_panchaangas[d + 1].jd_sunrise:
      moonset = '---'

    print('**%s (%s)**' % (
    getName('LOC', script), jyotisha.custom_transliteration.tr(panchaanga.city.name, script)),
          file=output_stream)

    if compute_lagnams:
      print('%s' % (lagna_data_str), file=output_stream)

    if daily_panchaanga.jd_moonrise < daily_panchaanga.jd_moonset:
      print('*%s*—%s; *%s*—%s' % (
      getName('sUryOdayaH', script), sunrise, getName('sUryAstamayaH', script), sunset),
            file=output_stream)
      print('*%s*—%s; *%s*—%s' % (
      getName('candrOdayaH', script), moonrise, getName('candrAstamayaH', script), moonset),
            file=output_stream)
    else:
      print('*%s*—%s; *%s*—%s' % (
      getName('sUryOdayaH', script), sunrise, getName('sUryAstamayaH', script), sunset),
            file=output_stream)
      print('*%s*—%s; *%s*—%s' % (
      getName('candrAstamayaH', script), moonset, getName('candrOdayaH', script), moonrise),
            file=output_stream)

    print('*%s*—%s►%s' % (getName('aparAhNa-kAlaH', script), aparahna, sayahna), file=output_stream)
    print('*%s*—%s' % (getName('dinAntaH', script), dinanta), file=output_stream)
    print('*%s*—%s;\n*%s*—%s;\n*%s*—%s' % (getName('rAhukAlaH', script), rahu,
                                           getName('yamaghaNTaH', script), yama,
                                           getName('gulikakAlaH', script), gulika), file=output_stream)

    shulam_end_jd = daily_panchaanga.jd_sunrise + (daily_panchaanga.jd_sunset - daily_panchaanga.jd_sunrise) * (
          SHULAM[daily_panchaanga.date.get_weekday()][1] / 30)
    print('*%s*—%s (►%s); *%s*–%s' % (
    getName('zUlam', script), getName(SHULAM[daily_panchaanga.date.get_weekday()][0], script),
    Hour(24 * (shulam_end_jd - jd)).toString(format=panchaanga.fmt),
    getName('parihAraH', script), getName(SHULAM[daily_panchaanga.date.get_weekday()][2], script)),
          file=output_stream)
    # Using set as an ugly workaround since we may have sometimes assigned the same
    # festival to the same day again!
    fest_list = []
    for f in sorted(set(daily_panchaanga.festivals)):
      fest_name_cleaned = jyotisha.custom_transliteration.tr(f, script).replace('~', ' ').replace('tamil',
                                                                                                             '')
      fest_name_cleaned = re.sub('[{}]', '', fest_name_cleaned).replace('\\', '').replace('textsf', '').replace('To',
                                                                                                                '►').replace(
        'RIGHTarrow', '►')
      fest_list.append(fest_name_cleaned)

    if len(fest_list):
      print('*%s*\n%s\n' % (getName('dina-vizESAH', script), '; '.join(fest_list)), file=output_stream)
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

  panchaanga = jyotisha.panchaanga.spatio_temporal.annual.get_panchaanga(city=city, year=year, 
                                                                         compute_lagnas=compute_lagnams)

  panchaanga.update_festival_details()

  ics_calendar = writeDailyICS(panchaanga, compute_lagnams)
  city_name_en = jyotisha.custom_transliteration.romanise(
    jyotisha.custom_transliteration.tr(city.name, sanscript.IAST)).title()
  output_file = os.path.expanduser('%s/%s-%d-%s-daily.ics' % ("../ics/daily", city_name_en, year, script))
  write_to_file(ics_calendar, output_file)
  print('Output ICS written to %s' % output_file, file=sys.stderr)


if __name__ == '__main__':
  main()
