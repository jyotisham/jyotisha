from jyotisha.panchaanga.spatio_temporal import City, periodical
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.temporal.festival.applier.solar import SolarFestivalAssigner
from jyotisha.panchaanga.temporal.time import Date

chennai = City.get_city_from_db('Chennai')


def test_mudavan_muzhukku():
  """muDavan2_muzhukku: day 1 of sidereal_solar month 8 (as reckoned at sunset), decided by comparing the
  month's own transition jd against sunrise -- transition before sunrise keeps the day, transition at/after
  sunrise shifts to the next day. Previously a day-loop in
  SolarFestivalAssigner.assign_month_day_muDavan_muzhukku; now driven by RuleLookupAssigner's new
  apply_month_transition_events() via a `[timing] month_type/month_number/anga_type="day"/anga_number/kaala`
  TOML rule. Verified against a direct reproduction of the exact original day-loop over a 20-year range."""
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2005, 1, 1), end_date=Date(2025, 12, 31),
                                      computation_system=computation_system)
  new_days = set(panchaanga.festival_id_to_days.get('muDavan2_muzhukku', set()))

  direct_days = set()
  daily_panchaangas = SolarFestivalAssigner(panchaanga).daily_panchaangas
  for d, daily_panchaanga in enumerate(daily_panchaangas[:-1]):
    if daily_panchaanga.solar_sidereal_date_sunset.month == 8 and daily_panchaanga.solar_sidereal_date_sunset.day == 1:
      if daily_panchaanga.solar_sidereal_date_sunset.month_transition is None or daily_panchaanga.solar_sidereal_date_sunset.month_transition < daily_panchaanga.jd_sunrise:
        direct_days.add(daily_panchaanga.date)
      else:
        direct_days.add(daily_panchaangas[d + 1].date)

  assert len(direct_days) > 0
  assert new_days == direct_days


def test_tula_kaveri_snana_arambhah():
  """tulA-kAvErI-snAna-ArambhaH: day 1 of sidereal_solar month 7 (Tula, as reckoned at sunset), decided by
  comparing the month's own transition jd against brAhma muhUrta's start -- transition before brAhma keeps the
  day, transition at/after it shifts to the next day. Previously a day-loop in
  SolarFestivalAssigner.assign_month_day_tulA_kAvErI_snAna_ArambhaH; now driven by apply_month_transition_events
  via the same mechanism as muDavan2_muzhukku (kaala="braahma" instead of "sunrise").

  The original had a real bug: a bare `return` right after the day-loop's first match exited the whole
  function, so across a multi-year Panchaanga it only ever assigned ONE occurrence total (the chronologically
  first), never recurring annually as the festival clearly should. Confirmed with the user and fixed as part of
  this conversion -- so this test verifies against the *corrected* per-year logic (the same decision, applied
  to every year in range, not just the first), not a byte-identical reproduction of the buggy original."""
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2005, 1, 1), end_date=Date(2025, 12, 31),
                                      computation_system=computation_system)
  new_days = set(panchaanga.festival_id_to_days.get('tulA-kAvErI-snAna-ArambhaH', set()))

  direct_days = set()
  daily_panchaangas = SolarFestivalAssigner(panchaanga).daily_panchaangas
  for d, daily_panchaanga in enumerate(daily_panchaangas[:-1]):
    if daily_panchaanga.solar_sidereal_date_sunset.month == 7 and daily_panchaanga.solar_sidereal_date_sunset.day == 1:
      transition = daily_panchaanga.solar_sidereal_date_sunset.month_transition
      braahma_start = daily_panchaanga.day_length_based_periods.fifteen_fold_division.braahma.jd_start
      if transition is None or transition < braahma_start:
        direct_days.add(daily_panchaanga.date)
      else:
        direct_days.add(daily_panchaangas[d + 1].date)

  # Sanity check that the fix actually recurs annually (not just the single pre-bugfix occurrence).
  assert len(direct_days) >= 15
  assert new_days == direct_days
