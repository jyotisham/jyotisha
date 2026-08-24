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


def test_ayushmad_bava_saumya_yoga():
  """AyuSmad-bava-saumya-saMyOgaH: every Wednesday (VARA), YOGA=3 (AyuSmAn) & KARANA in BAVA_KARANA
  (list(range(2,52,7)) -- the repeating bava karana slot across the lunar month), searched sunrise-to-sunset on
  each such day -- previously a day-loop in SolarFestivalAssigner.assign_ayushmad_bava_saumya_yoga making one
  _assign_anga_intersection call per (day, karana value) pair. Verified against a direct reproduction of that
  same day-loop (8 separate per-karana calls per Wednesday, not a single OR-list call) over a 21-year range, to
  establish the exact original semantics before converting to a TOML `intersection_groups` OR-list."""
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2010, 1, 1), end_date=Date(2030, 12, 31),
                                      computation_system=computation_system)
  new_days = set(panchaanga.festival_id_to_days.get('AyuSmad-bava-saumya-saMyOgaH', set()))

  assigner = SolarFestivalAssigner(panchaanga)
  BAVA_KARANA = list(range(2, 52, 7))
  for daily_panchaanga in assigner.daily_panchaangas:
    if daily_panchaanga.date.get_weekday() == 3:
      for karana_ID in BAVA_KARANA:
        assigner._assign_anga_intersection(
          'test~ayushmad-direct', [(AngaType.YOGA, 3), (AngaType.KARANA, karana_ID)],
          jd_start=daily_panchaanga.jd_sunrise, jd_end=daily_panchaanga.jd_sunset, show_debug_info=False)
  direct_days = set(panchaanga.festival_id_to_days.get('test~ayushmad-direct', set()))

  assert len(direct_days) > 0
  assert new_days == direct_days


def test_pushkara_yoga():
  """tripuSkara-yOgaH~{0,2,6} / dvipuSkara-yOgaH~{0,2,6}: 6 separate festival ids (3 weekdays x 2 nakshatra-sets),
  previously a day-loop in SolarFestivalAssigner.assign_pushkara_yoga. On each day, the loop picks the LAST
  nakshatra-transition matching TRI_PUSHKARA_NAKSHATRA=[3,7,12,16,21,25] (or DVI_PUSHKARA_NAKSHATRA=[5,14,23])
  and the LAST tithi-transition matching PUSHKARA_TITHI=[2,7,12,17,22,27] that day, then -- only if the weekday
  is in PUSHKARA_WDAY=[0,2,6] (Sun/Tue/Sat) -- calls _assign_anga_intersection with that SPECIFIC (single)
  nakshatra+tithi pair, windowed sunrise-to-next_sunrise, id suffixed by weekday. Verified against a direct
  reproduction of that exact day-loop (not a naive NAKSHATRA-list x TITHI-list combinatorial search) over a
  15-year range, since the two are not obviously equivalent (the original always resolves to at most one
  specific nakshatra/tithi value per day, not every list member)."""
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2010, 1, 1), end_date=Date(2025, 12, 31),
                                      computation_system=computation_system)

  PUSHKARA_TITHI = [2, 7, 12, 17, 22, 27]
  TRI_PUSHKARA_NAKSHATRA = [3, 7, 12, 16, 21, 25]
  DVI_PUSHKARA_NAKSHATRA = [5, 14, 23]
  PUSHKARA_WDAY = [0, 2, 6]

  assigner = SolarFestivalAssigner(panchaanga)
  for daily_panchaanga in assigner.daily_panchaangas:
    dp_nakshatra = tp_nakshatra = p_tithi = None
    for nakshatra_span in daily_panchaanga.sunrise_day_angas.nakshatras_with_ends:
      nakshatra_ID = nakshatra_span.anga.index
      if nakshatra_ID in TRI_PUSHKARA_NAKSHATRA:
        tp_nakshatra = nakshatra_ID
      elif nakshatra_ID in DVI_PUSHKARA_NAKSHATRA:
        dp_nakshatra = nakshatra_ID
    for tithi_span in daily_panchaanga.sunrise_day_angas.tithis_with_ends:
      tithi_ID = tithi_span.anga.index
      if tithi_ID in PUSHKARA_TITHI:
        p_tithi = tithi_ID
    wday = daily_panchaanga.date.get_weekday()
    if p_tithi is not None and wday in PUSHKARA_WDAY:
      if tp_nakshatra is not None:
        assigner._assign_anga_intersection(
          'test~tripuSkara-direct~%d' % wday, [(AngaType.NAKSHATRA, tp_nakshatra), (AngaType.TITHI, p_tithi)],
          jd_start=daily_panchaanga.jd_sunrise, jd_end=daily_panchaanga.jd_next_sunrise, show_debug_info=False)
      if dp_nakshatra is not None:
        assigner._assign_anga_intersection(
          'test~dvipuSkara-direct~%d' % wday, [(AngaType.NAKSHATRA, dp_nakshatra), (AngaType.TITHI, p_tithi)],
          jd_start=daily_panchaanga.jd_sunrise, jd_end=daily_panchaanga.jd_next_sunrise, show_debug_info=False)

  any_checked = False
  for wday in PUSHKARA_WDAY:
    for prefix, direct_prefix in [('tripuSkara-yOgaH', 'test~tripuSkara-direct'), ('dvipuSkara-yOgaH', 'test~dvipuSkara-direct')]:
      new_days = set(panchaanga.festival_id_to_days.get('%s~%d' % (prefix, wday), set()))
      direct_days = set(panchaanga.festival_id_to_days.get('%s~%d' % (direct_prefix, wday), set()))
      assert new_days == direct_days, '%s~%d: %s vs %s' % (prefix, wday, new_days, direct_days)
      any_checked = True
  assert any_checked


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
