from jyotisha.panchaanga.spatio_temporal import City, periodical
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.temporal.festival.rules import resolve_vaara_index
from jyotisha.panchaanga.temporal.time import Date
from jyotisha.panchaanga.temporal.zodiac import AngaType

chennai = City.get_city_from_db('Chennai')


def test_resolve_vaara_index_accepts_names_and_ints():
  assert resolve_vaara_index(2) == 2
  assert resolve_vaara_index(None) is None
  for name, expected in [("Bhanu", 1), ("soma", 2), ("Indu", 2), ("Mangala", 3), ("bhauma", 3),
                          ("Saumya", 4), ("BUDHA", 4), ("guru", 5), ("Shukra", 6), ("bhrigu", 6),
                          ("Shani", 7), ("sthira", 7)]:
    assert resolve_vaara_index(name) == expected, name


def test_kaarttika_somavaasara():
  """kArttika~sOmavAsaraH: lunar month 8, every Monday -- the first festival converted to the lightweight
  `[timing] vaara = "soma"` mechanism (apply_vaara_conditioned_events), as opposed to the heavier multi-anga
  intersection search engine. Verifies it recurs on every matching Monday (not just the first) and matches
  the original hand-written condition exactly."""
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2018, 1, 1), end_date=Date(2020, 12, 31),
                                      computation_system=computation_system)
  new_days = set(panchaanga.festival_id_to_days.get('kArttika~sOmavAsaraH', set()))

  old_days = set()
  daily_panchaangas = panchaanga.daily_panchaangas_sorted()
  for d in range(panchaanga.duration_prior_padding, panchaanga.duration + panchaanga.duration_prior_padding):
    dp = daily_panchaangas[d]
    if dp.lunar_date.month.index == 8 and dp.date.get_weekday() == 1:
      old_days.add(dp.date)

  assert len(new_days) > 4  # recurs weekly through most of Kartika, across 3 years -- not just once per year
  assert new_days == old_days
  assert all(d.get_weekday() == 1 for d in new_days)


def test_masa_vara_yoga_fests_tn():
  """The 6 solar-month + weekday Tamil festivals (assign_masa_vara_yoga_fests_tn, now retired) -- same
  month_type=sidereal_solar_month + vaara shape as kArttika~sOmavAsaraH, just keyed on the solar month."""
  FESTS = ((5, 0, 'AvaNi~JAyir2r2ukkizhamai'),
           (6, 6, 'puraTTAci~can2ikkizhamai'),
           (8, 0, 'kArttigai~JAyir2r2ukkizhamai'),
           (4, 5, 'ADi~veLLikkizhamai'),
           (10, 5, 'tai~veLLikkizhamai'),
           (11, 2, 'mAci~cevvAy'))
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2018, 1, 1), end_date=Date(2020, 12, 31),
                                      computation_system=computation_system)
  daily_panchaangas = panchaanga.daily_panchaangas_sorted()
  for month, weekday, fest_id in FESTS:
    new_days = set(panchaanga.festival_id_to_days.get(fest_id, set()))
    old_days = set()
    for d in range(panchaanga.duration_prior_padding, panchaanga.duration + panchaanga.duration_prior_padding):
      dp = daily_panchaangas[d]
      if dp.solar_sidereal_date_sunset.month == month and dp.date.get_weekday() == weekday:
        old_days.add(dp.date)
    assert len(new_days) > 4, fest_id
    assert new_days == old_days, fest_id
    assert all(d.get_weekday() == weekday for d in new_days), fest_id


def test_angaaraki_caturthi():
  """aGgArakI~caturthI / sukhA~aGgArakI~caturthI: tithi 19 (krishna) / tithi 4 (shukla) touching the day, on a
  Tuesday. The original Python (VaraFestivalAssigner.assign_tithi_vara_yoga_mangala_angaaraka, now retired) had
  a latent bug: its "is it shukla" name check reused a variable already reduced mod 15, so a krishna-caturthi
  (tithi 19) touching sunset specifically (19 % 15 == 4) was misnamed sukhA~ (documented as shukla-paksha only).
  This conversion fixes that by matching on the true tithi index (4 vs 19) via two separate TOML rules, so it is
  compared against a *corrected* reference computation, not the original buggy one -- with 2015-09-01 and
  2016-04-26 (both real krishna-caturthi-on-Tuesday dates the old code mislabeled) checked explicitly."""
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2015, 1, 1), end_date=Date(2020, 12, 31),
                                      computation_system=computation_system)
  daily_panchaangas = panchaanga.daily_panchaangas_sorted()

  expected = {'aGgArakI~caturthI': set(), 'sukhA~aGgArakI~caturthI': set()}
  for d in range(panchaanga.duration_prior_padding, panchaanga.duration + panchaanga.duration_prior_padding):
    dp = daily_panchaangas[d]
    if dp.date.get_weekday() != 2:
      continue
    tithi_sunrise = dp.sunrise_day_angas.tithi_at_sunrise.index
    tithi_sunset = dp.sunrise_day_angas.get_anga_at_jd(jd=dp.jd_sunset, anga_type=AngaType.TITHI).index
    if tithi_sunrise % 15 == 4 or tithi_sunset % 15 == 4:
      name = 'sukhA~aGgArakI~caturthI' if (tithi_sunrise == 4 or tithi_sunset == 4) else 'aGgArakI~caturthI'
      expected[name].add(dp.date)

  for fest_id in expected:
    assert set(panchaanga.festival_id_to_days.get(fest_id, set())) == expected[fest_id], fest_id

  plain_days = set(panchaanga.festival_id_to_days.get('aGgArakI~caturthI', set()))
  assert Date(2015, 9, 1) in plain_days  # tithi 18->19 at sunset -- old code mislabeled this sukhA~
  assert Date(2016, 4, 26) in plain_days  # tithi 19 all day -- likewise mislabeled
