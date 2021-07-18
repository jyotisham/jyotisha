#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import os
import os.path
import sys
from datetime import datetime

from indic_transliteration import sanscript

from jyotisha.panchaanga.temporal import names
from jyotisha.panchaanga.temporal.time import Timezone, Hour
from pytz import timezone as tz

import jyotisha
import jyotisha.custom_transliteration
from jyotisha.panchaanga.spatio_temporal import City, annual
from jyotisha.panchaanga.temporal import time, names
from jyotisha.panchaanga.temporal.festival import rules
from jyotisha.panchaanga.writer.tex import day_details

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def write_monthly_tex(panchaanga, time_format="hh:mm", languages=None, scripts=None):
  """Write out the panchaanga TeX using a specified template
  """
  if scripts is None:
    scripts = [sanscript.DEVANAGARI]
  day_colours = {0: 'blue', 1: 'blue', 2: 'blue',
                 3: 'blue', 4: 'blue', 5: 'blue', 6: 'blue'}

  if languages is None:
    languages = ["sa"]

  monthly_template_file = open(os.path.join(os.path.dirname(__file__), 'templates/monthly_cal_template.tex'))

  template_lines = monthly_template_file.readlines()
  for i in range(0, len(template_lines) - 3):
    print(template_lines[i][:-1])

  samvatsara_id = (panchaanga.year - 1568) % 60 + 1  # distance from prabhava
  samvatsara_names = '%s–%s' % (names.NAMES['SAMVATSARA_NAMES']['sa'][scripts[0]][samvatsara_id],
                                names.NAMES['SAMVATSARA_NAMES']['sa'][scripts[0]][(samvatsara_id % 60) + 1])

  print('\\mbox{}')
  print('{\\sffamily\\fontsize{60}{25}\\selectfont %d\\\\[0.5cm]}' % panchaanga.year)
  print('\\mbox{\\font\\x="Siddhanta:language=deva" at 48 pt\\x %s}\\\\[0.5cm]' %
        samvatsara_names)
  print('\\mbox{\\font\\x="Siddhanta:language=deva" at 32 pt\\x %s } %%'
        % jyotisha.custom_transliteration.tr('kali', scripts[0]))
  print('{\\sffamily\\fontsize{32}{25}\\selectfont %d–%d\\\\[0.5cm]}'
        % (panchaanga.year + 3100, panchaanga.year + 3101))
  print('{\\sffamily\\fontsize{48}{25}\\selectfont \\uppercase{%s}\\\\[0.2cm]}' %
        panchaanga.city.name)
  print('{\\sffamily\\fontsize{16}{25}\\selectfont {%s}\\\\[0.5cm]}' %
        jyotisha.custom_transliteration.print_lat_lon(panchaanga.city.latitude, panchaanga.city.longitude))
  print('\\hrule')

  print('\\newpage')
  print('\\centering')
  print('\\centerline{\\LARGE {{%s}}}' % jyotisha.custom_transliteration.tr('mAsAntara-vizESAH', scripts[0]))
  print('\\begin{multicols*}{3}')
  print('\\TrickSupertabularIntoMulticols')
  print('\\begin{supertabular}' +
        '{>{\\sffamily}r>{\\sffamily}r>{\\sffamily}c>{\\hangindent=2ex}p{8cm}}')

  mlast = 1
  daily_panchaangas = panchaanga.daily_panchaangas_sorted()
  for d in range(panchaanga.duration_prior_padding, jyotisha.panchaanga.temporal.MAX_SZ - 1):
    [y, m, dt, t] = time.jd_to_utc_gregorian(panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()
    daily_panchaanga = daily_panchaangas[d]

    rules_collection = rules.RulesCollection.get_cached(
      repos_tuple=tuple(panchaanga.computation_system.festival_options.repos), julian_handling=panchaanga.computation_system.festival_options.julian_handling)
    fest_details_dict = rules_collection.name_to_rule

    if len(daily_panchaanga.festival_id_to_instance) != 0:
      if m != mlast:
        mlast = m
        print('\\\\')

      print('%s & %s & %s & {\\raggedright %s} \\\\' %
            (names.month_map[m], dt, names.weekday_short_map[daily_panchaanga.date.get_weekday()],
             '\\\\'.join([f.tex_code(languages=languages, scripts=scripts, timezone=panchaanga.city.timezone, fest_details_dict=fest_details_dict, reference_date=daily_panchaanga.date)
                          for f in sorted(daily_panchaanga.festival_id_to_instance.values())])))

    if m == 12 and dt == 31:
      break

  print('\\end{supertabular}')
  print('\\end{multicols*}')
  print('\\renewcommand{\\tamil}[1]{%')
  print('{\\fontspec[Scale=0.9,FakeStretch=0.9]{Noto Sans Tamil}\\fontsize{7}{12}\\selectfont #1}}')

  # print('\\clearpage')

  month_text = ''
  W6D1 = W6D2 = ''
  for d in range(panchaanga.duration_prior_padding, jyotisha.panchaanga.temporal.MAX_SZ - 1):
    [y, m, dt, t] = time.jd_to_utc_gregorian(panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

    # checking @ 6am local - can we do any better?
    local_time = tz(panchaanga.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
    # compute offset from UTC in hours
    tz_off = (datetime.utcoffset(local_time).days * 86400 +
              datetime.utcoffset(local_time).seconds) / 3600.0

    # What is the jd at 00:00 local time today?
    jd = daily_panchaanga.julian_day_start

    if dt == 1:
      currWeek = 1
      if m > 1:
        month_text = month_text.replace('W6D1', W6D1)
        month_text = month_text.replace('W6D2', W6D2)
        print(month_text)
        month_text = W6D1 = W6D2 = ''
        if currWeek < 6:
          if daily_panchaanga.date.get_weekday() != 0:  # Space till Sunday
            for i in range(daily_panchaanga.date.get_weekday(), 6):
              print("\\mbox{}  & %% %d" % currWeek)
            print("\\\\ \\hline")
        print('\\end{tabular}')
        print('\n\n')

      # Begin tabular
      print('\\begin{tabular}{|c|c|c|c|c|c|c|}')
      print('\\multicolumn{7}{c}{\\Large \\bfseries \\sffamily %s %s}\\\\[3mm]' % (
        names.month_map[m], y))
      print('\\hline')
      WDAY_NAMES = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
      print(' & '.join(['\\textbf{\\textsf{%s}}' %
                        _day for _day in WDAY_NAMES]) + ' \\\\ \\hline')

      # Blanks for previous weekdays
      for i in range(0, daily_panchaanga.date.get_weekday()):
        if i == 0:
          month_text += '\n' + ("{W6D1}  &")
        elif i == 1:
          month_text += '\n' + ("{W6D2}  &")
        else:
          month_text += '\n' + ("{}  &")

    tithi_data_str = day_details.get_tithi_data_str(daily_panchaanga, scripts, time_format)

    nakshatra_data_str = day_details.get_nakshatra_data_str(daily_panchaanga, scripts, time_format)

    yoga_data_str = day_details.get_yoga_data_str(daily_panchaanga, scripts, time_format)

    karana_data_str = day_details.get_karaNa_data_str(daily_panchaanga, scripts, time_format)


    sunrise = Hour(24 * (daily_panchaanga.jd_sunrise - jd)).to_string(
      format=time_format)
    sunset = Hour(24 * (daily_panchaanga.jd_sunset - jd)).to_string(format=time_format)
    saangava = Hour(24 * (daily_panchaanga.day_length_based_periods.fifteen_fold_division.saangava.jd_start - jd)).to_string(
      format=time_format)
    rahu = '%s--%s' % (
      Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.raahu.jd_start - jd)).to_string(
        format=time_format),
      Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.raahu.jd_end - jd)).to_string(
        format=time_format))
    yama = '%s--%s' % (
      Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.yama.jd_start - jd)).to_string(
        format=time_format),
      Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.yama.jd_end - jd)).to_string(
        format=time_format))

    if daily_panchaanga.solar_sidereal_date_sunset.month_transition is None:
      month_end_str = ''
    else:
      _m = daily_panchaangas[d - 1].solar_sidereal_date_sunset.month
      if daily_panchaanga.solar_sidereal_date_sunset.month_transition >= daily_panchaangas[d + 1].jd_sunrise:
        month_end_str = '\\mbox{%s{\\tiny\\RIGHTarrow}\\textsf{%s}}' % (
          names.NAMES['RASHI_NAMES']['sa'][scripts[0]][_m], Hour(
            24 * (daily_panchaanga.solar_sidereal_date_sunset.month_transition - daily_panchaangas[d + 1].julian_day_start)).to_string(format=time_format))
      else:
        month_end_str = '\\mbox{%s{\\tiny\\RIGHTarrow}\\textsf{%s}}' % (
          names.NAMES['RASHI_NAMES']['sa'][scripts[0]][_m], Hour(
            24 * (daily_panchaanga.solar_sidereal_date_sunset.month_transition - daily_panchaanga.julian_day_start)).to_string(format=time_format))

    month_data = '\\sunmonth{%s}{%d}{%s}' % (
      names.NAMES['RASHI_NAMES']['sa'][scripts[0]][daily_panchaanga.solar_sidereal_date_sunset.month], daily_panchaanga.solar_sidereal_date_sunset.day,
      month_end_str)

    if currWeek < 6:
      month_text += '\n' + ('\\caldata{\\textcolor{%s}{%s}}{%s{%s}}%%' %
                            (day_colours[daily_panchaanga.date.get_weekday()], dt, month_data,
                             names.get_chandra_masa(daily_panchaanga.lunar_month_sunrise, scripts[0])))
      month_text += '\n' + ('{\\sundata{%s}{%s}{%s}}%%' % (sunrise, sunset, saangava))
      month_text += '\n' + ('{\\tnyk{%s}%%\n{%s}%%\n{%s}%%\n{%s}}%%' % (tithi_data_str, nakshatra_data_str,
                                                                        yoga_data_str, karana_data_str))
      month_text += '\n' + ('{\\rahuyama{%s}{%s}}%%' % (rahu, yama))

      # Using set as an ugly workaround since we may have sometimes assigned the same
      # festival to the same day again!
      month_text += '\n' + ('{%s}' % '\\eventsep '.join(
        [f.tex_code(languages=languages, scripts=scripts, timezone=panchaanga.city.timezone, fest_details_dict=fest_details_dict, reference_date=daily_panchaanga.date) for f in
         sorted(daily_panchaanga.festival_id_to_instance.values())]))
    else:
      if daily_panchaanga.date.get_weekday() == 0:
        W6D1 = '\n' + ('\\caldata{\\textcolor{%s}{%s}}{%s{%s}}%%' %
                       (day_colours[daily_panchaanga.date.get_weekday()], dt, month_data,
                        names.get_chandra_masa(daily_panchaanga.lunar_month_sunrise,scripts[0])))
        W6D1 += '\n' + ('{\\sundata{%s}{%s}{%s}}%%' % (sunrise, sunset, saangava))
        W6D1 += '\n' + ('{\\tnyk{%s}%%\n{%s}%%\n{%s}%%\n{%s}}%%' % (tithi_data_str, nakshatra_data_str,
                                                                    yoga_data_str, karana_data_str))
        W6D1 += '\n' + ('{\\rahuyama{%s}{%s}}%%' % (rahu, yama))

        # Using set as an ugly workaround since we may have sometimes assigned the same
        # festival to the same day again!
        W6D1 += '\n' + ('{%s}' % '\\eventsep '.join(
          [f.tex_code(languages=languages, scripts=scripts, timezone=Timezone(panchaanga.city.timezone), fest_details_dict=fest_details_dict, reference_date=daily_panchaanga.date) for f in sorted(daily_panchaanga.festival_id_to_instance.values())]))
      elif daily_panchaanga.date.get_weekday() == 1:
        W6D2 = '\n' + ('\\caldata{\\textcolor{%s}{%s}}{%s{%s}}%%' %
                       (day_colours[daily_panchaanga.date.get_weekday()], dt, month_data,
                        names.get_chandra_masa(daily_panchaanga.lunar_month_sunrise,scripts[0])))
        W6D2 += '\n' + ('{\\sundata{%s}{%s}{%s}}%%' % (sunrise, sunset, saangava))
        W6D2 += '\n' + ('{\\tnyk{%s}%%\n{%s}%%\n{%s}%%\n{%s}}%%' % (tithi_data_str, nakshatra_data_str,
                                                                    yoga_data_str, karana_data_str))
        W6D2 += '\n' + ('{\\rahuyama{%s}{%s}}%%' % (rahu, yama))

        # Using set as an ugly workaround since we may have sometimes assigned the same
        # festival to the same day again!
        W6D2 += '\n' + ('{%s}' % '\\eventsep '.join(
          [f.tex_code(languages=languages, scripts=scripts, timezone=panchaanga.city.timezone, fest_details_dict=fest_details_dict, reference_date=daily_panchaanga.date) for f in sorted(daily_panchaanga.festival_id_to_instance.values())]))
      else:
        # Cannot be here, since we cannot have more than 2 days in week 6 of any month!
        pass

    if daily_panchaanga.date.get_weekday() == 6:
      month_text += '\n' + ("\\\\ \\hline %%END OF WEEK %d" % (currWeek))
      currWeek += 1
    else:
      if currWeek < 6:
        month_text += '\n' + ("&")

    if m == 12 and dt == 31:
      break

  month_text = month_text.replace('W6D1', W6D1)
  month_text = month_text.replace('W6D2', W6D2)
  print(month_text)

  if currWeek < 6:
    for i in range(daily_panchaanga.date.get_weekday() + 1, 6):
      print("{}  &")
    if daily_panchaanga.date.get_weekday() != 6:
      print("\\\\ \\hline")
  print('\\end{tabular}')
  print('\n\n')

  print(template_lines[-2][:-1])
  print(template_lines[-1][:-1])


def main():
  [city_name, latitude, longitude, tz] = sys.argv[1:5]
  year = int(sys.argv[5])

  scripts = [sanscript.DEVANAGARI]  # Default language is devanagari

  if len(sys.argv) == 7:
    scripts = sys.argv[6].split(",")

  # logging.debug(language)

  city = City(city_name, latitude, longitude, tz)
  panchaanga = annual.get_panchaanga_for_civil_year(city=city, year=year)

  panchaanga.update_festival_details()

  write_monthly_tex(panchaanga)
  # panchaanga.writeDebugLog()


if __name__ == '__main__':
  main()
