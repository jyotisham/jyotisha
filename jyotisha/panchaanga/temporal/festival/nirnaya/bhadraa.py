""" bhadrA (viSTi karaNa): its spans, and its parts (mukha, kaNTha, hRdaya, nAbhi, kaTi, puccha).

Smriti Kaustubha p.564-565 (viSTi-nirNaya):
- Where it falls (jyotiHprakAza): "चतुर्युकादशी रात्रौ शुक्ले पूर्णाष्टमी दिवा। भद्रा त्रिदशमी रात्रौ कृष्णे त्र्यद्रिमनौ तिथौ॥" --
  the 2nd half of zukla 4 and 11 and kRSNa 3 and 10, the 1st half of zukla 8 and 15 and kRSNa 7 and 14; ie. jyotisha's
  karaNa indices 8, 15, 22, ..., 57 (VISHTI_KARANAS).
- Its parts (nArada): "मुखे पञ्च गले त्वेका वक्षस्येकादश स्मृताः। नाभौ चतस्रः षट् श्रोण्यां तिस्रः पुच्छाख्यनाडिकाः॥" --
  5, 1, 11, 4, 6 and 3 of a nominal 30 ghaTikA. SK scales them to the actual viSTi: "कल्पितो विष्टिदशमांश उक्तप्रदेशस्थः
  पुच्छम्। एवं षष्ठांशाद्यात्मकं मुखाद्यपि" (puccha a tenth, mukha a sixth).
- Where the mukha is (zrIpati): in the tithi-yAma named by the direction "जलशिखिशशिरक्षाशर्वकीनाशवायुत्रिदशपतिककुप्सु",
  counted from the east -- so, as a fraction of the viSTi, the mukha starts at zukla 4: 0, 8: 1/4, 11: 1/2, 15: 3/4 and
  kRSNa 3: 3/4, 7: 1/2, 10: 1/4, 14: 0; the parts run on from there in nArada's order, wrapping round, so that the puccha
  ends where the mukha starts (bopadeva: "भेष्वर्कनखनाड्यूर्ध्वं भद्रापुच्छं घटीत्रयम्। क्रमेण शुक्लपक्षे स्याद्युत्क्रमेण सितेतरे").

This placement reproduces the bhadrA mukha/puccha/end times Drik Panchang publishes (see the tests).
"""

from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.temporal.zodiac import AngaSpanFinder, Ayanamsha
from jyotisha.panchaanga.temporal.zodiac.angas import AngaType

VISHTI_KARANAS = tuple(range(8, 60, 7))

MUKHA_START_FRACTION = {8: 0.0, 15: 0.25, 22: 0.5, 29: 0.75, 36: 0.75, 43: 0.5, 50: 0.25, 57: 0.0}

PARTS = (('mukha', 5), ('kaNTha', 1), ('hRdaya', 11), ('nAbhi', 4), ('kaTi', 6), ('puccha', 3))
PART_NAMES = tuple(name for name, _ in PARTS)


class BhadraaSpan(object):
  def __init__(self, jd_start, jd_end, karana_index):
    self.jd_start = jd_start
    self.jd_end = jd_end
    self.karana_index = karana_index

  def get_parts(self):
    """ [(part_name, Interval)] in time order; a part that wraps past the end of the viSTi comes as two pieces. """
    length = self.jd_end - self.jd_start
    pos = MUKHA_START_FRACTION[self.karana_index]
    pieces = []
    for name, ghatikas in PARTS:
      start, end = pos, pos + ghatikas / 30.0
      if end <= 1.0 + 1e-9:
        pieces.append((name, start, min(end, 1.0)))
        pos = end
      else:
        if start < 1.0:
          pieces.append((name, start, 1.0))
        pieces.append((name, max(start - 1.0, 0.0), end - 1.0))
        pos = end - 1.0
    pieces.sort(key=lambda p: p[1])
    return [(name, Interval(jd_start=self.jd_start + a * length, jd_end=self.jd_start + b * length, name=name))
            for name, a, b in pieces if b > a]

  def get_part(self, name):
    return [interval for part_name, interval in self.get_parts() if part_name == name]

  def to_interval(self):
    return Interval(jd_start=self.jd_start, jd_end=self.jd_end, name='bhadrA')

  def __repr__(self):
    return 'BhadraaSpan(%s, %s, karana %d)' % (self.jd_start, self.jd_end, self.karana_index)


def get_bhadraa_spans(jd1, jd2):
  """ All bhadrA spans overlapping [jd1, jd2], each with both of its ends (searched for beyond [jd1, jd2]). karaNa
  depends only on the moon-sun elongation, so no ayanAMza enters. """
  finder = AngaSpanFinder.get_cached(ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0, anga_type=AngaType.KARANA)
  spans = []
  for span in finder.get_all_angas_in_period(jd1=jd1 - 1, jd2=jd2 + 1):
    if span.anga.index not in VISHTI_KARANAS or span.jd_start is None or span.jd_end is None:
      continue
    if span.jd_end <= jd1 or span.jd_start >= jd2:
      continue
    spans.append(BhadraaSpan(jd_start=span.jd_start, jd_end=span.jd_end, karana_index=span.anga.index))
  return spans


# Plain (start, end) interval arithmetic, used by the bhadrA-aware procedures.

def intersect(a, b):
  """ Intersection of two (start, end) pairs, or None. """
  if a is None or b is None:
    return None
  start, end = max(a[0], b[0]), min(a[1], b[1])
  return (start, end) if end > start else None


def subtract(interval, removals):
  """ (start, end) minus a list of (start, end): the remaining pieces, in time order. """
  pieces = [interval] if interval is not None else []
  for r_start, r_end in sorted(removals):
    new_pieces = []
    for start, end in pieces:
      if r_end <= start or r_start >= end:
        new_pieces.append((start, end))
        continue
      if r_start > start:
        new_pieces.append((start, r_start))
      if r_end < end:
        new_pieces.append((r_end, end))
    pieces = new_pieces
  return pieces


def get_avoided_intervals(jd1, jd2, avoid="whole"):
  """ (start, end) pairs of bhadrA to avoid within [jd1, jd2]: the whole of each bhadrA, or only its mukha. """
  intervals = []
  for span in get_bhadraa_spans(jd1=jd1, jd2=jd2):
    if avoid == "whole":
      intervals.append((span.jd_start, span.jd_end))
    elif avoid == "mukha":
      intervals.extend((p.jd_start, p.jd_end) for p in span.get_part("mukha"))
    else:
      raise ValueError("avoid must be 'whole' or 'mukha', not %r" % avoid)
  return intervals


def get_puccha_intervals(jd1, jd2):
  return [(p.jd_start, p.jd_end) for span in get_bhadraa_spans(jd1=jd1, jd2=jd2) for p in span.get_part("puccha")]
