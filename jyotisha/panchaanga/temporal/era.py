ERA_GREGORIAN = "gregorian"
ERA_KALI = "kali"
ERA_SHAKA = "shaka"
ERA_VIKRAMA = "vikrama"
ERA_BENGALI = "vanga"
ERA_KOLLAM = "kollam"
ERA_BUDDHA = "buddha"
ERA_MAHAVIRA = "mahAvIra"
ERA_TIPU_MAULUDI = "TipU-maulUdI"


def get_year_0_offset(era_id):
  year_0_offset = None
  if era_id == ERA_GREGORIAN:
    year_0_offset = 0
  elif era_id == ERA_SHAKA:
    year_0_offset = -78
  elif era_id == ERA_KALI:
    # 5121 year begins Apr. 2020
    year_0_offset = 3101
  elif era_id == ERA_VIKRAMA:
    year_0_offset = 57
  elif era_id == ERA_BENGALI:
    year_0_offset = -593
  elif era_id == ERA_KOLLAM:
    year_0_offset = 1196 - 2020
  elif era_id == ERA_BUDDHA:
    year_0_offset = 2564 - 2020
  elif era_id == ERA_MAHAVIRA:
    year_0_offset = 2547 - 2020
  elif era_id == ERA_TIPU_MAULUDI:
    year_0_offset = -572
  return year_0_offset
