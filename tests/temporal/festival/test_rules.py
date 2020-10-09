from pprint import pprint

from jyotisha.panchaanga.temporal.festival import rules


def test_rules_dicts():
  rule_set = rules.RulesCollection()
  pprint(rule_set)
  assert 'pUrNimA~vratam' in rule_set.tree[rules.RulesRepo.LUNAR_MONTH_DIR][rules.RulesRepo.TITHI_DIR]["00"]["15"]