import logging

from jyotisha.panchangam.spatio_temporal import City

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

def test_solar_day():
  from jyotisha.panchangam.spatio_temporal import daily
  panchangam = daily.Panchangam(city=City('Chennai', '13:05:24', '80:16:12', 'Asia/Calcutta'), julian_day=2457023.27)
  panchangam.compute_solar_day()
  logging.debug(str(panchangam))
  assert panchangam.solar_month_day == 17
  assert panchangam.solar_month == 9


def test_tb_muhuurta():
  from jyotisha.panchangam.spatio_temporal import daily
  panchangam = daily.Panchangam(city=City('Chennai', '13:05:24', '80:16:12', 'Asia/Calcutta'), julian_day=2457023.27)
  panchangam.compute_tb_muhuurtas()
  logging.debug(str(panchangam))
  assert len(panchangam.tb_muhuurtas) == 15
  assert panchangam.tb_muhuurtas[0].jd_start == panchangam.jd_sunrise
  import numpy.testing
  numpy.testing.assert_approx_equal(panchangam.tb_muhuurtas[14].jd_end, panchangam.jd_sunrise)
