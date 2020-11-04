from jyotisha.panchaanga.spatio_temporal import City


def test_moonrise_time():
  city = City.get_city_from_db(name="Bangalore")
  from jyotisha.panchaanga.temporal.body import Graha
  assert city.get_rising_time(julian_day_start=2459107.33, body=Graha.MOON) == 2459107.4297038973
