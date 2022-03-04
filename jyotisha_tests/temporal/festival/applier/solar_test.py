from jyotisha.panchaanga.spatio_temporal import City, periodical
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.temporal.time import Date

chennai = City.get_city_from_db('Chennai')


def test_daily_solar_viSukkaNi():

  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2018, 4, 14), end_date=Date(2018, 4, 15), computation_system=computation_system)
 
  assert "viSukkan2i" in panchaanga.date_str_to_panchaanga[Date(2018, 4, 14).get_date_str()].festival_id_to_instance.keys()
  assert "viSukkan2i" not in panchaanga.date_str_to_panchaanga[Date(2018, 4, 15).get_date_str()].festival_id_to_instance


def test_periodic_solar_viSukkaNi():
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2018, 4, 10), end_date=Date(2018, 4, 18), computation_system=computation_system)
  assert "viSukkan2i" in panchaanga.date_str_to_panchaanga[Date(2018, 4, 14).get_date_str()].festival_id_to_instance
  assert "viSukkan2i" not in panchaanga.date_str_to_panchaanga[Date(2018, 4, 15).get_date_str()].festival_id_to_instance

def test_periodic_solar_mUDavaN_muLukku():
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2018, 11, 14), end_date=Date(2018, 11, 20), computation_system=computation_system)
  assert "muDavan2_muzhukku" in panchaanga.date_str_to_panchaanga[Date(2018, 11, 17).get_date_str()].festival_id_to_instance
  assert "muDavan2_muzhukku" not in panchaanga.date_str_to_panchaanga[Date(2018, 11, 18).get_date_str()].festival_id_to_instance
