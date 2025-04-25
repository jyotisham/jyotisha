
import logging
import sys

from jyotisha.panchaanga.temporal import PeriodicPanchaangaApplier, interval, get_2_day_interval_boundary_angas
from jyotisha.panchaanga.temporal import time
from jyotisha.panchaanga.temporal.zodiac.angas import AngaType, Anga
from jyotisha.panchaanga.temporal.festival import FestivalInstance
from jyotisha.panchaanga.temporal.festival.applier import solar

from sanskrit_data.schema import common


def get_tithi(jd):
  """Returns the tithi prevailing at a given moment

  Tithi is computed as the difference in the longitudes of the moon
  and sun at any given point of time. Therefore, even the ayanaamsha
  does not matter, as it gets cancelled out.

  Returns:
    int tithi, where 1 stands for ShuklapakshaPrathama, ..., 15 stands
    for Paurnamasi, ..., 23 stands for KrishnapakshaAshtami, 30 stands
    for Amavasya

  """
  from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision, Ayanamsha
  # VERNAL_EQUINOX_AT_0 does not involve lookups, hence sending it - though ayanAmsha does not matter.
  return NakshatraDivision(jd=jd, ayanaamsha_id=Ayanamsha.VERNAL_EQUINOX_AT_0).get_anga(AngaType.TITHI)


class ShraadhaTithiAssigner(PeriodicPanchaangaApplier):
  def reset_shraaddha_tithis(self):
    for daily_panchaanga in self.daily_panchaangas:
      daily_panchaanga.solar_shraaddha_tithi = []
      daily_panchaanga.lunar_shraaddha_tithi = []

  def assign_shraaddha_tithi(self, debug_shraaddha_tithi=False):
    self.reset_shraaddha_tithis()
    tithi_days = [{z: [] for z in range(0, 31)} for _x in range(13)]
    lunar_tithi_days = {}
    daily_panchaangas = self.daily_panchaangas

    lunar_month_list = sorted(list(set(
      [(dp.lunar_date.month.index) for dp in self.panchaanga.daily_panchaangas_sorted()[2:self.panchaanga.duration + 2]] + [
        13, 14])))
    # Including 13, 14 for next lunar year's chaitra/vaishakha
    lunar_tithi_days = {_m: {t: [] for t in range(0, 31)} for _m in lunar_month_list}

    # Identify the pakshas correctly, accounting for adhika masas
    saptama_apara_paksha = lunar_month_list[lunar_month_list.index(4) + 3]
    navama_apara_paksha = lunar_month_list[lunar_month_list.index(4) + 4]

    yest_tithis, aparaahna = self.panchaanga.daily_panchaangas_sorted()[1].get_interval_anga_spans(interval_id="aparaahna",
                                                                                              anga_type=AngaType.TITHI)
    for dp in self.panchaanga.daily_panchaangas_sorted()[2:self.panchaanga.duration + 3]:
      tithis, aparaahna = dp.get_interval_anga_spans(interval_id="aparaahna", anga_type=AngaType.TITHI)
      if (tithis[0].anga.index - yest_tithis[-1].anga.index) % 30 == 2:
        # We have a tithi that hasn't touched aparaahna at all!
        # Assign to today, but actually check for full saayaahna vyaapti 🤷 yesterday
        praatah_tithis, interval = dp.get_interval_anga_spans(interval_id="praatah", anga_type=AngaType.TITHI)
        tithis.insert(0, praatah_tithis[0])
      yest_tithis = tithis
      for t in tithis:
        if t.jd_start is None or t.jd_start < aparaahna.jd_start:
          start_time = aparaahna.jd_start
        else:
          start_time = t.jd_start

        if t.jd_end is None or t.jd_end > aparaahna.jd_end:
          end_time = aparaahna.jd_end
        else:
          end_time = t.jd_end

        span = (end_time - start_time)/(aparaahna.jd_end - aparaahna.jd_start)
        if span < 0:
          span = 0
          if debug_shraaddha_tithi:
            logging.warning(('WARN: span is negative, perhaps because tithi was skipped in aparaahna!', dp))
        tithi_details_tuple = (dp.date, span)
        m = dp.lunar_date.month.index
        if m == 1 and (start_time - self.panchaanga.jd_start) > 200:
          m = 13
        if m == 2 and (start_time - self.panchaanga.jd_start) > 200:
          m = 14
        if t.anga.index == 1:
          # Check if it has to be assigned to current month or next
          if dp.sunrise_day_angas.get_angas_with_ends(AngaType.TITHI)[0].anga.index == 30:
            # Assign to "next" month, as month has started
            m = lunar_month_list[lunar_month_list.index(m) + 1]
            lunar_tithi_days[m][t.anga.index].append(tithi_details_tuple)
          else:
            # We are in the correct month
            lunar_tithi_days[m][t.anga.index].append(tithi_details_tuple)
        else:
          lunar_tithi_days[m][t.anga.index].append(tithi_details_tuple)

    # Process multiple tithis
    for m in lunar_month_list:
      for t in range(1, 31):
        nTithis = len(lunar_tithi_days[m][t])
        if nTithis == 0:
          if m not in (1, 13):
            if debug_shraaddha_tithi:
              logging.warning(('WARN (nTithis = 0) :', m, t, len(lunar_tithi_days[m][t]), lunar_tithi_days[m][t]))
        elif nTithis == 2:
          for i in range(nTithis - 1):
            if debug_shraaddha_tithi:
              logging.debug((nTithis, lunar_tithi_days[m][t], i))
            d0, span0 = lunar_tithi_days[m][t][i]
            d1, span1 = lunar_tithi_days[m][t][i + 1]
            if d1 - d0 == 1:
              if span0 > span1:
                if debug_shraaddha_tithi:
                  logging.debug('deleting %d from %s' % (i + 1, str(lunar_tithi_days[m][t])))
                del_id = i + 1
              else:
                if debug_shraaddha_tithi:
                  logging.debug('deleting %d from %s' % (i, str(lunar_tithi_days[m][t])))
                del_id = i
          del lunar_tithi_days[m][t][del_id]
        elif nTithis > 2:
          if debug_shraaddha_tithi:
            logging.warning(('WARN (nTithis > 2!):', m, t, len(lunar_tithi_days[m][t]), lunar_tithi_days[m][t]))

    # Assign panchama, saptama and navama apara pakshas
    if saptama_apara_paksha != 6: # If there is adhika shrAvaNa, saptama_apara_paksha will be in bhAdrapada, which is anyway mahAlaya paksha - no need to annotate separately!
      sap_start_dt = lunar_tithi_days[saptama_apara_paksha][16][0][0]
      sap_end_dt = lunar_tithi_days[saptama_apara_paksha][30][0][0]
      self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='saptama-(apara)-pakSa-ArambhaH',
                                            interval=self.panchaanga.daily_panchaanga_for_date(sap_start_dt).get_interval(interval_id="full_day")), date=sap_start_dt)
      self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='saptama-(apara)-pakSa-samApanam',
                                            interval=self.panchaanga.daily_panchaanga_for_date(sap_end_dt).get_interval(interval_id="full_day")), date=sap_end_dt)

    if 4.5 in lunar_month_list or 5.5 in lunar_month_list:
      nap_start_dt = lunar_tithi_days[navama_apara_paksha][16][0][0]
      nap_end_dt = lunar_tithi_days[navama_apara_paksha][30][0][0]
      self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='navama-(apara)-pakSa-ArambhaH',
                                            interval=self.panchaanga.daily_panchaanga_for_date(nap_start_dt).get_interval(interval_id="full_day")), date=nap_start_dt)
      self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='navama-(apara)-pakSa-samApanam',
                                            interval=self.panchaanga.daily_panchaanga_for_date(nap_end_dt).get_interval(interval_id="full_day")), date=nap_end_dt)

    # Compute Sankranti Days
    # sankranti_dushta_days = []
    sankranti_dushta_days = solar.SolarFestivalAssigner(panchaanga=self.panchaanga).assign_sidereal_sankranti_punyakaala(force_computation=True)

    # for dp in self.panchaanga.daily_panchaangas_sorted()[2:self.panchaanga.duration + 2]:
    #   if dp.solar_sidereal_date_sunset.month_transition is not None:
    #     madhyaraatri_start = dp.day_length_based_periods.fifteen_fold_division.vaidhaatra.jd_start
    #     madhyaraatri_end = dp.day_length_based_periods.fifteen_fold_division.vaidhaatra.jd_end
    #     #TODO: Should ideally assign based on the punyakaala day!
    #     if dp.solar_sidereal_date_sunset.month_transition < madhyaraatri_start:
    #       sankranti_dushta_days.append(dp.date)
    #     else:
    #       sankranti_dushta_days.append(dp.date + 1)

    # Compute Solar Month Tithis
    solar_tithi_days = [{t: [] for t in range(0, 32)} for _m in range(13)]
    yest_tithis, aparaahna = self.panchaanga.daily_panchaangas_sorted()[1].get_interval_anga_spans(interval_id="aparaahna",
                                                                                              anga_type=AngaType.TITHI)
    for dp in self.panchaanga.daily_panchaangas_sorted()[2:self.panchaanga.duration + 2]:
      tithis, aparaahna = dp.get_interval_anga_spans(interval_id="aparaahna", anga_type=AngaType.TITHI)
      if (tithis[0].anga.index - yest_tithis[-1].anga.index) % 30 == 2:
        # We have a tithi that hasn't touched aparaahna at all!
        # Assign to today, but actually check for full saayaahna vyaapti 🤷 yesterday
        praatah_tithis, interval = dp.get_interval_anga_spans(interval_id="praatah", anga_type=AngaType.TITHI)
        tithis.insert(0, praatah_tithis[0])
      yest_tithis = tithis
      for t in tithis:
        if t.jd_start is None or t.jd_start < aparaahna.jd_start:
          start_time = aparaahna.jd_start
        else:
          start_time = t.jd_start

        if t.jd_end is None or t.jd_end > aparaahna.jd_end:
          end_time = aparaahna.jd_end
        else:
          end_time = t.jd_end

        span = (end_time - start_time)/(aparaahna.jd_end - aparaahna.jd_start)
        if span < 0:
          span = 0
          if debug_shraaddha_tithi:
            logging.warning(('WARN: span is negative, perhaps because tithi was skipped in aparaahna!', dp))
        tithi_details_tuple = (dp.date, span)
        if dp.solar_sidereal_date_sunset.month_transition is not None:
          if start_time > dp.solar_sidereal_date_sunset.month_transition:
            m = dp.solar_sidereal_date_sunset.month
            solar_tithi_days[m][t.anga.index].append(tithi_details_tuple)
          elif end_time < dp.solar_sidereal_date_sunset.month_transition:
            if dp.solar_sidereal_date_sunset.day == 1:
              # Assign to previous month, only if today is Day 1 of next month, otherwise the aparaahna is still
              # for the current month, so no issues!
              m = dp.solar_sidereal_date_sunset.month - 1
            else:
              m = dp.solar_sidereal_date_sunset.month
            if m == 0:
              # This needs some work, as we are talking about the previous year's Mina month!
              pass
            else:
              solar_tithi_days[m][t.anga.index].append(tithi_details_tuple)
          elif start_time < dp.solar_sidereal_date_sunset.month_transition < end_time:
            # Assign to both!
            m = dp.solar_sidereal_date_sunset.month
            solar_tithi_days[m][t.anga.index].append(tithi_details_tuple)
            if m != 1:
              solar_tithi_days[m - 1][t.anga.index].append(tithi_details_tuple)
        else:
          m = dp.solar_sidereal_date_sunset.month
          solar_tithi_days[m][t.anga.index].append(tithi_details_tuple)
    if debug_shraaddha_tithi:
      # Pretty print the tithi days
      for m in range(1, 13):
        for t in range(1, 31):
          logging.debug((m, t, len(solar_tithi_days[m][t]), solar_tithi_days[m][t]))
    # Process multiple tithis
    for m in range(1, 13):
      for t in range(1, 31):
        nTithis = len(solar_tithi_days[m][t])
        if nTithis == 0:
          if debug_shraaddha_tithi:
            logging.debug(('WARN:', m, t, len(solar_tithi_days[m][t]), solar_tithi_days[m][t]))
        elif nTithis > 1:
          del_id = None
          for i in range(nTithis - 1):
            if debug_shraaddha_tithi:
              logging.debug((nTithis, solar_tithi_days[m][t], i))
            d0, span0 = solar_tithi_days[m][t][i]
            d1, span1 = solar_tithi_days[m][t][i + 1]
            if d1 - d0 == 1:
              if span0 > span1 or d1 in sankranti_dushta_days:
                if debug_shraaddha_tithi:
                  logging.debug(('deleting %d from %s' % (i + 1, str(solar_tithi_days[m][t]))))
                del_id = i + 1
              else:
                if debug_shraaddha_tithi:
                  logging.debug(('deleting %d from %s' % (i, str(solar_tithi_days[m][t]))))
                del_id = i
          if del_id is not None:
            del solar_tithi_days[m][t][del_id]

    # Eliminate Sankranti Dushta Tithis
    for m in range(1, 13):
      for t in range(1, 31):
        nTithis = len(solar_tithi_days[m][t])
        if nTithis > 1:
          assert nTithis == 2
          d0, span0 = solar_tithi_days[m][t][0]
          d1, span1 = solar_tithi_days[m][t][1]
          if d0 in sankranti_dushta_days and d1 in sankranti_dushta_days:
            d0_panchaanga = self.panchaanga.daily_panchaanga_for_date(d0)
            d0_aparaahna = d0_panchaanga.get_interval(interval_id="aparaahna")
            d1_panchaanga = self.panchaanga.daily_panchaanga_for_date(d1)
            d1_aparaahna = d1_panchaanga.get_interval(interval_id="aparaahna")
            d0_in_aparaahna = False
            d1_in_aparaahna = False
            sankranti_0 = d0_panchaanga.solar_sidereal_date_sunset.month_transition
            sankranti_1 = d1_panchaanga.solar_sidereal_date_sunset.month_transition
            if sankranti_0 is not None:
              d0_in_aparaahna = d0_aparaahna.jd_start < sankranti_0 < d0_aparaahna.jd_end
            if sankranti_1 is not None:
              d1_in_aparaahna = d1_aparaahna.jd_start < sankranti_1 < d1_aparaahna.jd_end
            if d0_in_aparaahna and d1_in_aparaahna:
              logging.debug('Both sankrantis are in aparaahna, so doing more checks!')
              # What is the span of each tithi in aparaahna in the maasa?
              span0 = (d0_aparaahna.jd_end - sankranti_0) / (d0_aparaahna.jd_end - d0_aparaahna.jd_start)
              span1 = (sankranti_1 - d1_aparaahna.jd_start) / (d1_aparaahna.jd_end - d1_aparaahna.jd_start)
              logging.debug((span0, span1))
              if span0 > span1:
                if debug_shraaddha_tithi:
                  logging.debug('deleting %d from %s' % (1, str(solar_tithi_days[m][t])))
                del solar_tithi_days[m][t][1]
              else:
                if debug_shraaddha_tithi:
                  logging.debug('deleting %d from %s' % (0, str(solar_tithi_days[m][t])))
                del solar_tithi_days[m][t][0]
            elif sankranti_0 is not None and sankranti_0 < d0_panchaanga.get_interval(interval_id="puurvaahna").jd_end:
              # First sankranti is in puurvahna, so keep it
              if debug_shraaddha_tithi:
                logging.debug('deleting %d from %s' % (1, str(solar_tithi_days[m][t])))
              del solar_tithi_days[m][t][1]
            else:
              if debug_shraaddha_tithi:
                logging.debug('deleting %d from %s' % (0, str(solar_tithi_days[m][t])))
              fday = int(solar_tithi_days[m][t][0][0] - self.panchaanga.daily_panchaangas_sorted()[0].date)
              # Add Shunya tithi
              if 0 not in self.daily_panchaangas[fday].solar_shraaddha_tithi:
                self.daily_panchaangas[fday].solar_shraaddha_tithi.append(0)
              del solar_tithi_days[m][t][0]
          else:
            if d1 in sankranti_dushta_days:
              if debug_shraaddha_tithi:
                logging.debug('deleting %d from %s' % (1, str(solar_tithi_days[m][t])))
              fday = int(solar_tithi_days[m][t][1][0] - self.panchaanga.daily_panchaangas_sorted()[0].date)
              # Add Shunya tithi
              if 0 not in self.daily_panchaangas[fday].solar_shraaddha_tithi:
                self.daily_panchaangas[fday].solar_shraaddha_tithi.append(0)
              del solar_tithi_days[m][t][1]
            else:
              if debug_shraaddha_tithi:
                logging.debug('deleting %d from %s' % (0, str(solar_tithi_days[m][t])))
              fday = int(solar_tithi_days[m][t][0][0] - self.panchaanga.daily_panchaangas_sorted()[0].date)
              # Add Shunya tithi
              if 0 not in self.daily_panchaangas[fday].solar_shraaddha_tithi:
                self.daily_panchaangas[fday].solar_shraaddha_tithi.append(0)
              del solar_tithi_days[m][t][0]
        elif nTithis == 0:
          # No tithi found, use chandramana tithi!
          # सौरमासे तिथ्यलाभे चान्द्रमानेन कारयेत्
          solar_tithi_days[m][t] = lunar_tithi_days[m][t]
          if debug_shraaddha_tithi:
            logging.warning('Using lunar tithi for %d, %d: %s' % (m, t, str(solar_tithi_days[m][t])))

    for m in range(1, 13):
      for t in range(1, 31):
        fday = int(solar_tithi_days[m][t][0][0] - self.panchaanga.daily_panchaangas_sorted()[0].date)
        if 0 in self.daily_panchaangas[fday].solar_shraaddha_tithi:
          logging.warning('No longer shUnya')
          self.daily_panchaangas[fday].solar_shraaddha_tithi.remove(0)
        self.daily_panchaangas[fday].solar_shraaddha_tithi.append((m, t))

    for m in lunar_month_list:
      for t in range(1, 31):
        if lunar_tithi_days[m][t]:
          fday = int(lunar_tithi_days[m][t][0][0] - self.panchaanga.daily_panchaangas_sorted()[0].date)
          self.daily_panchaangas[fday].lunar_shraaddha_tithi.append(t)


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
