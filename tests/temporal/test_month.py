from jyotisha.panchaanga.spatio_temporal import daily
import tests.spatio_temporal
from jyotisha.panchaanga.temporal import time, ComputationSystem, set_constants
from jyotisha.panchaanga.temporal.time import Date

set_constants()


def test_SolsticePostDark10AdhikaAssigner():
  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=tests.spatio_temporal.chennai, julian_day=time.utc_gregorian_to_jd(Date(2020, 10, 3)), computation_system=ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180)
  assert panchaanga.lunar_month_sunrise == 8
