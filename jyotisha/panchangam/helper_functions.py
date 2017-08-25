#!/usr/bin/python3
#  -*- coding: utf-8 -*-

import re
import sys
from math import floor

import swisseph as swe

from indic_transliteration import sanscript
from scipy.optimize import brentq

from jyotisha.names.init_names_auto import init_names_auto

NAMES = init_names_auto()

MAX_DAYS = 366
MAX_SZ = MAX_DAYS + 3  # plus one and minus one are usually necessary

MIN_DAYS_NEXT_ECL = 25
# next new/full moon from current one is at least 27.3 days away

TITHI          = {'arc_len': 360.0 / 30.0,  'w_moon': 1, 'w_sun': -1}
TITHI_PADA     = {'arc_len': 360.0 / 120.0, 'w_moon': 1, 'w_sun': -1}
NAKSHATRAM     = {'arc_len': 360.0 / 27.0,  'w_moon': 1, 'w_sun':  0}
NAKSHATRA_PADA = {'arc_len': 360.0 / 108.0, 'w_moon': 1, 'w_sun':  0}
RASHI          = {'arc_len': 360.0 / 12.0,  'w_moon': 1, 'w_sun':  0}
YOGAM          = {'arc_len': 360.0 / 27.0,  'w_moon': 1, 'w_sun':  1}
KARANAM        = {'arc_len': 360.0 / 60.0,  'w_moon': 1, 'w_sun': -1}
SOLAR_MONTH    = {'arc_len': 360.0 / 12.0,  'w_moon': 0, 'w_sun':  1}
SOLAR_NAKSH    = {'arc_len': 360.0 / 27.0,  'w_moon': 0, 'w_sun':  1}


class city:

    """This class enables the construction of a city object
    """

    def __init__(self, name, latitude, longitude, timezone):
        """Constructor for city"""
        self.name = name
        self.latstr = latitude
        self.lonstr = longitude
        self.latitude = sexastr2deci(latitude)
        self.longitude = sexastr2deci(longitude)
        self.timezone = timezone


class time:

    """This  class is a time class with methods for printing, conversion etc.
    """

    def __init__(self, t):
        if type(t) == float or type(t) == int:
            self.t = t
        else:
            raise(TypeError('Input to time class must be int or float!'))

    def toString(self, default_suffix='', format='hh:mm'):
        secs = round(self.t * 3600)  # round to nearest second
        hour = secs // 3600
        secs = secs % 3600

        if hour >= 24:
            hour -= 24
            suffix = '(+1)'
        else:
            suffix = default_suffix

        minute = secs // 60
        secs = secs % 60
        second = secs

        if format == 'hh:mm':
            return '%02d:%02d%s' % (hour, minute, suffix)
        elif format == 'hh:mm:ss':
            return '%02d:%02d:%02d%s' % (hour, minute, second, suffix)
        else:
            """Thrown an exception, for unknown format"""

    def __str__(self):
        return self.toString(format='hh:mm:ss')


def romanise(iast_text):
    swapTable = {'ā': 'a', 'Ā': 'A', 'ī': 'i', 'ū': 'u', 'ṅ': 'n', 'ṇ': 'n',
                 'ḍ': 'd', 'ṭ': 't', 'ṃ': 'm', 'ñ': 'n', 'ṛ': 'ri', 'ś': 'sh',
                 'Ś': 'Sh', 'ṣ': 'sh', 'Ṣ': 'Sh', 'ḥ': '', '~': '-', ' ': '-'}

    roman_text = ''
    for char in iast_text:
        if char in swapTable:
            roman_text += swapTable[char]
        else:
            roman_text += char
    return roman_text.lower()


def dn2tam(dn_text):
    swapTable = {' ': ' ', '-': '-', '~': '~', '/': '/', 'ऀ': 'ऀ', 'ँ': 'ँ', 'ं': 'ஂ', 'ः': 'ஃ',
                 'अ': 'அ', 'आ': 'ஆ', 'इ': 'இ', 'ई': 'ஈ', 'उ': 'உ', 'ऊ': 'ஊ',
                 'ऋ': 'ற', 'ऌ': 'ऌ', 'ऍ': 'ऍ',
                 'ऎ': 'எ', 'ए': 'ஏ', 'ऐ': 'ஐ', 'ऑ': 'ऑ', 'ऒ': 'ஒ', 'ओ': 'ஓ', 'औ': 'ஔ',
                 'क': 'க', 'ख': 'க', 'ग': 'க', 'घ': 'க', 'ङ': 'ங',
                 'च': 'ச', 'छ': 'ச', 'ज': 'ஜ', 'झ': 'ச', 'ञ': 'ஞ',
                 'ट': 'ட', 'ठ': 'ட', 'ड': 'ட', 'ढ': 'ட', 'ण': 'ண',
                 'त': 'த', 'थ': 'த', 'द': 'த', 'ध': 'த', 'न': 'ந', 'ऩ': 'ன',
                 'प': 'ப', 'फ': 'ப', 'ब': 'ப', 'भ': 'ப', 'म': 'ம',
                 'य': 'ய', 'र': 'ர', 'ऱ': 'ற', 'ल': 'ல', 'ळ': 'ள', 'ऴ': 'ழ', 'व': 'வ',
                 'श': 'ஶ', 'ष': 'ஷ', 'स': 'ஸ', 'ह': 'ஹ',
                 'ऺ': 'ऺ', 'ऻ': 'ऻ', '़': '़', 'ऽ': 'ऽ',
                 'ा': 'ா', 'ि': 'ி', 'ी': 'ீ', 'ु': 'ு', 'ू': 'ூ', 'ृ': 'று', 'ॄ': '௄', 'ॅ': 'ॅ',
                 'ॆ': 'ெ', 'े': 'ே', 'ै': 'ை', 'ॉ': 'ॉ', 'ॊ': 'ொ', 'ो': 'ோ', 'ौ': 'ௌ',
                 '्': '்', 'ॎ': 'ॎ', 'ॏ': 'ॏ', 'ॐ': 'ௐ',
                 '॑': '॑', '॒': '॒', '॓': '॓', '॔': '॔', 'ॕ': 'ॕ', 'ॖ': 'ॖ', 'ॗ': 'ॗ',
                 'ॠ': 'ॠ', 'ॡ': 'ॡ', 'ॢ': '௢', 'ॣ': '௣',
                 '।': '।', '॥': '॥', '०': '௦',
                 '१': '௧', '२': '௨', '३': '௩', '४': '௪', '५': '௫',
                 '६': '௬', '७': '௭', '८': '௮', '९': '௯', '॰': '॰',
                 'ॱ': 'ॱ', '{': '{', '}': '}'}

    tam_text = ''
    for char in dn_text:
        if char in swapTable:
            tam_text += swapTable[char]
        else:
            tam_text += '!'  # Noting errors with !
            sys.stderr.write('Unknown character in input! %s\n' % char)
    return tam_text.strip('{}')  # .replace(' ன', ' ந').replace('-ன', 'ந')


def tr(text, scr, titled=True, fontize=False):
    if scr == 'hk':
        scr = sanscript.HK
    if text == '':
        return ''

    text = re.sub('.~samApanam', '-samApanam', text)
    text = re.sub('.~ArambhaH', '-ArambhaH', text)

    text_bits = text.split('|')
    transliterated_text = []

    if titled:
        for t in text_bits:
            t = t.rstrip('~0123456789 ')
            if t[:3] == 'ta:':
                # Force Tamil!
                t = t[3:]
                if fontize:
                    transliterated_text.append('\\tamil{%s}' % dn2tam(
                        str(sanscript.transliterate(_text=t, _from=sanscript.HK, _to=scr), 'utf8').title()))
                else:
                    transliterated_text.append(dn2tam(
                        str(sanscript.transliterate(_text=t, _from=sanscript.HK, _to=scr), 'utf8').title()))

            else:
                if t.find('RIGHTarrow') == -1:
                    transliterated_text.append(
                        str(sanscript.transliterate(_text=t, _from=sanscript.HK, _to=scr), 'utf8').title())
                else:
                    [txt, t1, arrow, t2] = t.split('\\')
                    transliterated_text.append(
                        '\\'.join([str(sanscript.transliterate(_text=txt, _from=sanscript.HK, _to=scr), 'utf8').title(),
                                   t1, arrow, t2]))
    else:
        for t in text_bits:
            t = t.rstrip('~0123456789 ')
            if t[:3] == 'ta:':
                # Force Tamil!
                t = t[3:]
                transliterated_text.append(dn2tam(
                    str(sanscript.transliterate(_text=t, _from=sanscript.HK, _to=scr), 'utf8').title()))
            else:
                if t.find('RIGHTarrow') == -1:
                    transliterated_text.append(str(sanscript.transliterate(_text=t, _from=sanscript.HK, _to=scr), 'utf8'))
                else:
                    [txt, t1, arrow, t2] = t.split('\\')
                    transliterated_text.append(
                        '\\'.join([str(sanscript.transliterate(txt, _from=sanscript.HK, _to=scr), 'utf8'),
                                   t1, arrow, t2]))

    return '|'.join(transliterated_text)


def sexastr2deci(sexa_str):
    """Converts as sexagesimal string to decimal

    Converts a given sexagesimal string to its decimal value

    Args:
      A string encoding of a sexagesimal value, with the various
      components separated by colons

    Returns:
      A decimal value corresponding to the sexagesimal string

    Examples:
      >>> sexastr2deci('15:30:00')
      15.5
      >>> sexastr2deci('-15:30:45')
      -15.5125
    """

    if sexa_str[0] == '-':
        sgn = -1.0
        dms = sexa_str[1:].split(':')  # dms = degree minute second
    else:
        sgn = 1.0
        dms = sexa_str.split(':')

    decival = 0
    for i in range(0, len(dms)):
        decival = decival + float(dms[i]) / (60.0 ** i)

    return decival * sgn


def revjul(jd, formatstr='%4d-%02d-%02d %02d:%02d:%02d', tz_off=0):
    """Returns a more human readable revjul compared to swe

    Converts a given jd (float) to a tuple [y,m,d,h,mm,ss]

    Args:
      A float corresponding to a Julian day

    Returns:
      A tuple detailing the year, month, day, hour, minute and second

    Examples:
      >>> revjul(2444961.7125, None)
      (1981, 12, 23, 5, 6, 0)
      >>> revjul(2444961.7125)
      '1981-12-23 05:06:00'
    """

    if jd is None:
        return None

    year, month, day, h_float = swe.revjul(jd + tz_off / 24.0)

    hour = floor(h_float)
    h_float = (h_float - hour) * 60

    minute = floor(h_float)
    h_float = (h_float - minute) * 60

    second = int(round(h_float))

    if second == 60:
        minute += 1
        second = 0
        if minute == 60:
            hour += 1
            minute = 0
            if hour == 24:
                year, month, day, _h = swe.revjul(jd + (tz_off + 1) / 24.0)

    if formatstr is None:
        return (year, month, day, hour, minute, second)
    else:
        return (formatstr % (year, month, day, hour, minute, second))


def print_lat_lon(latstr, lonstr):
    """Returns a formatted string for a latitude and longitude

    Returns a formatted string for latitude and longitude, given sexagesimal
    'strings' using colons for separation

    Args:
      str latstr
      str lonstr

    Returns:
      string corresponding to the formatted latitude and longitude

    Examples:
      >>> print_lat_lon('13:05:24','80:16:12') #Chennai
      "13°05'24''N, 80°16'12''E"
      >>> print_lat_lon('37:23:59','-122:08:34') #Palo Alto
      "37°23'59''N, 122°08'34''W"
      >>> print_lat_lon('1','-1')
      "1°0'0''N, 1°0'0''W"
    """

    if(latstr[0] == '-'):
        latstr = latstr[1:]
        lat_suffix = 'S'
    else:
        lat_suffix = 'N'

    lat_data = latstr.split(':')
    while len(lat_data) < 3:
        lat_data.append(0)
    formatted_string = '%s°%s\'%s\'\'%s' % (lat_data[0], lat_data[1], lat_data[2], lat_suffix)

    if lonstr[0] == '-':
        lonstr = lonstr[1:]
        lon_suffix = 'W'
    else:
        lon_suffix = 'E'

    lon_data = lonstr.split(':')
    while len(lon_data) < 3:
        lon_data.append(0)
    formatted_string = '%s, %s°%s\'%s\'\'%s' % (formatted_string, lon_data[0],
                                                lon_data[1], lon_data[2], lon_suffix)

    return formatted_string


def get_ekadashi_name(paksha, lmonth):
    """Return the name of an ekadashi
    """
    if paksha == 'shukla':
        if lmonth == int(lmonth):
            return '%s~EkAdazI' % NAMES['SHUKLA_EKADASHI']['hk'][lmonth]
        else:
            # adhika mAsam
            return '%s~EkAdazI' % NAMES['SHUKLA_EKADASHI']['hk'][13]
    elif paksha == 'krishna':
        if lmonth == int(lmonth):
            return '%s~EkAdazI' % NAMES['KRISHNA_EKADASHI']['hk'][lmonth]
        else:
            # adhika mAsam
            return '%s~EkAdazI' % NAMES['KRISHNA_EKADASHI']['hk'][13]


def get_chandra_masa(month, NAMES, script):
    if month == int(month):
        return NAMES['CHANDRA_MASA'][script][month]
    else:
        return '%s~(%s)' % (NAMES['CHANDRA_MASA'][script][int(month) + 1], tr('adhika', script))


def get_tithi(jd):
    """Returns the tithi prevailing at a given moment

    Tithi is computed as the difference in the longitudes of the moon
    and sun at any given point of time. Therefore, even the ayanamsha
    does not matter, as it gets cancelled out.

    Args:
      float jd, the Julian day

    Returns:
      int tithi, where 1 stands for ShuklapakshaPrathama, ..., 15 stands
      for Paurnamasi, ..., 23 stands for KrishnapakshaAshtami, 30 stands
      for Amavasya

    Examples:
      >>> get_tithi(2444961.7125)
      28
    """

    return get_angam(jd, TITHI)


def get_nakshatram(jd):
    """Returns the nakshatram prevailing at a given moment

    Nakshatram is computed based on the longitude of the Moon; in
    addition, to obtain the absolute value of the longitude, the
    ayanamsa is required to be subtracted.

    Args:
      float jd, the Julian day

    Returns:
      int nakShatram, where 1 stands for Ashwini, ..., 14 stands
      for Chitra, ..., 27 stands for Revati

    Examples:
      >>> get_nakshatram(2444961.7125)
      16
    """

    return get_angam(jd, NAKSHATRAM)


def get_solar_rashi(jd):
    """Returns the solar rashi prevailing at a given moment

    Solar month is computed based on the longitude of the sun; in
    addition, to obtain the absolute value of the longitude, the
    ayanamsa is required to be subtracted.

    Args:
      float jd, the Julian day

    Returns:
      int rashi, where 1 stands for mESa, ..., 12 stands for mIna

    Examples:
      >>> get_solar_rashi(2444961.7125)
      9
    """

    return get_angam(jd, SOLAR_MONTH)


def get_angam_float(jd, angam_type, offset=0, debug=False):
    """Returns the angam

      Args:
        float jd: The Julian Day at which the angam is to be computed
        angam_type: One of the pre-defined constants in the panchangam
        class, such as TITHI, NAKSHATRAM, YOGAM, KARANAM or SOLAR_MONTH

      Returns:
        float angam

      Examples:
        >>> get_angam_float(2444961.7125,NAKSHATRAM)
        15.967801358055189
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)  # Force Lahiri Ayanamsha
    w_moon = angam_type['w_moon']
    w_sun = angam_type['w_sun']
    arc_len = angam_type['arc_len']

    lcalc = 0  # computing weighted longitudes
    if debug:
        print('## get_angam_float(): jd=', jd)

    if w_moon != 0:
        lmoon = (swe.calc_ut(jd, swe.MOON)[0] - swe.get_ayanamsa(jd)) % 360
        if(debug):
            print('## get_angam_float(): lmoon=', lmoon)
        lcalc += w_moon * lmoon

    if w_sun != 0:
        lsun = (swe.calc_ut(jd, swe.SUN)[0] - swe.get_ayanamsa(jd)) % 360
        if(debug):
            print('## get_angam_float(): lsun=', lsun)
        lcalc += w_sun * lsun

    if debug:
        print('## get_angam_float(): lcalc=', lcalc)

    lcalc = lcalc % 360

    if debug:
        print('## get_angam_float(): lcalc%360=', lcalc)
        print("offset: ", offset)
        print(offset + int(360.0 / arc_len))
    if offset + int(360.0 / arc_len) == 0 and lcalc + offset >= 0:
        return (lcalc / arc_len)
    else:
        return (lcalc / arc_len) + offset


def get_nirayana_sun_lon(jd, offset=0, debug=False):
    """Returns the nirayana longitude of the sun

      Args:
        float jd: The Julian Day at which the angam is to be computed

      Returns:
        float longitude

      Examples:
    """
    lsun = (swe.calc_ut(jd, swe.SUN)[0]) % 360

    if debug:
        print('## get_angam_float(): lsun (nirayana) =', lsun)

    return lsun + offset


def get_angam(jd, angam_type):
    """Returns the angam prevailing at a particular time

      Args:
        float jd: The Julian Day at which the angam is to be computed
        float arc_len: The arc_len for the corresponding angam
        w_moon: The multiplier for moon's longitude
        w_sun: The multiplier for sun's longitude

      Returns:
        int angam

      Examples:
      >>> get_angam(2444961.7125,NAKSHATRAM)
      16

      >>> get_angam(2444961.7125,TITHI)
      28

      >>> get_angam(2444961.7125,YOGAM)
      8

      >>> get_angam(2444961.7125,KARANAM)
      55
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)  # Force Lahiri Ayanamsha

    return int(1 + floor(get_angam_float(jd, angam_type)))


def get_angam_span(jd1, jd2, angam_type, target, debug=False):
    """Computes angam spans for angams such as tithi, nakshatram, yogam
        and karanam.

        Args:
          jd1: return all spans that start after this date
          jd2: return all spans that end before this date
          angam_type: TITHI, NAKSHATRAM, YOGAM, KARANAM, SOLAR_MONTH, SOLAR_NAKSH

        Returns:
          list: A list comprising tuples of start and end times that lie within
            jd1 and jd2
    """

    angam_start = angam_end = None

    num_angas = int(360.0 / angam_type['arc_len'])

    jd_bracket_L = jd1
    jd_bracket_R = jd2

    h = 0.5   # Min Step for moving

    jd_now = jd1
    while jd_now < jd2 and angam_start is None:
        angam_now = get_angam(jd_now, angam_type)

        if debug:
            print('%%', jd_now, revjul(jd_now), angam_now, get_angam_float(jd_now, angam_type))
        if angam_now < target:
            if debug:
                print('%% jd_bracket_L ', jd_now)
            jd_bracket_L = jd_now
        if angam_now == target:
            angam_start = brentq(get_angam_float, jd_bracket_L, jd_now,
                                 args=(angam_type, -target + 1, False))
            if debug:
                print('%% angam_start', angam_start)
        # if angam_now > target and angam_start is not None:
        #     angam_end = brentq(get_angam_float, angam_start, jd_now,
        #                        args=(angam_type, -target, False))
        jd_now += h

    if angam_start is None:
        return (None, None)  # If it doesn't start, we don't care if it ends!
    jd_now = angam_start

    while jd_now < jd2 and angam_end is None:
        angam_now = get_angam(jd_now, angam_type)

        if debug:
            print('%%#', jd_now, revjul(jd_now), angam_now, get_angam_float(jd_now, angam_type))
        if target == num_angas:
            # Wait till we land at the next anga!
            if angam_now == 1:
                jd_bracket_R = jd_now
                if debug:
                    print('%%# jd_bracket_R ', jd_now)
                break
        else:
            if angam_now > target:
                jd_bracket_R = jd_now
                if debug:
                    print('%%! jd_bracket_R ', jd_now)
                break
        jd_now += h

    try:
        angam_end = brentq(get_angam_float, angam_start, jd_bracket_R,
                           args=(angam_type, -target, False))
    except:
        sys.stderr.write('Unable to compute angam_end (%s->%d); possibly could not bracket correctly!\n' % (str(angam_type), target))

    if debug:
        print('%% angam_end', angam_end)

    return (angam_start, angam_end)


def get_angam_data(jd_sunrise, jd_sunrise_tmrw, angam_type):
    """Computes angam data for angams such as tithi, nakshatram, yogam
    and karanam.

    Args:
      angam_type: TITHI, NAKSHATRAM, YOGAM, KARANAM, SOLAR_MONTH, SOLAR_NAKSH


    Returns:
      tuple: A tuple comprising
        angam_sunrise: The angam that prevails as sunrise
        angam_data: a list of (int, float) tuples detailing the angams
        for the day and their end-times (Julian day)

    Examples:
      >>> get_angam_data(2444961.54042,2444962.54076,TITHI)
      [(27, 2444961.599213231)]
      >>> get_angam_data(2444961.54042,2444962.54076,NAKSHATRAM)
      [(16, 2444961.7487953394)]
      >>> get_angam_data(2444961.54042,2444962.54076,YOGAM)
      [(8, 2444962.1861976916)]
      >>> get_angam_data(2444961.54042,2444962.54076,KARANAM)
      [(54, 2444961.599213231), (55, 2444962.15444546)]
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)  # Force Lahiri Ayanamsha

    w_moon = angam_type['w_moon']
    w_sun = angam_type['w_sun']
    arc_len = angam_type['arc_len']

    num_angas = int(360.0 / arc_len)

    # Compute angam details
    angam_now = get_angam(jd_sunrise, angam_type)
    angam_tmrw = get_angam(jd_sunrise_tmrw, angam_type)

    angams_list = []

    num_angas_today = (angam_tmrw - angam_now) % num_angas

    if num_angas_today == 0:
        # The angam does not change until sunrise tomorrow
        return [(angam_now, None)]
    else:
        lmoon = (swe.calc_ut(jd_sunrise, swe.MOON)[0] - swe.get_ayanamsa(jd_sunrise)) % 360

        lsun = (swe.calc_ut(jd_sunrise, swe.SUN)[0] - swe.get_ayanamsa(jd_sunrise)) % 360

        lmoon_tmrw = (swe.calc_ut(jd_sunrise_tmrw, swe.MOON)[0] -
                      swe.get_ayanamsa(jd_sunrise_tmrw)) % 360

        lsun_tmrw = (swe.calc_ut(jd_sunrise_tmrw, swe.SUN)[0] -
                     swe.get_ayanamsa(jd_sunrise_tmrw)) % 360

        for i in range(num_angas_today):
            angam_remaining = arc_len * (i + 1) - (((lmoon * w_moon +
                                                     lsun * w_sun) % 360) % arc_len)

            # First compute approximate end time by essentially assuming
            # the speed of the moon and the sun to be constant
            # throughout the day. Therefore, angam_remaining is computed
            # just based on the difference in longitudes for sun and
            # moon today and tomorrow.
            approx_end = jd_sunrise + angam_remaining / (((lmoon_tmrw - lmoon) % 360) * w_moon +
                                                         ((lsun_tmrw - lsun) % 360) * w_sun)

            # Initial guess value for the exact end time of the angam
            x0 = approx_end

            # What is the target (next) angam? It is needed to be passed
            # to get_angam_float for zero-finding. If the target angam
            # is say, 12, then we need to subtract 12 from the value
            # returned by get_angam_float, so that this function can be
            # passed as is to a zero-finding method like brentq or
            # newton. Since we have a good x0 guess, it is easy to
            # bracket the function in an interval where the function
            # changes sign. Therefore, brenth can be used, as suggested
            # in the scipy documentation.
            target = (angam_now + i - 1) % num_angas + 1

            # Approximate error in calculation of end time -- arbitrary
            # used to bracket the root, for brenth
            TDELTA = 0.05
            t_act = brentq(get_angam_float, x0 - TDELTA, x0 + TDELTA,
                           args=(angam_type, -target, False))
            angams_list.extend([((angam_now + i - 1) % num_angas + 1, t_act)])
    return angams_list


def get_lagna_float(jd, lat, lon, offset=0, debug=False):
    """Returns the angam

      Args:
        float jd: The Julian Day at which the lagnam is to be computed
        lat: Latitude of the place where the lagnam is to be computed
        lon: Longitude of the place where the lagnam is to be computed
        offset: Used by internal functions for bracketing

      Returns:
        float lagna

      Examples:
        >>> get_lagna_float(2444961.7125,13.08784, 80.27847)
        10.353595502472984
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)  # Force Lahiri Ayanamsha
    lcalc = swe.houses_ex(jd, lat, lon)[1][0] - swe.get_ayanamsa_ut(jd)
    lcalc = lcalc % 360

    if offset == 0:
        return lcalc / 30

    else:
        if (debug):
            print('offset:', offset)
            print('lcalc/30', lcalc / 30)
            print('lcalc/30 + offset = ', lcalc / 30 + offset)

        # The max expected value is somewhere between 2 and -2, with bracketing

        if (lcalc / 30 + offset) >= 3:
            return (lcalc / 30) + offset - 12
        elif (lcalc / 30 + offset) <= -3:
            return (lcalc / 30)
        else:
            return (lcalc / 30) + offset


def get_lagna_data(jd_sunrise, lat, lon, tz_off, debug=False):
    """Returns the lagna data

      Args:
        float jd: The Julian Day at which the lagnam is to be computed
        lat: Latitude of the place where the lagnam is to be computed
        lon: Longitude of the place where the lagnam is to be computed
        offset: Used by internal functions for bracketing

      Returns:
        tuples detailing the end time of each lagna, beginning with the one
        prevailing at sunrise

      Examples:
        >>> get_lagna_data(2458222.5208333335, lat=13.08784, lon=80.27847, tz_off=5.5)
        [(12, 2458222.5214310056), (1, 2458222.596420153), (2, 2458222.6812926503), (3, 2458222.772619788), (4, 2458222.8624254186), (5, 2458222.9478168003), (6, 2458223.0322211445), (7, 2458223.1202004547), (8, 2458223.211770839), (9, 2458223.3000455885), (10, 2458223.3787625884), (11, 2458223.4494649624)]
    """
    lagna_sunrise = 1 + floor(get_lagna_float(jd_sunrise, lat, lon))

    lagna_list = [(x + lagna_sunrise - 1) % 12 + 1 for x in range(12)]

    lbrack = jd_sunrise - 3 / 24
    rbrack = jd_sunrise + 3 / 24
    lagna_data = []

    for lagna in lagna_list:
        # print('---\n', lagna)
        if (debug):
            print('lagna sunrise', get_lagna_float(jd_sunrise))
            print('lbrack', get_lagna_float(lbrack, lat, lon, -lagna))
            print('rbrack', get_lagna_float(rbrack, lat, lon, -lagna))

        lagna_end_time = brentq(get_lagna_float, lbrack, rbrack,
                                args=(lat, lon, -lagna, debug))
        lbrack = lagna_end_time + 1 / 24
        rbrack = lagna_end_time + 3 / 24
        lagna_data.append((lagna, lagna_end_time))
    return lagna_data


def get_solar_month_day(jd_start, city):
    """Compute the solar month and day for a given Julian day

    Computes the solar month and day on the day corresponding to a given
    Julian day

    Args:
      float jd
      city

    Returns:
      int solar_month
      int solar_month_day

    Examples:
      >>> get_solar_month_day(2457023.27, city('Chennai', '13:05:24', \
'80:16:12', 'Asia/Calcutta'))
      (9, 17)
    """

    jd_sunset = swe.rise_trans(jd_start=jd_start, body=swe.SUN, lon=city.longitude,
                               lat=city.latitude, rsmi=swe.CALC_SET | swe.BIT_DISC_CENTER)[1][0]

    solar_month = get_angam(jd_sunset, SOLAR_MONTH)
    target = floor(solar_month) - 1

    jd_masa_transit = brentq(get_angam_float, jd_start - 34, jd_start + 1,
                             args=(SOLAR_MONTH, -target, False))

    jd_next_sunset = swe.rise_trans(jd_start=jd_masa_transit, body=swe.SUN,
                                    lon=city.longitude, lat=city.latitude,
                                    rsmi=swe.CALC_SET | swe.BIT_DISC_CENTER)[1][0]

    jd_next_sunrise = swe.rise_trans(jd_start=jd_masa_transit, body=swe.SUN,
                                     lon=city.longitude, lat=city.latitude,
                                     rsmi=swe.CALC_RISE | swe.BIT_DISC_CENTER)[1][0]

    if jd_next_sunset > jd_next_sunrise:
        # Masa begins after sunset and before sunrise
        # Therefore Masa 1 is on the day when the sun rises next
        solar_month_day = floor(jd_sunset - jd_next_sunrise) + 1
    else:
        # Masa has started before sunset
        solar_month_day = round(jd_sunset - jd_next_sunset) + 1

    return (solar_month, solar_month_day)


def get_kalas(start_span, end_span, part_start, num_parts):
    """Compute kalas in a given span with specified fractions

    Args:
      float (jd) start_span
      float (jd) end_span
      int part_start
      int num_parts

    Returns:
       tuple (start_time_jd, end_time_jd)

    Examples:

    """
    start_fraction = part_start / num_parts
    end_fraction = (part_start + 1) / num_parts

    start_time = start_span + (end_span - start_span) * start_fraction
    end_time = start_span + (end_span - start_span) * end_fraction

    return (start_time, end_time)
