#!/usr/bin/python3
import jyotisha
from jyotisha.panchaanga.temporal import interval, time, ComputationSystem, FestivalOptions, names
from jyotisha.panchaanga.temporal.festival import rules
from jyotisha.panchaanga.spatio_temporal import annual
from jyotisha.panchaanga.temporal.festival.rules import RulesRepo
from jyotisha.panchaanga.spatio_temporal import City
city = City.get_city_from_db("Chennai")
year = int(5123)

computation_system = ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180
computation_system.festival_options = FestivalOptions(fest_repos = [RulesRepo(name="devatA/gaNapati"), RulesRepo(name="devatA/graha"), RulesRepo(name="devatA/kaumAra"), RulesRepo(name="devatA/lakShmI"), RulesRepo(name="devatA/misc-fauna"), RulesRepo(name="devatA/misc-flora"), RulesRepo(name="devatA/nadI"), RulesRepo(name="devatA/pitR"), RulesRepo(name="devatA/shaiva"), RulesRepo(name="devatA/shakti"), RulesRepo(name="devatA/dashamahAvidyA"), RulesRepo(name="devatA/umA"), RulesRepo(name="devatA/vaiShNava"), RulesRepo(name="gRhya/Apastamba"), RulesRepo(name="gRhya/general"), RulesRepo(name="general"), RulesRepo(name="mahApuruSha/ALvAr"), RulesRepo(name="mahApuruSha/general-indic-non-tropical"), RulesRepo(name="mahApuruSha/RShi"), RulesRepo(name="mahApuruSha/kAnchI-maTha"), RulesRepo(name="mahApuruSha/zRGgErI-maTha"), RulesRepo(name="mahApuruSha/mAdhva-misc"), RulesRepo(name="mahApuruSha/nAyanAr"), RulesRepo(name="mahApuruSha/sangIta-kRt"), RulesRepo(name="mahApuruSha/smArta-misc"), RulesRepo(name="mahApuruSha/vaiShNava-misc"), RulesRepo(name="mahApuruSha/xatra"), RulesRepo(name="tamil"), RulesRepo(name="temples/Andhra"), RulesRepo(name="temples/Kerala"), RulesRepo(name="temples/North"), RulesRepo(name="temples/Odisha"), RulesRepo(name="temples/Tamil"), RulesRepo(name="temples/venkaTAchala"), RulesRepo(name="time_focus/Eclipses"), RulesRepo(name="time_focus/amrita-siddhi"), RulesRepo(name="time_focus/Rtu"), RulesRepo(name="time_focus/misc"), RulesRepo(name="time_focus/misc_combinations"), RulesRepo(name="time_focus/special-tithis"), RulesRepo(name="time_focus/tithi-vara-combinations"), RulesRepo(name="time_focus/monthly/amAvAsyA"), RulesRepo(name="time_focus/monthly/dvAdashI"), RulesRepo(name="time_focus/monthly/ekAdashI"), RulesRepo(name="time_focus/monthly/pradoSha"), RulesRepo(name="time_focus/nakShatra"), RulesRepo(name="time_focus/puShkara"), RulesRepo(name="time_focus/sankrAnti"), RulesRepo(name="time_focus/yugAdiH")])
panchaanga = annual.get_panchaanga_for_kali_year(city=city, year=year, computation_system=computation_system)
rules_collection = rules.RulesCollection.get_cached(repos_tuple=tuple(panchaanga.computation_system.festival_options.repos))
rules_collection.fix_filenames()
