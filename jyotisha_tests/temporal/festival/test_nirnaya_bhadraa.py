""" Tests for bhadrA (viSTi) and the bhadrA-aware nirNaya procedures (hOlikA, rakSAbandhana).

Where each expected value comes from is stated with it; none is taken from the code under test:
- DRIK: Drik Panchang's Raksha Bandhan pages for New Delhi, 2023-2025 (drikpanchang.com/festivals/raksha-bandhan/
  raksha-bandhan-date-time.html?year=YYYY), which print the pUrNimA times, the bhadrA puccha/mukha/end and the muhUrta.
  Times are compared within a few minutes: jyotisha's ephemeris and sunrise convention differ slightly from Drik's.
- SABHA: the rule of the samanvaya-sabhA 2024 (adyatithi references/samanvaya-sabha-2024.md, #7) applied by hand to
  Drik's published tithi times.
- SK (hand-worked): the Smriti Kaustubha hOlikA chain (p.517-518) worked by hand from the tithi, sunrise/sunset and
  bhadrA times of that year, as listed in each case. Those inputs come from jyotisha's existing (unchanged) tithi and
  sunrise computations, and the bhadrA times from the helper tested against DRIK above.
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


# --- hOlikA --------------------------------------------------------------------------------------------------------

def _holikaa(year, options=None):
  assigner = _assigner('Mumbai', '%d-02-10' % year, '%d-04-05' % year)
  [result] = holikaa.decide(assigner, _rule(12, 'holikaa', kaala='प्रदोषः', options=options))
  return result


def test_holikaa_1954_second_day_by_pratipat_rule():
  # SK step 3a (hand-worked, Mumbai). pUrNimA 18 Mar 16:05 - 19 Mar 18:12: not in 19 Mar's pradoSa (from 18:45);
  # 18 Mar's pradoSa (18:45-20:15) is all bhadrA (16:05 - 05:07). On 19 Mar the pUrNimA lasts 11.4 h after sunrise
  # (06:47) >= 3 1/2 yAma of a 12.0 h day (10.5 h), and pratipat lasts 13.7 h after 20 Mar's sunrise > 11.4 h:
  # increasing. So 19 Mar, in its pradoSa.
  result = _holikaa(1954)
  assert result.date.get_date_str() == '1954-03-19'
  assert result.interval.name == 'प्रदोषः'


def test_holikaa_1975_first_day_puccha():
  # SK steps 3a-3c (hand-worked, Mumbai). pUrNimA 26 Mar 19:45 - 27 Mar 16:06: 26 Mar's pradoSa (18:47-20:16) has it
  # only in bhadrA (19:45 - 27 Mar 05:54); on 27 Mar it lasts 9.4 h after sunrise < 3 1/2 yAma (10.6 h), so not 3a.
  # bhadrA ends at 05:54, after the cut-off 2 ghaTikA (48 min) before the 06:41 sunrise, so not 3b; hence the puccha.
  result = _holikaa(1975)
  assert result.date.get_date_str() == '1975-03-26'
  assert result.interval.name == 'bhadrA-puccha'


@pytest.mark.parametrize("vardhamaana, expected_date, expected_name", [
  # SK hand-worked, Mumbai 1964: pUrNimA 26 Feb 19:09 - 27 Feb 18:09, so only 26 Feb's pradoSa has it, in bhadrA
  # (19:09 - 27 Feb 06:36). On 27 Feb it lasts 11.1 h after sunrise >= 3 1/2 yAma (10.2 h). Pratipat (27 Feb 18:09 -
  # 28 Feb 17:36) lasts 10.6 h after 28 Feb's sunrise, less than the pUrNimA's 11.1 h, but its whole length (23.45 h)
  # exceeds the pUrNimA's (22.99 h): the two readings of "प्रतिपद्वर्धमाना" disagree.
  ('after_sunrise', '1964-02-26', 'bhadrA-puccha'),  # bhadrA ends after the cut-off (06:15): so the puccha
  ('duration', '1964-02-27', 'प्रदोषः'),
])
def test_holikaa_1964_vardhamaana_readings(vardhamaana, expected_date, expected_name):
  result = _holikaa(1964, options={'vardhamaana': vardhamaana})
  assert result.date.get_date_str() == expected_date
  assert result.interval.name == expected_name


def test_holikaa_2026_after_bhadraa_ends():
  # SK step 3b (hand-worked, Mumbai). pUrNimA 2 Mar 17:56 - 3 Mar 17:07: only 2 Mar's pradoSa, all bhadrA (17:56 -
  # 3 Mar 05:28); on 3 Mar 10.2 h after sunrise < 3 1/2 yAma (10.3 h); bhadrA ends at 05:28, before the cut-off 2 ghaTikA
  # before the 3 Mar sunrise (06:58 - 48 min): from 05:28.
  result = _holikaa(2026)
  assert result.date.get_date_str() == '2026-03-02'
  assert result.interval.name == 'bhadrA-anta'
  _close(result.interval.jd_start, _jd(2026, 3, 3, 5, 28), 3)


def test_holikaa_rejects_bad_options():
  with pytest.raises(ValueError):
    holikaa.decide(_assigner('Mumbai', '2026-02-10', '2026-04-05'), _rule(12, 'holikaa', kaala='प्रदोषः', options={'yaama': 'ghaTikA'}))
