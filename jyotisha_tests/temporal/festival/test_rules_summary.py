import os
import codecs
from indic_transliteration import sanscript
from jyotisha.panchaanga.temporal import RulesCollection, RulesRepo
from jyotisha.panchaanga.temporal.festival.rules import summary


def test_describe_fest():
  rule_set = RulesCollection(repos=[RulesRepo(name="test_repo", path=os.path.join(os.path.dirname(__file__), 'data/test_repo'))], julian_handling=None)

  # rule_set = rules.RulesCollection.get_cached(repos_tuple=rules.rule_repos)
  expected_md_file = os.path.join(os.path.dirname(__file__), 'data/taittirIya-utsargaH_paurNamAsyAm.md')
  with codecs.open(expected_md_file, "r", "utf-8") as f:
    summary_md = summary.describe_fest(rule=rule_set.name_to_rule["taittirIya-utsargaH_paurNamAsyAm"], include_images=False, include_shlokas=False, include_url=False, is_brief=False, script=sanscript.DEVANAGARI, truncate=False, header_md="#####")
    expected_md = f.read()
    if summary_md != expected_md:
      with codecs.open(expected_md_file + ".local", "w", "utf-8") as g:
        g.write(summary_md)
    assert summary_md == expected_md

  expected_md_file = os.path.join(os.path.dirname(__file__), 'data/throchi-durge_goraxa-sainika-nighAtaH.md')
  with codecs.open(expected_md_file, "r", "utf-8") as f:
    summary_md = summary.describe_fest(rule=rule_set.name_to_rule["throchi-durge_goraxa-sainika-nighAtaH"], include_images=False, include_shlokas=False, include_url=False, is_brief=False, script=sanscript.DEVANAGARI, truncate=False, header_md="#####")
    expected_md = f.read()
    if summary_md != expected_md:
      with codecs.open(expected_md_file + ".local", "w", "utf-8") as g:
        g.write(summary_md)
    assert summary_md == expected_md

