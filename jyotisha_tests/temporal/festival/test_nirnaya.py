""" Tests for the `nirnaya` hook (festival.nirnaya): rules that name a decision procedure are kept out of the generic
engines and dispatched to that procedure. The upAkarma procedure's dates are covered by the stored annual outputs in
jyotisha_tests/spatio_temporal (unchanged by its move from the hand-coded applier). """

import pytest

from jyotisha.panchaanga.temporal.festival import nirnaya, rules
from jyotisha.panchaanga.temporal.festival.nirnaya import upaakarma


UPAAKARMA_IDS = ['RgvEda-upAkarma', 'yajurvEda-upAkarma', 'bOdhAyana-yajurvEda-upAkarma', 'zukla-yajurvEda-upAkarma',
                 'sAmavEda-upAkarma']


def _rule_set():
  return rules.RulesCollection.get_cached(repos_tuple=rules.rule_repos)


def _make_rule(nirnaya_name="upaakarma", options=None):
  rule = rules.HinduCalendarEvent(id="test-nirnaya-rule")
  rule.timing = rules.HinduCalendarEventTiming()
  rule.timing.month_type = "lunar_month"
  rule.timing.month_number = 5
  rule.timing.anga_type = "tithi"
  rule.timing.anga_number = 15
  rule.timing.nirnaya = nirnaya_name
  rule.timing.nirnaya_options = options
  return rule


def test_nirnaya_rule_is_stored_outside_timing_tree():
  rule = _make_rule()
  # Not under lunar_month/tithi/05/15, where apply_month_anga_events would find it.
  assert rule.get_storage_file_name(base_dir="base", undo_conversions=False) == "base/nirnaya/test-nirnaya-rule.toml"


def test_upaakarma_rules_are_dispatched_not_tree_indexed():
  rule_set = _rule_set()
  for fest_id in UPAAKARMA_IDS:
    rule = rule_set.name_to_rule[fest_id]
    assert rule.timing.nirnaya == "upaakarma"
    assert rule.path_actual.endswith("/nirnaya/%s.toml" % fest_id)
    assert rule.timing.nirnaya in nirnaya.get_procedures()
  # The primary slot of the (kRSNa) yajurvEda upAkarma -- zrAvaNa pUrNimA -- must not list it for the generic engine.
  purnima_fests = rule_set.get_month_anga_fests(month_type="lunar_month", month=5, anga_type_id="tithi", anga=15)
  assert not set(UPAAKARMA_IDS) & set(purnima_fests)


def test_upaakarma_options_from_toml():
  rule_set = _rule_set()
  bodhaayana = upaakarma._get_candidates(rule_set.name_to_rule['bOdhAyana-yajurvEda-upAkarma'])
  yajus = upaakarma._get_candidates(rule_set.name_to_rule['yajurvEda-upAkarma'])
  # Same primary (zrAvaNa pUrNimA at madhyAhna, paraviddha), fall-back months in the opposite order.
  assert [(c.month_number, c.anga_type, c.anga_number) for c in bodhaayana] == [(5, 'tithi', 15), (4, 'tithi', 15), (6, 'tithi', 15)]
  assert [c.month_number for c in yajus] == [5, 6, 4]
  assert all(c.kaala == 'मध्याह्नः' and c.priority == 'paraviddha' for c in bodhaayana + yajus)
  rgveda = upaakarma._get_candidates(rule_set.name_to_rule['RgvEda-upAkarma'])
  assert [(c.month_number, c.anga_type, c.anga_number, c.kaala) for c in rgveda] == [
    (5, 'nakshatra', 22, 'मैत्रः'), (6, 'tithi', 5, 'मध्याह्नः'), (4, 'tithi', 5, 'मध्याह्नः')]


class _FakeAssigner(object):
  panchaanga = None


@pytest.mark.parametrize("options", [
  {"maudhya_graha": "pluto", "on_flaw": "keep"},
  {"maudhya_graha": "zukra", "on_flaw": "sometimes"},
  None,
])
def test_upaakarma_rejects_bad_options(options):
  with pytest.raises(ValueError):
    upaakarma.UpaakarmaDecider(assigner=_FakeAssigner(), rule=_make_rule(options=options))
