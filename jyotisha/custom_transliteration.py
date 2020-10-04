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
  """
  
  NOTE: Please don't put your custom tex/ md/ ics whatever code here and pollute core library functions. Wrap this in your own functions if you must. Functions should be atomic."""
  if script == 'hk':
    script = sanscript.HK
  if text == '':
    return ''
  # TODO: Fix this ugliness.
  t = text.replace('~', '##~##')  # Simple fix to prevent transliteration of ~
  # logging.debug(transliterated_text)
  transliterated_text = sanscript.transliterate(data=t, _from=sanscript.HK, _to=script).replace('C', 'Ch').replace('c', 'ch')
  if titled:
    transliterated_text = transliterated_text.title()

  if script == sanscript.TAMIL:
    transliterated_text = sanscript.SCHEMES[sanscript.TAMIL].apply_roman_numerals(transliterated_text)
  if script == 'iast':
    transliterated_text = transliterated_text.replace('ṉ', 'n')
  return transliterated_text


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
