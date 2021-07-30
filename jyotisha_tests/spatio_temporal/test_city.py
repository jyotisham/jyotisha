from jyotisha.panchaanga.spatio_temporal import City
import numpy


def test_moonrise_time():
  city = City.get_city_from_db(name="Bangalore")
  from jyotisha.panchaanga.temporal.body import Graha
  numpy.testing.assert_approx_equal(city.get_rising_time(julian_day_start=2459107.33, body=Graha.MOON), 2459107.4297038973)
