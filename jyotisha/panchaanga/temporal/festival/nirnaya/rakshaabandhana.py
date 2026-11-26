""" The rakSAbandhana nirNaya (Smriti Kaustubha p.167), for the pUrNimA (or any tithi) named in the rule's timing.

SK: "अस्मिन्कर्मण्यौदयिकी तिथिर्ग्राह्या। पौर्णमास्यां दिनोदये इत्युपक्रमात् … इदं कर्म भद्रायां न कर्तव्यम्" ("भद्रायां द्वे न
कर्तव्ये श्रावणी फाल्गुनी तथा").

TOML:

  [timing]
  month_type = "lunar_month"
  month_number = 5
  anga_type = "tithi"
  anga_number = 15
  nirnaya = "rakshaabandhana"

  [timing.nirnaya_options]
  min_ghatikas_after_sunrise = 2    # optional, default 0

`kaala` and `priority` are not read.

The day (audayikI tithi): the first day at whose sunrise the tithi prevails. With `min_ghatikas_after_sunrise` = N > 0,
if the tithi lasts less than N ghaTikA after that sunrise, the day before (on which the tithi began) is taken instead;
SK states only the bare audayikI rule (N = 0), and the samanvaya-sabhA 2024 (#7) reconciles the nibandhas with N = 2
(earlier 6). If the tithi prevails at no sunrise (kSaya), the day on which it falls; if at two (vRddhi), the first
(sabhA: "अहोरात्र के दिन अर्थात् पूर्वदिन").

The time (not in bhadrA): on the chosen day, the first stretch of the tithi, between that day's sunrise and the next,
outside bhadrA. Since viSTi is the first half of a pUrNimA, this is from sunrise when the tithi was already in its second
half then, and from the end of bhadrA when the day is the one the tithi began on. If no such stretch exists, the day is
assigned without a time.
"""

import logging

from jyotisha.panchaanga.temporal.festival.nirnaya import NirnayaResult, find_tithi_spans
from jyotisha.panchaanga.temporal.festival.nirnaya.bhadraa import intersect, subtract, get_avoided_intervals
from jyotisha.panchaanga.temporal.interval import Interval

COMPANION_SUFFIXES = []


def choose_day(days, d, ts, te, min_ghatikas):
  """ Index (into `days`) of the chosen day for the tithi [ts, te) beginning on day d. """
  sunrise_days = [i for i in (d + 1, d + 2) if ts <= days[i].jd_sunrise < te]
  if not sunrise_days:
    return d  # kSaya
  b = sunrise_days[0]
  ghatika = (days[b].jd_next_sunrise - days[b].jd_sunrise) / 60.0
  if min_ghatikas > 0 and te - days[b].jd_sunrise < min_ghatikas * ghatika:
    return d
  return b


def decide(assigner, rule):
  timing = rule.timing
  if timing.anga_type != 'tithi':
    raise ValueError('%s: the rakshaabandhana nirnaya needs anga_type = "tithi"' % rule.id)
  options = timing.nirnaya_options or {}
  min_ghatikas = options.get('min_ghatikas_after_sunrise', 0)
  days = assigner.daily_panchaangas
  results = []
  for (d, ts, te) in find_tithi_spans(assigner, month_number=timing.month_number, tithi_index=timing.anga_number):
    x = choose_day(days, d, ts, te, min_ghatikas)
    day = days[x]
    on_day = intersect((day.jd_sunrise, day.jd_next_sunrise), (ts, te))
    free = subtract(on_day, get_avoided_intervals(*on_day)) if on_day is not None else []
    if free:
      results.append(NirnayaResult(fest_id=rule.id, date=day.date, interval=Interval(jd_start=free[0][0], jd_end=free[0][1], name='bhadrA-rahita')))
    else:
      logging.warning('%s on %s: no bhadrA-free time of the tithi that day; assigning the day without a time.',
                      rule.id, day.date.get_date_str())
      results.append(NirnayaResult(fest_id=rule.id, date=day.date))
  return results
