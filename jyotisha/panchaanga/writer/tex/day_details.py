import logging
import jyotisha
from jyotisha import custom_transliteration
from jyotisha.panchaanga.temporal import time, names
from jyotisha.panchaanga.temporal.body import Graha

def _get_relative_nadikas(jd, daily_panchaanga):
  nadika_time = 0
  if daily_panchaanga.jd_previous_sunset < jd < daily_panchaanga.jd_sunrise:
    jd -= daily_panchaanga.jd_previous_sunset
    nadika_time += 30
    one_ghatika = (daily_panchaanga.jd_sunrise - daily_panchaanga.jd_previous_sunset) / 30
    nadika_time += jd / one_ghatika
  elif daily_panchaanga.jd_sunrise < jd < daily_panchaanga.jd_sunset:
    jd -= daily_panchaanga.jd_sunrise
    one_ghatika = (daily_panchaanga.jd_sunset - daily_panchaanga.jd_sunrise) / 30
    nadika_time += jd / one_ghatika
  elif daily_panchaanga.jd_sunset < jd < daily_panchaanga.jd_next_sunrise:
    jd -= daily_panchaanga.jd_sunset
    nadika_time +=30
    one_ghatika = (daily_panchaanga.jd_next_sunrise - daily_panchaanga.jd_sunset) / 30
    nadika_time += jd / one_ghatika
  elif daily_panchaanga.jd_next_sunrise < jd:
    nadika_time +=60
    jd -= daily_panchaanga.jd_next_sunrise
    # approximating
    logging.warning('Approximating ghatika as end time is > next sunrise!')
    one_ghatika = (daily_panchaanga.jd_sunset - daily_panchaanga.jd_sunrise) / 30
    nadika_time += jd / one_ghatika
  else:
    logging.warning('Unexpected situation with ghatika conversion (jd = %f, jd_sunrise = %f, jd_next_sunrise = %f!' % (jd, daily_panchaanga.jd_sunrise, daily_panchaanga.jd_next_sunrise))
  gg = int(nadika_time)
  pp = int((nadika_time - gg)*60)
  return '%d-%d' % (gg, pp)

def get_lagna_data_str(daily_panchaanga, scripts, time_format):
  jd = daily_panchaanga.julian_day_start
  lagna_data_str = jyotisha.custom_transliteration.tr('lagnAni—', scripts[0])
  for lagna_ID, lagna_end_jd in daily_panchaanga.lagna_data:
    lagna = names.NAMES['RASHI_NAMES']['sa'][scripts[0]][lagna_ID]
    lagna_data_str = '%s\\lagna{%s}{%s} ' % \
                     (lagna_data_str, lagna,
                      time.Hour(24 * (lagna_end_jd - jd)).to_string(
                        format=time_format))
  return lagna_data_str


def get_hora_data_str(daily_panchaanga, scripts, time_format):
  jd = daily_panchaanga.julian_day_start
  GRAHA_NAMES = {Graha.SUN: 'sUryaH', Graha.MOON: 'candraH', Graha.MARS: 'maGgalaH', Graha.MERCURY: 'budhaH', Graha.JUPITER: 'guruH', Graha.VENUS: 'zukraH', Graha.SATURN: 'zaniH', Graha.RAHU: 'rAhuH'}
  hora_data_str = jyotisha.custom_transliteration.tr('hOrAH—', scripts[0])

  for hora_ID, hora_graha_name, hora_end_jd in daily_panchaanga.hora_data:
    hora = jyotisha.custom_transliteration.tr(GRAHA_NAMES[hora_graha_name], scripts[0])
    hora_data_str = '%s\\hora{%s}{%s} ' % \
                     (hora_data_str, hora,
                      time.Hour(24 * (hora_end_jd - jd)).to_string(
                        format=time_format))
  return hora_data_str

def get_solar_shraaddha_tithi_data_str(daily_panchaanga, scripts, time_format):
    if not daily_panchaanga.solar_shraaddha_tithi:
        return '---'

    if daily_panchaanga.solar_shraaddha_tithi[0] == 0:
        return jyotisha.custom_transliteration.tr('zUnyatithiH', scripts[0])

    showMonth = any(m != daily_panchaanga.solar_sidereal_date_sunset.month for m, t in daily_panchaanga.solar_shraaddha_tithi)
    tithi_strings = []

    for month, tithi in daily_panchaanga.solar_shraaddha_tithi:
        tithi_name = names.NAMES['TITHI_NAMES']['sa'][scripts[0]][tithi].split('-')[-1]
        if showMonth:
            rashi_name = names.NAMES['RASHI_NAMES']['sa'][scripts[0]][month]
            tithi_strings.append(f"{tithi_name} ({rashi_name})")
        else:
            tithi_strings.append(tithi_name)

    tithi_count = len(daily_panchaanga.solar_shraaddha_tithi)
    if tithi_count == 1:
        return tithi_strings[0]
    elif tithi_count == 2:
        return f"{tithi_strings[0]}/{tithi_strings[1]} ({jyotisha.custom_transliteration.tr('tithidvayam', scripts[0])})"
    elif tithi_count == 3:
        return f"{tithi_strings[0]}/{tithi_strings[1]}/{tithi_strings[2]} ({jyotisha.custom_transliteration.tr('tithitrayam', scripts[0])})"

    return '/'.join(tithi_strings)


def get_lunar_shraaddha_tithi_data_str(daily_panchaanga, scripts, time_format):
    if not daily_panchaanga.lunar_shraaddha_tithi:
        return '---'

    tithi_strings = []

    for tithi in daily_panchaanga.lunar_shraaddha_tithi:
      tithi_name = names.NAMES['TITHI_NAMES']['sa'][scripts[0]][tithi].split('-')[-1]
      tithi_strings.append(tithi_name)

    tithi_count = len(daily_panchaanga.lunar_shraaddha_tithi)
    if tithi_count == 1:
        return tithi_strings[0]
    elif tithi_count == 2:
        return f"{tithi_strings[0]}/{tithi_strings[1]} ({jyotisha.custom_transliteration.tr('tithidvayam', scripts[0])})"
    elif tithi_count == 3:
        return f"{tithi_strings[0]}/{tithi_strings[1]}/{tithi_strings[2]} ({jyotisha.custom_transliteration.tr('tithitrayam', scripts[0])})"

    return '/'.join(tithi_strings)


def get_raahu_yama_gulika_strings(daily_panchaanga, time_format):
  jd = daily_panchaanga.julian_day_start
  rahu = '%s--%s' % (
    time.Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.raahu.jd_start - jd)).to_string(
      format=time_format),
    time.Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.raahu.jd_end - jd)).to_string(
      format=time_format))
  yama = '%s--%s' % (
    time.Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.yama.jd_start - jd)).to_string(
      format=time_format),
    time.Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.yama.jd_end - jd)).to_string(
      format=time_format))
  raatri_yama = '%s--%s' % (
    time.Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.raatri_yama.jd_start - jd)).to_string(
      format=time_format),
    time.Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.raatri_yama.jd_end - jd)).to_string(
      format=time_format))
  gulika = '%s--%s' % (
    time.Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.gulika.jd_start - jd)).to_string(
      format=time_format),
    time.Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.gulika.jd_end - jd)).to_string(
      format=time_format))
  raatri_gulika = '%s--%s' % (
    time.Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.raatri_gulika.jd_start - jd)).to_string(
      format=time_format),
    time.Hour(24 * (daily_panchaanga.day_length_based_periods.eight_fold_division.raatri_gulika.jd_end - jd)).to_string(
      format=time_format))
  durmuhurta1 = '%s--%s' % (
    time.Hour(24 * (daily_panchaanga.day_length_based_periods.fifteen_fold_division.durmuhurta1.jd_start - jd)).to_string(
      format=time_format),
    time.Hour(24 * (daily_panchaanga.day_length_based_periods.fifteen_fold_division.durmuhurta1.jd_end - jd)).to_string(
      format=time_format))
  if daily_panchaanga.day_length_based_periods.fifteen_fold_division.durmuhurta2 is None:
    durmuhurta2 = None
  else:
    durmuhurta2 = '%s--%s' % (
      time.Hour(24 * (daily_panchaanga.day_length_based_periods.fifteen_fold_division.durmuhurta2.jd_start - jd)).to_string(
        format=time_format),
      time.Hour(24 * (daily_panchaanga.day_length_based_periods.fifteen_fold_division.durmuhurta2.jd_end - jd)).to_string(
        format=time_format))
  return gulika, rahu, yama, raatri_gulika, raatri_yama, durmuhurta1, durmuhurta2


def get_karaNa_data_str(daily_panchaanga, scripts, time_format, previous_day_panchaanga=None, include_early_end_angas=False, relative_nadikas=True):
  jd = daily_panchaanga.julian_day_start
  karana_data_str = ''
  for numKaranam, karana_span in enumerate(daily_panchaanga.sunrise_day_angas.karanas_with_ends):
    (karana_ID, karana_end_jd) = (karana_span.anga.index, karana_span.jd_end)
    # if numKaranam == 1:
    #     karana_data_str += '\\hspace{1ex}'
    karana = names.NAMES['KARANA_NAMES']['sa'][scripts[0]][karana_ID]
    if karana_end_jd is None:
      karana_data_str = '%s\\uanga{%s}' % \
                        (karana_data_str, karana)
    else:
      if relative_nadikas:
        time_string = _get_relative_nadikas(karana_end_jd, daily_panchaanga)
      else:
        time_string = time.Hour(24 * (karana_end_jd - daily_panchaanga.jd_sunrise)).to_string(format='gg-pp')
      karana_data_str = '%s\\anga{%s}{\\time{%s}{%s}}\\hspace{1ex}' % \
                        (karana_data_str, karana,
                         time_string,
                         time.Hour(24 * (karana_end_jd - jd)).to_string(format=time_format))

  if include_early_end_angas:
    if previous_day_panchaanga is None:
      logging.error('Unable to include early end angas, as previous_day_panchaanga is not supplied!')
    if len(previous_day_panchaanga.sunrise_day_angas.karanas_with_ends) > 1:
      karana_span = previous_day_panchaanga.sunrise_day_angas.karanas_with_ends[-2]
      (karana_ID, karana_end_jd) = (karana_span.anga.index, karana_span.jd_end)
      karana = names.NAMES['KARANA_NAMES']['sa'][scripts[0]][karana_ID]
      if karana_span.jd_end is not None and  karana_span.jd_end > previous_day_panchaanga.day_length_based_periods.fifteen_fold_division.saura.jd_start:
        if relative_nadikas:
          time_string = _get_relative_nadikas(karana_end_jd, daily_panchaanga)
        else:
          time_string = time.Hour(24 * (karana_end_jd - previous_day_panchaanga.jd_sunrise)).to_string(format='gg-pp')
        karana_data_str = '\\prev{\\anga{%s}{\\time{*%s}{%s}}}\\hspace{1ex}' % \
                        (karana,
                         time_string,
                         time.Hour(24 * (karana_end_jd - jd)).to_string(format=time_format)) + karana_data_str

  return karana_data_str


def get_yoga_data_str(daily_panchaanga, scripts, time_format, previous_day_panchaanga=None, include_early_end_angas=False, relative_nadikas=True):
  jd = daily_panchaanga.julian_day_start
  yoga_data_str = ''
  for iYoga, yoga_span in enumerate(daily_panchaanga.sunrise_day_angas.yogas_with_ends):
    (yoga_ID, yoga_end_jd) = (yoga_span.anga.index, yoga_span.jd_end)
    # if yoga_data_str != '':
    #     yoga_data_str += '\\hspace{1ex}'
    yoga = names.NAMES['YOGA_NAMES']['sa'][scripts[0]][yoga_ID]
    if yoga_end_jd is None:
      if iYoga == 0:
        yoga_data_str = '%s\\fullanga{%s}' % (yoga_data_str, yoga)
      else:
        yoga_data_str = '%s\\uanga{%s}' % (yoga_data_str, yoga)
    else:
      if relative_nadikas:
        time_string = _get_relative_nadikas(yoga_end_jd, daily_panchaanga)
      else:
        time_string = time.Hour(24 * (yoga_end_jd - daily_panchaanga.jd_sunrise)).to_string(format='gg-pp')
      yoga_data_str = '%s\\anga{%s}{\\time{%s}{%s}}\\hspace{1ex}' % \
                      (yoga_data_str, yoga,
                       time_string,
                       time.Hour(24 * (yoga_end_jd - jd)).to_string(format=time_format))
  if yoga_end_jd is not None:
    yoga_data_str += '\\uanga{%s}' % (
      names.NAMES['YOGA_NAMES']['sa'][scripts[0]][(yoga_ID % 27) + 1])

  if include_early_end_angas:
    if previous_day_panchaanga is None:
      logging.error('Unable to include early end angas, as previous_day_panchaanga is not supplied!')
    if len(previous_day_panchaanga.sunrise_day_angas.yogas_with_ends) > 1:
      yoga_span = previous_day_panchaanga.sunrise_day_angas.yogas_with_ends[-2]
      (yoga_ID, yoga_end_jd) = (yoga_span.anga.index, yoga_span.jd_end)
      yoga = names.NAMES['YOGA_NAMES']['sa'][scripts[0]][yoga_ID]
      if yoga_span.jd_end is not None and  yoga_span.jd_end > previous_day_panchaanga.day_length_based_periods.fifteen_fold_division.saura.jd_start:
        if relative_nadikas:
          time_string = _get_relative_nadikas(yoga_end_jd, daily_panchaanga)
        else:
          time_string = time.Hour(24 * (yoga_end_jd - previous_day_panchaanga.jd_sunrise)).to_string(format='gg-pp')
        yoga_data_str = '\\prev{\\anga{%s}{\\time{*%s}{%s}}}\\hspace{1ex}' % \
                        (yoga,
                         time_string,
                         time.Hour(24 * (yoga_end_jd - jd)).to_string(format=time_format)) + yoga_data_str

  return yoga_data_str


def get_raashi_data_str(daily_panchaanga, scripts, time_format):
  jd = daily_panchaanga.julian_day_start
  raashi_data_str = custom_transliteration.tr('candrarAziH—', scripts[0])
  for iRaashi, raashi_span in enumerate(daily_panchaanga.sunrise_day_angas.raashis_with_ends):
    if iRaashi == 0:
      (raashi_ID, raashi_end_jd) = (raashi_span.anga.index, raashi_span.jd_end)
      # if raashi_data_str != '':
      #     raashi_data_str += '\\hspace{1ex}'
      raashi = names.NAMES['RASHI_NAMES']['sa'][scripts[0]][raashi_ID]
      if raashi_end_jd is None:
        raashi_data_str = '%s\\mbox{%s}' % (raashi_data_str, raashi)
      else:
        raashi_data_str = '%s\\mbox{%s\\RIGHTarrow{%s}}' % \
                         (raashi_data_str, raashi,
                          time.Hour(24 * (raashi_end_jd - jd)).to_string(
                            format=time_format))
 
  return raashi_data_str


def get_nakshatra_data_str(daily_panchaanga, scripts, time_format, previous_day_panchaanga=None, include_early_end_angas=False, relative_nadikas=True):
  jd = daily_panchaanga.julian_day_start
  nakshatra_data_str = ''
  for iNakshatra, nakshatra_span in enumerate(daily_panchaanga.sunrise_day_angas.nakshatras_with_ends):
    (nakshatra_ID, nakshatra_end_jd) = (nakshatra_span.anga.index, nakshatra_span.jd_end)
    if nakshatra_data_str != '':
      nakshatra_data_str += '\\hspace{1ex}'
    nakshatra = names.NAMES['NAKSHATRA_NAMES']['sa'][scripts[0]][nakshatra_ID]
    if nakshatra_end_jd is None:
      if iNakshatra == 0:
        nakshatra_data_str = '%s\\fullanga{%s}' % (nakshatra_data_str, nakshatra)
    else:
      if relative_nadikas:
        time_string = _get_relative_nadikas(nakshatra_end_jd, daily_panchaanga)
      else:
        time_string = time.Hour(24 * (nakshatra_end_jd - daily_panchaanga.jd_sunrise)).to_string(format='gg-pp')
      nakshatra_data_str = '%s\\anga{%s}{\\time{%s}{%s}}' % \
                           (nakshatra_data_str, nakshatra,
                            time_string,                            
                            time.Hour(24 * (nakshatra_end_jd - jd)).to_string(format=time_format))
    if iNakshatra == 2:
      nakshatra_data_str += '\\avamA{}'

  if include_early_end_angas:
    if previous_day_panchaanga is None:
      logging.error('Unable to include early end angas, as previous_day_panchaanga is not supplied!')
    if len(previous_day_panchaanga.sunrise_day_angas.nakshatras_with_ends) > 1:
      nakshatra_span = previous_day_panchaanga.sunrise_day_angas.nakshatras_with_ends[-2]
      (nakshatra_ID, nakshatra_end_jd) = (nakshatra_span.anga.index, nakshatra_span.jd_end)
      nakshatra = names.NAMES['NAKSHATRA_NAMES']['sa'][scripts[0]][nakshatra_ID]
      if nakshatra_span.jd_end is not None and  nakshatra_span.jd_end > previous_day_panchaanga.day_length_based_periods.fifteen_fold_division.saura.jd_start:
        if relative_nadikas:
          time_string = _get_relative_nadikas(nakshatra_end_jd, daily_panchaanga)
        else:
          time_string = time.Hour(24 * (nakshatra_end_jd - previous_day_panchaanga.jd_sunrise)).to_string(format='gg-pp')

        nakshatra_data_str = '\\prev{\\anga{%s}{\\time{*%s}{%s}}}\\hspace{1ex}' % \
                        (nakshatra,
                         time_string,
                         time.Hour(24 * (nakshatra_end_jd - jd)).to_string(format=time_format)) + nakshatra_data_str

  return nakshatra_data_str


def get_tithi_data_str(daily_panchaanga, scripts, time_format, previous_day_panchaanga=None, include_early_end_angas=False, relative_nadikas=True):
  # What is the jd at 00:00 local time today?
  jd = daily_panchaanga.julian_day_start
  tithi_data_str = ''
  for iTithi, tithi_span in enumerate(daily_panchaanga.sunrise_day_angas.tithis_with_ends):
    (tithi_ID, tithi_end_jd) = (tithi_span.anga.index, tithi_span.jd_end)
    tithi = '\\tithi{%d}{%s}' % (tithi_ID,
            names.NAMES['TITHI_NAMES']['sa'][scripts[0]][tithi_ID])
    if tithi_end_jd is None:
      if iTithi == 0:
        tithi_data_str = '%s\\fulltithi{%s}' % (tithi_data_str, tithi)
    else:
      if relative_nadikas:
        time_string = _get_relative_nadikas(tithi_end_jd, daily_panchaanga)
      else:
        time_string = time.Hour(24 * (tithi_end_jd - daily_panchaanga.jd_sunrise)).to_string(format='gg-pp')
      tithi_data_str = '%s\\anga{%s}{\\time{%s}{%s}}\\hspace{1ex}' % \
                       (tithi_data_str, tithi,
                        time_string,
                        time.Hour(24 * (tithi_end_jd - jd)).to_string(format=time_format))
    if iTithi == 2:
      tithi_data_str += '\\avamA{}'

  if include_early_end_angas:
    if previous_day_panchaanga is None:
      logging.error('Unable to include early end angas, as previous_day_panchaanga is not supplied!')
    if len(previous_day_panchaanga.sunrise_day_angas.tithis_with_ends) > 1:
      tithi_span = previous_day_panchaanga.sunrise_day_angas.tithis_with_ends[-2]
      (tithi_ID, tithi_end_jd) = (tithi_span.anga.index, tithi_span.jd_end)
      tithi = '\\tithi{%d}{%s}' % (tithi_ID, names.NAMES['TITHI_NAMES']['sa'][scripts[0]][tithi_ID])
      if tithi_span.jd_end is not None and  tithi_span.jd_end > previous_day_panchaanga.day_length_based_periods.fifteen_fold_division.saura.jd_start:
        if relative_nadikas:
          time_string = _get_relative_nadikas(tithi_end_jd, daily_panchaanga)
        else:
          time_string = time.Hour(24 * (tithi_end_jd - previous_day_panchaanga.jd_sunrise)).to_string(format='gg-pp')
        tithi_data_str = '\\prev{\\anga{%s}{\\time{*%s}{%s}}}\\hspace{1ex}' % \
                        (tithi,
                         time_string,
                         time.Hour(24 * (tithi_end_jd - jd)).to_string(format=time_format)) + tithi_data_str


  return tithi_data_str