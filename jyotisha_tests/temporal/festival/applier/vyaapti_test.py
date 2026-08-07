from jyotisha.panchaanga.spatio_temporal import City, periodical
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.temporal.time import Date

chennai = City.get_city_from_db('Chennai')


def test_vyaapti_moves_to_day2_when_both_days_fully_cover_kaala():
  # 2028, Chennai: the amAvAsyA tithi is unusually long (~26.7 hours) and fully covers aparaahna on
  # both 2028-02-24 and 2028-02-25. decide_vyaapti's true-duration tie-break (AngaSpanFinder-based)
  # favors 2028-02-25 by a small margin; the assignment must land there, not on 2028-02-24 merely
  # because that day was reached first in the day-by-day scan (see _should_assign_festival's former
  # unconditional "yesterday already assigned" guard for priority='vyaapti').
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2028, 2, 20), end_date=Date(2028, 2, 28), computation_system=computation_system)

  day24 = panchaanga.date_str_to_panchaanga[Date(2028, 2, 24).get_date_str()]
  day25 = panchaanga.date_str_to_panchaanga[Date(2028, 2, 25).get_date_str()]

  main_amavasya_24 = [k for k in day24.festival_id_to_instance if 'mAgha-amAvAsyA' in k and 'bOdhAyana' not in k]
  main_amavasya_25 = [k for k in day25.festival_id_to_instance if 'mAgha-amAvAsyA' in k and 'bOdhAyana' not in k]

  assert main_amavasya_24 == []
  assert main_amavasya_25 != []


def test_vyaapti_does_not_shift_onto_spurious_tail_bleed():
  # 2020, Chennai: manvAdiH~(uttamaH~[3]) (priority='vyaapti', kaala='aparaahna', tithi 3) is
  # unambiguously assigned to 2020-03-27 via the "d0 fully covers, d1 trails past q" boundary-touch
  # branch. The very next day-pair (2020-03-27, 2020-03-28) independently re-detects the tail end of
  # that same tithi transition via a different branch of decide_vyaapti (2020-03-27 touches q only at
  # its own kaala's start, having transitioned in from the previous day, so its own trailing edge into
  # r during 2020-03-28's kaala looks -- in isolation -- like 2020-03-28 has some claim too). This must
  # NOT be allowed to delete the correct 2020-03-27 assignment: apply_month_anga_events's direct
  # vyaapti-duration re-comparison between the two adjacent days (2020-03-27's near-total kaala
  # coverage vs. 2020-03-28's sliver) must keep 2020-03-27, unlike the genuine tie case covered by
  # test_vyaapti_moves_to_day2_when_both_days_fully_cover_kaala.
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2020, 3, 20), end_date=Date(2020, 4, 1), computation_system=computation_system)

  festival_name = 'manvAdiH~(uttamaH~[3])'
  assert panchaanga.festival_id_to_days[festival_name] == {Date(2020, 3, 27)}

  day28 = panchaanga.date_str_to_panchaanga[Date(2020, 3, 28).get_date_str()]
  assert festival_name not in day28.festival_id_to_instance
