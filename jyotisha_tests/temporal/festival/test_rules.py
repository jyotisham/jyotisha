import codecs
import os
from pprint import pprint

from indic_transliteration import sanscript
from jyotisha.panchaanga.temporal import RulesCollection, RulesRepo
from jyotisha.panchaanga.temporal.festival import rules
from jyotisha.panchaanga.temporal.festival.rules import summary


def test_rules_dicts():
  rule_set = rules.RulesCollection.get_cached(repos_tuple=rules.rule_repos)
  pprint(rule_set)
  assert 'pUrNimA~vratam' in rule_set.tree[rules.RulesRepo.LUNAR_MONTH_DIR][rules.RulesRepo.TITHI_DIR]["00"]["15"]


def test_get_url():
  rule_set = rules.RulesCollection.get_cached(repos_tuple=rules.rule_repos)
  assert rule_set.tree[rules.RulesRepo.GREGORIAN_MONTH_DIR][rules.RulesRepo.DAY_DIR]["02"]["09"]["proklas-janma"].get_url() == "https://github.com/jyotisham/adyatithi/blob/master/mahApuruSha/general-tropical/julian/day/02/08/proklas-janma.toml"


def test_describe_fest():
  rule_set = RulesCollection(repos=[RulesRepo(name="gRhya/Apastamba")], julian_handling=None)
  # rule_set = rules.RulesCollection.get_cached(repos_tuple=rules.rule_repos)
  expected_md_file = os.path.join(os.path.dirname(__file__), 'data/taittirIya-utsargaH_paurNamAsyAm.md')
  with codecs.open(expected_md_file, "r", "utf-8") as f:
    summary_md = summary.describe_fest(rule=rule_set.name_to_rule["taittirIya-utsargaH_paurNamAsyAm"], include_images=False, include_shlokas=False, include_url=False, is_brief=False, script=sanscript.DEVANAGARI, truncate=False, header_md="#####")
    print(summary_md)
    assert summary_md == f.read()
