#!/usr/bin/python3
#  -*- coding: utf-8 -*-

import re
import swisseph as swe
from math import floor

from indic_transliteration import xsanscript as sanscript
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def romanise(iast_text):
    swapTable = {'ā': 'a', 'Ā': 'A', 'ī': 'i', 'ū': 'u', 'ê': 'e', 'ṅ': 'n', 'ṇ': 'n',
                 'ḍ': 'd', 'ṭ': 't', 'ṃ': 'm', 'ñ': 'n', 'ṛ': 'ri', 'ś': 'sh',
                 'Ś': 'Sh', 'ṣ': 'sh', 'Ṣ': 'Sh', 'ḥ': '', '-': '-', ' ': '-'}

    roman_text = ''
    for char in iast_text:
        if char in swapTable:
            roman_text += swapTable[char]
        else:
            roman_text += char
    return roman_text.lower()


def tr(text, scr, titled=True):
    # titled = True seems to be primarily for NOT TitleCasing IAST Shlokas...
    if scr == 'hk':
        scr = sanscript.HK
    if text == '':
        return ''
    text = text.replace('~', '##~##')  # Simple fix to prevent transliteration of ~
    text_bits = text.split('|')
    transliterated_text = []

    if titled:
        for t in text_bits:
            t = t.rstrip('#~0123456789 ')
            if t[:3] == 'ta:':
                # Force Tamil!
                if scr == sanscript.DEVANAGARI:
                    scr = sanscript.TAMIL
                t = t[3:]
                if scr == sanscript.TAMIL:
                    transliterated_text.append('\\tamil{%s}' % sanscript.transliterate(data=t, _from=sanscript.HK, _to=scr).replace('C', 'Ch').replace('c', 'ch').title())
                else:
                    transliterated_text.append(sanscript.transliterate(data=t, _from=sanscript.HK, _to=scr).replace('C', 'Ch').replace('c', 'ch').title())

            else:
                if t.find('RIGHTarrow') == -1:
                    transliterated_text.append(sanscript.transliterate(data=t, _from=sanscript.HK, _to=scr).replace('C', 'Ch').replace('c', 'ch').title())
                else:
                    [txt, t1, arrow, t2] = t.split('\\')
                    transliterated_text.append('\\'.join([sanscript.transliterate(data=txt, _from=sanscript.HK, _to=scr).replace('C', 'Ch').replace('c', 'ch').title(),
                                                          t1, arrow, t2]))
    else:
        for t in text_bits:
            t = t.rstrip('~0123456789 ')
            if t[:3] == 'ta:':
                # Force Tamil!
                if scr == sanscript.DEVANAGARI:
                    scr = sanscript.TAMIL
                t = t[3:]
                transliterated_text.append(sanscript.transliterate(data=t, _from=sanscript.HK, _to=scr).replace('C', 'Ch').replace('c', 'ch').strip("{}").title())
            else:
                if t.find('RIGHTarrow') == -1:
                    transliterated_text.append(sanscript.transliterate(data=t, _from=sanscript.HK, _to=scr))
                else:
                    [txt, t1, arrow, t2] = t.split('\\')
                    transliterated_text.append('\\'.join([sanscript.transliterate(txt, _from=sanscript.HK, _to=scr), t1, arrow, t2]))

    output_text = '|'.join(transliterated_text)

    return output_text


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


def print_lat_lon(lat, lon):
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
      >>> print_lat_lon(1, -1)
      "1°0'0''N, 1°0'0''W"
    """

    if lat < 0:
        lat = -lat
        lat_suffix = 'S'
    else:
        lat_suffix = 'N'

    if lon < 0:
        lon = -lon
        lon_suffix = 'W'
    else:
        lon_suffix = 'E'

    return '%.6f°%s, %.6f°%s' % (lat, lat_suffix, lon, lon_suffix)


def longitudeToRightAscension(longitude):
    return (360 - longitude) / 360 * 24
