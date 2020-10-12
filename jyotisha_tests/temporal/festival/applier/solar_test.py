from jyotisha.panchaanga.spatio_temporal import City, daily
from jyotisha.panchaanga.temporal.festival.applier.solar import DailySolarAssigner
from jyotisha.panchaanga.temporal.time import Date

chennai = City.get_city_from_db('Chennai')


def disabled_test_daily_solar_viSukkaNi():
  panchaanga_14 = daily.DailyPanchaanga(city=chennai, date=Date(year=2018, month=4, day=14))
  
  panchaanga_15 = daily.DailyPanchaanga(city=chennai, date=Date(year=2018, month=4, day=15), previous_day_panchaanga=panchaanga_14)
  DailySolarAssigner(panchaanga=panchaanga_15, previous_day_panchaanga=panchaanga_14).apply_month_day_events()

  panchaanga_16 = daily.DailyPanchaanga(city=chennai, date=Date(year=2018, month=4, day=16), previous_day_panchaanga=panchaanga_15)
  DailySolarAssigner(panchaanga=panchaanga_16, previous_day_panchaanga=panchaanga_15).apply_month_day_events()
 
  panchaanga_17 = daily.DailyPanchaanga(city=chennai, date=Date(year=2018, month=4, day=17), previous_day_panchaanga=panchaanga_16)
  DailySolarAssigner(panchaanga=panchaanga_17, previous_day_panchaanga=panchaanga_16).apply_month_day_events()

  assert list(panchaanga_15.festival_id_to_instance.keys()) == ["viSukkan2i"]
  assert list(panchaanga_16.festival_id_to_instance.keys()) == []