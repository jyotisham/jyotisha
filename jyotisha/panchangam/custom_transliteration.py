#!/usr/bin/python3
#  -*- coding: utf-8 -*-

import re
import swisseph as swe
import sys
from math import floor

from indic_transliteration import sanscript


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


