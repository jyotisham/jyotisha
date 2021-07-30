import numpy
from jyotisha.panchaanga.temporal import zodiac, time
from jyotisha.panchaanga.temporal.time import Date
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision, Ayanamsha, AngaSpanFinder
from jyotisha.panchaanga.temporal.zodiac.angas import AngaType


def test_get_ayanaamsha():
  ayanaamsha = zodiac.Ayanamsha.singleton(ayanaamsha_id=zodiac.Ayanamsha.CHITRA_AT_180)
  numpy.testing.assert_approx_equal(ayanaamsha.get_offset(2458434.083333251), 24.094859396693067)


def disabled_test_swe_ayanaamsha_api():
  import swisseph as swe
  swe.set_sid_mode(swe.SIDM_LAHIRI)
  # city = City.from_address_and_timezone('Cupertino, CA', "America/Los_Angeles")
  # jd = city.local_time_to_julian_day(year=2018, month=11, day=11, hours=6, minutes=0, seconds=0)
  assert swe.get_ayanamsa_ut(2458434.083333251) == 24.120535828308334



def test_get_anga():

  nd = NakshatraDivision(jd=time.ist_timezone.local_time_to_julian_day(Date(2018, 7, 14)), ayanaamsha_id=Ayanamsha.CHITRA_AT_180)
  assert nd.get_anga(
    anga_type=AngaType.TITHI).index == 1

  nd = NakshatraDivision(jd=time.ist_timezone.local_time_to_julian_day(Date(2018, 7, 14, 6, 1)), ayanaamsha_id=Ayanamsha.CHITRA_AT_180)
  assert nd.get_anga(
    anga_type=AngaType.TITHI).index == 2

  nd = NakshatraDivision(jd=time.ist_timezone.local_time_to_julian_day(Date(2018, 7, 13)), ayanaamsha_id=Ayanamsha.CHITRA_AT_180)
  assert nd.get_anga(
    anga_type=AngaType.TITHI).index == 30
  assert nd.get_anga(
    anga_type=AngaType.SIDEREAL_MONTH).index == 3

  # Just before meSha sankrAnti
  assert NakshatraDivision(jd=time.ist_timezone.local_time_to_julian_day(Date(2018, 4, 13)), ayanaamsha_id=Ayanamsha.CHITRA_AT_180).get_anga(
    anga_type=AngaType.SIDEREAL_MONTH).index == 12


  # 5:6:0.00 UT on December 23, 1981
  nd = NakshatraDivision(2444961.7125, ayanaamsha_id=Ayanamsha.CHITRA_AT_180)
  assert nd.get_anga(AngaType.NAKSHATRA).index == 16
  assert nd.get_anga(AngaType.TITHI).index == 28
  assert nd.get_anga(AngaType.YOGA).index == 8
  assert nd.get_anga(AngaType.KARANA).index == 55
  assert nd.get_solar_raashi().index == 9

def test_get_anga_span_solar_month():
  from jyotisha.panchaanga.temporal import time
  span_finder = AngaSpanFinder.get_cached(anga_type=AngaType.SIDEREAL_MONTH, ayanaamsha_id=Ayanamsha.CHITRA_AT_180)

  numpy.testing.assert_array_almost_equal(span_finder.find(jd1=2458222.0333434483-32, jd2=2458222.0333434483 + 4, target_anga_id=12,).to_tuple(), (2458192.24785228, 2458222.6026552585), decimal=3)

  jd2 = time.ist_timezone.local_time_to_julian_day(time.Date(2020, 4, 16))
  numpy.testing.assert_array_almost_equal(numpy.array(span_finder.find(jd1=jd2-32, jd2=jd2, target_anga_id=1).to_tuple(), dtype=numpy.float), numpy.array((2458953.10966, None), dtype=numpy.float), decimal=4)

  numpy.testing.assert_array_almost_equal(numpy.array(span_finder.find(jd1=2458133.0189002366-32, jd2=2458133.0189002366, target_anga_id=10).to_tuple(), dtype=numpy.float), numpy.array((2458132.8291680976, None), dtype=numpy.float), decimal=4)


def test_get_anga_span_tithi():
  span_finder = AngaSpanFinder.get_cached(anga_type=AngaType.TITHI, ayanaamsha_id=Ayanamsha.CHITRA_AT_180)

  numpy.testing.assert_array_almost_equal(span_finder.find(jd1=2458102.5, jd2=2458108.5, target_anga_id=30).to_tuple(), (2458104.6663699686, 2458105.771125107))

  numpy.testing.assert_array_almost_equal(span_finder.find(jd1=2444959.54042, jd2=2444963.54076, target_anga_id=27).to_tuple(), (2444960.4924699212, 2444961.599213224))


def test_get_tithis_in_period():
  span_finder = AngaSpanFinder.get_cached(anga_type=AngaType.TITHI, ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0)
  spans = span_finder.get_spans_in_period(jd_start=time.ist_timezone.local_time_to_julian_day(Date(year=2020, month=1, day=1)), jd_end=time.ist_timezone.local_time_to_julian_day(Date(year=2020, month=6, day=30)), target_anga_id=30)
  jds = [x.jd_start for x in spans]
  numpy.testing.assert_array_almost_equal(jds, [2458872.36655025,
                                                         2458902.0647052005,
                                                         2458931.792117506,
                                                         2458961.5055956016,
                                                         2458991.1712410315,
                                                         2459020.765607745], decimal=3)


def test_get_karanas_in_period():
  span_finder = AngaSpanFinder.get_cached(anga_type=AngaType.KARANA, ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0)
  spans = span_finder.get_spans_in_period(jd_start=time.ist_timezone.local_time_to_julian_day(Date(year=2020, month=1, day=1)), jd_end=time.ist_timezone.local_time_to_julian_day(Date(year=2020, month=6, day=30)), target_anga_id=30)
  jds = [x.jd_start for x in spans]
  numpy.testing.assert_array_almost_equal(jds, [2458858.845, 2458888.379, 2458917.821, 2458947.19 , 2458976.52 , 2459005.852], decimal=3)


def test_get_yogas_in_period():
  span_finder = AngaSpanFinder.get_cached(anga_type=AngaType.KARANA, ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0)
  spans = span_finder.get_spans_in_period(jd_start=time.ist_timezone.local_time_to_julian_day(Date(year=2020, month=1, day=1)), jd_end=time.ist_timezone.local_time_to_julian_day(Date(year=2020, month=6, day=30)), target_anga_id=15)
  jds = [x.jd_start for x in spans]
  numpy.testing.assert_array_almost_equal(jds, [2458851.146, 2458881.029, 2458910.808, 2458940.431, 2458969.882, 2458999.185, 2459028.392], decimal=3)


def test_get_previous_solstice():
  solstice = zodiac.get_previous_solstice_month_span(jd=time.ist_timezone.local_time_to_julian_day(Date(2018, 1, 14)))
  expected_jd_start = time.ist_timezone.local_time_to_julian_day(date=Date(year=2017, month=12, day=21, hour=16, minute=28))
  numpy.testing.assert_approx_equal(solstice.jd_start, expected_jd_start, significant=4)

  solstice = zodiac.get_previous_solstice_month_span(jd=time.ist_timezone.local_time_to_julian_day(Date(2018, 3, 14)))
  expected_jd_start = time.ist_timezone.local_time_to_julian_day(date=Date(year=2017, month=12, day=21, hour=16, minute=28))
  numpy.testing.assert_approx_equal(solstice.jd_start, expected_jd_start, significant=4)

  solstice = zodiac.get_previous_solstice_month_span(jd=time.ist_timezone.local_time_to_julian_day(Date(2018, 7, 14)))
  expected_jd_start = time.ist_timezone.local_time_to_julian_day(date=Date(year=2018, month=6, day=20, hour=21, minute=44))
  numpy.testing.assert_approx_equal(solstice.jd_start, expected_jd_start, significant=4)
