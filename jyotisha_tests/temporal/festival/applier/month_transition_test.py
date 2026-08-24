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
