from jyotisha.panchaanga.spatio_temporal import City, periodical
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.temporal.time import Date

chennai = City.get_city_from_db('Chennai')


def test_paraviddha_settles_to_single_day_without_relying_on_post_hoc_cleanup():
  # 2018, Chennai: piNDa-pitR-yajJaH (priority='paraviddha', tithi 30/amAvAsyA, month_number=0 -- recurs
  # every lunar month). Before the look-ahead fix, this genuinely straddled two adjacent days (the anga
  # touched the kaala on both 2018-01-17 and 2018-01-18), so decide_paraviddha's own pairwise result
  # committed *both* days, and only FestivalAssigner.cleanup_festivals's post-hoc "remove paraviddha
  # assigned on consecutive days" pass (which always keeps the later of the two) cleaned it up to
  # 2018-01-17 in a second pass. With the look-ahead in apply_month_anga_events, 2018-01-17's commit is
  # deferred until the (17, 18) pairing settles it directly, so only 2018-01-17 is ever committed --
  # matching the same final answer, without a delete-and-reassign round trip.
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2018, 1, 12), end_date=Date(2018, 1, 21), computation_system=computation_system)

  festival_name = 'piNDa-pitR-yajJaH'
  assert panchaanga.festival_id_to_days[festival_name] == {Date(2018, 1, 17)}

  day18 = panchaanga.date_str_to_panchaanga[Date(2018, 1, 18).get_date_str()]
  assert festival_name not in day18.festival_id_to_instance


def test_anadhyayana_paraviddha_still_allows_genuine_two_day_straddle():
  # 2019, Chennai: anadhyAyaH~23 (priority='paraviddha', tithi 23/kRSNASTamI, kaala='sAGgavaH',
  # month_number=0). Unlike most paraviddha festivals, anadhyAyaH (non-study day) observances are
  # traditionally kept on *both* days of a genuine straddle, not resolved down to a single day --
  # FestivalAssigner.cleanup_festivals's adjacent-day cleanup has always explicitly excluded
  # 'anadhyAyaH' festivals from its single-day collapsing for this reason. The look-ahead deferral (and
  # its accompanying _should_assign_festival guard) must respect the same exemption, rather than
  # collapsing this genuine two-day case down to just 2019-08-24.
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2019, 8, 20), end_date=Date(2019, 9, 10), computation_system=computation_system)

  festival_name = 'anadhyAyaH~23'
  assert {Date(2019, 8, 23), Date(2019, 8, 24)} <= panchaanga.festival_id_to_days[festival_name]


def test_paraviddha_short_straddle_prefers_second_regardless_of_duration():
  # 2023, Chennai: yama_or_bhrAtR-dvitIyA (priority='paraviddha', tithi 2, kaala='aparAhNa'). dvitIyA
  # touches 2023-11-14's aparAhNa only in its last ~42 minutes (d0.end == target, a bare trailing touch)
  # and 2023-11-15's aparAhNa only in its first ~46 minutes (d1.start == target, before crossing to
  # tritIyA) -- a genuine straddle across both days, not one day exclusively owning it.
  # decide_paraviddha used to special-case d0.end == target_anga unconditionally as "day 1 wins",
  # without checking whether day 2 also had a claim. paraviddha means "touched by what follows" --
  # if the anga touches both days at all, day 2 wins outright, with no regard to which day's touch is
  # longer (unlike vyaapti). See also test_paraviddha_short_straddle_prefers_second_even_when_day_one_dominates.
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2023, 11, 8), end_date=Date(2023, 11, 20), computation_system=computation_system)

  festival_name = 'yama_or_bhrAtR-dvitIyA'
  assert panchaanga.festival_id_to_days[festival_name] == {Date(2023, 11, 15)}


def test_paraviddha_short_straddle_prefers_second_even_when_day_one_dominates():
  # 2018, Chennai: anadhyAyaH~29 (priority='paraviddha', tithi 29/caturdazI, kaala='sAGgavaH'). Unlike
  # the yama_or_bhrAtR-dvitIyA case above, here caturdazI dominates 2018-04-14's sAGgava (~104 of 148
  # minutes) and only brushes the first ~10 minutes of 2018-04-15's sAGgava before crossing to
  # amAvAsyA. paraviddha's "prefer second" rule is not duration-weighted (that's vyaapti's job) --
  # even though day 1's claim is far larger, the festival still moves to 2018-04-15, since the anga
  # touches both days' kaalas at all.
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2018, 4, 10), end_date=Date(2018, 4, 18), computation_system=computation_system)

  festival_name = 'anadhyAyaH~29'
  assert panchaanga.festival_id_to_days[festival_name] == {Date(2018, 4, 15)}


def test_paraviddha_exclusive_trailing_touch_still_resolves_without_d1_claim():
  # 2019, Chennai: zrIrAmanavamI (priority='paraviddha', tithi 9/navamI, kaala='madhyAhna'). navamI
  # touches 2019-04-13's madhyAhna only at its very end (d0.end == target_anga) and 2019-04-14's
  # madhyAhna doesn't touch navamI at all (already dazamI) -- an exclusive, unambiguous claim for
  # day 1, distinct from the genuine-straddle cases above where day 2 also has a claim.
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2019, 4, 8), end_date=Date(2019, 4, 18), computation_system=computation_system)

  festival_name = 'zrIrAmanavamI'
  assert panchaanga.festival_id_to_days[festival_name] == {Date(2019, 4, 13)}


def test_paraviddha_resolves_inline_across_a_month_boundary():
  # 2015, Chennai: tiruvADippUram (priority='paraviddha', sidereal_solar_month=4, nakshatra 11/pUrva-
  # phalgunI, kaala='prAtaH'). decide_paraviddha((2015-08-15, 2015-08-16)) picks 2015-08-16 outright
  # (2015-08-15 doesn't touch nakSatra 11 at all; 2015-08-16 fully covers it). 2015-08-17 also briefly
  # touches nakSatra 11 at its own start, so apply_month_anga_events settles it directly by calling
  # decide_paraviddha((2015-08-16, 2015-08-17)) itself -- which (praatah kaala's "prefer first" rule)
  # confirms 2015-08-16 -- rather than deferring and hoping a later turn resolves it. That would have
  # been unsafe here: 2015-08-17 has already crossed into sidereal_solar_month 5, so
  # _get_relevant_festivals (which filters candidates by month) would never reconsider this month=4
  # festival on 2015-08-17's own turn, losing the assignment outright. An earlier, spurious month=4
  # candidate on 2015-07-20 must also not survive.
  computation_system = ComputationSystem.DEFAULT
  panchaanga = periodical.Panchaanga(city=chennai, start_date=Date(2015, 6, 1), end_date=Date(2015, 12, 1), computation_system=computation_system)

  festival_name = 'tiruvADippUram'
  assert panchaanga.festival_id_to_days[festival_name] == {Date(2015, 8, 16)}
