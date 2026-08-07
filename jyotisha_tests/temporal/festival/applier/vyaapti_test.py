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
