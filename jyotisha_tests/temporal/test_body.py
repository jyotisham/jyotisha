import logging

import numpy

from jyotisha.panchaanga.temporal import body
from jyotisha.panchaanga.temporal.body import Graha, Transit

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def test_graha_get_longitude():
  numpy.testing.assert_approx_equal(Graha.singleton(Graha.SUN).get_longitude(jd=2458434.083333251), 229.12286985575702)

def test_longitude_difference():
  numpy.testing.assert_approx_equal(body.longitude_difference(jd=2458484.545, body1=Graha.singleton(Graha.SUN), body2=Graha.singleton(Graha.MARS)), -79.66, significant=2)
  numpy.testing.assert_approx_equal(body.longitude_difference(jd=2458485.5453, body1=Graha.singleton(Graha.SUN), body2=Graha.singleton(Graha.MARS)), -79.31, significant=2)


def test_graha_get_next_raashi_transit():
  from jyotisha.panchaanga.temporal.zodiac import Ayanamsha
  from jyotisha.panchaanga.temporal.zodiac import AngaType
  transits = Graha.singleton(Graha.JUPITER).get_transits(jd_start=2457755, jd_end=2458120, anga_type=AngaType.RASHI, ayanaamsha_id=Ayanamsha.CHITRA_AT_180)
  from sanskrit_data import collection_helper
  collection_helper.assert_approx_equals(transits, [
           Transit(body=Graha.JUPITER, jd=2458008.4510242934, anga_type=AngaType.RASHI.name, value_1=6, value_2=7)], floating_point_precision=4)
  assert Graha.singleton(Graha.SUN).get_transits(jd_start=2458162.545722, jd_end=2458177.545722, anga_type=AngaType.RASHI, ayanaamsha_id=Ayanamsha.CHITRA_AT_180) == []


def test_get_star_longitude():
  numpy.testing.assert_approx_equal(body.get_star_longitude(star="Spica", jd=2458434.083333251), 204.09485939669307)
