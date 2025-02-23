from jyotisha.panchaanga.spatio_temporal import daily
from jyotisha.panchaanga.temporal import ComputationSystem, set_constants
from jyotisha.panchaanga.temporal.time import Date
from jyotisha_tests.spatio_temporal import chennai

set_constants()


def test_MultiNewMoonAssigner():
  # Online - https://www.drikpanchang.com/panchang/month-panchang.html?date=13/07/2018
  # karka-sankrAnti was on 16th.
  panchaanga = daily.DailyPanchaanga(
    city=chennai, date=Date(2018, 7, 13), computation_system=ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA__CHITRA_180)
  assert panchaanga.lunar_date.month.index == 3
  panchaanga = daily.DailyPanchaanga(
    # dvitIyA following amAvAsyA - can trip up previous day panchAnga utilization logic.
    city=chennai, date=Date(2018, 7, 14), computation_system=ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA__CHITRA_180, previous_day_panchaanga=panchaanga)
  assert panchaanga.lunar_date.month.index == 4


  # Online : https://www.drikpanchang.com/panchang/month-panchang.html?date=21/07/2018
  panchaanga = daily.DailyPanchaanga(
    city=chennai, date=Date(2018, 7, 21), computation_system=ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA__CHITRA_180)
  assert panchaanga.lunar_date.month.index == 4


def test_MultiFullMoonAssigner():
  # Online - https://www.drikpanchang.com/panchang/month-panchang.html?date=13/07/2018 https://www.prokerala.com/astrology/panchang/2018-july-13.html
  # karka-sankrAnti was on 16th.
  panchaanga = daily.DailyPanchaanga(
    city=chennai, date=Date(2018, 7, 13), computation_system=ComputationSystem.MULTI_FULL_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180)
  assert panchaanga.lunar_date.month.index == 4
  panchaanga = daily.DailyPanchaanga(
    city=chennai, date=Date(2018, 7, 14), computation_system=ComputationSystem.MULTI_FULL_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180, previous_day_panchaanga=panchaanga)
  assert panchaanga.lunar_date.month.index == 4
  panchaanga = daily.DailyPanchaanga(
    city=chennai, date=Date(2024, 6, 23), computation_system=ComputationSystem.MULTI_FULL_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180)
  assert panchaanga.lunar_date.month.index == 4


def test_SolsticePostDark10AdhikaAssigner():
  """See https://vishvasa.github.io/jyotiSham/kAla-mAnam/kauNDinyAyana/adhika-mAsa-gaNanam/
 for a convenient list of verified solsticial lunar months."""


  panchaanga = daily.DailyPanchaanga(
    city=chennai, date=Date(2019, 12, 1), computation_system=ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180)
  assert panchaanga.lunar_date.month.index == 10.5

  panchaanga = daily.DailyPanchaanga(
    city=chennai, date=Date(2020, 3, 20), computation_system=ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180)
  assert panchaanga.lunar_date.month.index == 1

  # Though this month contained a solstice on amAvAsyA, it is not intercalary since the preceding solstice was intercalary.
  panchaanga = daily.DailyPanchaanga(
    city=chennai, date=Date(2020, 6, 1), computation_system=ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180)
  assert panchaanga.lunar_date.month.index == 4

  # Though this month contained a solstice on amAvAsyA, it is not intercalary since the preceding solstice was intercalary.
  panchaanga = daily.DailyPanchaanga(
    city=chennai, date=Date(2020, 6, 21), computation_system=ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180)
  assert panchaanga.lunar_date.month.index == 4

  panchaanga = daily.DailyPanchaanga(
    city=chennai, date=Date(2020, 12, 15), computation_system=ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180)
  assert panchaanga.lunar_date.month.index == 11

  panchaanga = daily.DailyPanchaanga(
    city=chennai, date=Date(2020, 12, 16), computation_system=ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180)
  assert panchaanga.lunar_date.month.index == 11

  panchaanga = daily.DailyPanchaanga(
    city=chennai, date=Date(2021, 7, 11), computation_system=ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180)
  assert panchaanga.lunar_date.month.index == 6

  panchaanga = daily.DailyPanchaanga(
    city=chennai, date=Date(2022, 1, 1), computation_system=ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180)
  assert panchaanga.lunar_date.month.index == 11

  panchaanga = daily.DailyPanchaanga(
    city=chennai, date=Date(2022, 12, 21), computation_system=ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180)
  assert panchaanga.lunar_date.month.index == 10.5


  # sphuTa-tithi at noon on this day is 2, but it follows a short tithi 1 - (2024-03-10 14:30:23.078209+, 2024-03-11 10:45:26.293762+05:30)
  panchaanga = daily.DailyPanchaanga(
    city=chennai, date=Date(2024, 3, 11), computation_system=ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180)
  assert panchaanga.lunar_date.month.index == 2
  assert panchaanga.lunar_date.month.index == 2
