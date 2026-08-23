import pytest

from jyotisha.panchaanga.spatio_temporal import City, periodical
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.temporal.festival import rules
from jyotisha.panchaanga.temporal.festival.applier.solar import SolarFestivalAssigner
from jyotisha.panchaanga.temporal.festival.rules import HinduCalendarEvent
from jyotisha.panchaanga.temporal.time import Date
from jyotisha.panchaanga.temporal.zodiac.angas import AngaType

chennai = City.get_city_from_db('Chennai')


def _rules_collection():
  computation_system = ComputationSystem.DEFAULT
  return rules.RulesCollection.get_cached(
    repos_tuple=tuple(computation_system.festival_options.repos),
    julian_handling=computation_system.festival_options.julian_handling)


def test_vara_span_matches_get_weekday():
  """AngaType.VARA span-finding (day-granularity, sunrise-anchored) must agree exactly with
  daily_panchaanga.date.get_weekday(), the source of truth used everywhere else in the codebase."""
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2024, 1, 1), end_date=Date(2024, 1, 14),
                                      computation_system=computation_system)
  assigner = SolarFestivalAssigner(panchaanga)
  for target_index in range(1, 8):
    span = assigner._find_vara_span(jd1=panchaanga.jd_start, jd2=panchaanga.jd_end, target_anga_id=target_index)
    assert span is not None, target_index
    matches = [dp for dp in assigner.daily_panchaangas
               if dp.jd_sunrise == span.jd_start and dp.jd_next_sunrise == span.jd_end]
    assert len(matches) == 1
    assert matches[0].date.get_weekday() + 1 == target_index


def test_anga_intersection_or_list_and_vara():
  """_assign_anga_intersection: a VARA condition, combined with a list-valued (OR) anga, should find a match
  wherever the true value is among the candidates -- the OR-list mechanism several rules need (eg.
  assign_ayushmad_bava_saumya_yoga's `for karana_ID in BAVA_KARANA: ...` hand-loop). Uses a real day's actual
  tithi/weekday (deterministic) rather than searching for a rare astronomical coincidence, plus a decoy
  alternative in the OR-list to prove it isn't just matching the first candidate."""
  # Note: end_date is deliberately not near a lunar-month-4/6/8 boundary ~30 days out, to avoid an unrelated
  # pre-existing off-by-one in assign_anadhyayana_dvadashi_yoga (solar.py:511-513, `daily_panchaangas[d + 1]`
  # on the very last enumerated day) that this refactor doesn't touch and isn't the concern of this test.
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2018, 4, 1), end_date=Date(2018, 4, 30),
                                      computation_system=computation_system)
  assigner = SolarFestivalAssigner(panchaanga)
  target_day = assigner.daily_panchaangas[panchaanga.duration_prior_padding + 3]
  actual_tithi = target_day.sunrise_day_angas.tithi_at_sunrise.index
  actual_vara = target_day.date.get_weekday() + 1
  decoy_tithi = (actual_tithi % 30) + 1  # guaranteed different from actual_tithi

  assigner._assign_anga_intersection(
    'test~or-list', [(AngaType.VARA, actual_vara), (AngaType.TITHI, [decoy_tithi, actual_tithi])],
    jd_start=target_day.jd_sunrise, jd_end=target_day.jd_next_sunrise, show_debug_info=False)

  assert panchaanga.festival_id_to_days.get('test~or-list', set()) == {target_day.date}

  # A VARA value that does NOT match today should not assign anything.
  wrong_vara = (actual_vara % 7) + 1
  assigner._assign_anga_intersection(
    'test~or-list-no-match', [(AngaType.VARA, wrong_vara), (AngaType.TITHI, actual_tithi)],
    jd_start=target_day.jd_sunrise, jd_end=target_day.jd_next_sunrise, show_debug_info=False)
  assert panchaanga.festival_id_to_days.get('test~or-list-no-match', set()) == set()


def test_apply_anga_intersection_events_from_toml():
  """End-to-end: a TOML rule using `intersection_groups` (the real gajacchAyA-yOgaH conditions, under a test id)
  should, via apply_anga_intersection_events, assign the festival on exactly the same days as calling
  _assign_anga_intersection directly with the same two intersect_lists (what assign_gajachhaya_yoga does)."""
  collection = _rules_collection()
  test_id = 'test~gajacchAyA-yOgaH'
  assert test_id not in collection.name_to_rule
  event = HinduCalendarEvent(id=test_id)
  event.timing = rules.HinduCalendarEventTiming()
  event.timing.window = "full_period"
  event.timing.intersection_groups = [
    {"angas": [{"anga_type": "solar_nakshatra", "anga_number": 13}, {"anga_type": "nakshatra", "anga_number": 10}, {"anga_type": "tithi", "anga_number": 28}]},
    {"angas": [{"anga_type": "solar_nakshatra", "anga_number": 13}, {"anga_type": "nakshatra", "anga_number": 13}, {"anga_type": "tithi", "anga_number": 30}]},
  ]
  collection.name_to_rule[test_id] = event
  try:
    computation_system = ComputationSystem.DEFAULT
    panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2018, 1, 1), end_date=Date(2023, 12, 31),
                                        computation_system=computation_system)
    assigner = SolarFestivalAssigner(panchaanga)
    assigner._assign_anga_intersection('test~gajacchAyA-direct', [(AngaType.SOLAR_NAKSH, 13), (AngaType.NAKSHATRA, 10), (AngaType.TITHI, 28)],
                                        jd_start=panchaanga.jd_start, jd_end=panchaanga.jd_end, show_debug_info=False)
    assigner._assign_anga_intersection('test~gajacchAyA-direct', [(AngaType.SOLAR_NAKSH, 13), (AngaType.NAKSHATRA, 13), (AngaType.TITHI, 30)],
                                        jd_start=panchaanga.jd_start, jd_end=panchaanga.jd_end, show_debug_info=False)

    toml_days = panchaanga.festival_id_to_days.get(test_id, set())
    direct_days = panchaanga.festival_id_to_days.get('test~gajacchAyA-direct', set())
    assert len(direct_days) > 0
    assert toml_days == direct_days
    # And it should agree with the real (unconverted) production festival too.
    assert toml_days == panchaanga.festival_id_to_days.get('gajacchAyA-yOgaH', set())
  finally:
    del collection.name_to_rule[test_id]
