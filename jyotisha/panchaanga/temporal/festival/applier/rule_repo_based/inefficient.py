import logging

from jyotisha.panchaanga.temporal import Anga
from jyotisha.panchaanga.temporal.festival import rules, priority_decision
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from timebudget import timebudget


class FestivalsTimesDaysAssigner(FestivalAssigner):

  @timebudget
  def assign_festivals_from_rules(self):
    # ASSIGN ALL FESTIVALS FROM adyatithi submodule
    # festival_rules = get_festival_rules_dict(os.path.join(CODE_ROOT, 'panchaanga/data/festival_rules_test.json'))
    def to_be_assigned(x):
      if x.timing is None or x.timing.month_type is None:
        # Maybe only description of the festival is given, as computation has been
        # done in computeFestivals(), without using a rule in festival_rules.json!
        return False

      if x.timing.month_type == rules.RulesRepo.SIDEREAL_SOLAR_MONTH_DIR and x.timing.anga_type in (rules.RulesRepo.DAY_DIR, rules.RulesRepo.TITHI_DIR, rules.RulesRepo.YOGA_DIR):
        return False

      # if x.timing.month_type == rules.RulesRepo.LUNAR_MONTH_DIR and x.timing.anga_type in (rules.RulesRepo.TITHI_DIR):
      #   return False

      return True
    festival_rules_dict = {k: v for k, v in self.rules_collection.name_to_rule.items() if to_be_assigned(v)}
    # assert "naTarAjar mahAbhiSEkam~2" not in festival_rules_dict
    # assert "kar2pagAmbAL–kapAlIzvarar tirukkalyANam" in festival_rules_dict


    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + 1):
      for rule in festival_rules_dict.values():
        self.assign_festival(fest_rule=rule, d=d)

  @timebudget
  def assign_festival(self, fest_rule, d):
    festival_name = fest_rule.id
    month_type = fest_rule.timing.month_type
    month_num = fest_rule.timing.month_number
    anga_type = fest_rule.timing.anga_type
    anga_num = fest_rule.timing.anga_number
    if month_type is None or month_num is None or anga_type is None or anga_num is None:
      return


    if anga_type == 'tithi' and month_type == 'lunar_month' and anga_num == 1:
      # Shukla prathama tithis need to be dealt carefully, if e.g. the prathama tithi
      # does not touch sunrise on either day (the regular check won't work, because
      # the month itself is different the previous day!)
      if self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise.index == 30 and self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise.index == 2 and \
          self.daily_panchaangas[d + 1].lunar_month_sunrise.index == month_num:
        # Only in this case, we have a problem
        self.festival_id_to_days[festival_name].add(self.daily_panchaangas[d].date)
        return

    if (month_type == 'lunar_month' and ((self.daily_panchaangas[d].lunar_month_sunrise.index == month_num or month_num == 0) or (
        (self.daily_panchaangas[d + 1].lunar_month_sunrise.index == month_num and anga_num == 1)))) or \
        (month_type == 'sidereal_solar_month' and (self.daily_panchaangas[d].solar_sidereal_date_sunset.month == month_num or month_num == 0)):
      self.assign_tithi_yoga_nakshatra_fest(fest_rule=fest_rule, d=d)

  @timebudget
  def assign_tithi_yoga_nakshatra_fest(self, fest_rule, d):
    """
    
    Tithi yoga and nakShatra have roughly day-long duration. So we can have one method to deal with them.
    """
    festival_name = fest_rule.id
    month_type = fest_rule.timing.month_type
    month_num = fest_rule.timing.month_number
    anga_type_str = fest_rule.timing.anga_type
    target_anga = Anga.get_cached(index=fest_rule.timing.anga_number, anga_type_id=anga_type_str.upper())
    if month_type is None or month_num is None or anga_type_str is None or target_anga is None:
      raise ValueError(str(fest_rule))
    kaala = fest_rule.timing.get_kaala()
    priority = fest_rule.timing.get_priority()

    anga_type = target_anga.get_type()
    prev_anga = target_anga - 1
    anga_sunrise = self.daily_panchaangas[d].sunrise_day_angas.get_angas_with_ends(anga_type=anga_type)[0].anga

    fday = None

    if anga_sunrise == prev_anga or anga_sunrise == target_anga:
      # Some error, e.g. weird kaala, so skip festival
      p0 = self.daily_panchaangas[d]
      p1 = self.daily_panchaangas[d+1]
      d_offset = priority_decision.decide(p0=p0, p1=p1, target_anga=target_anga, kaala=kaala, ayanaamsha_id=self.ayanaamsha_id, priority=priority)
      if d_offset is not None:
        if priority not in ('puurvaviddha', 'vyaapti'):
          fday = d + d_offset
        elif self.daily_panchaangas[d-1].date not in self.panchaanga.festival_id_to_days.get(festival_name, []):
          # puurvaviddha or vyaapti fest. More careful condition.
          fday = d + d_offset
        # else:
        #   if d0_angas.start > target_anga:
        #     logging.info("vyApti, %s: %s, %s, %s.", festival_name, str(d0_angas.to_tuple()), str(d1_angas.to_tuple()), str(target_anga.index))
      else:
        logging.error('Unknown priority "%s" for %s! Check the rules!' % (priority, festival_name))

    if fday is not None:
      if (month_type == 'lunar_month' and ((self.daily_panchaangas[d].lunar_month_sunrise.index == month_num or month_num == 0) or (
          (self.daily_panchaangas[d + 1].lunar_month_sunrise.index == month_num and target_anga.index == 1)))) or \
          (month_type == 'sidereal_solar_month' and (
              self.daily_panchaangas[fday].solar_sidereal_date_sunset.month == month_num or month_num == 0)):
        # If month on fday is incorrect, we ignore and move.
        if month_type == 'lunar_month' and target_anga.index == 1 and self.daily_panchaangas[
          fday + 1].lunar_month_sunrise.index != month_num:
          return
          # if festival_name.find('\\') == -1 and \
        #         'kaala' in fest_rule and \
        #         festival_rules[festival_name].timing.kaala == 'arunodaya':
        #     fday += 1
        if self.daily_panchaangas[d-1].date in self.panchaanga.festival_id_to_days.get(festival_name, []):
          # No festival occurs on consecutive days; paraviddha assigned twice
          logging.warning(
            '%s occurring on two consecutive days (%d, %d). Removing! paraviddha assigned twice?' % (
              festival_name, d - 1, d))
          self.panchaanga.festival_id_to_days[festival_name].remove(self.daily_panchaangas[d-1].date)

        self.festival_id_to_days[festival_name].add(self.daily_panchaangas[fday].date)