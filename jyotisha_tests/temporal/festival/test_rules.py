from pprint import pprint

from sanskrit_data import collection_helper

from jyotisha.panchaanga.temporal.festival import rules


def test_rules_dicts():
  rule_set = rules.RulesCollection.get_cached(repos_tuple=rules.rule_repos)
  pprint(rule_set)
  assert 'pUrNimA~vratam' in rule_set.tree[rules.RulesRepo.LUNAR_MONTH_DIR][rules.RulesRepo.TITHI_DIR]["00"]["15"]


def test_get_url():
  rule_set = rules.RulesCollection.get_cached(repos_tuple=rules.rule_repos)
  assert rule_set.tree[rules.RulesRepo.GREGORIAN_MONTH_DIR][rules.RulesRepo.DAY_DIR]["02"]["09"]["proklas-janma"][collection_helper.LEAVES_KEY][0].get_url() == "https://github.com/jyotisham/adyatithi/blob/master/mahApuruSha/general-indic-tropical/julian/day/02/08/proklas-janma.toml"
