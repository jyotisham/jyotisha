#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
from io import StringIO
import os
import os.path
import re
import swisseph as swe
import sys

from indic_transliteration import xsanscript as sanscript

from icalendar import Calendar, Event, Alarm
from datetime import datetime, date, timedelta

import jyotisha
import jyotisha.custom_transliteration
import jyotisha.panchangam.spatio_temporal.annual
import jyotisha.panchangam.temporal
from jyotisha.panchangam.spatio_temporal import City
from math import ceil

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s  %(filename)s:%(lineno)d : %(message)s "
)


CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def getName(text, script):
  translation = {'candrAstaH': 'சந்த்ராஸ்தமனம்',
                 'candrOdayaH': 'சந்த்ரோதயம்',
                 'cAndramAnam': 'சாந்த்ரமானம்',
                 'ahOrAtram': 'நாள் முழுவதும்',
                 'tithiH': 'திதி',
                 'nakSatram': 'நக்ஷத்ரம்',
                 'yOgaH': 'யோகம்',
                 'mAsaH': 'மாஸம்',
                 'RtuH': 'ருதுஃ',
                 'ayanam': 'அயனம்',
                 'karaNam': 'கரணம்',
                 'rAziH': 'ராஶிஃ',
                 'lagnam': 'லக்னம்',
                 'candrASTamaH': 'சந்த்ராஷ்டமம்',
                 'zUlam': 'ஶூலம்',
                 'vAsaraH': 'வாஸரம்',
                 'dina-vizESAH': 'தின-விஶேஷங்கள்',
                 'saMvatsaraH': 'ஸம்வத்ஸரம்',
                 'sUryAstaH': 'ஸூர்யாஸ்தமனம்',
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
      logging.warning('%s not found in translation table. Transliterating to %s' % (text, jyotisha.custom_transliteration.tr(text, script)))
      return jyotisha.custom_transliteration.tr(text, script)
  else:
    return jyotisha.custom_transliteration.tr(text, script)


def write_to_file(ics_calendar, fname):
    ics_calendar_file = open(fname, 'wb')
    ics_calendar_file.write(ics_calendar.to_ical())
    ics_calendar_file.close()


def writeDailyICS(panchangam, compute_lagnams=True):
    """Write out the panchangam TeX using a specified template
    """
    output_stream = StringIO()
    month = {1: 'January', 2: 'February', 3: 'March', 4: 'April',
             5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September',
             10: 'October', 11: 'November', 12: 'December'}
    WDAY = {0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
    SHULAM = [('pratIcI dik', 12, 'guDam'), ('prAcI dik', 8, 'dadhi'), ('udIcI dik', 12, 'kSIram'),
              ('udIcI dik', 16, 'kSIram'), ('dakSiNA dik', 20, 'tailam'), ('pratIcI dik', 12, 'guDam'),
              ('prAcI dik', 8, 'dadhi')]

    samvatsara_id = (panchangam.year - 1568) % 60 + 1  # distance from prabhava
    samvatsara_names = (jyotisha.panchangam.temporal.NAMES['SAMVATSARA_NAMES'][panchangam.script][samvatsara_id],
                        jyotisha.panchangam.temporal.NAMES['SAMVATSARA_NAMES'][panchangam.script][(samvatsara_id % 60) + 1])

    yname_solar = samvatsara_names[0]  # Assign year name until Mesha Sankranti
    yname_lunar = samvatsara_names[0]  # Assign year name until Mesha Sankranti

    # print(' \\sffamily \\fontsize 43  43 \\selectfont  %d–%d\\\\[0.5cm] \n\\hrule\n\\vspace 0.2cm '
    #       % (panchangam.year + 3100, panchangam.year + 3101), file=output_stream)
    # print(' \\sffamily \\fontsize 23  23 \\selectfont   %s \\\\[0.2cm] '
    #       % jyotisha.custom_transliteration.print_lat_lon(panchangam.city.latitude, panchangam.city.longitude), file=output_stream)

    panchangam.get_kaalas()

    ics_calendar = Calendar()

    alarm = Alarm()
    alarm.add('action', 'DISPLAY')
    alarm.add('trigger', timedelta(hours=-4))  # default alarm, with a 4 hour reminder

    for d in range(1, jyotisha.panchangam.temporal.MAX_SZ - 1):

        [y, m, dt, t] = swe.revjul(panchangam.jd_start_utc + d - 1)

        print('%s %02d-%s-%4d' % (WDAY[panchangam.weekday[d]], dt, month[m], y), file=output_stream)
        event = Event()
        event.add('summary', '%s %02d-%s-%4d (%s)' % (WDAY[panchangam.weekday[d]][:3].upper(), dt, month[m], y, jyotisha.custom_transliteration.tr(panchangam.city.name, panchangam.script)))

        jd = panchangam.jd_midnight[d]

        tithi_data_str = ''
        for tithi_ID, tithi_end_jd in panchangam.tithi_data[d]:
            tithi = jyotisha.panchangam.temporal.NAMES['TITHI_NAMES'][panchangam.script][tithi_ID].replace('-', jyotisha.custom_transliteration.tr('pakSa', panchangam.script) + ' ')
            if tithi_end_jd is None:
                tithi_data_str = '%s; %s►%s' % \
                                 (tithi_data_str, tithi, jyotisha.custom_transliteration.tr('ahOrAtram (tridinaspRk)', panchangam.script))
            else:
                tithi_data_str = '%s; %s►%s%s' % \
                                 (tithi_data_str, tithi,
                                  jyotisha.panchangam.temporal.Time(24 * (tithi_end_jd - jd)).toString(format=panchangam.fmt),
                                  ' ')
        tithi_data_str = '<b>' + getName('tithiH', panchangam.script) + '</b>—' + tithi_data_str[2:]

        nakshatram_data_str = ''
        for nakshatram_ID, nakshatram_end_jd in panchangam.nakshatram_data[d]:
            nakshatram = jyotisha.panchangam.temporal.NAMES['NAKSHATRAM_NAMES'][panchangam.script][nakshatram_ID]
            if nakshatram_end_jd is None:
                nakshatram_data_str = '%s; %s►%s' % \
                                      (nakshatram_data_str, nakshatram,
                                       jyotisha.custom_transliteration.tr('ahOrAtram', panchangam.script))
            else:
                nakshatram_data_str = '%s; %s►%s' % \
                                      (nakshatram_data_str, nakshatram,
                                       jyotisha.panchangam.temporal.Time(24 * (nakshatram_end_jd -
                                                                               jd)).toString(format=panchangam.fmt))
        nakshatram_data_str = '<b>' + getName('nakSatram', panchangam.script) + '</b>—' + nakshatram_data_str[2:]

        chandrashtama_rashi_data_str = ''
        for rashi_ID, rashi_end_jd in panchangam.rashi_data[d]:
            rashi = jyotisha.panchangam.temporal.NAMES['RASHI_SUFFIXED_NAMES'][panchangam.script][rashi_ID]
            if rashi_end_jd is None:
                rashi_data_str = '%s' % (rashi)
                chandrashtama_rashi_data_str = '<b>' + getName('candrASTamaH', panchangam.script) + '</b>—%s' % (jyotisha.panchangam.temporal.NAMES['RASHI_SUFFIXED_NAMES'][panchangam.script][((rashi_ID - 8) % 12) + 1])
            else:
                rashi_data_str = '%s►%s' % (rashi, jyotisha.panchangam.temporal.Time(24 * (rashi_end_jd - jd)).toString(format=panchangam.fmt))
                # logging.debug(((jyotisha.panchangam.temporal.NAMES['RASHI_SUFFIXED_NAMES'][panchangam.script][((rashi_ID + 7) % 12) + 1], jyotisha.panchangam.temporal.Time(24 * (rashi_end_jd - jd)).toString(format=panchangam.fmt), jyotisha.panchangam.temporal.NAMES['RASHI_SUFFIXED_NAMES'][panchangam.script][((rashi_ID + 8) % 12) + 1])))
                chandrashtama_rashi_data_str = '<b>' + getName('candrASTamaH', panchangam.script) + '</b>—%s►%s; %s ➥' % (jyotisha.panchangam.temporal.NAMES['RASHI_SUFFIXED_NAMES'][panchangam.script][((rashi_ID - 8) % 12) + 1], jyotisha.panchangam.temporal.Time(24 * (rashi_end_jd - jd)).toString(format=panchangam.fmt), jyotisha.panchangam.temporal.NAMES['RASHI_SUFFIXED_NAMES'][panchangam.script][((rashi_ID - 7) % 12) + 1])

        if compute_lagnams:
            lagna_data_str = ''
            for lagna_ID, lagna_end_jd in panchangam.lagna_data[d]:
                lagna = jyotisha.panchangam.temporal.NAMES['RASHI_NAMES'][panchangam.script][lagna_ID]
                lagna_data_str = '%s; %s►%s' % \
                                 (lagna_data_str, lagna,
                                  jyotisha.panchangam.temporal.Time(24 * (lagna_end_jd - jd)).toString(format=panchangam.fmt))
            lagna_data_str = '<b>' + getName('lagnam', panchangam.script) + '</b>—' + lagna_data_str[2:]

        yoga_data_str = ''
        for yoga_ID, yoga_end_jd in panchangam.yoga_data[d]:
            # if yoga_data_str != '':
            #     yoga_data_str += ' '
            yoga = jyotisha.panchangam.temporal.NAMES['YOGA_NAMES'][panchangam.script][yoga_ID]
            if yoga_end_jd is None:
                yoga_data_str = '%s; %s►%s' % (yoga_data_str, yoga, jyotisha.custom_transliteration.tr('ahOrAtram', panchangam.script))
            else:
                yoga_data_str = '%s; %s►%s' % (yoga_data_str, yoga, jyotisha.panchangam.temporal.Time(24 * (yoga_end_jd - jd)).toString(format=panchangam.fmt))
        if yoga_end_jd is not None:
            yoga_data_str += '; %s ➥' % (jyotisha.panchangam.temporal.NAMES['YOGA_NAMES'][panchangam.script][(yoga_ID % 27) + 1])
        yoga_data_str = '<b>' + getName('yOgaH', panchangam.script) + '</b>—' + yoga_data_str[2:]

        karanam_data_str = ''
        for numKaranam, (karanam_ID, karanam_end_jd) in enumerate(panchangam.karanam_data[d]):
            # if numKaranam == 1:
            #     karanam_data_str += ' '
            karanam = jyotisha.panchangam.temporal.NAMES['KARANAM_NAMES'][panchangam.script][karanam_ID]
            if karanam_end_jd is None:
                karanam_data_str = '%s; %s►%s' % \
                                   (karanam_data_str, karanam, jyotisha.custom_transliteration.tr('ahOrAtram', panchangam.script))
            else:
                karanam_data_str = '%s; %s►%s' % \
                                   (karanam_data_str, karanam,
                                    jyotisha.panchangam.temporal.Time(24 * (karanam_end_jd - jd)).toString(format=panchangam.fmt))
        if karanam_end_jd is not None:
            karanam_data_str += '; %s ➥' % (jyotisha.panchangam.temporal.NAMES['KARANAM_NAMES'][panchangam.script][(karanam_ID % 60) + 1])
        karanam_data_str = '<b>' + getName('karaNam', panchangam.script) + '</b>—' + karanam_data_str[2:]

        sunrise = jyotisha.panchangam.temporal.Time(24 * (panchangam.jd_sunrise[d] - jd)).toString(format=panchangam.fmt)
        sunset = jyotisha.panchangam.temporal.Time(24 * (panchangam.jd_sunset[d] - jd)).toString(format=panchangam.fmt)
        moonrise = jyotisha.panchangam.temporal.Time(24 * (panchangam.jd_moonrise[d] - jd)).toString(format=panchangam.fmt)
        moonset = jyotisha.panchangam.temporal.Time(24 * (panchangam.jd_moonset[d] - jd)).toString(format=panchangam.fmt)

        # braahma = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['braahma'][0] - jd)).toString(format=panchangam.fmt)
        # pratahsandhya = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['prAtaH sandhyA'][0] - jd)).toString(format=panchangam.fmt)
        # pratahsandhya_end = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['prAtaH sandhyA end'][0] - jd)).toString(format=panchangam.fmt)
        # sangava = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['saGgava'][0] - jd)).toString(format=panchangam.fmt)
        # madhyaahna = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['madhyAhna'][0] - jd)).toString(format=panchangam.fmt)
        # madhyahnika_sandhya = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['mAdhyAhnika sandhyA'][0] - jd)).toString(format=panchangam.fmt)
        # madhyahnika_sandhya_end = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['mAdhyAhnika sandhyA end'][0] - jd)).toString(format=panchangam.fmt)
        aparahna = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['aparAhna'][0] - jd)).toString(format=panchangam.fmt)
        sayahna = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['sAyAhna'][0] - jd)).toString(format=panchangam.fmt)
        # sayamsandhya = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['sAyaM sandhyA'][0] - jd)).toString(format=panchangam.fmt)
        # sayamsandhya_end = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['sAyaM sandhyA end'][0] - jd)).toString(format=panchangam.fmt)
        # ratriyama1 = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['rAtri yAma 1'][0] - jd)).toString(format=panchangam.fmt)
        # sayana_time = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['zayana'][0] - jd)).toString(format=panchangam.fmt)
        dinanta = jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['dinAnta'][0] - jd)).toString(format=panchangam.fmt)

        rahu = '%s–%s' % (
            jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['rahu'][0] - jd)).toString(format=panchangam.fmt),
            jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['rahu'][1] - jd)).toString(format=panchangam.fmt))
        yama = '%s–%s' % (
            jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['yama'][0] - jd)).toString(format=panchangam.fmt),
            jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['yama'][1] - jd)).toString(format=panchangam.fmt))
        gulika = '%s–%s' % (
            jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['gulika'][0] - jd)).toString(format=panchangam.fmt),
            jyotisha.panchangam.temporal.Time(24 * (panchangam.kaalas[d]['gulika'][1] - jd)).toString(format=panchangam.fmt))

        if panchangam.solar_month[d] == 1:
            # Flip the year name for the remaining days
            yname_solar = samvatsara_names[1]
        if panchangam.lunar_month[d] == 1:
            # Flip the year name for the remaining days
            yname_lunar = samvatsara_names[1]

        # Assign samvatsara, ayana, rtu #
        ayanam = jyotisha.panchangam.temporal.NAMES['AYANA_NAMES'][panchangam.script][panchangam.solar_month[d]]
        rtu_solar = jyotisha.panchangam.temporal.NAMES['RTU_NAMES'][panchangam.script][panchangam.solar_month[d]]
        rtu_lunar = jyotisha.panchangam.temporal.NAMES['RTU_NAMES'][panchangam.script][int(ceil(panchangam.lunar_month[d]))]

        if panchangam.solar_month_end_time[d] is None:
            month_end_str = ''
        else:
            _m = panchangam.solar_month[d - 1]
            if panchangam.solar_month_end_time[d] >= panchangam.jd_sunrise[d + 1]:
                month_end_str = '%s►%s' % (jyotisha.panchangam.temporal.NAMES['RASHI_NAMES'][panchangam.script][_m], jyotisha.panchangam.temporal.Time(24 * (panchangam.solar_month_end_time[d] - panchangam.jd_midnight[d + 1])).toString(format=panchangam.fmt))
            else:
                month_end_str = '%s►%s' % (jyotisha.panchangam.temporal.NAMES['RASHI_NAMES'][panchangam.script][_m], jyotisha.panchangam.temporal.Time(24 * (panchangam.solar_month_end_time[d] - panchangam.jd_midnight[d])).toString(format=panchangam.fmt))
        if month_end_str == '':
          month_data = '%s %d' % (jyotisha.panchangam.temporal.NAMES['RASHI_NAMES'][panchangam.script][panchangam.solar_month[d]], panchangam.solar_month_day[d])
        else:
          month_data = '%s %d; %s' % (jyotisha.panchangam.temporal.NAMES['RASHI_NAMES'][panchangam.script][panchangam.solar_month[d]], jyotisha.custom_transliteration(panchangam.solar_month_day[d], panchangam.script), month_end_str)

        vara = jyotisha.panchangam.temporal.NAMES['VARA_NAMES'][panchangam.script][panchangam.weekday[d]]

        if yname_lunar == yname_solar:
          print('<b>' + getName('saMvatsaraH', panchangam.script) + '</b>—%s' % yname_lunar, file=output_stream)
          print('<b>' + getName('ayanam', panchangam.script) + '</b>—%s' % ayanam, file=output_stream)
        if rtu_lunar == rtu_solar:
          print('<b>' + getName('RtuH', panchangam.script) + '</b>—%s' % rtu_lunar, file=output_stream)

        print('°' * 25, file=output_stream)
        print('☀ ' + getName('sauramAnam', panchangam.script), file=output_stream)
        if yname_lunar != yname_solar:
          print('<b>' + getName('saMvatsaraH', panchangam.script) + '</b>—%s' % yname_solar, file=output_stream)
          print('<b>' + getName('ayanam', panchangam.script) + '</b>—%s' % ayanam, file=output_stream)
        if rtu_lunar != rtu_solar:
          print('<b>' + getName('RtuH', panchangam.script) + '</b>—%s' % rtu_solar, file=output_stream)
        print('<b>' + getName('mAsaH', panchangam.script) + '</b>—%s' % month_data, file=output_stream)
        print('°' * 25, file=output_stream)

        print('⚪ ' + getName('cAndramAnam', panchangam.script), file=output_stream)
        if yname_lunar != yname_solar:
          print('<b>' + getName('saMvatsaraH', panchangam.script) + '</b>—%s' % yname_lunar, file=output_stream)
          print('<b>' + getName('ayanam', panchangam.script) + '</b>—%s' % ayanam, file=output_stream)
        if rtu_lunar != rtu_solar:
          print('<b>' + getName('RtuH', panchangam.script) + '</b>—%s' % rtu_lunar, file=output_stream)
        print('<b>' + getName('mAsaH', panchangam.script) + '</b>—%s' % jyotisha.panchangam.temporal.get_chandra_masa(panchangam.lunar_month[d], jyotisha.panchangam.temporal.NAMES, panchangam.script), file=output_stream)
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
        print('%s' % (tithi_data_str), file=output_stream)
        print('<b>%s</b>—%s' % (getName('vAsaraH', panchangam.script), vara), file=output_stream)
        print('%s (%s)' % (nakshatram_data_str, rashi_data_str), file=output_stream)
        print('%s' % (yoga_data_str), file=output_stream)
        print('%s' % (karanam_data_str), file=output_stream)
        print('%s' % (chandrashtama_rashi_data_str), file=output_stream)

        if panchangam.jd_moonrise[d] > panchangam.jd_sunrise[d + 1]:
          moonrise = '---'
        if panchangam.jd_moonset[d] > panchangam.jd_sunrise[d + 1]:
          moonset = '---'

        print('\nLocation-specific data (for %s):' % jyotisha.custom_transliteration.tr(panchangam.city.name, panchangam.script), file=output_stream)

        if compute_lagnams:
          print('%s' % (lagna_data_str), file=output_stream)

        if panchangam.jd_moonrise[d] < panchangam.jd_moonset[d]:
          print('<b>%s</b>—%s; <b>%s</b>—%s' % (getName('sUryOdayaH', panchangam.script), sunrise, getName('sUryAstaH', panchangam.script), sunset), file=output_stream)
          print('<b>%s</b>—%s; <b>%s</b>—%s' % (getName('candrOdayaH', panchangam.script), moonrise, getName('candrAstaH', panchangam.script), moonset), file=output_stream)
        else:
          print('<b>%s</b>—%s; <b>%s</b>—%s' % (getName('sUryOdayaH', panchangam.script), sunrise, getName('sUryAstaH', panchangam.script), sunset), file=output_stream)
          print('<b>%s</b>—%s; <b>%s</b>—%s' % (getName('candrAstaH', panchangam.script), moonset, getName('candrOdayaH', panchangam.script), moonrise), file=output_stream)

        print('<b>%s</b>—%s►%s' % (getName('aparAhNa-kAlaH', panchangam.script), aparahna, sayahna), file=output_stream)
        print('<b>%s</b>—%s' % (getName('dinAntaH', panchangam.script), dinanta), file=output_stream)
        print('<b>%s</b>—%s; <b>%s</b>—%s; <b>%s</b>—%s' % (getName('rAhukAlaH', panchangam.script), rahu,
                                                            getName('yamaghaNTaH', panchangam.script), yama,
                                                            getName('gulikakAlaH', panchangam.script), gulika), file=output_stream)

        shulam_end_jd = panchangam.jd_sunrise[d] + (panchangam.jd_sunset[d] - panchangam.jd_sunrise[d]) * (SHULAM[panchangam.weekday[d]][1] / 30)
        print('<b>%s</b>—%s (►%s); <b>%s</b>–%s' % (getName('zUlam', panchangam.script), getName(SHULAM[panchangam.weekday[d]][0], panchangam.script),
                                                    jyotisha.panchangam.temporal.Time(24 * (shulam_end_jd - jd)).toString(format=panchangam.fmt),
                                                    getName('parihAraH', panchangam.script), getName(SHULAM[panchangam.weekday[d]][2], panchangam.script)), file=output_stream)
        # Using set as an ugly workaround since we may have sometimes assigned the same
        # festival to the same day again!
        fest_list = []
        fest_classes = ['kAJcI', 'EkAdazI']
        for f in sorted(set(panchangam.festivals[d])):
          for fcl in fest_classes:
            if f.find(fcl) != -1:
              fest_name_cleaned = jyotisha.custom_transliteration.tr(f, panchangam.script).replace('~', ' ')
              fest_name_cleaned = re.sub('[{}]', '', fest_name_cleaned).replace('\\', '')
              fest_list.append(fest_name_cleaned.replace('ஆராதநா', 'ஆராதனை'))
        if len(fest_list):
          print('<b>%s</b>—%s' % (getName('dina-vizESAH', panchangam.script), '; '.join(fest_list)), file=output_stream)

        output_text = output_stream.getvalue()
        output_text = re.sub('([^ ])ந', '\\1ன', output_text)
        output_text = re.sub('\<ன', 'ந', output_text)
        output_text = re.sub('^ன', 'ந', output_text)
        output_text = re.sub('\nன', '\nந', output_text)
        output_text = re.sub('—ன', '—ந', output_text)
        output_text = re.sub('-ன', '-ந', output_text)
        output_text = re.sub('ன்த', 'ந்த', output_text)
        output_text = re.sub('ன்த்', 'ந்த்', output_text)
        # print(output_text)

        event.add('dtstart', date(y, m, dt))
        event.add('dtend', (datetime(y, m, dt) + timedelta(1)).date())
        event.add_component(alarm)
        event.add('description', output_text.replace('\n', '<br/>'))
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

    panchangam = jyotisha.panchangam.spatio_temporal.annual.get_panchangam(city=city, year=year, script=script, fmt=fmt, compute_lagnams=compute_lagnams)
    panchangam.script = script  # Force script irrespective of what was obtained from saved file
    panchangam.fmt = fmt  # Force fmt

    panchangam.update_festival_details()

    ics_calendar = writeDailyICS(panchangam, compute_lagnams)
    output_file = os.path.expanduser('%s/%s-%d-%s-daily.ics' % ("~/Documents", city.name, year, script))
    write_to_file(ics_calendar, output_file)


if __name__ == '__main__':
    main()
