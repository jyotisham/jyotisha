import os

from indic_transliteration import sanscript
from jyotisha.panchaanga.temporal import festival, ComputationOptions
from jyotisha.panchaanga.temporal.festival import rules


def test_serializability():
  festival_instance = festival.FestivalInstance(name="test_fest")
  festival_instance.dump_to_file(filename=os.path.join(os.path.dirname(__file__), "test_fest.json.local"))


def test_get_best_transliterated_name():
  options = ComputationOptions()
  rules_collection = rules.RulesCollection.get_cached(repos=tuple(options.fest_repos))

  fest = festival.FestivalInstance(name="rAmAnuja-janma-nakSatram", ordinal=1000)
  name = fest.get_best_transliterated_name(scripts=[sanscript.DEVANAGARI, sanscript.TAMIL],
                                           fest_details_dict=rules_collection.name_to_rule)
  assert name["text"] == "रामानुज-जन्म-नक्षत्रम्"
