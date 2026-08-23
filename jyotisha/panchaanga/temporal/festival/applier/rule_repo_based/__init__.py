import logging

from timebudget import timebudget

from jyotisha.panchaanga.temporal import Anga, AngaType, get_2_day_interval_boundary_angas
from jyotisha.panchaanga.temporal.festival import priority_decision
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.festival.rules import RulesRepo, resolve_vaara_index


# TOML-facing anga_type names for `intersection_groups`, mapped to the AngaType singletons. Kept distinct from
# AngaType.from_name()'s (upper-cased AngaType.name) lookup since a couple of internal names are abbreviated
# (eg. AngaType.SOLAR_NAKSH) in ways that would be needlessly cryptic to require rule authors to know.
_INTERSECTION_ANGA_TYPES = {
  "tithi": AngaType.TITHI,
  "tithi_pada": AngaType.TITHI_PADA,
  "nakshatra": AngaType.NAKSHATRA,
  "nakshatra_pada": AngaType.NAKSHATRA_PADA,
  "rashi": AngaType.RASHI,
  "yoga": AngaType.YOGA,
  "yoga_pada": AngaType.YOGA_PADA,
  "karana": AngaType.KARANA,
  "vaara": AngaType.VARA,
  "solar_nakshatra": AngaType.SOLAR_NAKSH,
  "solar_nakshatra_pada": AngaType.SOLAR_NAKSH_PADA,
}


def _resolve_anga_number(anga_type_str, anga_number):
  """anga_number for anga_type="vaara" may be a name (or list of names) instead of an index; everything else
  passes through unchanged."""
  if anga_type_str != "vaara":
    return anga_number
  if isinstance(anga_number, (list, tuple)):
    return [resolve_vaara_index(v) for v in anga_number]
  return resolve_vaara_index(anga_number)


def _month_matches(daily_panchaanga, month_type, month_number):
  """month_number may be None (no filter), a single month, or a list of months (any-of)."""
  if month_number is None:
    return True
  months = month_number if isinstance(month_number, (list, tuple)) else [month_number]
  if 0 in months:
    return True
  day_month = daily_panchaanga.get_date(month_type=month_type).month
  return day_month in months


class RuleLookupAssigner(FestivalAssigner):
  def assign_varalakshmi_vratam(self):
    """ varalakSmI-vratam is set directly off zrAvaNa-pUrNimA (tithi 15 of nija zrAvaNa mAsa, decided at
    madhyAhna kAla with paraviddha priority), rather than anchored off yajurvEda-upAkarma -- upAkarma may be
    absent from a given festival set, or its own timing rule need not coincide with paraviddha/madhyAhna.
    """
    target_anga = Anga.get_cached(index=15, anga_type_id=AngaType.TITHI.name)
    kaala = "madhyaahna"
    purnima_date = None
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      day_panchaanga = self.daily_panchaangas[d]
      prev_day_panchaanga = self.daily_panchaangas[d - 1]
      if day_panchaanga.lunar_date.month.index != 5 and prev_day_panchaanga.lunar_date.month.index != 5:
        # pUrNimA's madhyAhna-touch can land on either the last day of (nija) zrAvaNa mAsa or the first
        # day of the next mAsa, depending on when the mAsa transition itself falls -- so a pair straddling
        # the mAsa boundary must still be checked as long as one side of it is zrAvaNa.
        continue
      decision = priority_decision.decide_paraviddha(p0=prev_day_panchaanga, p1=day_panchaanga, target_anga=target_anga, kaala=kaala)
      if decision is None or decision.fday is None:
        continue
      if decision.fday == 1:
        # decide_paraviddha() picked today over yesterday based on just this pair; a look at tomorrow
        # settles whether today's win is final (mirrors the same look-ahead used for generic paraviddha
        # festivals in apply_month_anga_events, and for the same reason: a tithi can never touch 3
        # consecutive days' kaalas, so if tomorrow's kaala doesn't touch pUrNimA at all, today's win stands;
        # if it does, resolve directly against tomorrow rather than risk a stale answer).
        next_day_panchaanga = self.daily_panchaangas[d + 1]
        tomorrow_decision = priority_decision.decide_paraviddha(p0=day_panchaanga, p1=next_day_panchaanga, target_anga=target_anga, kaala=kaala)
        if tomorrow_decision is not None and tomorrow_decision.fday is not None:
          decision = tomorrow_decision
      purnima_date = decision.day_panchaanga.date

    if purnima_date is None:
      logging.error('Could not determine zrAvaNa-pUrNimA (for varalakSmI-vratam)!')
      return

    # varalakSmI-vratam sits on the Friday preceding pUrNimA; if pUrNimA itself is a Friday, it moves a
    # full week earlier rather than coinciding with pUrNimA.
    days_since_friday = (purnima_date.get_weekday() - 5) % 7
    offset = days_since_friday if days_since_friday != 0 else 7
    self.panchaanga.add_festival(fest_id='varalakSmI-vratam', date=purnima_date - offset)

  def assign_relative_festivals(self):
    """ Add "RELATIVE" festival_id_to_instance --- festival_id_to_instance that happen before or after another festival with an exact timedelta! Example: 1 day after makara sankrAnti.
    
    :return: 
    """

    if 'varalakSmI-vratam' in self.rules_collection.name_to_rule:
      self.assign_varalakshmi_vratam()    
    
    name_to_rule = self.rules_collection.name_to_rule

    # Iterate over all other relative events.
    for festival_name in name_to_rule:
      # Skip over non-relative events.
      if name_to_rule[festival_name].timing is None or name_to_rule[festival_name].timing.offset is None:
        continue

      offset = int(name_to_rule[festival_name].timing.offset)
      anchor_festival_id = name_to_rule[festival_name].timing.anchor_festival_id
      
      if anchor_festival_id not in self.panchaanga.festival_id_to_days:
        # Sometimes, the recorded anchor_festival_id is not exact (Eg. navama-aparapakSa-samApanam 0 days from sarva-kArttika-amAvAsyA). So, we find an approx. match (Eg. kArttika\-amAvAsyA).
        matched_festivals = []
        if 'amAvAsyA' in anchor_festival_id:
          anchor_festival_id = anchor_festival_id.strip('sarva-')
        
        # Generally, we find a matching event by looking for superstring ids.
        for fest_key in self.panchaanga.festival_id_to_days:
          if anchor_festival_id in fest_key:
            # Match bOdhAyana festivals with bOdhAyana anchor ids only.
            if 'amAvAsyA' in anchor_festival_id:
              if 'bOdhAyana' not in anchor_festival_id and 'bOdhAyana' in fest_key:
                continue
            matched_festivals += [fest_key]

        if matched_festivals == []:
          logging.error('Relative festival %s not in festival_id_to_days!' % anchor_festival_id)
        elif len(matched_festivals) > 1:
          logging.error('Relative festival %s not in festival_id_to_days! Found more than one approximate match: %s' % (
            anchor_festival_id, str(matched_festivals)))
        else:
          for x in self.panchaanga.festival_id_to_days[matched_festivals[0]]:
            self.panchaanga.add_festival(fest_id=festival_name, date=x + offset)
      else:
        for x in self.panchaanga.festival_id_to_days[anchor_festival_id]:
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
    self.apply_anga_intersection_events()
    self.apply_vaara_conditioned_events()

  @timebudget
  def apply_vaara_conditioned_events(self):
    """ Apply festivals declared via `[timing] vaara = ...` -- a plain weekday filter, for festivals that recur
    on every day matching (month, weekday, and optionally a single anga touching that day), with no
    disambiguation and no anga-span search: the trivial "month/anga + weekday" shape (eg. kArttika~sOmavAsaraH:
    lunar month 8, every Monday), as opposed to the genuine multi-anga conjunctions
    apply_anga_intersection_events() searches for. See that method and apply_month_anga_events() above for the
    other two (heavier) mechanisms.
    """
    for fest_id, fest_rule in self.rules_collection.name_to_rule.items():
      if fest_rule.timing is None or fest_rule.timing.vaara is None:
        continue
      vaara_index = fest_rule.timing.get_vaara_index()
      target_anga = None
      if fest_rule.timing.anga_type is not None:
        target_anga = Anga.get_cached(index=fest_rule.timing.anga_number, anga_type_id=_INTERSECTION_ANGA_TYPES[fest_rule.timing.anga_type].name)
      touch_window = fest_rule.timing.window
      if touch_window is not None and touch_window not in ("sunrise_to_sunset", "sunrise_to_purvaahna"):
        raise ValueError("Unsupported window %r for vaara-conditioned rule %s (expected sunrise_to_sunset or sunrise_to_purvaahna)" % (touch_window, fest_id))
      for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
        daily_panchaanga = self.daily_panchaangas[d]
        if daily_panchaanga.date.get_weekday() + 1 != vaara_index:
          continue
        if not _month_matches(daily_panchaanga, fest_rule.timing.month_type, fest_rule.timing.month_number):
          continue
        if target_anga is not None:
          # Bounded to daytime (dinamaana, sunrise..sunset, or the narrower purvaahna half of it), never the
          # full sunrise..next_sunrise night-inclusive span: every hand-written festival of this shape checks
          # "anga at sunrise OR anga at {sunset,purvaahna_end}" (a vrata observed during daylight, sometimes
          # only its first half), so an anga that only appears later shouldn't count -- matching
          # find_anga_span's whole-day span would count it and diverge from the original.
          touch_interval = daily_panchaanga.day_length_based_periods.puurvaahna if touch_window == "sunrise_to_purvaahna" else daily_panchaanga.day_length_based_periods.dinamaana
          daytime_spans = daily_panchaanga.sunrise_day_angas.get_anga_spans_in_interval(anga_type=target_anga.get_type(), interval=touch_interval)
          if not any(span.anga == target_anga for span in daytime_spans):
            continue
        self.panchaanga.add_festival(fest_id=fest_id, date=daily_panchaanga.date)

  @timebudget
  def apply_anga_intersection_events(self):
    """ Apply festivals declared via `[timing] intersection_groups = [[...]]` -- multi-anga conjunctions (tithi
    AND nakshatra AND vaara ..., possibly VARA among them), the TOML-driven counterpart of the hand-written
    intersect_list calls to FestivalAssigner._assign_anga_intersection still used in solar.py/vaara.py. See
    apply_month_anga_events()/apply_month_day_events() above for the single-anga counterparts of this method.
    """
    for fest_id, fest_rule in self.rules_collection.name_to_rule.items():
      if fest_rule.timing is None or fest_rule.timing.intersection_groups is None:
        continue
      groups = [
        [(_INTERSECTION_ANGA_TYPES[item['anga_type']], _resolve_anga_number(item['anga_type'], item['anga_number'])) for item in group['angas']]
        for group in fest_rule.timing.intersection_groups
      ]
      window = fest_rule.timing.get_window()
      if window == "full_period":
        for group in groups:
          self._assign_anga_intersection(fest_id, group, jd_start=self.panchaanga.jd_start, jd_end=self.panchaanga.jd_end, show_debug_info=False)
      else:
        for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
          daily_panchaanga = self.daily_panchaangas[d]
          if not _month_matches(daily_panchaanga, fest_rule.timing.month_type, fest_rule.timing.month_number):
            continue
          if window == "sunrise_to_sunset":
            jd_start, jd_end = daily_panchaanga.jd_sunrise, daily_panchaanga.jd_sunset
          elif window == "sunrise_to_next_sunrise":
            jd_start, jd_end = daily_panchaanga.jd_sunrise, daily_panchaanga.jd_next_sunrise
          elif window == "padded_1_day":
            jd_start, jd_end = daily_panchaanga.jd_sunrise - 1, daily_panchaanga.jd_sunset + 2
          else:
            raise ValueError("Unknown window %s for %s" % (window, fest_id))
          for group in groups:
            self._assign_anga_intersection(fest_id, group, jd_start=jd_start, jd_end=jd_end, show_debug_info=False)

  def apply_month_day_events(self, day_panchaanga, month_type):
    """Apply events set to take place on a given (ordinal) day of a given month. Eg. Jan 1 as per Julian calendar, Aug 15 as per Gregorian calendar, 1st day of sidereal solar month 6. See calls from apply_festival_from_rules_repos().
    
    :param day_panchaanga: 
    :param month_type: 
    :return: 
    """
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
      if fest.timing.vaara is not None:
        # See the matching guard in apply_month_anga_events: owned by apply_vaara_conditioned_events instead.
        continue
      if month_type in [RulesRepo.GREGORIAN_MONTH_DIR, RulesRepo.JULIAN_MONTH_DIR]:
        self.panchaanga.add_festival(date=day_panchaanga.date, fest_id=fest_id, interval_id="julian_day")
      else:
        # TODO : Set intervals for preceding_arunodaya differently? 
        self.panchaanga.add_festival(date=day_panchaanga.date, fest_id=fest_id, interval_id="full_day")


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
    

    # Why do we consider angas from the previous days? Explanation below.
    # Consider festival "tiruccendUr mAcit tiruvizhA nir2aivu" occuring at sunrise on tithi 15 of sidereal solar month 11. In Chennai 2018, this tithi 15 occurs between sunrise of Mar 3 and sunrise of Mar 4.
    # In that case, during the round where we consider the pair of days Mar 3 and Mar 4, our decision functions identify this "skipped" tithi and correctly assign the festival - if asked to. For that, we consider angas from previous day as well so that matching festivals may be considered.
    anga_spans = self.panchaanga.get_interval_anga_spans(date=panchaangas[0].date, anga_type=anga_type, interval_id="full_day")
    month = panchaangas[1].get_date(month_type=month_type).month
    fest_dict = rule_set.get_possibly_relevant_fests(month=month, angas=[span.anga for span in anga_spans], month_type=month_type, anga_type_id=anga_type_id)

    anga_spans = self.panchaanga.get_interval_anga_spans(date=panchaangas[1].date, anga_type=anga_type, interval_id="full_day")
    month = panchaangas[1].get_date(month_type=month_type).month
    fest_dict.update(rule_set.get_possibly_relevant_fests(month=month, angas=[span.anga for span in anga_spans], month_type=month_type, anga_type_id=anga_type_id))
    # Note: The successive days may be in different months! Hence the two calls above.
    return fest_dict

  def _check_lunar_month_match(self, fday_date, fest_rule):
    month_match = False
    adhika_maasa_handling = fest_rule.timing.get_adhika_maasa_handling()
    if adhika_maasa_handling == 'adhika_and_nija':
      if fday_date.month == fest_rule.timing.month_number - 0.5 or fday_date.month == fest_rule.timing.month_number or fest_rule.timing.month_number == 0:
        month_match = True
    elif adhika_maasa_handling == 'adhika_only':
      if int(fday_date.month) != fday_date.month and (fday_date.month == fest_rule.timing.month_number or fest_rule.timing.month_number == 0):
        month_match = True
    elif adhika_maasa_handling == 'adhika_if_exists':
      if fday_date.month == fest_rule.timing.month_number - 0.5 and len(self.festival_id_to_days[fest_rule.id]) == 0:
        month_match = True
    elif adhika_maasa_handling == 'nija_only':
      if fday_date.month == fest_rule.timing.month_number or fest_rule.timing.month_number == 0:
        month_match = True

    return month_match

  def _should_assign_festival(self, p_fday, fest_rule):
    if p_fday.date in self.festival_id_to_days[fest_rule.id]:
      # Already assigned (likely in the previous iteration).
      return False

    month_type = fest_rule.timing.month_type
    priority = fest_rule.timing.get_priority()
    fday_date = p_fday.get_date(month_type=month_type)

    if month_type == RulesRepo.LUNAR_MONTH_DIR:
      month_match = self._check_lunar_month_match(fday_date=fday_date, fest_rule=fest_rule)
    else:
      month_match = fday_date.month == fest_rule.timing.month_number or fest_rule.timing.month_number == 0


    if not month_match:
      # This could legitimately happen in the case indicated in the below negated clause. Example: imagine a "skipped" shukla prathamA tithi.
      if not (fday_date.day == 30 and month_type == RulesRepo.LUNAR_MONTH_DIR):
        # Example where False should be returned: Suppose festival is on tithi 27 of solar sidereal month 10; last day of month 9 could have tithi 27, but not day 1 of month 10; though a much later day of month 10 has tithi 27.
        return False

    return priority not in ('puurvaviddha', 'vyaapti', 'paraviddha') or 'anadhyAyaH' in fest_rule.id or \
                      (p_fday.date - 1 not in self.festival_id_to_days[fest_rule.id])


  @timebudget
  def apply_month_anga_events(self, day_panchaanga, anga_type, month_type):
    """ Apply events set to take place on when an anga (tithi, naxatra, yoga ..) occurs within a given month. Eg. Chaitra shukla 1, rohiNI of taiShya. See calls from apply_festival_from_rules_repos().
    
    :param day_panchaanga: 
    :param anga_type: 
    :param month_type: 
    :return: 
    """
    from jyotisha.panchaanga.temporal.festival import priority_decision
    date = day_panchaanga.date
    month = day_panchaanga.get_date(month_type=month_type).month
    
    panchaangas = [self.panchaanga.date_str_to_panchaanga.get((date-2).get_date_str(), None), self.panchaanga.date_str_to_panchaanga.get((date-1).get_date_str(), None), day_panchaanga]
    if panchaangas[1] is None:
      # We require atleast 1 day history.
      return

    # Get festivals relevant to the previous day and the current day.
    fest_dict = self._get_relevant_festivals(panchaangas=panchaangas[1:], anga_type=anga_type, month_type=month_type)
    ###########################
    # Iterate over relevant festivals
    for fest_id, fest_rule in fest_dict.items():
      if fest_rule.timing.vaara is not None:
        # Owned by apply_vaara_conditioned_events instead: a rule can end up indexed into this (month_type,
        # anga_type, month, anga) tree bucket incidentally (via get_storage_file_name's path routing) even
        # though it also has `vaara` set and is meant to be weekday-gated -- this engine has no concept of
        # `vaara` at all, so it must not process such rules (it would otherwise assign them on every matching
        # day regardless of weekday, double-processing them alongside the correct, weekday-gated assignment).
        continue
      kaala = fest_rule.timing.get_kaala()
      priority = fest_rule.timing.get_priority()
      adhika_maasa_handling = fest_rule.timing.get_adhika_maasa_handling()
      anga_type_str = fest_rule.timing.anga_type
      target_anga = Anga.get_cached(index=fest_rule.timing.anga_number, anga_type_id=anga_type_str.upper())
      decision = priority_decision.decide(p0=panchaangas[1], p1=panchaangas[2], target_anga=target_anga, kaala=kaala, ayanaamsha_id=self.ayanaamsha_id, priority=priority)

      if decision is not None and priority in ('vyaapti', 'paraviddha') and decision.fday == 1 and 'anadhyAyaH' not in fest_id:
        # decide_vyaapti()/decide_paraviddha() picked today (panchaangas[2]) over yesterday based on just
        # this pair. Since an anga can never touch 3 consecutive days' kaalas (max anga duration < 2x kaala
        # spacing), a look at tomorrow settles whether today's win is final: if tomorrow's kaala doesn't
        # touch target_anga at all, today can't lose to it later, so today's decision stands. If tomorrow
        # does touch, today's boundary match may just be tomorrow's leading edge bleeding backwards (or, for
        # paraviddha, a genuine straddle that itself continues into tomorrow) -- settle it directly, by
        # calling decide() on the (today, tomorrow) pair ourselves right now, rather than deferring and
        # hoping a future turn resolves it. Deferring is unsafe whenever tomorrow's own turn might never
        # actually reconsider this festival at all -- eg. at a month boundary, where _get_relevant_festivals
        # (which filters candidates by month) would silently exclude a month-scoped festival on tomorrow's
        # turn, losing the assignment outright instead of confirming it (this broke arivATTAya, tiruvADippUram
        # and mAn2akkaJcAra in practice). Resolving inline sidesteps that dependency entirely.
        # anadhyAyaH (non-study day) festivals are exempt: unlike other paraviddha festivals, a genuine
        # 2-day straddle is traditionally observed on *both* days, not resolved down to one (see the same
        # exemption in FestivalAssigner.cleanup_festivals's adjacent-day cleanup).
        tomorrow = self.panchaanga.date_str_to_panchaanga.get((date + 1).get_date_str(), None)
        if tomorrow is not None:
          (_, tomorrow_angas) = get_2_day_interval_boundary_angas(kaala=kaala, anga_type=target_anga.get_type(), p0=panchaangas[2], p1=tomorrow)
          if tomorrow_angas.start == target_anga or tomorrow_angas.end == target_anga:
            decision = priority_decision.decide(p0=panchaangas[2], p1=tomorrow, target_anga=target_anga, kaala=kaala, ayanaamsha_id=self.ayanaamsha_id, priority=priority)

      if decision is not None:
        p_fday = decision.day_panchaanga
        assign_festival = self._should_assign_festival(p_fday=p_fday, fest_rule=fest_rule)
        if assign_festival:
          if len(self.festival_id_to_days[fest_id]) > 0:
            previous_fest_day = sorted(self.festival_id_to_days[fest_id])[-1]
            p_previous_fday = self.panchaanga.date_str_to_panchaanga[previous_fest_day.get_date_str()]
            # Regarding the fest_rule.timing.month_number != 0 below:
            # This is required so as to avoid omissions as in the following case: sthAlIpAka_1 (which occurs every lunar month on tithi 1 at pUrvaviddha pUrvAhNa) occurs within the same "sunrise lunar month" but on different "pUrvAhNa lunar months" on 2019-07-03 and 2019-08-01.
            # Plus, a gap of not much more than 1 month is desirable for monthly festivals even otherwise - https://github.com/jyotisham/jyotisha/issues/54#issuecomment-735355325 .
            if fest_rule.timing.month_number != 0 and p_fday.date - previous_fest_day <= 32 and p_previous_fday.get_date(month_type=month_type).month == month:
              self.panchaanga.delete_festival_date(fest_id=fest_id, date=previous_fest_day)
          # TODO : Set intervals for preceeding_arunodaya differently?

          if assign_festival:
            self.panchaanga.add_festival(fest_id=fest_id, date=p_fday.date)

