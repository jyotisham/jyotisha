import logging
import sys
from datetime import datetime
from math import floor

from pytz import timezone as tz
from scipy.optimize import brentq

from jyotisha import names
from jyotisha.panchaanga import temporal
from jyotisha.panchaanga.temporal import time
from jyotisha.panchaanga.temporal import zodiac, tithi
from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal.festival import FestivalInstance
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision
from sanskrit_data.schema import common


class TithiFestivalAssigner(FestivalAssigner):
  def assign_all(self, debug=False):
    self.assign_chandra_darshanam(debug_festivals=debug)
    self.assign_chaturthi_vratam(debug_festivals=debug)
    self.assign_shasthi_vratam(debug_festivals=debug)
    self.assign_vishesha_saptami(debug_festivals=debug)
    self.assign_ekaadashii_vratam(debug_festivals=debug)
    self.assign_mahaadvaadashii(debug_festivals=debug)
    self.assign_pradosha_vratam(debug_festivals=debug)
    self.assign_vishesha_trayodashi(debug_festivals=debug)
    self.assign_amavasya_yoga(debug_festivals=debug)
  
  def assign_chaturthi_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

      # SANKATAHARA chaturthi
      if self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise == 18 or self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise == 19:
        ldiff_moonrise_yest = (Graha.singleton(Graha.MOON).get_longitude(self.daily_panchaangas[d - 1].jd_moonrise) - Graha.singleton(
          Graha.SUN).get_longitude(self.daily_panchaangas[d - 1].jd_moonrise)) % 360
        ldiff_moonrise = (Graha.singleton(Graha.MOON).get_longitude(self.daily_panchaangas[d].jd_moonrise) - Graha.singleton(Graha.SUN).get_longitude(
          self.daily_panchaangas[d].jd_moonrise)) % 360
        ldiff_moonrise_tmrw = (Graha.singleton(Graha.MOON).get_longitude(self.daily_panchaangas[d + 1].jd_moonrise) - Graha.singleton(
          Graha.SUN).get_longitude(self.daily_panchaangas[d + 1].jd_moonrise)) % 360
        tithi_moonrise_yest = int(1 + floor(ldiff_moonrise_yest / 12.0))
        tithi_moonrise = int(1 + floor(ldiff_moonrise / 12.0))
        tithi_moonrise_tmrw = int(1 + floor(ldiff_moonrise_tmrw / 12.0))

        _m = self.daily_panchaangas[d].lunar_month_sunrise
        if floor(_m) != _m:
          _m = 13  # Adhika masa
        chaturthi_name = names.NAMES['SANKATAHARA_CHATURTHI_NAMES']['hk'][_m] + '-mahAgaNapati '

        if tithi_moonrise == 19:
          # otherwise yesterday would have already been assigned
          if tithi_moonrise_yest != 19:
            chaturthi_name = '%s%s' % ('aGgArakI~' if self.daily_panchaangas[d].date.get_weekday() == 2 else '', chaturthi_name)
            fest = FestivalInstance(
              name=chaturthi_name + 'saGkaTahara-caturthI-vratam')
            self.daily_panchaangas[d].festival_id_to_instance[fest.name] =  fest
            # shravana krishna chaturthi
            if self.daily_panchaangas[d].lunar_month_sunrise == 5:
              chaturthi_name = '%s%s' % ('aGgArakI~' if self.daily_panchaangas[d].date.get_weekday() == 2 else '', chaturthi_name)
              fest = FestivalInstance(
                name=chaturthi_name + 'mahAsaGkaTahara-caturthI-vratam')
              self.daily_panchaangas[d].festival_id_to_instance[fest.name] = fest
        elif tithi_moonrise_tmrw == 19:
          chaturthi_name = '%s%s' % ('aGgArakI~' if self.daily_panchaangas[d + 1].date.get_weekday() == 2 else '', chaturthi_name)
          fest = FestivalInstance(
            name=chaturthi_name + 'saGkaTahara-caturthI-vratam')
          self.daily_panchaangas[d + 1].festival_id_to_instance[fest.name] =  fest
          # self.date_str_to_panchaanga[d].lunar_month_sunrise and[d + 1] are same, so checking [d] is enough
          if self.daily_panchaangas[d].lunar_month_sunrise == 5:
            chaturthi_name = '%s%s' % ('aGgArakI~' if self.daily_panchaangas[d].date.get_weekday() == 2 else '', chaturthi_name)
            fest = FestivalInstance(
              name=chaturthi_name + 'mahAsaGkaTahara-caturthI-vratam')
            self.daily_panchaangas[d + 1].festival_id_to_instance[fest.name] = fest
        else:
          if tithi_moonrise_yest != 19:
            if tithi_moonrise == 18 and tithi_moonrise_tmrw == 20:
              # No vyApti on either day -- pick parA, i.e. next day.
              chaturthi_name = '%s%s' % ('aGgArakI~' if self.daily_panchaangas[d + 1].date.get_weekday() == 2 else '', chaturthi_name)
              fest = FestivalInstance(
                name=chaturthi_name + 'saGkaTahara-caturthI-vratam')
              self.daily_panchaangas[d + 1].festival_id_to_instance[fest.name] =  fest
              # shravana krishna chaturthi
              if self.daily_panchaangas[d].lunar_month_sunrise == 5:
                chaturthi_name = '%s%s' % (
                  'aGgArakI~' if self.daily_panchaangas[d + 1].date.get_weekday() == 2 else '', chaturthi_name)
                fest = FestivalInstance(
                  name=chaturthi_name + 'mahAsaGkaTahara-caturthI-vratam')
                self.daily_panchaangas[d + 1].festival_id_to_instance[fest.name] = fest

  def assign_shasthi_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()
      # # SHASHTHI Vratam
      # Check only for Adhika maasa here...
      festival_name = 'SaSThI-vratam'
      if self.daily_panchaangas[d].lunar_month_sunrise == 8:
        festival_name = 'skanda' + festival_name
      elif self.daily_panchaangas[d].lunar_month_sunrise == 4:
        festival_name = 'kumAra-' + festival_name
      elif self.daily_panchaangas[d].lunar_month_sunrise == 6:
        festival_name = 'SaSThIdEvI-' + festival_name
      elif self.daily_panchaangas[d].lunar_month_sunrise == 9:
        festival_name = 'subrahmaNya-' + festival_name

      if self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise == 5 or self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise == 6:
        angams = self.panchaanga.get_angas_for_interval_boundaries(d, lambda x: temporal.tithi.get_tithi(x),
                                            'madhyaahna')
        if angams[0] == 6 or angams[1] == 6:
          if festival_name in self.panchaanga.festival_id_to_days:
            # Check if yesterday was assigned already
            # to this puurvaviddha festival!
            if self.panchaanga.festival_id_to_days[festival_name].count(self.daily_panchaangas[d - 1].date) == 0:
              self.add_festival(festival_name, d)
          else:
            self.add_festival(festival_name, d)
        elif angams[2] == 6 or angams[3] == 6:
          self.add_festival(festival_name, d + 1)
        else:
          # This means that the correct anga did not
          # touch the kaala on either day!
          # sys.stderr.write('Could not assign puurvaviddha day for %s!\
          # Please check for unusual cases.\n' % festival_name)
          if angams[2] == 6 + 1 or angams[3] == 6 + 1:
            # Need to assign a day to the festival here
            # since the anga did not touch kaala on either day
            # BUT ONLY IF YESTERDAY WASN'T ALREADY ASSIGNED,
            # THIS BEING PURVAVIDDHA
            # Perhaps just need better checking of
            # conditions instead of this fix
            if festival_name in self.panchaanga.festival_id_to_days:
              if self.panchaanga.festival_id_to_days[festival_name].count(self.daily_panchaangas[d - 1].date) == 0:
                self.add_festival(festival_name, d)
            else:
              self.add_festival(festival_name, d)

  def assign_vishesha_saptami(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

      # SPECIAL SAPTAMIs
      if self.daily_panchaangas[d].date.get_weekday() == 0 and (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 7:
        festival_name = 'bhAnusaptamI'
        if self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise == 7:
          festival_name = 'vijayA' + '~' + festival_name
        if self.daily_panchaangas[d].sunrise_day_angas.nakshatra_at_sunrise == 27:
          # Even more auspicious!
          festival_name += '★'
        self.add_festival(festival_name, d)

      if NakshatraDivision(self.daily_panchaangas[d].jd_sunrise, ayanaamsha_id=self.ayanaamsha_id).get_anga(
          zodiac.AngaType.NAKSHATRA_PADA) == 49 and \
          self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise == 7:
        self.add_festival('bhadrA~saptamI', d)

      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition is not None:
        # we have a Sankranti!
        if self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise == 7:
          self.add_festival('mahAjayA~saptamI', d)

  def assign_ekaadashii_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

      # checking @ 6am local - can we do any better?
      local_time = tz(self.panchaanga.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
      # compute offset from UTC in hours
      tz_off = (datetime.utcoffset(local_time).days * 86400 +
                datetime.utcoffset(local_time).seconds) / 3600.0

      # EKADASHI Vratam
      # One of two consecutive tithis must appear @ sunrise!

      if (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 10 or (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 11:
        yati_ekaadashii_fday = smaarta_ekaadashii_fday = vaishnava_ekaadashii_fday = None
        ekaadashii_tithi_days = [x.sunrise_day_angas.tithi_at_sunrise % 15 for x in self.daily_panchaangas[d:d + 3]]
        if self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise > 15:
          ekaadashii_paksha = 'krishna'
        else:
          ekaadashii_paksha = 'shukla'
        if ekaadashii_tithi_days in [[11, 11, 12], [10, 12, 12]]:
          smaarta_ekaadashii_fday = d + 1
          tithi_arunodayam = tithi.get_tithi(self.daily_panchaangas[d + 1].jd_sunrise - (1 / 15.0) * (self.daily_panchaangas[d + 1].jd_sunrise - self.daily_panchaangas[d].jd_sunrise))
          if tithi_arunodayam % 15 == 10:
            vaishnava_ekaadashii_fday = d + 2
          else:
            vaishnava_ekaadashii_fday = d + 1
        elif ekaadashii_tithi_days in [[10, 12, 13], [11, 12, 13], [11, 12, 12], [11, 12, 14]]:
          smaarta_ekaadashii_fday = d
          tithi_arunodayam = temporal.tithi.get_tithi(self.daily_panchaangas[d].jd_sunrise - (1 / 15.0) * (self.daily_panchaangas[d].jd_sunrise - self.daily_panchaangas[d - 1].jd_sunrise))
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
            self.add_festival(
              'sarva-' + names.get_ekaadashii_name(ekaadashii_paksha, self.daily_panchaangas[d].lunar_month_sunrise),
              smaarta_ekaadashii_fday)
            if ekaadashii_paksha == 'shukla':
              if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 9:
                self.add_festival('sarva-vaikuNTha-EkAdazI', smaarta_ekaadashii_fday)
          else:
            self.add_festival(
              'smArta-' + names.get_ekaadashii_name(ekaadashii_paksha, self.daily_panchaangas[d].lunar_month_sunrise),
              smaarta_ekaadashii_fday)
            self.add_festival(
              'vaiSNava-' + names.get_ekaadashii_name(ekaadashii_paksha, self.daily_panchaangas[d].lunar_month_sunrise),
              vaishnava_ekaadashii_fday)
            if ekaadashii_paksha == 'shukla':
              if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 9:
                self.add_festival('smArta-vaikuNTha-EkAdazI', smaarta_ekaadashii_fday)
                self.add_festival('vaiSNava-vaikuNTha-EkAdazI', vaishnava_ekaadashii_fday,
                                  debug_festivals)
        else:
          self.add_festival('smArta-' + names.get_ekaadashii_name(ekaadashii_paksha,
                                                                  self.daily_panchaangas[d].lunar_month_sunrise) + ' (gRhastha)',
                            smaarta_ekaadashii_fday)
          self.add_festival('smArta-' + names.get_ekaadashii_name(ekaadashii_paksha, self.daily_panchaangas[
            d].lunar_month_sunrise) + ' (sannyastha)', yati_ekaadashii_fday)
          self.add_festival(
            'vaiSNava-' + names.get_ekaadashii_name(ekaadashii_paksha, self.daily_panchaangas[d].lunar_month_sunrise),
            vaishnava_ekaadashii_fday)
          if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 9:
            if ekaadashii_paksha == 'shukla':
              self.add_festival('smArta-vaikuNTha-EkAdazI (gRhastha)', smaarta_ekaadashii_fday)
              self.add_festival('smArta-vaikuNTha-EkAdazI (sannyastha)', yati_ekaadashii_fday)
              self.add_festival('vaiSNava-vaikuNTha-EkAdazI', vaishnava_ekaadashii_fday)

        if yati_ekaadashii_fday == smaarta_ekaadashii_fday == vaishnava_ekaadashii_fday is None:
          # Must have already assigned
          pass
        else:
          if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 8 and ekaadashii_paksha == 'shukla':
            # self.add_festival('guruvAyupura-EkAdazI', smaarta_ekaadashii_fday)
            self.add_festival('guruvAyupura-EkAdazI', vaishnava_ekaadashii_fday)
            self.add_festival('kaizika-EkAdazI', vaishnava_ekaadashii_fday)

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
          _date = time.jd_to_utc_gregorian(harivasara_end + (tz_off / 24.0))
          _date.set_time_to_day_start()
          fday_hv = time.utc_gregorian_to_jd(_date) - self.panchaanga.jd_start + 1
          fest = FestivalInstance(name='harivAsaraH', interval=Interval(jd_start=None, jd_end=harivasara_end))
          self.daily_panchaangas[int(fday_hv)].festival_id_to_instance[fest.name] =  fest

  def assign_mahaadvaadashii(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()
      # 8 MAHA DWADASHIS
      if (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 11 and (self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise % 15) == 11:
        self.add_festival('unmIlanI~mahAdvAdazI', d + 1)

      if (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 12 and (self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise % 15) == 12:
        self.add_festival('vyaJjulI~mahAdvAdazI', d)

      if (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 11 and (self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise % 15) == 13:
        self.add_festival('trisparzA~mahAdvAdazI', d)

      if (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 0 and (self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise % 15) == 0:
        # Might miss out on those parva days right after Dec 31!
        if (d - 3) > 0:
          self.add_festival('pakSavardhinI~mahAdvAdazI', d - 3)

      if self.daily_panchaangas[d].sunrise_day_angas.nakshatra_at_sunrise == 4 and (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 12:
        self.add_festival('pApanAzinI~mahAdvAdazI', d)

      if self.daily_panchaangas[d].sunrise_day_angas.nakshatra_at_sunrise == 7 and (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 12:
        self.add_festival('jayantI~mahAdvAdazI', d)

      if self.daily_panchaangas[d].sunrise_day_angas.nakshatra_at_sunrise == 8 and (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 12:
        self.add_festival('jayA~mahAdvAdazI', d)

      if self.daily_panchaangas[d].sunrise_day_angas.nakshatra_at_sunrise == 8 and (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 12 and self.daily_panchaangas[d].lunar_month_sunrise == 12:
        # Better checking needed (for other than sunrise).
        # Last occurred on 27-02-1961 - pushya nakshatra and phalguna krishna dvadashi (or shukla!?)
        self.add_festival('gOvinda~mahAdvAdazI', d)

      if (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 12:
        if self.daily_panchaangas[d].sunrise_day_angas.nakshatra_at_sunrise in [21, 22, 23]:
          # We have a dvaadashii near shravana, check for Shravana sparsha
          for td in [x.sunrise_day_angas.tithis_with_ends for x in self.daily_panchaangas[d:d + 2]]:
            (t12, t12_end) = (td[0].name, td[0].jd_end)
            if t12_end is None:
              continue
            if (t12 % 15) == 11:
              if NakshatraDivision(t12_end, ayanaamsha_id=self.ayanaamsha_id).get_anga(
                  zodiac.AngaType.NAKSHATRA) == 22:
                if (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 12 and (self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d)
                elif (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d)
                elif (self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d + 1)
            if (t12 % 15) == 12:
              if NakshatraDivision(t12_end, ayanaamsha_id=self.ayanaamsha_id).get_anga(
                  zodiac.AngaType.NAKSHATRA) == 22:
                if (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 12 and (self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d)
                elif (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d)
                elif (self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d + 1)

      if self.daily_panchaangas[d].sunrise_day_angas.nakshatra_at_sunrise == 22 and (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise % 15) == 12:
        self.add_festival('vijayA/zravaNa-mahAdvAdazI', d)

  def assign_pradosha_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()
      # compute offset from UTC in hours
      # PRADOSHA Vratam
      pref = ''
      if self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise in (12, 13, 27, 28):
        tithi_sunset = temporal.tithi.get_tithi(self.daily_panchaangas[d].jd_sunset) % 15
        tithi_sunset_tmrw = temporal.tithi.get_tithi(self.daily_panchaangas[d + 1].jd_sunset) % 15
        if tithi_sunset <= 13 and tithi_sunset_tmrw != 13:
          fday = d
        elif tithi_sunset_tmrw == 13:
          fday = d + 1
        if self.daily_panchaangas[fday].date.get_weekday() == 1:
          pref = 'sOma-'
        elif self.daily_panchaangas[fday].date.get_weekday() == 6:
          pref = 'zani-'
        self.add_festival(pref + 'pradOSa-vratam', fday)

  def assign_amavasya_yoga(self, debug_festivals=False):
    if 'amAvAsyA' not in self.panchaanga.festival_id_to_days:
      logging.error('Must compute amAvAsyA before coming here!')
    else:
      ama_days = self.panchaanga.festival_id_to_days['amAvAsyA']
      for ama_day in ama_days:
        d = int(ama_day - self.daily_panchaangas[0].date)
        # Get Name
        if self.daily_panchaangas[d].lunar_month_sunrise == 6:
          pref = '(%s) mahAlaya ' % (
            names.get_chandra_masa(self.daily_panchaangas[d].lunar_month_sunrise, names.NAMES, 'hk', visarga=False))
        elif self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 4:
          pref = '%s (kaTaka) ' % (
            names.get_chandra_masa(self.daily_panchaangas[d].lunar_month_sunrise, names.NAMES, 'hk', visarga=False))
        elif self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 10:
          pref = 'mauni (%s/makara) ' % (
            names.get_chandra_masa(self.daily_panchaangas[d].lunar_month_sunrise, names.NAMES, 'hk', visarga=False))
        else:
          pref = names.get_chandra_masa(self.daily_panchaangas[d].lunar_month_sunrise, names.NAMES, 'hk',
                                        visarga=False) + '-'

        ama_nakshatra_today = self.panchaanga.get_angas_for_interval_boundaries(d, lambda x: NakshatraDivision(x,
                                                                                                                ayanaamsha_id=self.ayanaamsha_id).get_nakshatra(),
                                                          'aparaahna')[:2]
        suff = ''
        # Assign
        if 23 in ama_nakshatra_today and self.daily_panchaangas[d].lunar_month_sunrise == 10:
          suff = ' (alabhyam–zraviSThA)'
        elif 24 in ama_nakshatra_today and self.daily_panchaangas[d].lunar_month_sunrise == 10:
          suff = ' (alabhyam–zatabhiSak)'
        elif ama_nakshatra_today[0] in [15, 16, 17, 6, 7, 8, 23, 24, 25]:
          suff = ' (alabhyam–%s)' % names.NAMES['NAKSHATRA_NAMES']['hk'][ama_nakshatra_today[0]]
        elif ama_nakshatra_today[1] in [15, 16, 17, 6, 7, 8, 23, 24, 25]:
          suff = ' (alabhyam–%s)' % names.NAMES['NAKSHATRA_NAMES']['hk'][ama_nakshatra_today[1]]
        if self.daily_panchaangas[d].date.get_weekday() in [1, 2, 4]:
          if suff == '':
            suff = ' (alabhyam–puSkalA)'
          else:
            suff = suff.replace(')', ', puSkalA)')
        self.add_festival(pref + 'amAvAsyA' + suff, d)
    if 'amAvAsyA' in self.panchaanga.festival_id_to_days:
      del self.panchaanga.festival_id_to_days['amAvAsyA']

    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

      # SOMAMAVASYA
      if self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise == 30 and self.daily_panchaangas[d].date.get_weekday() == 1:
        self.add_festival('sOmavatI amAvAsyA', d)

      # AMA-VYATIPATA YOGAH
      # श्रवणाश्विधनिष्ठार्द्रानागदैवतमापतेत् ।
      # रविवारयुतामायां व्यतीपातः स उच्यते ॥
      # व्यतीपाताख्ययोगोऽयं शतार्कग्रहसन्निभः ॥
      # “In Mahabharata, if on a Sunday, Amavasya and one of the stars –
      # Sravanam, Asvini, Avittam, Tiruvadirai or Ayilyam, occurs, then it is called ‘Vyatipatam’.
      # This Vyatipata yoga is equal to a hundred Surya grahanas in merit.”
      tithi_sunset = NakshatraDivision(self.daily_panchaangas[d].jd_sunset, ayanaamsha_id=self.ayanaamsha_id).get_anga(
        zodiac.AngaType.TITHI)
      if self.daily_panchaangas[d].date.get_weekday() == 0 and (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise == 30 or tithi_sunset == 30):
        # AMAVASYA on a Sunday
        if (self.daily_panchaangas[d].sunrise_day_angas.nakshatra_at_sunrise in [1, 6, 9, 22, 23] and self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise == 30) or \
            (tithi_sunset == 30 and NakshatraDivision(self.daily_panchaangas[d].jd_sunset,
                                                      ayanaamsha_id=self.ayanaamsha_id).get_anga(
              zodiac.AngaType.NAKSHATRA) in [
               1, 6, 9, 22, 23]):
          festival_name = 'vyatIpAta-yOgaH (alabhyam)'
          self.add_festival(festival_name, d)
          logging.debug('* %d-%02d-%02d> %s!' % (y, m, dt, festival_name))

  def assign_chandra_darshanam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()
      # Chandra Darshanam
      if self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise == 1 or self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise == 2:
        tithi_sunset = temporal.tithi.get_tithi(self.daily_panchaangas[d].jd_sunset)
        tithi_sunset_tmrw = temporal.tithi.get_tithi(self.daily_panchaangas[d + 1].jd_sunset)
        # if tithi_sunset <= 2 and tithi_sunset_tmrw != 2:
        fest = FestivalInstance(name='candra-darzanam')
        if tithi_sunset <= 2:
          if tithi_sunset == 1:
            self.daily_panchaangas[d + 1].festival_id_to_instance[fest.name] =  fest
          else:
            self.daily_panchaangas[d].festival_id_to_instance[fest.name] =  fest
        elif tithi_sunset_tmrw == 2:
          self.daily_panchaangas[d + 1].festival_id_to_instance[fest.name] =  fest

  def assign_vishesha_trayodashi(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()
      # VARUNI TRAYODASHI
      if self.daily_panchaangas[d].lunar_month_sunrise == 12 and self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise == 28:
        if NakshatraDivision(self.daily_panchaangas[d].jd_sunrise, ayanaamsha_id=self.ayanaamsha_id).get_anga(
            zodiac.AngaType.NAKSHATRA) == 24:
          vtr_name = 'vAruNI~trayOdazI'
          if self.daily_panchaangas[d].date.get_weekday() == 6:
            vtr_name = 'mahA' + vtr_name
            if NakshatraDivision(self.daily_panchaangas[d].jd_sunrise, ayanaamsha_id=self.ayanaamsha_id).get_anga(
                zodiac.AngaType.NAKSHATRA) == 23:
              vtr_name = 'mahA' + vtr_name
          self.add_festival(vtr_name, d)


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
