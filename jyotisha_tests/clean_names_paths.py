#!/usr/bin/env python
import jyotisha
from jyotisha.panchaanga.temporal import interval, time, ComputationSystem, FestivalOptions, names
from jyotisha.panchaanga.temporal.festival import rules
from jyotisha.panchaanga.spatio_temporal import annual
from jyotisha.panchaanga.temporal.festival.rules import RulesRepo
from jyotisha.panchaanga.spatio_temporal import City
city = City.get_city_from_db("Chennai")
year = int(5123)

computation_system = ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA__CHITRA_180
fest_repos_excluded_patterns = [".*xatra-later", ".*general-indic-tropical", ".*devIparva", ".*zRGgErI.*", ".*sci-tech.*", "gRhya/Apastamba_seasonal"]
computation_system.festival_options = FestivalOptions(tropical_month_start="madhu_at_equinox", fest_repos_excluded_patterns = fest_repos_excluded_patterns)
panchaanga = annual.get_panchaanga_for_kali_year(city=city, year=year, computation_system=computation_system)
rules_collection = rules.RulesCollection.get_cached(repos_tuple=tuple(panchaanga.computation_system.festival_options.repos))
rules_collection.fix_filenames()
