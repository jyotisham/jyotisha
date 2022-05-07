#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import os
import os.path
import sys
from datetime import datetime
from math import ceil

from indic_transliteration import sanscript
from pytz import timezone as tz

import jyotisha
import jyotisha.custom_transliteration
import jyotisha.panchaanga.temporal.names
import jyotisha.panchaanga.spatio_temporal.annual
import jyotisha.panchaanga.temporal
from jyotisha.panchaanga.temporal import names
from jyotisha.panchaanga.spatio_temporal import City
from jyotisha.panchaanga.temporal import time
from jyotisha.panchaanga.temporal.festival import rules
from jyotisha.panchaanga.temporal.time import Timezone
from jyotisha.panchaanga.writer.tex.day_details import get_lagna_data_str, get_raahu_yama_gulika_strings, \
  get_karaNa_data_str, get_yoga_data_str, get_raashi_data_str, get_nakshatra_data_str, get_tithi_data_str

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def emit(panchaanga, time_format="hh:mm", languages=None, scripts=None, output_stream=None):
  """Write out the panchaanga TeX using a specified template
  """
  # day_colours = {0: 'blue', 1: 'blue', 2: 'blue',
  #                3: 'blue', 4: 'blue', 5: 'blue', 6: 'blue'}
  compute_lagnams = panchaanga.computation_system.festival_options.set_lagnas
  if scripts is None:
    scripts = [sanscript.DEVANAGARI]
  if languages is None:
    languages = ["sa"]

  template_file = open(os.path.join(os.path.dirname(__file__), 'templates/daily_cal_template.tex'))

  template_lines = template_file.readlines()
  for i in range(len(template_lines)):
    print(template_lines[i][:-1], file=output_stream)

  year = panchaanga.start_date.year
  logging.debug(year)

  samvatsara_id = (year - 1568) % 60 + 1  # distance from prabhava
  samvatsara_names = (names.NAMES['SAMVATSARA_NAMES']['sa'][scripts[0]][samvatsara_id],
                      names.NAMES['SAMVATSARA_NAMES']['sa'][scripts[0]][(samvatsara_id % 60) + 1])

  yname = samvatsara_names[0]  # Assign year name until Mesha Sankranti

  set_top_content(output_stream, panchaanga, samvatsara_names, scripts, year)

  daily_panchaangas = panchaanga.daily_panchaangas_sorted()
  for d, daily_panchaanga in enumerate(daily_panchaangas):
    if d == 0:
      previous_day_panchaanga = None
    else:
      previous_day_panchaanga = daily_panchaangas[d - 1]
    if daily_panchaanga.date < panchaanga.start_date or daily_panchaanga.date > panchaanga.end_date:
      continue
    [y, m, dt] = [daily_panchaanga.date.year, daily_panchaanga.date.month, daily_panchaanga.date.day]

    # checking @ 6am local - can we do any better?
    local_time = tz(panchaanga.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
    # compute offset from UTC in hours
    tz_off = (datetime.utcoffset(local_time).days * 86400 +
              datetime.utcoffset(local_time).seconds) / 3600.0

    tithi_data_str = get_tithi_data_str(daily_panchaanga, scripts, time_format, previous_day_panchaanga, include_early_end_angas=True)

    nakshatra_data_str = get_nakshatra_data_str(daily_panchaanga, scripts, time_format, previous_day_panchaanga, include_early_end_angas=True)

    yoga_data_str = get_yoga_data_str(daily_panchaanga, scripts, time_format, previous_day_panchaanga, include_early_end_angas=True)

    karana_data_str = get_karaNa_data_str(daily_panchaanga, scripts, time_format, previous_day_panchaanga, include_early_end_angas=True)

    rashi_data_str = get_raashi_data_str(daily_panchaanga, scripts, time_format)
    
    lagna_data_str = get_lagna_data_str(daily_panchaanga, scripts, time_format) if compute_lagnams else ''

    gulika, rahu, yama, raatri_gulika, raatri_yama, durmuhurta1, durmuhurta2 = get_raahu_yama_gulika_strings(daily_panchaanga, time_format)

    if daily_panchaanga.solar_sidereal_date_sunset.month == 1:
      # Flip the year name for the remaining days
      yname = samvatsara_names[1]

    # Assign samvatsara, ayana, rtu #
    sar_data = '{%s}{%s}{%s}' % (yname,
                                 names.NAMES['AYANA_NAMES']['sa'][scripts[0]][daily_panchaanga.solar_sidereal_date_sunset.month],
                                 names.NAMES['RTU_NAMES']['sa'][scripts[0]][daily_panchaanga.solar_sidereal_date_sunset.month])

    if daily_panchaanga.solar_sidereal_date_sunset.month_transition is None:
      month_end_str = ''
    else:
      _m = daily_panchaangas[d - 1].solar_sidereal_date_sunset.month
      if daily_panchaanga.solar_sidereal_date_sunset.month_transition >= daily_panchaangas[d + 1].jd_sunrise:
        month_end_str = '\\mbox{%s{\\tiny\\RIGHTarrow}{%s}}' % (
          names.NAMES['RASHI_NAMES']['sa'][scripts[0]][_m], time.Hour(
            24 * (daily_panchaanga.solar_sidereal_date_sunset.month_transition - daily_panchaangas[d + 1].julian_day_start)).to_string(format=time_format))
      else:
        month_end_str = '\\mbox{%s{\\tiny\\RIGHTarrow}{%s}}' % (
          names.NAMES['RASHI_NAMES']['sa'][scripts[0]][_m], time.Hour(
            24 * (daily_panchaanga.solar_sidereal_date_sunset.month_transition - daily_panchaanga.julian_day_start)).to_string(format=time_format))

    month_data = '\\sunmonth{%s}{%d}{%s}' % (
      names.NAMES['RASHI_NAMES']['sa'][scripts[0]][daily_panchaanga.solar_sidereal_date_sunset.month], daily_panchaanga.solar_sidereal_date_sunset.day,
      month_end_str)

    print('\\caldata{%s}{%s}{%s{%s}{%s}{%s}%s}' %
          (names.month_map[m].upper(), dt, month_data,
           names.get_chandra_masa(daily_panchaanga.lunar_month_sunrise.index, scripts[0]),
           names.NAMES['RTU_NAMES']['sa'][scripts[0]][int(ceil(daily_panchaanga.lunar_month_sunrise.index))],
           names.NAMES['VARA_NAMES']['sa'][scripts[0]][daily_panchaanga.date.get_weekday()], sar_data), file=output_stream)

    stream_sun_moon_rise_data(daily_panchaanga, output_stream, time_format)

    stream_daylength_based_periods(daily_panchaanga, output_stream, time_format)

    print('{\\tnykdata{%s}%%\n{%s}{%s}%%\n{%s}%%\n{%s}{%s}\n}'
          % (tithi_data_str, nakshatra_data_str, rashi_data_str, yoga_data_str,
             karana_data_str, lagna_data_str), file=output_stream)

    print_festivals_to_stream(daily_panchaanga, output_stream, panchaanga, languages, scripts)

    print('{%s} ' % names.weekday_short_map[daily_panchaanga.date.get_weekday()], file=output_stream)
    print('\\cfoot{\\rygdata{%s}{%s}{%s}}' % (rahu, yama, gulika), file=output_stream)

    if m == 12 and dt == 31:
      break

  print('\\end{document}', file=output_stream)


def stream_daylength_based_periods(daily_panchaanga, output_stream, time_format):
  jd = daily_panchaanga.julian_day_start

  braahma_start = time.Hour(24 * (daily_panchaanga.day_length_based_periods.fifteen_fold_division.braahma.jd_start - jd)).to_string(
    format=time_format)
  praatahsandhya_start = time.Hour(
    24 * (daily_panchaanga.day_length_based_periods.fifteen_fold_division.praatas_sandhyaa.jd_start - jd)).to_string(format=time_format)
  praatahsandhya_end = time.Hour(
    24 * (daily_panchaanga.day_length_based_periods.fifteen_fold_division.praatas_sandhyaa.jd_end - jd)).to_string(format=time_format)
  saangava = time.Hour(24 * (daily_panchaanga.day_length_based_periods.fifteen_fold_division.saangava.jd_start - jd)).to_string(
    format=time_format)
  madhyaahna = time.Hour(24 * (daily_panchaanga.day_length_based_periods.fifteen_fold_division.madhyaahna.jd_start - jd)).to_string(
    format=time_format)
  madhyahnika_sandhya_start = time.Hour(
    24 * (daily_panchaanga.day_length_based_periods.fifteen_fold_division.maadhyaahnika_sandhyaa.jd_start - jd)).to_string(format=time_format)
  madhyahnika_sandhya_end = time.Hour(
    24 * (daily_panchaanga.day_length_based_periods.fifteen_fold_division.maadhyaahnika_sandhyaa.jd_end - jd)).to_string(
    format=time_format)
  aparaahna = time.Hour(
    24 * (daily_panchaanga.day_length_based_periods.fifteen_fold_division.aparaahna.jd_start - jd)).to_string(
    format=time_format)
  sayahna = time.Hour(24 * (daily_panchaanga.day_length_based_periods.fifteen_fold_division.saayaahna.jd_start - jd)).to_string(
    format=time_format)
  sayamsandhya_start = time.Hour(
    24 * (daily_panchaanga.day_length_based_periods.fifteen_fold_division.saayam_sandhyaa.jd_start - jd)).to_string(format=time_format)
  sayamsandhya_end = time.Hour(
    24 * (daily_panchaanga.day_length_based_periods.fifteen_fold_division.saayam_sandhyaa.jd_end - jd)).to_string(format=time_format)
  ratriyama1 = time.Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.raatri_yaama[0].jd_end - jd)).to_string(
    format=time_format)
  shayana_time_end = time.Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.shayana.jd_start - jd)).to_string(
    format=time_format)
  dinaanta = time.Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.dinaanta.jd_start - jd)).to_string(
    format=time_format)
  print(
    '{\\kalas{%s %s %s %s %s %s %s %s %s %s %s %s %s %s}}}' % (braahma_start, praatahsandhya_start, praatahsandhya_end,
                                                               saangava,
                                                               madhyahnika_sandhya_start, madhyahnika_sandhya_end,
                                                               madhyaahna, aparaahna, sayahna,
                                                               sayamsandhya_start, sayamsandhya_end,
                                                               ratriyama1, shayana_time_end, dinaanta),
    file=output_stream)


def stream_sun_moon_rise_data(daily_panchaanga, output_stream, time_format):
  jd = daily_panchaanga.julian_day_start
  sunrise = time.Hour(24 * (daily_panchaanga.jd_sunrise - jd)).to_string(
    format=time_format)
  sunset = time.Hour(24 * (daily_panchaanga.jd_sunset - jd)).to_string(format=time_format)
  moonrise = time.Hour(24 * (daily_panchaanga.jd_moonrise - jd)).to_string(
    format=time_format)
  moonset = time.Hour(24 * (daily_panchaanga.jd_moonset - jd)).to_string(
    format=time_format)
  midday = time.Hour(24 * (daily_panchaanga.jd_sunrise*0.5 + daily_panchaanga.jd_sunset*0.5 - jd)).to_string(
  format=time_format)

  if daily_panchaanga.jd_moonrise > daily_panchaanga.jd_next_sunrise:
    moonrise = '---'
  if daily_panchaanga.jd_moonset > daily_panchaanga.jd_next_sunrise:
    moonset = '---'
  if daily_panchaanga.jd_moonrise < daily_panchaanga.jd_moonset:
    print('{\\sunmoonrsdata{%s}{%s}{%s}{%s}{%s}' % (sunrise, sunset, moonrise, moonset, midday), file=output_stream)
  else:
    print('{\\sunmoonsrdata{%s}{%s}{%s}{%s}{%s}' % (sunrise, sunset, moonrise, moonset, midday), file=output_stream)


def print_festivals_to_stream(daily_panchaanga, output_stream, panchaanga, languages, scripts):
  rules_collection = rules.RulesCollection.get_cached(
    repos_tuple=tuple(panchaanga.computation_system.festival_options.repos), julian_handling=panchaanga.computation_system.festival_options.julian_handling)
  fest_details_dict = rules_collection.name_to_rule
  print('{%s}' % '\\eventsep '.join(
    [f.tex_code(languages=languages, scripts=scripts, timezone=Timezone(timezone_id=panchaanga.city.timezone),
                fest_details_dict=fest_details_dict, reference_date=daily_panchaanga.date) for f in
     sorted(daily_panchaanga.festival_id_to_instance.values())]), file=output_stream)


def set_top_content(output_stream, panchaanga, samvatsara_names, scripts, year):
  print('\\mbox{}', file=output_stream)
  print('\\renewcommand{\\yearname}{%d}' % year, file=output_stream)
  print('\\begin{center}', file=output_stream)
  print('{\\sffamily \\fontsize{80}{80}\\selectfont  %d\\\\[0.5cm]}' % year, file=output_stream)
  print('\\mbox{\\fontsize{48}{48}\\selectfont %s–%s}\\\\'
        % samvatsara_names, file=output_stream)
  print('\\mbox{\\fontsize{32}{32}\\selectfont %s } %%'
        % jyotisha.custom_transliteration.tr('kali', scripts[0]), file=output_stream)
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


def main():
  [city_name, latitude, longitude, tz] = sys.argv[1:5]
  year = int(sys.argv[5])

  compute_lagnams = False  # Default
  scripts = [sanscript.DEVANAGARI]  # Default language is devanagari
  fmt = 'hh:mm'

  if len(sys.argv) == 9:
    compute_lagnams = True
    fmt = sys.argv[7]
    scripts = sys.argv[6].split(",")
  elif len(sys.argv) == 8:
    scripts = sys.argv[6].split(",")
    fmt = sys.argv[7]
    compute_lagnams = False
  elif len(sys.argv) == 7:
    scripts = sys.argv[6].split(",")
    compute_lagnams = False

  city = City(city_name, latitude, longitude, tz)

  panchaanga = jyotisha.panchaanga.spatio_temporal.annual.get_panchaanga_for_civil_year(city=city, year=year)

  emit(panchaanga, scripts=scripts)
  # panchaanga.writeDebugLog()


if __name__ == '__main__':
  main()
