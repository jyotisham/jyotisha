from jyotisha.panchaanga.temporal.zodiac import angas
from sanskrit_data.schema import common

# from jyotisha_tests import conftest
pytest_plugins = ["sanskrit_data.testing.pytest_plugin"]


def test_minus():
  a1 = angas.Anga.get_cached(index=27, anga_type_id=angas.AngaType.NAKSHATRA.name)
  a2 = angas.Anga.get_cached(index=1, anga_type_id=angas.AngaType.NAKSHATRA.name)
  assert a1 - a2 == -1
  assert a2 - a1 == 1
  assert a1 - 1 == angas.Anga.get_cached(index=26, anga_type_id=angas.AngaType.NAKSHATRA.name)
  assert a2 - 1 == a1
  assert a1 + 1 == a2
  assert str(a1 + .5) == str(angas.Anga.get_cached(index=0.5, anga_type_id=angas.AngaType.NAKSHATRA.name))
  a1 = angas.Anga.get_cached(index=1, anga_type_id=angas.AngaType.RASHI.name)
  assert a1 - 1 == angas.Anga.get_cached(index=12, anga_type_id=angas.AngaType.RASHI.name)


def test_degree_minus():
  a1 = angas.Anga.get_cached(index=26, anga_type_id=angas.AngaType.DEGREE.name)
  a2 = angas.Anga(index=1, anga_type_id=angas.AngaType.DEGREE.name)
  assert a1 - a2 == 25

  a2 = angas.Anga(index=359, anga_type_id=angas.AngaType.DEGREE.name)
  assert a1 - a2 == 27
  assert a2 - a1 == -27

  a2 = angas.Anga(index=359.5, anga_type_id=angas.AngaType.DEGREE.name)
  assert a1 - a2 == 26.5

def test_comparison():
  a1 = angas.Anga.get_cached(index=27, anga_type_id=angas.AngaType.NAKSHATRA.name)
  a3 = angas.Anga.get_cached(index=27, anga_type_id=angas.AngaType.NAKSHATRA.name)
  a2 = angas.Anga.get_cached(index=1, anga_type_id=angas.AngaType.NAKSHATRA.name)
  assert a1 < a2
  assert a1 == a3


def test_hashability():
  a1 = angas.Anga.get_cached(index=27, anga_type_id=angas.AngaType.NAKSHATRA.name)
  a3 = angas.Anga.get_cached(index=27, anga_type_id=angas.AngaType.NAKSHATRA.name)
  a2 = angas.Anga.get_cached(index=1, anga_type_id=angas.AngaType.NAKSHATRA.name)
  set([a1, a2, a3])


def test_get_name():
  a1 = angas.Anga.get_cached(index=27, anga_type_id=angas.AngaType.NAKSHATRA.name)
  a2 = angas.Anga.get_cached(index=1, anga_type_id=angas.AngaType.NAKSHATRA.name)
  assert a1.get_name() == "rEvatI"
  assert a2.get_name() == "azvinI"
