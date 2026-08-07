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
