import logging
import sys
import re
from datetime import datetime
from math import floor

from jyotisha.panchaanga.temporal import names
from jyotisha.panchaanga import temporal
from jyotisha.panchaanga.temporal import time, get_2_day_interval_boundary_angas
from jyotisha.panchaanga.temporal import zodiac, tithi
from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal.festival import FestivalInstance
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision, AngaType
from pytz import timezone as tz
from scipy.optimize import brentq

from sanskrit_data.schema import common
from indic_transliteration import sanscript

class TithiFestivalAssigner(FestivalAssigner):
  def assign_all(self):
    self.assign_solar_sidereal_amaavaasyaa()
    self.assign_amaavaasya_vyatiipaata()
    # Force computation of chandra darshanam for bodhayana amavasya's sake
    self.assign_chandra_darshanam(force_computation=True)
    self.assign_bodhaayana_amaavaasyaa()
    self.assign_amaavaasyaa_soma()
    self.assign_chaturthi_vratam()
    self.assign_shasthi_vratam()
    self.assign_vishesha_saptami()
    self.assign_ekaadashii_vratam()
    self.assign_mahaadvaadashii()
    self.assign_pradosha_vratam()
    self.assign_vaarunii_trayodashi()
    self.assign_yama_chaturthi()
    self.assign_vajapeyaphala_snana_yoga()
    self.assign_mahaa_paurnamii()
  
  def assign_chaturthi_vratam(self):
    if "vikaTa-mahAgaNapati_saGkaTahara-caturthI-vratam" not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      # SANKATAHARA chaturthi
      if self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise.index == 18 or self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise.index == 19:
        day_panchaanga = self.daily_panchaangas[d]
        ldiff_moonrise_yest = (Graha.singleton(Graha.MOON).get_longitude(self.daily_panchaangas[d - 1].jd_moonrise) - Graha.singleton(
          Graha.SUN).get_longitude(self.daily_panchaangas[d - 1].jd_moonrise)) % 360
        ldiff_moonrise = (Graha.singleton(Graha.MOON).get_longitude(day_panchaanga.jd_moonrise) - Graha.singleton(Graha.SUN).get_longitude(
          day_panchaanga.jd_moonrise)) % 360
        ldiff_moonrise_tmrw = (Graha.singleton(Graha.MOON).get_longitude(self.daily_panchaangas[d + 1].jd_moonrise) - Graha.singleton(
          Graha.SUN).get_longitude(self.daily_panchaangas[d + 1].jd_moonrise)) % 360
        tithi_moonrise_yest = int(1 + floor(ldiff_moonrise_yest / 12.0))
        tithi_moonrise = int(1 + floor(ldiff_moonrise / 12.0))
        tithi_moonrise_tmrw = int(1 + floor(ldiff_moonrise_tmrw / 12.0))

        _m = day_panchaanga.lunar_month_sunrise.index
        if floor(_m) != _m:
          _m = 13  # Adhika masa
        chaturthi_name = names.NAMES['SANKATAHARA_CHATURTHI_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][_m] + '-mahAgaNapati_'

        if tithi_moonrise == 19:
          # otherwise yesterday would have already been assigned
          if tithi_moonrise_yest != 19:
            chaturthi_name = '%s%s' % ('aGgArakI~' if day_panchaanga.date.get_weekday() == 2 else '', chaturthi_name)
            fest = FestivalInstance(
              name=chaturthi_name + 'saGkaTahara-caturthI-vratam', interval=day_panchaanga.get_interval(interval_id="full_day"))
            if day_panchaanga.lunar_month_sunrise.index != 5:
              self.panchaanga.add_festival_instance(festival_instance=fest, date=day_panchaanga.date)
            # shravana krishna chaturthi
            if day_panchaanga.lunar_month_sunrise.index == 5:
              chaturthi_name = '%s%s' % ('aGgArakI~' if day_panchaanga.date.get_weekday() == 2 else '', chaturthi_name)
              fest = FestivalInstance(
                name=chaturthi_name + 'mahAsaGkaTahara-caturthI-vratam', interval=day_panchaanga.get_interval(interval_id="full_day"))
              self.panchaanga.add_festival_instance(festival_instance=fest, date=day_panchaanga.date)
        elif tithi_moonrise_tmrw == 19:
          chaturthi_name = '%s%s' % ('aGgArakI~' if self.daily_panchaangas[d + 1].date.get_weekday() == 2 else '', chaturthi_name)
          fest = FestivalInstance(
            name=chaturthi_name + 'saGkaTahara-caturthI-vratam', interval=day_panchaanga.get_interval(interval_id="full_day"))
          if day_panchaanga.lunar_month_sunrise.index != 5:
            self.panchaanga.add_festival_instance(festival_instance=fest, date=self.daily_panchaangas[d+1].date)
          # self.date_str_to_panchaanga[d].lunar_month_sunrise and[d + 1] are same, so checking [d] is enough
          if day_panchaanga.lunar_month_sunrise.index == 5:
            chaturthi_name = '%s%s' % ('aGgArakI~' if day_panchaanga.date.get_weekday() == 2 else '', chaturthi_name)
            fest = FestivalInstance(
              name=chaturthi_name + 'mahAsaGkaTahara-caturthI-vratam', interval=day_panchaanga.get_interval(interval_id="full_day"))
            self.panchaanga.add_festival_instance(festival_instance=fest, date=self.daily_panchaangas[d+1].date)
        else:
          if tithi_moonrise_yest != 19:
            if tithi_moonrise == 18 and tithi_moonrise_tmrw == 20:
              # No vyApti on either day -- pick parA, i.e. next day.
              chaturthi_name = '%s%s' % ('aGgArakI~' if self.daily_panchaangas[d + 1].date.get_weekday() == 2 else '', chaturthi_name)
              fest = FestivalInstance(
                name=chaturthi_name + 'saGkaTahara-caturthI-vratam', interval=day_panchaanga.get_interval(interval_id="full_day"))
              if day_panchaanga.lunar_month_sunrise.index != 5:
                self.panchaanga.add_festival_instance(festival_instance=fest, date=self.daily_panchaangas[d+1].date)
              # shravana krishna chaturthi
              if day_panchaanga.lunar_month_sunrise.index == 5:
                chaturthi_name = '%s%s' % (
                  'aGgArakI~' if self.daily_panchaangas[d + 1].date.get_weekday() == 2 else '', chaturthi_name)
                fest = FestivalInstance(
                  name=chaturthi_name + 'mahAsaGkaTahara-caturthI-vratam', interval=day_panchaanga.get_interval(interval_id="full_day"))
                self.panchaanga.add_festival_instance(festival_instance=fest, date=self.daily_panchaangas[d+1].date)

  def assign_shasthi_vratam(self):
    if 'SaSThI-vratam' not in self.rules_collection.name_to_rule:
      return 
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      day_panchaanga = self.daily_panchaangas[d]
      # # SHASHTHI Vratam
      # Check only for Adhika maasa here...
      festival_name = 'SaSThI-vratam'
      if day_panchaanga.lunar_month_sunrise.index == 8:
        festival_name = 'skanda' + festival_name
      elif day_panchaanga.lunar_month_sunrise.index == 4:
        festival_name = 'kumAra-' + festival_name
      elif day_panchaanga.lunar_month_sunrise.index == 6:
        festival_name = 'SaSThIdEvI-' + festival_name
      elif day_panchaanga.lunar_month_sunrise.index == 9:
        festival_name = 'subrahmaNya-' + festival_name

      if day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 5 or day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 6:
        (d0_angas, d1_angas) = get_2_day_interval_boundary_angas(kaala="madhyaahna", anga_type=AngaType.TITHI, p0=day_panchaanga, p1=self.daily_panchaangas[d+1])

        if d0_angas.start.index == 6 or d0_angas.end.index == 6:
          if festival_name in self.panchaanga.festival_id_to_days:
            # Check if yesterday was assigned already
            # to this puurvaviddha festival!
            if self.daily_panchaangas[d - 1].date not in self.panchaanga.festival_id_to_days[festival_name]:
              self.panchaanga.add_festival(fest_id=festival_name, date=day_panchaanga.date)
          else:
            self.panchaanga.add_festival(fest_id=festival_name, date=day_panchaanga.date)
        elif d1_angas.start.index == 6 or d1_angas.end.index == 6:
          self.panchaanga.add_festival(fest_id=festival_name, date=self.daily_panchaangas[d + 1].date)
        else:
          # This means that the correct anga did not
          # touch the kaala on either day!
          # sys.stderr.write('Could not assign puurvaviddha day for %s!\
          # Please check for unusual cases.\n' % festival_name)
          if d1_angas.start.index == 6 + 1 or d1_angas.end.index == 6 + 1:
            # Need to assign a day to the festival here
            # since the anga did not touch kaala on either day
            # BUT ONLY IF YESTERDAY WASN'T ALREADY ASSIGNED,
            # THIS BEING PURVAVIDDHA
            # Perhaps just need better checking of
            # conditions instead of this fix
            if festival_name in self.panchaanga.festival_id_to_days:
              if self.daily_panchaangas[d - 1].date not in self.panchaanga.festival_id_to_days[festival_name]:
                self.panchaanga.add_festival(fest_id=festival_name, date=day_panchaanga.date)
            else:
              self.panchaanga.add_festival(fest_id=festival_name, date=day_panchaanga.date)

  def assign_vishesha_saptami(self):
    if 'bhAnusaptamI' in self.rules_collection.name_to_rule:
      for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
        day_panchaanga = self.daily_panchaangas[d]
        # SPECIAL SAPTAMIs
        if day_panchaanga.date.get_weekday() == 0 and (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 7:
          festival_name = 'bhAnusaptamI'
          if day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 7:
            festival_name = 'vijayA' + '~' + festival_name
          if day_panchaanga.sunrise_day_angas.nakshatra_at_sunrise.index == 27:
            # Even more auspicious!
            festival_name += '★'
          self.panchaanga.add_festival(fest_id=festival_name, date=day_panchaanga.date)

    if 'bhadrA~saptamI' in self.rules_collection.name_to_rule:
      for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
        day_panchaanga = self.daily_panchaangas[d]
        if NakshatraDivision(day_panchaanga.jd_sunrise, ayanaamsha_id=self.ayanaamsha_id).get_anga(
            zodiac.AngaType.NAKSHATRA_PADA).index == 49 and \
            day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 7:
          self.panchaanga.add_festival(fest_id='bhadrA~saptamI', date=day_panchaanga.date)

    if 'mahAjayA~saptamI' in self.rules_collection.name_to_rule:
      for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
        day_panchaanga = self.daily_panchaangas[d]
        if day_panchaanga.solar_sidereal_date_sunset.month_transition is not None:
          # we have a Sankranti!
          if day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 7:
            self.panchaanga.add_festival(fest_id='mahAjayA~saptamI', date=day_panchaanga.date)

  def assign_vishesha_ashtami(self):
    if 'jayantI~aSTamI' in self.rules_collection.name_to_rule:
      for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
        day_panchaanga = self.daily_panchaangas[d]
        # SPECIAL ASHTAMIs
        if day_panchaanga.lunar_month_sunrise.index == 10 and NakshatraDivision(day_panchaanga.jd_sunrise, ayanaamsha_id=self.ayanaamsha_id).get_anga(
            zodiac.AngaType.NAKSHATRA).index == 2 and \
            day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 8:
          self.panchaanga.add_festival(fest_id='jayantI~aSTamI', date=day_panchaanga.date)

  def assign_ekaadashii_vratam(self):
    if "ajA-EkAdazI" not in self.rules_collection.name_to_rule:
      return 
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      day_panchaanga = self.daily_panchaangas[d]
      # EKADASHI Vratam
      # One of two consecutive tithis must appear @ sunrise!

      if (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 10 or (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 11:
        yati_ekaadashii_fday = smaarta_ekaadashii_fday = vaishnava_ekaadashii_fday = None
        ekaadashii_tithi_days = [x.sunrise_day_angas.tithi_at_sunrise.index % 15 for x in self.daily_panchaangas[d:d + 3]]
        if day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index > 15:
          ekaadashii_paksha = 'krishna'
        else:
          ekaadashii_paksha = 'shukla'
        if ekaadashii_tithi_days in [[11, 11, 12], [10, 12, 12]]:
          smaarta_ekaadashii_fday = d + 1
          tithi_arunodayam = tithi.get_tithi(self.daily_panchaangas[d + 1].jd_sunrise - (1 / 15.0) * (self.daily_panchaangas[d + 1].jd_sunrise - day_panchaanga.jd_sunrise)).index
          if tithi_arunodayam % 15 == 10:
            vaishnava_ekaadashii_fday = d + 2
          else:
            vaishnava_ekaadashii_fday = d + 1
        elif ekaadashii_tithi_days in [[10, 12, 13], [11, 12, 13], [11, 12, 12], [11, 12, 14]]:
          smaarta_ekaadashii_fday = d
          tithi_arunodayam = temporal.tithi.get_tithi(day_panchaanga.jd_sunrise - (1 / 15.0) * (day_panchaanga.jd_sunrise - self.daily_panchaangas[d - 1].jd_sunrise)).index
          if tithi_arunodayam % 15 == 11 and ekaadashii_tithi_days in [[11, 12, 13], [11, 12, 14]]:
            vaishnava_ekaadashii_fday = d
          else:
            vaishnava_ekaadashii_fday = d + 1
        elif ekaadashii_tithi_days in [[10, 11, 13], [11, 11, 13]]:
          smaarta_ekaadashii_fday = d
          vaishnava_ekaadashii_fday = d + 1
          yati_ekaadashii_fday = d + 1
        else:
          pass
          # These combinations are taken care of, either in the past or future.
          # if ekaadashii_tithi_days == [10, 11, 12]:
          #     logging.debug('Not assigning. Maybe tomorrow?')
          # else:
          #     logging.debug(('!!', d, ekaadashii_tithi_days))

        if yati_ekaadashii_fday == smaarta_ekaadashii_fday == vaishnava_ekaadashii_fday is None:
          # Must have already assigned
          pass
        elif yati_ekaadashii_fday is None:
          if smaarta_ekaadashii_fday == vaishnava_ekaadashii_fday:
            # It's sarva ekaadashii
            self.panchaanga.add_festival(fest_id=
              'sarva-' + names.get_ekaadashii_name(ekaadashii_paksha, day_panchaanga.lunar_month_sunrise.index),
              date=self.daily_panchaangas[smaarta_ekaadashii_fday].date)
            if ekaadashii_paksha == 'shukla':
              if day_panchaanga.solar_sidereal_date_sunset.month == 9:
                self.panchaanga.add_festival(fest_id='sarva-vaikuNTha-EkAdazI', date=self.daily_panchaangas[smaarta_ekaadashii_fday].date)
          else:
            self.panchaanga.add_festival(fest_id=
              'smArta-' + names.get_ekaadashii_name(ekaadashii_paksha, day_panchaanga.lunar_month_sunrise.index), date=
              self.daily_panchaangas[smaarta_ekaadashii_fday].date)
            self.panchaanga.add_festival(
              fest_id='vaiSNava-' + names.get_ekaadashii_name(ekaadashii_paksha, day_panchaanga.lunar_month_sunrise.index), date=
              self.daily_panchaangas[vaishnava_ekaadashii_fday].date)
            if ekaadashii_paksha == 'shukla':
              if day_panchaanga.solar_sidereal_date_sunset.month == 9:
                self.panchaanga.add_festival(fest_id='smArta-vaikuNTha-EkAdazI', date=self.daily_panchaangas[smaarta_ekaadashii_fday].date)
                self.panchaanga.add_festival(fest_id='vaiSNava-vaikuNTha-EkAdazI', date=self.daily_panchaangas[vaishnava_ekaadashii_fday].date)
        else:
          self.panchaanga.add_festival(fest_id='smArta-' + names.get_ekaadashii_name(ekaadashii_paksha,
                                                                                     day_panchaanga.lunar_month_sunrise.index) + ' (gRhastha)', date=self.daily_panchaangas[smaarta_ekaadashii_fday].date)
          self.panchaanga.add_festival(fest_id='smArta-' + names.get_ekaadashii_name(ekaadashii_paksha, self.daily_panchaangas[
            d].lunar_month_sunrise.index) + ' (sannyasta)', date=self.daily_panchaangas[yati_ekaadashii_fday].date)
          self.panchaanga.add_festival(
            fest_id='vaiSNava-' + names.get_ekaadashii_name(ekaadashii_paksha, day_panchaanga.lunar_month_sunrise.index), date=self.daily_panchaangas[vaishnava_ekaadashii_fday].date)
          if day_panchaanga.solar_sidereal_date_sunset.month == 9:
            if ekaadashii_paksha == 'shukla':
              self.panchaanga.add_festival(fest_id='smArta-vaikuNTha-EkAdazI (gRhastha)', date=self.daily_panchaangas[smaarta_ekaadashii_fday].date)
              self.panchaanga.add_festival(fest_id='smArta-vaikuNTha-EkAdazI (sannyasta)', date=self.daily_panchaangas[yati_ekaadashii_fday].date)
              self.panchaanga.add_festival(fest_id='vaiSNava-vaikuNTha-EkAdazI', date=self.daily_panchaangas[vaishnava_ekaadashii_fday].date)

        if yati_ekaadashii_fday == smaarta_ekaadashii_fday == vaishnava_ekaadashii_fday is None:
          # Must have already assigned
          pass
        else:
          if day_panchaanga.solar_sidereal_date_sunset.month == 8 and ekaadashii_paksha == 'shukla':
            # self.add_festival('guruvAyupura-EkAdazI', smaarta_ekaadashii_fday)
            self.panchaanga.add_festival(fest_id='guruvAyupura-EkAdazI', date=self.daily_panchaangas[vaishnava_ekaadashii_fday].date)
            self.panchaanga.add_festival(fest_id='kaizika-EkAdazI', date=self.daily_panchaangas[vaishnava_ekaadashii_fday].date)

          # Harivasara Computation
          if ekaadashii_paksha == 'shukla':
            def f(x):
              tp_float = NakshatraDivision(x, ayanaamsha_id=self.ayanaamsha_id).get_anga_float(
                zodiac.AngaType.TITHI_PADA)
              return tp_float - 45
            harivasara_end = brentq(
              f,
              self.daily_panchaangas[smaarta_ekaadashii_fday].jd_sunrise - 2,
              self.daily_panchaangas[smaarta_ekaadashii_fday].jd_sunrise + 2)
          else:
            def f(x):
              tp_float = NakshatraDivision(x, ayanaamsha_id=self.ayanaamsha_id).get_anga_float(
                zodiac.AngaType.TITHI_PADA)
              return tp_float - 105
            harivasara_end = brentq(
              f,
              self.daily_panchaangas[smaarta_ekaadashii_fday].jd_sunrise - 2,
              self.daily_panchaangas[smaarta_ekaadashii_fday].jd_sunrise + 2)
          _date = self.panchaanga.city.get_timezone_obj().julian_day_to_local_time(julian_day=harivasara_end)
          _date.set_time_to_day_start()
          fday_hv = time.utc_gregorian_to_jd(_date) - time.utc_gregorian_to_jd(self.daily_panchaangas[0].date)
          fest = FestivalInstance(name='harivAsaraH', interval=Interval(jd_start=None, jd_end=harivasara_end))
          if harivasara_end > self.daily_panchaangas[smaarta_ekaadashii_fday + 1].jd_sunrise:
            self.panchaanga.add_festival_instance(festival_instance=fest, date=self.daily_panchaangas[int(fday_hv)].date)

  def assign_mahaadvaadashii(self):
    if 'pakSavardhinI~mahAdvAdazI' not in self.rules_collection.name_to_rule:
      return 
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      day_panchaanga = self.daily_panchaangas[d]
      # 8 MAHA DWADASHIS
      if (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 11 and (self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise.index % 15) == 11:
        self.panchaanga.add_festival(fest_id='unmIlanI~mahAdvAdazI', date=day_panchaanga.date + 1)

      if (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 12 and (self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise.index % 15) == 12:
        self.panchaanga.add_festival(fest_id='vyaJjulI~mahAdvAdazI', date=day_panchaanga.date)

      if (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 11 and (self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise.index % 15) == 13:
        self.panchaanga.add_festival(fest_id='trisparzA~mahAdvAdazI', date=day_panchaanga.date)

      if (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 0 and (self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise.index % 15) == 0:
        # Might miss out on those parva days right after Dec 31!
        if (d - 3) > 0:
          self.panchaanga.add_festival(fest_id='pakSavardhinI~mahAdvAdazI', date=day_panchaanga.date - 3)

      if day_panchaanga.sunrise_day_angas.nakshatra_at_sunrise.index == 4 and (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 12:
        self.panchaanga.add_festival(fest_id='pApanAzinI~mahAdvAdazI', date=day_panchaanga.date)

      if day_panchaanga.sunrise_day_angas.nakshatra_at_sunrise.index == 7 and (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 12:
        self.panchaanga.add_festival(fest_id='jayantI~mahAdvAdazI', date=day_panchaanga.date)

      if day_panchaanga.sunrise_day_angas.nakshatra_at_sunrise.index == 8 and (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 12:
        self.panchaanga.add_festival(fest_id='jayA~mahAdvAdazI', date=day_panchaanga.date)

      if day_panchaanga.sunrise_day_angas.nakshatra_at_sunrise.index == 8 and (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 12 and day_panchaanga.lunar_month_sunrise.index == 12:
        # Better checking needed (for other than sunrise).
        # Last occurred on 27-02-1961 - pushya nakshatra and phalguna krishna dvadashi (or shukla!?)
        self.panchaanga.add_festival(fest_id='gOvinda~mahAdvAdazI', date=day_panchaanga.date)

      if (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 12:
        if day_panchaanga.sunrise_day_angas.nakshatra_at_sunrise.index in [21, 22, 23]:
          # We have a dvaadashii near shravana, check for Shravana sparsha
          for td in [x.sunrise_day_angas.tithis_with_ends for x in self.daily_panchaangas[d:d + 2]]:
            (t12, t12_end) = (td[0].anga, td[0].jd_end)
            if t12_end is None:
              continue
            if (t12 % 15) == 11:
              if NakshatraDivision(t12_end, ayanaamsha_id=self.ayanaamsha_id).get_anga(
                  zodiac.AngaType.NAKSHATRA).index == 22:
                if (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 12 and (self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise.index % 15) == 12:
                  self.panchaanga.add_festival(fest_id='vijayA/zravaNa-mahAdvAdazI', date=day_panchaanga.date)
                elif (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 12:
                  self.panchaanga.add_festival(fest_id='vijayA/zravaNa-mahAdvAdazI', date=day_panchaanga.date)
                elif (self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise.index % 15) == 12:
                  self.panchaanga.add_festival(fest_id='vijayA/zravaNa-mahAdvAdazI', date=day_panchaanga.date + 1)
            if (t12 % 15) == 12:
              if NakshatraDivision(t12_end, ayanaamsha_id=self.ayanaamsha_id).get_anga(
                  zodiac.AngaType.NAKSHATRA).index == 22:
                if (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 12 and (self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise.index % 15) == 12:
                  self.panchaanga.add_festival(fest_id='vijayA/zravaNa-mahAdvAdazI', date=day_panchaanga.date)
                elif (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 12:
                  self.panchaanga.add_festival(fest_id='vijayA/zravaNa-mahAdvAdazI', date=day_panchaanga.date)
                elif (self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise.index % 15) == 12:
                  self.panchaanga.add_festival(fest_id='vijayA/zravaNa-mahAdvAdazI', date=day_panchaanga.date + 1)

      if day_panchaanga.sunrise_day_angas.nakshatra_at_sunrise.index == 22 and (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index % 15) == 12:
        self.panchaanga.add_festival(fest_id='vijayA/zravaNa-mahAdvAdazI', date=day_panchaanga.date)

  def assign_pradosha_vratam(self):
    if 'pradOSa-vratam' not in self.rules_collection.name_to_rule:
      return
    # त्रयोदश्यां प्रदोषकाले व्रतम्।
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      day_panchaanga = self.daily_panchaangas[d]
      # compute offset from UTC in hours
      # PRADOSHA Vratam
      pref = ''
      tithi_sunset = day_panchaanga.sunrise_day_angas.get_anga_at_jd(jd=day_panchaanga.jd_sunset, anga_type=AngaType.TITHI) % 15
      tithi_sunset_tmrw = self.daily_panchaangas[d+1].sunrise_day_angas.get_anga_at_jd(jd=self.daily_panchaangas[d+1].jd_sunset, anga_type=AngaType.TITHI) % 15
      fday = None
      if tithi_sunset_tmrw == 13:
        # Let's worry about assigning this tomorrow!
        continue
      if tithi_sunset in [12, 13] and tithi_sunset_tmrw in [14, 0]:
        jd_pradosha_end_today = day_panchaanga.day_length_based_periods.fifteen_fold_division.pradosha.jd_end
        if day_panchaanga.sunrise_day_angas.get_anga_at_jd(jd=jd_pradosha_end_today, anga_type=AngaType.TITHI) % 15 == 12:
          fday = d + 1
        else:
          fday = d
      elif tithi_sunset in [12, 13] and tithi_sunset_tmrw == 13:
        fday = d + 1
      if fday is not None:
        if self.daily_panchaangas[fday].date.get_weekday() == 1:
          pref = 'sOma-'
        elif self.daily_panchaangas[fday].date.get_weekday() == 6:
          pref = 'zani-'
        self.panchaanga.add_festival(fest_id=pref + 'pradOSa-vratam', date=self.daily_panchaangas[fday].date, interval_id="pradosha")

  def assign_solar_sidereal_amaavaasyaa(self):
    if 'sidereal_solar_month_amAvAsyA' not in self.rules_collection.name_to_rule:
      return 
    if 'sidereal_solar_month_amAvAsyA' not in self.panchaanga.festival_id_to_days:
      logging.error('Must compute amAvAsyA before coming here!')
      return 
    ama_days = self.panchaanga.festival_id_to_days['sidereal_solar_month_amAvAsyA']
    for ama_day in ama_days:
      d = int(ama_day - self.daily_panchaangas[0].date)
      day_panchaanga = self.daily_panchaangas[d]
      # Get Name
      if day_panchaanga.lunar_month_sunrise.index == 6:
        pref = '(%s) mahAlaya ' % (
          names.get_chandra_masa(day_panchaanga.lunar_month_sunrise.index, sanscript.roman.HK_DRAVIDIAN, visarga=False))
      elif day_panchaanga.solar_sidereal_date_sunset.month == 4:
        pref = '%s (karkaTa) ' % (
          names.get_chandra_masa(day_panchaanga.lunar_month_sunrise.index, sanscript.roman.HK_DRAVIDIAN, visarga=False))
      elif day_panchaanga.solar_sidereal_date_sunset.month == 10:
        pref = 'mauni (%s/makara) ' % (
          names.get_chandra_masa(day_panchaanga.lunar_month_sunrise.index,  sanscript.roman.HK_DRAVIDIAN, visarga=False))
      else:
        pref = names.get_chandra_masa(day_panchaanga.lunar_month_sunrise.index,  sanscript.roman.HK_DRAVIDIAN,
                                      visarga=False) + '-'

      apraahna_interval = day_panchaanga.get_interval("अपराह्णः")
      ama_nakshatra_today = [y for y in apraahna_interval.get_boundary_angas(anga_type=AngaType.NAKSHATRA, ayanaamsha_id=self.ayanaamsha_id).to_tuple()]
      suff = ''
      # Assign
      if 23 in ama_nakshatra_today and day_panchaanga.lunar_month_sunrise.index == 11:
        suff = ' (alabhyam–mAgha-zraviSThA)'
      elif 24 in ama_nakshatra_today and day_panchaanga.lunar_month_sunrise.index == 11:
        suff = ' (alabhyam–mAgha-zatabhiSak)'
      elif ama_nakshatra_today[0] in [15, 16, 17, 6, 7, 8, 23, 24, 25]:
        suff = ' (alabhyam–%s)' % names.NAMES['NAKSHATRA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][ama_nakshatra_today[0]]
      elif ama_nakshatra_today[1] in [15, 16, 17, 6, 7, 8, 23, 24, 25]:
        suff = ' (alabhyam–%s)' % names.NAMES['NAKSHATRA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][ama_nakshatra_today[1]]
      if day_panchaanga.date.get_weekday() in [1, 2, 4]:
        if suff == '':
          suff = ' (alabhyam–puSkalA)'
        else:
          suff = suff.replace(')', ', puSkalA)')
      self.panchaanga.add_festival(fest_id=pref + 'amAvAsyA' + suff, date=day_panchaanga.date)

    self.panchaanga.delete_festival(fest_id='sidereal_solar_month_amAvAsyA')

  def assign_amaavaasyaa_soma(self):
    if 'sOmavatI_amAvAsyA' not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      day_panchaanga = self.daily_panchaangas[d]
      # SOMAMAVASYA
      if day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 30 and day_panchaanga.date.get_weekday() == 1:
        self.panchaanga.add_festival(fest_id='sOmavatI amAvAsyA', date=day_panchaanga.date)

  def assign_amaavaasya_vyatiipaata(self):
    if 'vyatIpAta-yOgaH_(alabhyam)' not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      day_panchaanga = self.daily_panchaangas[d]
      # AMA-VYATIPATA YOGAH
      # श्रवणाश्विधनिष्ठार्द्रानागदैवतमापतेत् ।
      # रविवारयुतामायां व्यतीपातः स उच्यते ॥
      # व्यतीपाताख्ययोगोऽयं शतार्कग्रहसन्निभः ॥
      # “In Mahabharata, if on a Sunday, Amavasya and one of the stars –
      # Sravanam, Asvini, Avittam, Tiruvadirai or Ayilyam, occurs, then it is called ‘Vyatipatam’.
      # This Vyatipata yoga is equal to a hundred Surya grahanas in merit.”
      tithi_sunset = NakshatraDivision(day_panchaanga.jd_sunset, ayanaamsha_id=self.ayanaamsha_id).get_anga(
        zodiac.AngaType.TITHI).index
      if day_panchaanga.date.get_weekday() == 0 and (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 30 or tithi_sunset == 30):
        # AMAVASYA on a Sunday
        if (day_panchaanga.sunrise_day_angas.nakshatra_at_sunrise.index in [1, 6, 9, 22, 23] and day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 30) or \
            (tithi_sunset == 30 and 
             NakshatraDivision(day_panchaanga.jd_sunset,
             ayanaamsha_id=self.ayanaamsha_id).get_anga(zodiac.AngaType.NAKSHATRA).index in [1, 6, 9, 22, 23]):
          festival_name = 'vyatIpAta-yOgaH (alabhyam)'
          self.panchaanga.add_festival(fest_id=festival_name, date=day_panchaanga.date)


  def assign_mahaa_paurnamii(self):
    if 'mahAcaitrI-yOgaH' not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      day_panchaanga = self.daily_panchaangas[d]

      tithi_sunset = NakshatraDivision(day_panchaanga.jd_sunset, ayanaamsha_id=self.ayanaamsha_id).get_anga(
        zodiac.AngaType.TITHI).index

      if day_panchaanga.date.get_weekday() == 4 and (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 15 or tithi_sunset == 15):
        # PURNIMA on a Thursday
        lunar_month = int(day_panchaanga.lunar_month_sunrise.index) # to deal with adhika mAsas
        lunar_month_nakshatra = [None, 14, 16, 18, 20, 22, 25, 1, 3, 5, 8, 10, 11]
        fest_yoga_names = [None,  "caitrI", "vaizAkhI", "jyaiSThI", "ASADhI", "zrAvaNI", "bhAdrapadI", "AzvayujI", "kArtikI", "mArgazIrSI", "pauSI", "mAghI", "phAlgunI"]
        if (day_panchaanga.sunrise_day_angas.nakshatra_at_sunrise.index == lunar_month_nakshatra[lunar_month] and day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 15) or \
            (tithi_sunset == 15 and NakshatraDivision(day_panchaanga.jd_sunset, ayanaamsha_id=self.ayanaamsha_id).get_anga(zodiac.AngaType.NAKSHATRA).index == lunar_month_nakshatra[lunar_month]):
          festival_name = 'mahA-%s-yOgaH' % fest_yoga_names[lunar_month]
          self.panchaanga.add_festival(fest_id=festival_name, date=day_panchaanga.date)

  def assign_yama_chaturthi(self):
    if 'yamacaturthI-vratam' not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      day_panchaanga = self.daily_panchaangas[d]
      # चतुर्थी भरणीयोगः शनैश्चरदिने यदि ।
      # तदाभ्यर्च्य यमं देवं मुच्यते सर्वकिल्विषैः ॥
      tithi_sunset = NakshatraDivision(day_panchaanga.jd_sunset, ayanaamsha_id=self.ayanaamsha_id).get_anga(
        zodiac.AngaType.TITHI).index
      nakshatra_sunset = NakshatraDivision(day_panchaanga.jd_sunset, ayanaamsha_id=self.ayanaamsha_id).get_anga(
        zodiac.AngaType.NAKSHATRA).index
      if day_panchaanga.date.get_weekday() == 6 and (day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index in [4, 19] or tithi_sunset in [4, 19]):
        if day_panchaanga.sunrise_day_angas.nakshatra_at_sunrise.index == 2 or  nakshatra_sunset == 2:
          festival_name = 'yamacaturthI-vratam'
          self.panchaanga.add_festival(fest_id=festival_name, date=day_panchaanga.date)

  def assign_vajapeyaphala_snana_yoga(self):
    if 'vAjapEyaphala-snAna-yOgaH' not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      day_panchaanga = self.daily_panchaangas[d]
      # पुनर्वसुबुधोपेता चैत्रे मासि सिताष्टमी।
      # प्रातस्तु विधिवत्स्नात्वा वाजपेयफलं लभेत्॥
      if day_panchaanga.lunar_month_sunrise.index == 1 and day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 8 and day_panchaanga.date.get_weekday() == 3 and day_panchaanga.sunrise_day_angas.nakshatra_at_sunrise.index == 7:
        festival_name = 'vAjapEyaphala-snAna-yOgaH'
        self.panchaanga.add_festival(fest_id=festival_name, date=day_panchaanga.date)

  def assign_chandra_darshanam(self, force_computation=False):
    if 'candra-darzanam' not in self.rules_collection.name_to_rule and not force_computation:
      return
    d = self.panchaanga.duration_prior_padding
    while d < self.panchaanga.duration + self.panchaanga.duration_prior_padding:
      day_panchaanga = self.daily_panchaangas[d]
      # Chandra Darshanam
      if day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 1 or day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 2:
        tithi_sunset = temporal.tithi.get_tithi(day_panchaanga.jd_sunset).index
        tithi_sunset_tmrw = temporal.tithi.get_tithi(self.daily_panchaangas[d + 1].jd_sunset).index
        # if tithi_sunset <= 2 and tithi_sunset_tmrw != 2:
        if tithi_sunset <= 2:
          if tithi_sunset == 1:
            fest = FestivalInstance(name='candra-darzanam', interval=Interval(jd_start=self.daily_panchaangas[d+1].jd_sunset, jd_end=self.daily_panchaangas[d+1].jd_moonset))
            self.panchaanga.add_festival_instance(festival_instance=fest, date=self.daily_panchaangas[d+1].date)
            
            d += 25
          else:
            fest = FestivalInstance(name='candra-darzanam', interval=Interval(jd_start=self.daily_panchaangas[d].jd_sunset, jd_end=self.daily_panchaangas[d].jd_moonset))
            self.panchaanga.add_festival_instance(festival_instance=fest, date=self.daily_panchaangas[d].date)
            d += 25
        elif tithi_sunset_tmrw == 2:
          fest = FestivalInstance(name='candra-darzanam', interval=Interval(jd_start=self.daily_panchaangas[d+1].jd_sunset, jd_end=self.daily_panchaangas[d+1].jd_moonset))
          self.panchaanga.add_festival_instance(festival_instance=fest, date=self.daily_panchaangas[d+1].date)
          d += 25
      d += 1

  def assign_bodhaayana_amaavaasyaa(self):
    chandra_darshanam_days = list(self.panchaanga.festival_id_to_days['candra-darzanam'])
    for cdd in chandra_darshanam_days:
      if 'darsheShTiH' in self.panchaanga.daily_panchaanga_for_date(cdd).festival_id_to_instance.keys():
        self.panchaanga.add_festival(fest_id='bOdhAyana-iSTiH', date=self.panchaanga.daily_panchaanga_for_date(cdd - 1).date)

      ama_fest = [val for key, val in self.panchaanga.daily_panchaanga_for_date(cdd - 1).festival_id_to_instance.items() if 'amAvAsyA' in key]
      if ama_fest:
        # We have amAvAsyA preceding chandra darshanam. Therefore, the previous day must be assigned as bOdhAayana
        bodhaayana_fest = re.sub('amAvAsyA.*', 'amAvAsyA', 'bOdhAyana-' + ama_fest[0].name)
        self.panchaanga.add_festival(fest_id=bodhaayana_fest, date=self.panchaanga.daily_panchaanga_for_date(cdd - 2).date)
        self.panchaanga.add_festival(fest_id='bOdhAyana-iSTiH', date=self.panchaanga.daily_panchaanga_for_date(cdd - 1).date)
      else:
        for key, val in dict(self.panchaanga.daily_panchaanga_for_date(cdd - 2).festival_id_to_instance).items():
          if 'amAvAsyA' in key:
            fest_id = key
            self.panchaanga.delete_festival_date(fest_id=fest_id, date=self.panchaanga.daily_panchaanga_for_date(cdd - 2).date)
            self.panchaanga.add_festival(fest_id='sarva-' + fest_id, date=self.panchaanga.daily_panchaanga_for_date(cdd - 2).date)
    if 'candra-darzanam' not in self.rules_collection.name_to_rule:
      self.panchaanga.delete_festival(fest_id='candra-darzanam')

  def assign_vaarunii_trayodashi(self):
    if 'vAruNI~trayOdazI' not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      day_panchaanga = self.daily_panchaangas[d]
      # VARUNI TRAYODASHI
      if day_panchaanga.lunar_month_sunrise.index == 12 and day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 28:
        if NakshatraDivision(day_panchaanga.jd_sunrise, ayanaamsha_id=self.ayanaamsha_id).get_anga(
            zodiac.AngaType.NAKSHATRA).index == 24:
          vtr_name = 'vAruNI~trayOdazI'
          if day_panchaanga.date.get_weekday() == 6:
            vtr_name = 'mahA' + vtr_name
            if NakshatraDivision(day_panchaanga.jd_sunrise, ayanaamsha_id=self.ayanaamsha_id).get_anga(
                zodiac.AngaType.YOGA).index == 23:
              vtr_name = 'mahA' + vtr_name
          self.panchaanga.add_festival(fest_id=vtr_name, date=day_panchaanga.date)


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
