""" The hOlikA nirNaya (Smriti Kaustubha p.517-518), for the pUrNimA (or any tithi) named in the rule's timing.

TOML:

  [timing]
  month_type = "lunar_month"
  month_number = 12
  anga_type = "tithi"
  anga_number = 15
  kaala = "प्रदोषः"          # the kAla the tithi should pervade (SK: "प्रदोषव्यापिनी ग्राह्या पूर्णिमा फाल्गुनी सदा")
  nirnaya = "holikaa"

  [timing.nirnaya_options]   # optional; how to measure the two conditions of step 3a below
  yaama = "dinamaana"        # a yAma is a quarter of the daytime (default), or "ahoraatra": an eighth of the full day
  vardhamaana = "after_sunrise"  # the next tithi is "increasing" if it lasts longer after its sunrise than the tithi
                             # did after its own (default), or "duration": if its whole length is greater

`priority` is not read: the procedure below replaces it.

Let A be the civil day (sunrise to next sunrise) on which the tithi begins and B the next. "Free" time is time in the
kAla during the tithi and outside bhadrA (see bhadraa.py). SK's chain:

1. "अत्र च प्रदोषव्यापिपूर्णमासी भद्रारहिता ग्राह्या": the tithi in the kAla of only one day, and that time not all bhadrA
   -> that day, at the free time.
2. "दिनद्वये प्रदोषव्याप्तौ परदिने प्रदोषैकदेशव्याप्तिलाभे वा पूर्वदिने भद्रादोषादेव परैव ग्राह्या": the tithi in the kAla of both
   days (on B even partly) -> B. (On B the tithi is in its 2nd half, so free of bhadrA.)
3. Only A's kAla has the tithi, and it is all bhadrA:
   a. "सार्धयामत्रयं पूर्णा द्वितीये दिवसे यदा। प्रतिपद्वर्धमाना तु तदा सा होलिका स्मृता" (bhaviSyottara, via nirNayAmRta): if
      on B the tithi lasts 3 1/2 yAma (of B's daytime) after sunrise, and the next tithi is increasing (lasts longer
      after C's sunrise than the tithi did after B's) -> B, in its kAla (in the next tithi).
   b. "भद्रान्तं प्रतीक्ष्य … सूर्योदयपूर्वभाविघटिकाद्वयात्पूर्वं" ("रात्रौ भद्रावसाने च होलिकां तत्र दीपयेत्"): A, from the end of
      bhadrA, if that is during the tithi and before the 2 ghaTikA preceding B's sunrise.
   c. "पूर्वदिन एवोक्तसमये भद्रापुच्छे" ("तानि सर्वाणि सिध्यन्ति विष्टिपुच्छे"): A, in a bhadrA-puccha in that night window.
   d. "सर्वत्रैव भद्रायामपि कार्यं नतु परत्र सायाह्नादौ": A, in the kAla, even in bhadrA.
4. Neither day's kAla has the tithi ("दिनद्वयेऽपि पूर्णिमायाः प्रदोषस्यांशाभावः"): A, by 3b-3d (the tithi then begins after
   A's kAla), the earliest free time that night, else the puccha, else the tithi in that night.

The chosen time is recorded on the festival. Not modelled: the samanvaya-sabhA's eclipse clause (an eclipse in the kAla
permits the rite during it), which SK does not discuss here.
"""

import logging

from jyotisha.panchaanga.temporal.festival.nirnaya import NirnayaResult, find_tithi_spans
from jyotisha.panchaanga.temporal.festival.nirnaya.bhadraa import intersect, subtract, get_avoided_intervals, \
  get_puccha_intervals
from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.temporal.zodiac import AngaSpanFinder, Ayanamsha
from jyotisha.panchaanga.temporal.zodiac.angas import AngaType

COMPANION_SUFFIXES = []

YAAMAS_ON_SECOND_DAY = 3.5
GHATIKAS_BEFORE_SUNRISE = 2


def _kaala(day, kaala):
  interval = day.get_interval(interval_id=kaala)
  return (interval.jd_start, interval.jd_end)


def _ghatika(day):
  return (day.jd_next_sunrise - day.jd_sunrise) / 60.0


YAAMA_VALUES = ('dinamaana', 'ahoraatra')
VARDHAMAANA_VALUES = ('after_sunrise', 'duration')


def _next_tithi_is_increasing(tithi_start, tithi_end, day_b, day_c, tithi_index, vardhamaana):
  """ Whether the tithi after `tithi_index` is increasing (vardhamAna), by `vardhamaana` (see the module docstring). """
  finder = AngaSpanFinder.get_cached(ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0, anga_type=AngaType.TITHI)
  next_index = tithi_index % 30 + 1
  next_span = finder.find(jd1=tithi_end - 0.01, jd2=tithi_end + 3, target_anga_id=next_index)
  if next_span is None or next_span.jd_end is None:
    return False
  if vardhamaana == 'duration':
    return (next_span.jd_end - next_span.jd_start) > (tithi_end - tithi_start)
  return (next_span.jd_end - day_c.jd_sunrise) > (tithi_end - day_b.jd_sunrise)


def _interval(pair, name):
  return Interval(jd_start=pair[0], jd_end=pair[1], name=name)


def decide_one(assigner, fest_id, kaala, tithi_index, d, ts, te, yaama='dinamaana', vardhamaana='after_sunrise'):
  days = assigner.daily_panchaangas
  day_a, day_b, day_c = days[d], days[d + 1], days[d + 2]
  tithi = (ts, te)
  in_kaala_a = intersect(_kaala(day_a, kaala), tithi)
  in_kaala_b = intersect(_kaala(day_b, kaala), tithi)

  if in_kaala_a is not None and in_kaala_b is not None:
    # 2: both days -> B.
    free_b = subtract(in_kaala_b, get_avoided_intervals(*in_kaala_b))
    return NirnayaResult(fest_id=fest_id, date=day_b.date, interval=_interval(free_b[0] if free_b else in_kaala_b, kaala))
  if in_kaala_b is not None:
    # 1: only B.
    free_b = subtract(in_kaala_b, get_avoided_intervals(*in_kaala_b))
    return NirnayaResult(fest_id=fest_id, date=day_b.date, interval=_interval(free_b[0] if free_b else in_kaala_b, kaala))
  if in_kaala_a is not None:
    free_a = subtract(in_kaala_a, get_avoided_intervals(*in_kaala_a))
    if free_a:
      # 1: only A, with free time.
      return NirnayaResult(fest_id=fest_id, date=day_a.date, interval=_interval(free_a[0], kaala))
    # 3a: the next tithi increasing, and the tithi lasting 3 1/2 yAma on B -> B, in its kAla.
    if yaama == 'ahoraatra':
      yaama_b = (day_b.jd_next_sunrise - day_b.jd_sunrise) / 8.0
    else:
      yaama_b = (day_b.jd_sunset - day_b.jd_sunrise) / 4.0
    if te - day_b.jd_sunrise >= YAAMAS_ON_SECOND_DAY * yaama_b and \
        _next_tithi_is_increasing(tithi_start=ts, tithi_end=te, day_b=day_b, day_c=day_c, tithi_index=tithi_index,
                                  vardhamaana=vardhamaana):
      kaala_b = _kaala(day_b, kaala)
      return NirnayaResult(fest_id=fest_id, date=day_b.date, interval=_interval(kaala_b, kaala))

  # 3b-3d (and 4): A's night, from the kAla's start to 2 ghaTikA before B's sunrise.
  night = intersect((_kaala(day_a, kaala)[0], day_a.jd_next_sunrise - GHATIKAS_BEFORE_SUNRISE * _ghatika(day_a)), tithi)
  if night is None:
    logging.warning('%s: the tithi starting on %s is not in the kAla of either day, nor in that night before the 2 '
                    'ghaTikA preceding sunrise; assigning the day without a time.', fest_id, day_a.date.get_date_str())
    return NirnayaResult(fest_id=fest_id, date=day_a.date)
  free_night = subtract(night, get_avoided_intervals(*night))
  if free_night:
    return NirnayaResult(fest_id=fest_id, date=day_a.date, interval=_interval(free_night[0], 'bhadrA-anta'))
  puccha = [p for p in (intersect(night, puccha) for puccha in get_puccha_intervals(*night)) if p is not None]
  if puccha:
    return NirnayaResult(fest_id=fest_id, date=day_a.date, interval=_interval(puccha[0], 'bhadrA-puccha'))
  start = in_kaala_a if in_kaala_a is not None else night
  return NirnayaResult(fest_id=fest_id, date=day_a.date, interval=_interval(start, 'bhadrA'))


def decide(assigner, rule):
  timing = rule.timing
  if timing.anga_type != 'tithi':
    raise ValueError('%s: the holikaa nirnaya needs anga_type = "tithi"' % rule.id)
  kaala = timing.get_kaala()
  options = timing.nirnaya_options or {}
  yaama = options.get('yaama', 'dinamaana')
  vardhamaana = options.get('vardhamaana', 'after_sunrise')
  if yaama not in YAAMA_VALUES or vardhamaana not in VARDHAMAANA_VALUES:
    raise ValueError('%s: nirnaya_options.yaama must be one of %s and vardhamaana one of %s' % (rule.id, YAAMA_VALUES, VARDHAMAANA_VALUES))
  return [decide_one(assigner=assigner, fest_id=rule.id, kaala=kaala, tithi_index=timing.anga_number, d=d, ts=ts, te=te,
                     yaama=yaama, vardhamaana=vardhamaana)
          for (d, ts, te) in find_tithi_spans(assigner, month_number=timing.month_number, tithi_index=timing.anga_number)]
