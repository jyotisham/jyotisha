#!/usr/bin/python3
#  -*- coding: utf-8 -*-

import logging

from indic_transliteration import xsanscript as sanscript

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def romanise(iast_text):
  swapTable = {'ā': 'a', 'Ā': 'A', 'ī': 'i', 'ū': 'u', 'ê': 'e', 'ṅ': 'n', 'ṇ': 'n',
               'ḍ': 'd', 'ṭ': 't', 'ṃ': 'm', 'ñ': 'n', 'ṉ': 'n', 'ṛ': 'ri', 'ś': 'sh',
               'Ś': 'Sh', 'ṣ': 'sh', 'Ṣ': 'Sh', 'ḥ': '', '-': '-', ' ': '-'}

  roman_text = ''
  for char in iast_text:
    if char in swapTable:
      roman_text += swapTable[char]
    else:
      roman_text += char
  return roman_text.lower()


def tr(text, script, titled=True):
  # titled = True seems to be primarily for NOT TitleCasing IAST Shlokas...
  if script == 'hk':
    script = sanscript.HK
  if text == '':
    return ''
  text = text.replace('~', '##~##')  # Simple fix to prevent transliteration of ~
  text_bits = text.split('|')
  transliterated_text = []

  if titled:
    for t in text_bits:
      t = t.rstrip('#~0123456789 ')
      if t.split("__")[0] == 'ta':
        # Force Tamil!
        if script == sanscript.DEVANAGARI:
          script = sanscript.TAMIL
        t = t.split("__")[1]
        if script == sanscript.TAMIL:
          tamil_text = sanscript.SCHEMES[sanscript.TAMIL].apply_roman_numerals(
            sanscript.transliterate(data=t, _from=sanscript.HK, _to=script))
          transliterated_text.append('\\tamil{%s}' % tamil_text.replace('C', 'Ch').replace('c', 'ch').title())
        else:
          transliterated_text.append(
            sanscript.transliterate(data=t, _from=sanscript.HK, _to=script).replace('C', 'Ch').replace('c', 'ch').title())

      else:
        if t.find('RIGHTarrow') == -1:
          transliterated_text.append(
            sanscript.transliterate(data=t, _from=sanscript.HK, _to=script).replace('C', 'Ch').replace('c', 'ch').title())
        else:
          [txt, t1, arrow, t2] = t.split('\\')
          transliterated_text.append('\\'.join([sanscript.transliterate(data=txt, _from=sanscript.HK, _to=script).replace(
            'C', 'Ch').replace('c', 'ch').title(),
                                                t1, arrow, t2]))
  else:
    for t in text_bits:
      t = t.rstrip('~0123456789 ')
      if t.split("__")[0] == 'ta':
        # Force Tamil!
        if script == sanscript.DEVANAGARI:
          script = sanscript.TAMIL
        t = t.split("__")[1]
        tamil_text = sanscript.SCHEMES[sanscript.TAMIL].apply_roman_numerals(
          sanscript.transliterate(data=t, _from=sanscript.HK, _to=script))
        transliterated_text.append(tamil_text.replace('C', 'Ch').replace('c', 'ch').strip("{}").title())
        # logging.debug(transliterated_text)
      else:
        if t.find('RIGHTarrow') == -1:
          transliterated_text.append(sanscript.transliterate(data=t, _from=sanscript.HK, _to=script))
        else:
          [txt, t1, arrow, t2] = t.split('\\')
          transliterated_text.append(
            '\\'.join([sanscript.transliterate(txt, _from=sanscript.HK, _to=script), t1, arrow, t2]))

  output_text = '|'.join(transliterated_text)
  if script == 'tamil':
    output_text = sanscript.SCHEMES[sanscript.TAMIL].apply_roman_numerals(output_text)
  if script == 'iast':
    output_text = output_text.replace('ṉ', 'n')
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
