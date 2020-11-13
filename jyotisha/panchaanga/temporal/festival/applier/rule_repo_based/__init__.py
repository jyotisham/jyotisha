import logging

from jyotisha.panchaanga.temporal import Anga, AngaType
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.festival.rules import RulesRepo


class RuleLookupAssigner(FestivalAssigner):
  def assign_relative_festivals(self):
    # Add "RELATIVE" festival_id_to_instance --- festival_id_to_instance that happen before or
    # after other festival_id_to_instance with an exact timedelta!
    if 'yajurvEda-upAkarma' not in self.panchaanga.festival_id_to_days:
      logging.error('yajurvEda-upAkarma not in festival_id_to_instance!')
    else:
      # Extended for longer calendars where more than one upAkarma may be there
      self.panchaanga.festival_id_to_days['varalakSmI-vratam'] = set()
      for d in self.panchaanga.festival_id_to_days['yajurvEda-upAkarma']:
        self.panchaanga.festival_id_to_days['varalakSmI-vratam'].add(d - ((d.get_weekday() - 5) % 7))
      # self.panchaanga.festival_id_to_days['varalakSmI-vratam'] = [self.panchaanga.festival_id_to_days['yajurvEda-upAkarma'][0] -
      #                                        ((self.panchaanga.weekday_start - 1 + self.panchaanga.festival_id_to_days['yajurvEda-upAkarma'][
      #                                            0] - 5) % 7)]

    name_to_rule = self.rules_collection.name_to_rule

    for festival_name in name_to_rule:
      if name_to_rule[festival_name].timing is None or name_to_rule[festival_name].timing.offset is None:
        continue
      offset = int(name_to_rule[festival_name].timing.offset)
      rel_festival_name = name_to_rule[festival_name].timing.anchor_festival_id
      if rel_festival_name not in self.panchaanga.festival_id_to_days:
        # Check approx. match
        matched_festivals = []
        for fest_key in self.panchaanga.festival_id_to_days:
          if fest_key.startswith(rel_festival_name):
            matched_festivals += [fest_key]
        if matched_festivals == []:
          logging.error('Relative festival %s not in festival_id_to_days!' % rel_festival_name)
        elif len(matched_festivals) > 1:
          logging.error('Relative festival %s not in festival_id_to_days! Found more than one approximate match: %s' % (
            rel_festival_name, str(matched_festivals)))
        else:
          self.panchaanga.festival_id_to_days[festival_name] = set([x + offset for x in self.panchaanga.festival_id_to_days[matched_festivals[0]]])
      else:
        self.panchaanga.festival_id_to_days[festival_name] = set([x + offset for x in self.panchaanga.festival_id_to_days[rel_festival_name]])

  def apply_festival_from_rules_repos(self):
    for index, dp in enumerate(self.daily_panchaangas):
      self.apply_month_day_events(day_panchaanga=dp, month_type=RulesRepo.SIDEREAL_SOLAR_MONTH_DIR)
      self.apply_month_anga_events(day_panchaanga=dp, month_type=RulesRepo.SIDEREAL_SOLAR_MONTH_DIR, anga_type=AngaType.TITHI)
      self.apply_month_anga_events(day_panchaanga=dp, month_type=RulesRepo.SIDEREAL_SOLAR_MONTH_DIR, anga_type=AngaType.NAKSHATRA)
      self.apply_month_anga_events(day_panchaanga=dp, month_type=RulesRepo.SIDEREAL_SOLAR_MONTH_DIR, anga_type=AngaType.YOGA)
      # self.apply_month_anga_events(day_panchaanga=dp, month_type=RulesRepo.LUNAR_MONTH_DIR, anga_type=AngaType.TITHI)

  def apply_month_day_events(self, day_panchaanga, month_type):
    from jyotisha.panchaanga.temporal.festival import rules, FestivalInstance
    rule_set = rules.RulesCollection.get_cached(repos_tuple=tuple(self.computation_system.options.fest_repos))

    date = day_panchaanga.get_date(month_type=month_type)
    fest_dict = rule_set.get_month_anga_fests(month=date.month, anga=date.day, month_type=month_type, anga_type_id=rules.RulesRepo.DAY_DIR)
    for fest_id, fest in fest_dict.items():
      day_panchaanga.festival_id_to_instance[fest_id] = FestivalInstance(name=fest.id)
      self.festival_id_to_days[fest_id].add(day_panchaanga.date)

  def _get_relevant_festivals(self, anga_type, month_type, panchaangas):
    """
    
    :param anga_type: 
    :param month_type: 
    :param panchaangas: Array of panchaangas for 2 successive days 
    :return: 
    """
    from jyotisha.panchaanga.temporal.festival import rules
    rule_set = rules.RulesCollection.get_cached(repos_tuple=tuple(self.computation_system.options.fest_repos))
    anga_type_id = anga_type.name.lower()
    angas_2 = [x.anga for x in panchaangas[1].sunrise_day_angas.get_angas_with_ends(anga_type=anga_type)]
    if anga_type == AngaType.TITHI and angas_2[0].index in (29, 30):
      # We seek festivals based on angas belonging to this month only.
      angas_2 = [anga for anga in angas_2 if anga <= Anga(index=30, anga_type_id=AngaType.TITHI.name)]

    angas_1 = [x.anga for x in panchaangas[0].sunrise_day_angas.get_angas_with_ends(anga_type=anga_type)]
    if anga_type == AngaType.TITHI and angas_2[0].index in (1, 2):
      angas_1 = [anga for anga in angas_1 if anga >= Anga(index=1, anga_type_id=AngaType.TITHI.name)]
    angas = set(angas_2 + angas_1)
    # The filtering above avoids the below case (TODO: Check):
    # When applied to month_type = lunar_sideral and anga_type = tithi, this method (without the check) fails in certain corner cases. Consider the case: target_anga = tithi 1. It appears in the junction with the preceeding month or with the succeeding month. In that case, clearly, the former is salient - tithi 1 in the latter case belongs to the succeeding month. 
    month = panchaangas[1].get_date(month_type=month_type).month

    fest_dict = rule_set.get_possibly_relevant_fests(month=month, angas=angas, month_type=month_type, anga_type_id=anga_type_id)
    return fest_dict

  def _should_assign_festival(self, p_fday, fest_rule):
    if p_fday.date in self.festival_id_to_days[fest_rule.id]:
      # Already assigned (likely in the previous iteration).
      return False

    month_type = fest_rule.timing.month_type
    priority = fest_rule.timing.get_priority()
    fday_date = p_fday.get_date(month_type=month_type)
    if fday_date.month != fest_rule.timing.month_number and fest_rule.timing.month_number != 0:
      # This could legitimately happen in the case indicated in the below clause.
      if not (fday_date.day >= 30 and month_type == RulesRepo.LUNAR_MONTH_DIR):
        # Example: Suppose festival is on tithi 27 of solar siderial month 10; last day of month 9 could have tithi 27, but not day 1 of month 10; though a much later day of month 10 has tithi 27. 
        return False

    return priority not in ('puurvaviddha', 'vyaapti') or \
                      (p_fday.date - 1 not in self.festival_id_to_days[fest_rule.id])

  def apply_month_anga_events(self, day_panchaanga, anga_type, month_type):
    from jyotisha.panchaanga.temporal.festival import priority_decision
    date = day_panchaanga.date
    month = day_panchaanga.get_date(month_type=month_type).month
    
    panchaangas = [self.panchaanga.date_str_to_panchaanga.get((date-2).get_date_str(), None), self.panchaanga.date_str_to_panchaanga.get((date-1).get_date_str(), None), day_panchaanga]
    if panchaangas[1] is None:
      # We require atleast 1 day history.
      return

    fest_dict = self._get_relevant_festivals(panchaangas=panchaangas[1:], anga_type=anga_type, month_type=month_type)
    ###########################
    # Iterate over relevant festivals
    for fest_id, fest_rule in fest_dict.items():
      kaala = fest_rule.timing.get_kaala()
      priority = fest_rule.timing.get_priority()
      anga_type_str = fest_rule.timing.anga_type
      target_anga = Anga.get_cached(index=fest_rule.timing.anga_number, anga_type_id=anga_type_str.upper())
      decision = priority_decision.decide(p0=panchaangas[1], p1=panchaangas[2], target_anga=target_anga, kaala=kaala, ayanaamsha_id=self.ayanaamsha_id, priority=priority)

      if decision is not None:
        fday = decision.fday + 1
        p_fday = panchaangas[fday]
        assign_festival = self._should_assign_festival(p_fday=p_fday, fest_rule=fest_rule)
        if assign_festival:
          if len(self.festival_id_to_days[fest_id]) > 0:
            previous_fest_day = sorted(self.festival_id_to_days[fest_id])[-1]
            p_previous_fday = self.panchaanga.date_str_to_panchaanga[previous_fest_day.get_date_str()]
            if p_fday.date - previous_fest_day <= 31 and p_previous_fday.get_date(month_type=month_type).month == month:
              self.panchaanga.delete_festival_date(fest_id=fest_id, date=previous_fest_day)
          self.panchaanga.add_festival(fest_id=fest_id, date=p_fday.date)
    
    