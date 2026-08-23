from jyotisha.panchaanga.spatio_temporal import City, periodical
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.temporal.time import Date

chennai = City.get_city_from_db('Chennai')


def test_kaarttika_somavaasara():
  """kArttika~sOmavAsaraH: lunar month 8, every Monday -- the first festival converted to the lightweight
  `[timing] vara = N` mechanism (apply_vara_conditioned_events), as opposed to the heavier multi-anga
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
