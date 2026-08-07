from jyotisha.panchaanga.spatio_temporal import City, periodical
from jyotisha.panchaanga.temporal import Anga, AngaType, ComputationSystem
from jyotisha.panchaanga.temporal.festival import priority_decision
from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.temporal.time import Date
from jyotisha.panchaanga.temporal.zodiac.angas import BoundaryAngas

chennai = City.get_city_from_db('Chennai')


def test_compare_vyaapti_duration_aparaahna_full_coverage_always_picks_day2():
  # When both days fully cover aparaahna, practice (this is typically a shraaddha-type observance)
  # is to always prefer the second day outright -- not compare true durations, and not lean on
  # day-length (ahas) trend, since ahas only increases toward day 2 for part of the year. Construct a
  # synthetic case where day 2's kaala is the *shorter* of the two (ahas decreasing) to confirm the
  # day-length trend is genuinely ignored, not coincidentally matching it.
  target = Anga.get_cached(index=30, anga_type_id=AngaType.TITHI.name)
  d0 = BoundaryAngas(start=target, end=target, interval=Interval(jd_start=100.80, jd_end=100.90, name='अपराह्णः'))
  d1 = BoundaryAngas(start=target, end=target, interval=Interval(jd_start=101.79, jd_end=101.88, name='अपराह्णः'))  # shorter than d0's kaala
  assert priority_decision.compare_vyaapti_duration(d0_angas=d0, d1_angas=d1, target_anga=target, ayanaamsha_id=1) == 1


def test_vyaapti_moves_to_day2_when_both_days_fully_cover_kaala():
  # 2028, Chennai: the amAvAsyA tithi is unusually long (~26.7 hours) and fully covers aparaahna on
  # both 2028-02-24 and 2028-02-25. Per the rule above (aparaahna, both days fully covering -> always
  # day 2), the assignment must land on 2028-02-25, not on 2028-02-24 merely because that day was
  # reached first in the day-by-day scan (see _should_assign_festival's former unconditional
  # "yesterday already assigned" guard for priority='vyaapti').
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2028, 2, 20), end_date=Date(2028, 2, 28), computation_system=computation_system)

  day24 = panchaanga.date_str_to_panchaanga[Date(2028, 2, 24).get_date_str()]
  day25 = panchaanga.date_str_to_panchaanga[Date(2028, 2, 25).get_date_str()]

  main_amavasya_24 = [k for k in day24.festival_id_to_instance if 'mAgha-amAvAsyA' in k and 'bOdhAyana' not in k]
  main_amavasya_25 = [k for k in day25.festival_id_to_instance if 'mAgha-amAvAsyA' in k and 'bOdhAyana' not in k]

  assert main_amavasya_24 == []
  assert main_amavasya_25 != []


def test_vyaapti_does_not_shift_onto_spurious_tail_bleed():
  # 2020, Chennai: manvAdiH~(uttamaH~[3]) (priority='vyaapti', kaala='aparaahna', tithi 3). 2020-03-26's
  # aparaahna doesn't touch tithi 3 at all; 2020-03-27's fully covers it (d0 doesn't touch, d1 fully
  # covers -> decide_vyaapti unambiguously picks 2020-03-27, no tiebreak needed). 2020-03-28's aparaahna
  # is already fully into tithi 4 -- decide_vyaapti((2020-03-27, 2020-03-28)) correctly re-confirms
  # 2020-03-27 on its own (2020-03-27 fully covers its own kaala while 2020-03-28 doesn't touch tithi 3
  # at all), so this specific date doesn't exercise apply_month_anga_events's adjacent-conflict
  # resolution -- decide_vyaapti's own branches already agree end-to-end. Kept as an end-to-end sanity
  # check (a hypothetical case with a genuine "partial touch mistaken for a claim" boundary pattern
  # would instead need the conflict resolution in apply_month_anga_events, exercised more directly by
  # test_compare_vyaapti_duration_aparaahna_full_coverage_always_picks_day2 for the full-coverage case).
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2020, 3, 20), end_date=Date(2020, 4, 1), computation_system=computation_system)

  festival_name = 'manvAdiH~(uttamaH~[3])'
  assert panchaanga.festival_id_to_days[festival_name] == {Date(2020, 3, 27)}

  day28 = panchaanga.date_str_to_panchaanga[Date(2020, 3, 28).get_date_str()]
  assert festival_name not in day28.festival_id_to_instance
