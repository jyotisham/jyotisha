from jyotisha.panchaanga.spatio_temporal import City, periodical
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.temporal.festival.applier.tithi_festival import TithiFestivalAssigner
from jyotisha.panchaanga.temporal.time import Date

chennai = City.get_city_from_db('Chennai')

VINAYAKA_CHATURTHI = 'zrIvinAyaka-caturthI'


def test_check_vinayaka_chaturthi_overrules_for_full_day2_vyaapti():
  # 2023, Chennai: caturthI touches 2023-09-18's madhyaahna only at its end, but fully covers
  # 2023-09-19's madhyaahna and extends into 2023-09-19's aparaahna -- the traditional "puurna
  # vyaapti of day 2" exception, which should overrule a default (puurvaviddha, prefer day 1)
  # pick of day 1 to day 2.
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2023, 9, 15), end_date=Date(2023, 9, 21), computation_system=computation_system)
  assigner = TithiFestivalAssigner(panchaanga=panchaanga)

  # Simulate the generic engine's base decision (kaala="madhyaahna", priority="puurvaviddha"),
  # which -- absent the full-vyaapti exception -- would have picked day 1.
  panchaanga.festival_id_to_days[VINAYAKA_CHATURTHI] = {Date(2023, 9, 18)}
  assigner.check_vinayaka_chaturthi()
  assert panchaanga.festival_id_to_days[VINAYAKA_CHATURTHI] == {Date(2023, 9, 19)}


def test_check_vinayaka_chaturthi_no_op_without_full_day2_vyaapti():
  # 2027, Chennai: caturthI never touches 2027-09-03's madhyaahna at all (it begins only within
  # 2027-09-03's aparaahna), and only partially touches 2027-09-04's madhyaahna, ending before
  # 2027-09-04's aparaahna begins. Day 2 (2027-09-04, already correctly picked by the base
  # decision since only it touches madhyaahna) should not be moved further by the override.
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2027, 9, 1), end_date=Date(2027, 9, 7), computation_system=computation_system)
  assigner = TithiFestivalAssigner(panchaanga=panchaanga)

  panchaanga.festival_id_to_days[VINAYAKA_CHATURTHI] = {Date(2027, 9, 4)}
  assigner.check_vinayaka_chaturthi()
  assert panchaanga.festival_id_to_days[VINAYAKA_CHATURTHI] == {Date(2027, 9, 4)}
