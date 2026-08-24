from jyotisha.panchaanga.spatio_temporal import City, periodical
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.temporal.festival.applier.solar import SolarFestivalAssigner
from jyotisha.panchaanga.temporal.time import Date
from jyotisha.panchaanga.temporal.zodiac import AngaType

chennai = City.get_city_from_db('Chennai')


def test_gajacchaayaa_yoga():
  """gajacchAyA-yOgaH: SOLAR_NAKSH=13 & NAKSHATRA=10 & TITHI=28, OR SOLAR_NAKSH=13 & NAKSHATRA=13 & TITHI=30,
  over the whole computed period. The first conversion off the "genuine multi-anga search" list (as opposed to
  the trivial vaara-conditioned list) -- SolarFestivalAssigner.assign_gajachhaya_yoga (now retired) called
  _assign_anga_intersection with these same two intersect_lists directly; the TOML entry's `intersection_groups`
  now drives it via apply_anga_intersection_events instead. Verified against a direct call to
  _assign_anga_intersection with the original intersect_lists, over a 21-year range."""
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2010, 1, 1), end_date=Date(2030, 12, 31),
                                      computation_system=computation_system)
  new_days = set(panchaanga.festival_id_to_days.get('gajacchAyA-yOgaH', set()))

  assigner = SolarFestivalAssigner(panchaanga)
  assigner._assign_anga_intersection(
    'test~gajacchaayaa-direct', [(AngaType.SOLAR_NAKSH, 13), (AngaType.NAKSHATRA, 10), (AngaType.TITHI, 28)],
    jd_start=panchaanga.jd_start, jd_end=panchaanga.jd_end, show_debug_info=False)
  assigner._assign_anga_intersection(
    'test~gajacchaayaa-direct', [(AngaType.SOLAR_NAKSH, 13), (AngaType.NAKSHATRA, 13), (AngaType.TITHI, 30)],
    jd_start=panchaanga.jd_start, jd_end=panchaanga.jd_end, show_debug_info=False)
  direct_days = set(panchaanga.festival_id_to_days.get('test~gajacchaayaa-direct', set()))

  assert len(direct_days) > 0
  assert new_days == direct_days


def test_padmaka_yoga_3():
  """padmaka-yOgaH-3: SOLAR_NAKSH=16 (vizAkhA) & NAKSHATRA=3 (kRttikA), over the whole computed period, no vaara
  or other gate -- the simplest possible `intersection_groups` conversion (a single unconditional whole-period
  search, previously the standalone tail call in SolarFestivalAssigner.assign_padmaka_yoga; the two other
  sub-cases in that function, padmaka-yOga-puNyakAlaH and padmaka-yOgaH-2, are day-loop-gated/branching and stay
  custom Python). Verified against a direct call to _assign_anga_intersection with the original intersect_list,
  over a 25-year range."""
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2005, 1, 1), end_date=Date(2030, 12, 31),
                                      computation_system=computation_system)
  new_days = set(panchaanga.festival_id_to_days.get('padmaka-yOgaH-3', set()))

  assigner = SolarFestivalAssigner(panchaanga)
  assigner._assign_anga_intersection(
    'test~padmaka-direct', [(AngaType.SOLAR_NAKSH, 16), (AngaType.NAKSHATRA, 3)],
    jd_start=panchaanga.jd_start, jd_end=panchaanga.jd_end, show_debug_info=False)
  direct_days = set(panchaanga.festival_id_to_days.get('test~padmaka-direct', set()))

  assert len(direct_days) > 0
  assert new_days == direct_days
