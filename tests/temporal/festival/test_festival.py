import os

from jyotisha.panchaanga.temporal import festival


def test_serializability():
  festival_instance = festival.FestivalInstance(id="test_fest", days=[])
  festival_instance.dump_to_file(filename=os.path.join(os.path.dirname(__file__), "test_fest.json.local"))