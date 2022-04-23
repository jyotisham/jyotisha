import logging

from timebudget import timebudget

from jyotisha.panchaanga.temporal import Anga, AngaType
from jyotisha.panchaanga.temporal.festival import FestivalInstance
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.festival.rules import RulesRepo


class RuleLookupAssigner(FestivalAssigner):
  def assign_relative_festivals(self):
    # Add "RELATIVE" festival_id_to_instance --- festival_id_to_instance that happen before or
    # after other festival_id_to_instance with an exact timedelta!
    if 'yajurvEda-upAkarma' not in self.panchaanga.festival_id_to_days:
      logging.error('yajurvEda-upAkarma not in festival_id_to_instance!')
    elif 'varalakSmI-vratam' in self.rules_collection.name_to_rule:
      # Extended for longer calendars where more than one upAkarma may be there
      for d in self.panchaanga.festival_id_to_days['yajurvEda-upAkarma']:
        self.panchaanga.add_festival(fest_id='varalakSmI-vratam', date=d - ((d.get_weekday() - 5) % 7))

    name_to_rule = self.rules_collection.name_to_rule

    for festival_name in name_to_rule:
      if name_to_rule[festival_name].timing is None or name_to_rule[festival_name].timing.offset is None:
        continue
      offset = int(name_to_rule[festival_name].timing.offset)
      rel_festival_name = name_to_rule[festival_name].timing.anchor_festival_id
      if rel_festival_name not in self.panchaanga.festival_id_to_days:
        # Check approx. match
        matched_festivals = []
        if 'amAvAsyA' in rel_festival_name: # Handle amAvAsyAs a bit differently
          rel_festival_name = rel_festival_name.strip('sarva-')
        for fest_key in self.panchaanga.festival_id_to_days:
          if rel_festival_name in fest_key:
            if 'amAvAsyA' in rel_festival_name: # Handle amAvAsyAs a bit differently
              if 'bOdhAyana' not in rel_festival_name and 'bOdhAyana' in fest_key:
                continue
            matched_festivals += [fest_key]
        if matched_festivals == []:
          logging.error('Relative festival %s not in festival_id_to_days!' % rel_festival_name)
        elif len(matched_festivals) > 1:
          logging.error('Relative festival %s not in festival_id_to_days! Found more than one approximate match: %s' % (
            rel_festival_name, str(matched_festivals)))
        else:
          for x in self.panchaanga.festival_id_to_days[matched_festivals[0]]:
            self.panchaanga.add_festival(fest_id=festival_name, date=x + offset)
      else:
        for x in self.panchaanga.festival_id_to_days[rel_festival_name]:
          self.panchaanga.add_festival(fest_id=festival_name, date=x + offset)

  def apply_festival_from_rules_repos(self):
    for index, dp in enumerate(self.daily_panchaangas):
      self.apply_month_day_events(day_panchaanga=dp, month_type=RulesRepo.SIDEREAL_SOLAR_MONTH_DIR)
      self.apply_month_day_events(day_panchaanga=dp, month_type=RulesRepo.TROPICAL_MONTH_DIR)
      self.apply_month_day_events(day_panchaanga=dp, month_type=RulesRepo.GREGORIAN_MONTH_DIR)
      self.apply_month_anga_events(day_panchaanga=dp, month_type=RulesRepo.SIDEREAL_SOLAR_MONTH_DIR, anga_type=AngaType.TITHI)
      self.apply_month_anga_events(day_panchaanga=dp, month_type=RulesRepo.SIDEREAL_SOLAR_MONTH_DIR, anga_type=AngaType.NAKSHATRA)
      self.apply_month_anga_events(day_panchaanga=dp, month_type=RulesRepo.SIDEREAL_SOLAR_MONTH_DIR, anga_type=AngaType.YOGA)
      self.apply_month_anga_events(day_panchaanga=dp, month_type=RulesRepo.LUNAR_MONTH_DIR, anga_type=AngaType.TITHI)
      self.apply_month_anga_events(day_panchaanga=dp, month_type=RulesRepo.LUNAR_MONTH_DIR, anga_type=AngaType.NAKSHATRA)
      self.apply_month_anga_events(day_panchaanga=dp, month_type=RulesRepo.LUNAR_MONTH_DIR, anga_type=AngaType.YOGA)

  def apply_month_day_events(self, day_panchaanga, month_type):
    from jyotisha.panchaanga.temporal.festival import rules
    rule_set = rules.RulesCollection.get_cached(repos_tuple=tuple(self.computation_system.festival_options.repos), julian_handling=self.computation_system.festival_options.julian_handling)

    date = day_panchaanga.get_date(month_type=month_type)
    days = [date.day]
    if month_type == RulesRepo.GREGORIAN_MONTH_DIR:
      if (day_panchaanga.date + 1).month != day_panchaanga.date.month:
        if day_panchaanga.date.day == 28: 
          days = [28, 29, 30, 31]
        elif day_panchaanga.date.day == 29:
          days = [29, 30, 31]
        elif day_panchaanga.date.day == 30:
          days = [30, 31]
    fest_dict = rule_set.get_possibly_relevant_fests(month=date.month, angas=days, month_type=month_type, anga_type_id=rules.RulesRepo.DAY_DIR)
    for fest_id, fest in fest_dict.items():
      if month_type in [RulesRepo.GREGORIAN_MONTH_DIR, RulesRepo.JULIAN_MONTH_DIR]:
        interval = day_panchaanga.get_interval(interval_id="julian_day")
      else:
        # TODO : Set intervals for preceding_arunodaya differently? 
        interval = day_panchaanga.get_interval(interval_id="full_day")
      self.panchaanga.add_festival_instance(date=day_panchaanga.date, festival_instance=FestivalInstance(name=fest_id, interval=interval))

  @timebudget
  def _get_relevant_festivals(self, anga_type, month_type, panchaangas):
    """
    
    :param anga_type: 
    :param month_type: 
    :param panchaangas: Array of panchaangas for 2 successive days 
    :return: 
    """
    from jyotisha.panchaanga.temporal.festival import rules
    rule_set = rules.RulesCollection.get_cached(repos_tuple=tuple(self.computation_system.festival_options.repos), julian_handling=self.computation_system.festival_options.julian_handling)
    anga_type_id = anga_type.name.lower()
    
    anga_spans_2 = self.panchaanga.get_interval_anga_spans(date=panchaangas[1].date, anga_type=anga_type, interval_id="full_day")

    # Why do we consider angas from the previous days? Explanation below.
    # Consider festival "tiruccendUr mAcit tiruvizhA nir2aivu" occuring at sunrise on tithi 15 of sidereal solar month 11. In Chennai 2018, this tithi 15 occurs between sunrise of Mar 3 and sunrise of Mar 4.
    # In that case, during the round where we consider the pair of days Mar 3 and Mar 4, our decision functions identify this "skipped" tithi and correctly assign the festival - if asked to. For that, we consider angas from previous day as well so that matching festivals may be considered.
    anga_spans_1 = self.panchaanga.get_interval_anga_spans(date=panchaangas[0].date, anga_type=anga_type, interval_id="full_day")
    angas = set([span.anga for span in anga_spans_1  + anga_spans_2])
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


  @timebudget
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
            # Regarding the fest_rule.timing.month_number != 0 below:
            # This is required so as to avoid omissions as in the following case: sthAlIpAka_1 (which occurs every lunar month on tithi 1 at pUrvaviddha pUrvAhNa) occurs within the same "sunrise lunar month" but on different "pUrvAhNa lunar months" on 2019-07-03 and 2019-08-01.
            # Plus, a gap of not much more than 1 month is desirable for monthly festivals even otherwise - https://github.com/jyotisham/jyotisha/issues/54#issuecomment-735355325 . 
            if fest_rule.timing.month_number != 0 and p_fday.date - previous_fest_day <= 31 and p_previous_fday.get_date(month_type=month_type).month == month:
              self.panchaanga.delete_festival_date(fest_id=fest_id, date=previous_fest_day)
          # TODO : Set intervals for preceeding_arunodaya differently? 
          self.panchaanga.add_festival(fest_id=fest_id, date=p_fday.date)

