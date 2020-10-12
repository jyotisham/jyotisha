from jyotisha.panchaanga.spatio_temporal import City, daily, periodical
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.temporal.festival.applier.solar import DailySolarAssigner
from jyotisha.panchaanga.temporal.time import Date

chennai = City.get_city_from_db('Chennai')


def test_daily_solar_viSukkaNi():
  panchaanga_14 = daily.DailyPanchaanga(city=chennai, date=Date(year=2018, month=4, day=14))
  
  panchaanga_15 = daily.DailyPanchaanga(city=chennai, date=Date(year=2018, month=4, day=15), previous_day_panchaanga=panchaanga_14)
  DailySolarAssigner(panchaanga=panchaanga_15, previous_day_panchaanga=panchaanga_14).apply_month_day_events()

  panchaanga_16 = daily.DailyPanchaanga(city=chennai, date=Date(year=2018, month=4, day=16), previous_day_panchaanga=panchaanga_15)
  DailySolarAssigner(panchaanga=panchaanga_16, previous_day_panchaanga=panchaanga_15).apply_month_day_events()
 
  panchaanga_17 = daily.DailyPanchaanga(city=chennai, date=Date(year=2018, month=4, day=17), previous_day_panchaanga=panchaanga_16)
  DailySolarAssigner(panchaanga=panchaanga_17, previous_day_panchaanga=panchaanga_16).apply_month_day_events()

  assert list(panchaanga_15.festival_id_to_instance.keys()) == ["viSukkan2i"]
  assert list(panchaanga_16.festival_id_to_instance.keys()) == []


def test_periodic_solar_viSukkaNi():
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2018, 4, 10), end_date=Date(2018, 4, 18), computation_system=computation_system)
  assert "viSukkan2i" in panchaanga.date_str_to_panchaanga[Date(2018, 4, 15).get_date_str()].festival_id_to_instance
  assert "viSukkan2i" not in panchaanga.date_str_to_panchaanga[Date(2018, 4, 16).get_date_str()].festival_id_to_instance

def test_periodic_solar_mUDavaN_muLukku():
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2018, 11, 14), end_date=Date(2018, 11, 20), computation_system=computation_system)
  assert "muDavan2 muzhukku" in panchaanga.date_str_to_panchaanga[Date(2018, 11, 17).get_date_str()].festival_id_to_instance
  assert "muDavan2 muzhukku" not in panchaanga.date_str_to_panchaanga[Date(2018, 11, 18).get_date_str()].festival_id_to_instance
