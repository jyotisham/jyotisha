""" Tests for bhadrA (viSTi) and the bhadrA-aware nirNaya procedures (hOlikA, rakSAbandhana).

Where each expected value comes from is stated with it; none is taken from the code under test:
- DRIK: Drik Panchang's Raksha Bandhan pages for New Delhi, 2023-2025 (drikpanchang.com/festivals/raksha-bandhan/
  raksha-bandhan-date-time.html?year=YYYY), which print the pUrNimA times, the bhadrA puccha/mukha/end and the muhUrta.
  Times are compared within a few minutes: jyotisha's ephemeris and sunrise convention differ slightly from Drik's.
- SABHA: the rule of the samanvaya-sabhA 2024 (adyatithi references/samanvaya-sabha-2024.md, #7) applied by hand to
  Drik's published tithi times.
- SABHA-HOLIKA (hand-worked): the samanvaya-sabhA's hOlikA rule (#20, as amended) applied by hand to the tithi and
  pradoSa times of that year in Mumbai, as listed in each case. Those inputs come from jyotisha's existing (unchanged)
  tithi and sunrise computations, and the bhadrA times from the helper tested against DRIK above.
"""

import functools

import pytest

from jyotisha.panchaanga.spatio_temporal import City, periodical
from jyotisha.panchaanga.temporal import era, time
from jyotisha.panchaanga.temporal.festival import rules
from jyotisha.panchaanga.temporal.festival.nirnaya import NirnayaFestivalAssigner, bhadraa, holikaa, rakshaabandhana

TZ = time.Timezone('Asia/Kolkata')
NEW_DELHI = City('New Delhi', '28:38:08', '77:13:28', 'Asia/Kolkata')
MUMBAI = City('Mumbai', '18:58:00', '72:50:00', 'Asia/Kolkata')
MINUTE = 1 / 1440.0


def _jd(y, m, d, hh, mm):
  return TZ.local_time_to_julian_day(time.Date(y, m, d, hh, mm, 0))


def _close(jd, expected_jd, minutes):
  assert abs(jd - expected_jd) <= minutes * MINUTE, (TZ.julian_day_to_local_time_str(jd), TZ.julian_day_to_local_time_str(expected_jd))


@functools.lru_cache()
def _assigner(city_name, start, end):
  city = {'New Delhi': NEW_DELHI, 'Mumbai': MUMBAI}[city_name]
  panchaanga = periodical.Panchaanga(city=city, start_date=start, end_date=end, year_type=era.ERA_GREGORIAN,
                                     recompute_festivals=False)
  return NirnayaFestivalAssigner(panchaanga=panchaanga)


def _rule(month, nirnaya, kaala=None, options=None):
  rule = rules.HinduCalendarEvent(id='test-%s' % nirnaya)
  rule.timing = rules.HinduCalendarEventTiming()
  rule.timing.month_type = 'lunar_month'
  rule.timing.month_number = month
  rule.timing.anga_type = 'tithi'
  rule.timing.anga_number = 15
  rule.timing.kaala = kaala
  rule.timing.nirnaya = nirnaya
  rule.timing.nirnaya_options = options
  return rule


# --- bhadrA spans and parts ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("date, puccha, mukha, end", [
  # DRIK 2023: puccha 05:30 PM-06:31 PM, mukha 06:31 PM-08:11 PM, bhadrA end 09:01 PM (Aug 30).
  ((2023, 8, 30), ((17, 30), (18, 31)), ((18, 31), (20, 11)), (21, 1)),
  # DRIK 2024: puccha 09:51 AM-10:53 AM, mukha 10:53 AM-12:37 PM, bhadrA end 01:30 PM (Aug 19).
  ((2024, 8, 19), ((9, 51), (10, 53)), ((10, 53), (12, 37)), (13, 30)),
])
def test_bhadraa_parts_match_drik(date, puccha, mukha, end):
  y, m, d = date
  spans = bhadraa.get_bhadraa_spans(jd1=_jd(y, m, d, 0, 0), jd2=_jd(y, m, d, 23, 59))
  assert len(spans) == 1 and spans[0].karana_index == 29  # zukla-pUrNimA, first half
  span = spans[0]
  [p] = span.get_part('puccha')
  [mk] = span.get_part('mukha')
  _close(p.jd_start, _jd(y, m, d, *puccha[0]), 3)
  _close(p.jd_end, _jd(y, m, d, *puccha[1]), 3)
  _close(mk.jd_start, _jd(y, m, d, *mukha[0]), 3)
  _close(mk.jd_end, _jd(y, m, d, *mukha[1]), 4)
  _close(span.jd_end, _jd(y, m, d, *end), 3)


def test_bhadraa_part_proportions_and_order():
  # nArada's 5:1:11:4:6:3 of the viSTi, rotated so that the puccha ends where the mukha starts.
  span = bhadraa.BhadraaSpan(jd_start=0.0, jd_end=30.0, karana_index=29)  # mukha from 3/4 of the way
  parts = span.get_parts()
  lengths = {}
  for name, interval in parts:
    lengths[name] = lengths.get(name, 0) + interval.jd_end - interval.jd_start
  assert lengths == pytest.approx({'mukha': 5, 'kaNTha': 1, 'hRdaya': 11, 'nAbhi': 4, 'kaTi': 6, 'puccha': 3})
  [mukha] = span.get_part('mukha')
  [puccha] = span.get_part('puccha')
  assert mukha.jd_start == pytest.approx(22.5) and puccha.jd_end == pytest.approx(22.5)
  # zukla 4 / kRSNa 14: the mukha opens the viSTi and the puccha closes it (SK: "विष्ट्यन्ते … पुच्छम्").
  for karana in (8, 57):
    parts = bhadraa.BhadraaSpan(jd_start=0.0, jd_end=30.0, karana_index=karana).get_parts()
    assert parts[0][0] == 'mukha' and parts[0][1].jd_start == pytest.approx(0)
    assert parts[-1][0] == 'puccha' and parts[-1][1].jd_end == pytest.approx(30)


def test_interval_subtraction():
  assert bhadraa.subtract((0, 10), [(2, 3), (5, 12)]) == [(0, 2), (3, 5)]
  assert bhadraa.subtract((0, 10), [(-1, 11)]) == []
  assert bhadraa.intersect((0, 5), (5, 9)) is None


# --- rakSAbandhana -------------------------------------------------------------------------------------------------

def _raksha(year, min_ghatikas):
  assigner = _assigner('New Delhi', '%d-07-15' % year, '%d-09-15' % year)
  [result] = rakshaabandhana.decide(assigner, _rule(5, 'rakshaabandhana', options={'min_ghatikas_after_sunrise': min_ghatikas}))
  return result


def test_rakshaabandhana_2023_six_ghatikas_drik():
  # DRIK 2023: Aug 30, "after 09:01 PM" (pUrNimA 10:58 AM Aug 30 - 07:05 AM Aug 31, under 6 ghaTikA after the Aug 31
  # sunrise, so the earlier day; there, after bhadrA ends).
  result = _raksha(2023, 6)
  assert result.date.get_date_str() == '2023-08-30'
  _close(result.interval.jd_start, _jd(2023, 8, 30, 21, 1), 3)


@pytest.mark.parametrize("min_ghatikas", [0, 2])
def test_rakshaabandhana_2023_sunrise_tithi(min_ghatikas):
  # SK (audayikI, N = 0) and SABHA (N = 2): DRIK's pUrNimA ends 07:05 AM Aug 31, about an hour (> 2 ghaTikA = 48 min)
  # after that day's sunrise, so Aug 31, from sunrise until the tithi ends (2nd half of pUrNimA: no bhadrA).
  result = _raksha(2023, min_ghatikas)
  assert result.date.get_date_str() == '2023-08-31'
  _close(result.interval.jd_end, _jd(2023, 8, 31, 7, 5), 3)


@pytest.mark.parametrize("min_ghatikas", [0, 2, 6])
def test_rakshaabandhana_2024_drik(min_ghatikas):
  # DRIK 2024: Aug 19, 01:30 PM to 09:08 PM (bhadrA ends 01:30 PM; pUrNimA 03:04 AM - 11:55 PM Aug 19).
  result = _raksha(2024, min_ghatikas)
  assert result.date.get_date_str() == '2024-08-19'
  _close(result.interval.jd_start, _jd(2024, 8, 19, 13, 30), 3)
  _close(result.interval.jd_end, _jd(2024, 8, 19, 23, 55), 3)


@pytest.mark.parametrize("min_ghatikas", [0, 2, 6])
def test_rakshaabandhana_2025_drik(min_ghatikas):
  # DRIK 2025: Aug 9, 05:47 AM to 01:24 PM ("Bhadra got over before Sunrise"; pUrNimA ends 01:24 PM Aug 9).
  # jyotisha's sunrise is a few minutes after Drik's.
  result = _raksha(2025, min_ghatikas)
  assert result.date.get_date_str() == '2025-08-09'
  _close(result.interval.jd_start, _jd(2025, 8, 9, 5, 47), 6)
  _close(result.interval.jd_end, _jd(2025, 8, 9, 13, 24), 3)


# --- hOlikA (pradoSa = the first eighth of the night) ----------------------------------------------------------------

def _holikaa(year):
  assigner = _assigner('Mumbai', '%d-02-10' % year, '%d-04-05' % year)
  [result] = holikaa.decide(assigner, _rule(12, 'holikaa', kaala='प्रदोषः'))
  return result


def test_holikaa_only_first_day_avoids_mukha():
  # SABHA-HOLIKA #20.3, 2024: pUrNimA 24 Mar 09:55 - 25 Mar 12:30, so only 24 Mar's pradoSa (18:47-20:16) has it. The
  # bhadrA-mukha of that pUrNimA starts 19:54 (DRIK, New Delhi: 07:53 PM; the same instant in Mumbai): 18:47-19:54.
  result = _holikaa(2024)
  assert result.date.get_date_str() == '2024-03-24'
  assert result.interval.name == 'bhadrA-mukha-rahita'
  _close(result.interval.jd_start, _jd(2024, 3, 24, 18, 47), 3)
  _close(result.interval.jd_end, _jd(2024, 3, 24, 19, 53), 4)


def test_holikaa_1954_first_day_since_the_sabha_struck_the_pratipat_rule():
  # SABHA-HOLIKA #20.3, 1954 (a year the sabhA cites for the struck sArdhayAmatraya rule): pUrNimA 18 Mar 16:05 -
  # 19 Mar 18:12, before 19 Mar's pradoSa (from 18:45); so only 18 Mar's -> 18 Mar.
  assert _holikaa(1954).date.get_date_str() == '1954-03-18'


def test_holikaa_pradosha_all_mukha():
  # SABHA-HOLIKA #20.3, 1966: pUrNimA 6 Mar 11:07 - 7 Mar 07:15; only 6 Mar's pradoSa (18:42-20:14) has it, and all of
  # it is mukha (viSTi 11:07-21:11, 604 min; its mukha starts 3/4 in, at 18:40, and lasts a sixth, to 20:21): from the
  # end of the mukha.
  result = _holikaa(1966)
  assert result.date.get_date_str() == '1966-03-06'
  assert result.interval.name == 'bhadrA-mukha-anta'
  assert result.interval.jd_start < result.interval.jd_end


def test_holikaa_neither_day_takes_the_second():
  # SABHA-HOLIKA #20.2, 1956: pUrNimA 25 Mar 20:18 - 26 Mar 18:41, after 25 Mar's pradoSa (ends 20:16) and before 26
  # Mar's (from 18:47): neither -> 26 Mar (no eclipse at that moonrise).
  assert _holikaa(1956).date.get_date_str() == '1956-03-26'


def test_holikaa_only_second_day():
  # Main rule (pradoSa-vyApinI), 2017: pUrNimA 11 Mar 20:23 - 12 Mar 20:23, so only 12 Mar's pradoSa (18:44-20:15).
  result = _holikaa(2017)
  assert result.date.get_date_str() == '2017-03-12'
  assert result.interval.name == 'प्रदोषः'


def test_holikaa_both_days_with_grastodaya_eclipse_keeps_second():
  # SABHA-HOLIKA #20.1 and #20.4, 1961: pUrNimA 1 Mar 17:00 - 2 Mar 19:04, in both days' pradoSa -> 2 Mar; the moon
  # rises eclipsed on 2 Mar (the lunar eclipse of 2 Mar 1961), but the pUrNimA is in that pradoSa, so it stands.
  from jyotisha.panchaanga.temporal.festival.nirnaya import find_tithi_spans
  assigner = _assigner('Mumbai', '1961-02-10', '1961-04-05')
  [(d, _, _)] = find_tithi_spans(assigner, 12, 15)
  assert holikaa.has_grastodaya_lunar_eclipse(assigner.panchaanga.city, assigner.daily_panchaangas[d + 1])
  assert _holikaa(1961).date.get_date_str() == '1961-03-02'
