import logging
from datetime import datetime
from math import floor

from pytz import timezone as tz
from scipy.optimize import brentq

from jyotisha import names
from jyotisha.panchangam import temporal
from jyotisha.panchangam.temporal import zodiac
from jyotisha.panchangam.temporal.body import Graha
from jyotisha.panchangam.temporal.festival.applier import FestivalAssigner
from jyotisha.panchangam.temporal.hour import Hour
from jyotisha.panchangam.temporal.zodiac import NakshatraDivision


class TithiFestivalAssigner(FestivalAssigner):
  def assign_all(self, debug=False):
    self.assign_chandra_darshanam(debug_festivals=debug)
    self.assign_chaturthi_vratam(debug_festivals=debug)
    self.assign_shasthi_vratam(debug_festivals=debug)
    self.assign_vishesha_saptami(debug_festivals=debug)
    self.assign_ekadashi_vratam(debug_festivals=debug)
    self.assign_mahadwadashi(debug_festivals=debug)
    self.assign_pradosha_vratam(debug_festivals=debug)
    self.assign_vishesha_trayodashi(debug_festivals=debug)
    self.assign_amavasya_yoga(debug_festivals=debug)
  
  def assign_chaturthi_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # SANKATAHARA chaturthi
      if self.panchaanga.tithi_sunrise[d] == 18 or self.panchaanga.tithi_sunrise[d] == 19:
        ldiff_moonrise_yest = (Graha(Graha.MOON).get_longitude(self.panchaanga.jd_moonrise[d - 1]) - Graha(
          Graha.SUN).get_longitude(self.panchaanga.jd_moonrise[d - 1])) % 360
        ldiff_moonrise = (Graha(Graha.MOON).get_longitude(self.panchaanga.jd_moonrise[d]) - Graha(Graha.SUN).get_longitude(
          self.panchaanga.jd_moonrise[d])) % 360
        ldiff_moonrise_tmrw = (Graha(Graha.MOON).get_longitude(self.panchaanga.jd_moonrise[d + 1]) - Graha(
          Graha.SUN).get_longitude(self.panchaanga.jd_moonrise[d + 1])) % 360
        tithi_moonrise_yest = int(1 + floor(ldiff_moonrise_yest / 12.0))
        tithi_moonrise = int(1 + floor(ldiff_moonrise / 12.0))
        tithi_moonrise_tmrw = int(1 + floor(ldiff_moonrise_tmrw / 12.0))

        _m = self.panchaanga.lunar_month[d]
        if floor(_m) != _m:
          _m = 13  # Adhika masa
        chaturthi_name = names.NAMES['SANKATAHARA_CHATURTHI_NAMES']['hk'][_m] + '-mahAgaNapati '

        if tithi_moonrise == 19:
          # otherwise yesterday would have already been assigned
          if tithi_moonrise_yest != 19:
            chaturthi_name = '%s%s' % ('aGgArakI~' if self.panchaanga.weekday[d] == 2 else '', chaturthi_name)
            self.panchaanga.festivals[d].append(chaturthi_name + 'saGkaTahara-caturthI-vratam')
            # shravana krishna chaturthi
            if self.panchaanga.lunar_month[d] == 5:
              chaturthi_name = '%s%s' % ('aGgArakI~' if self.panchaanga.weekday[d] == 2 else '', chaturthi_name)
              self.panchaanga.festivals[d][-1] = chaturthi_name + 'mahAsaGkaTahara-caturthI-vratam'
        elif tithi_moonrise_tmrw == 19:
          chaturthi_name = '%s%s' % ('aGgArakI~' if self.panchaanga.weekday[d + 1] == 2 else '', chaturthi_name)
          self.panchaanga.festivals[d + 1].append(chaturthi_name + 'saGkaTahara-caturthI-vratam')
          # self.panchaanga.lunar_month[d] and[d + 1] are same, so checking [d] is enough
          if self.panchaanga.lunar_month[d] == 5:
            chaturthi_name = '%s%s' % ('aGgArakI~' if self.panchaanga.weekday[d] == 2 else '', chaturthi_name)
            self.panchaanga.festivals[d + 1][-1] = chaturthi_name + 'mahAsaGkaTahara-caturthI-vratam'
        else:
          if tithi_moonrise_yest != 19:
            if tithi_moonrise == 18 and tithi_moonrise_tmrw == 20:
              # No vyApti on either day -- pick parA, i.e. next day.
              chaturthi_name = '%s%s' % ('aGgArakI~' if self.panchaanga.weekday[d + 1] == 2 else '', chaturthi_name)
              self.panchaanga.festivals[d + 1].append(chaturthi_name + 'saGkaTahara-caturthI-vratam')
              # shravana krishna chaturthi
              if self.panchaanga.lunar_month[d] == 5:
                chaturthi_name = '%s%s' % (
                  'aGgArakI~' if self.panchaanga.weekday[d + 1] == 2 else '', chaturthi_name)
                self.panchaanga.festivals[d + 1][-1] = chaturthi_name + 'mahAsaGkaTahara-caturthI-vratam'

  def assign_shasthi_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)
      # # SHASHTHI Vratam
      # Check only for Adhika maasa here...
      festival_name = 'SaSThI-vratam'
      if self.panchaanga.lunar_month[d] == 8:
        festival_name = 'skanda' + festival_name
      elif self.panchaanga.lunar_month[d] == 4:
        festival_name = 'kumAra-' + festival_name
      elif self.panchaanga.lunar_month[d] == 6:
        festival_name = 'SaSThIdEvI-' + festival_name
      elif self.panchaanga.lunar_month[d] == 9:
        festival_name = 'subrahmaNya-' + festival_name

      if self.panchaanga.tithi_sunrise[d] == 5 or self.panchaanga.tithi_sunrise[d] == 6:
        angams = self.panchaanga.get_angas_for_interval_boundaries(d, lambda x: NakshatraDivision(x,
                                                                                                  ayanamsha_id=self.panchaanga.ayanamsha_id).get_tithi(),
                                            'madhyaahna')
        if angams[0] == 6 or angams[1] == 6:
          if festival_name in self.panchaanga.fest_days:
            # Check if yesterday was assigned already
            # to this puurvaviddha festival!
            if self.panchaanga.fest_days[festival_name].count(d - 1) == 0:
              self.add_festival(festival_name, d, debug_festivals)
          else:
            self.add_festival(festival_name, d, debug_festivals)
        elif angams[2] == 6 or angams[3] == 6:
          self.add_festival(festival_name, d + 1, debug_festivals)
        else:
          # This means that the correct angam did not
          # touch the kaala on either day!
          # sys.stderr.write('Could not assign puurvaviddha day for %s!\
          # Please check for unusual cases.\n' % festival_name)
          if angams[2] == 6 + 1 or angams[3] == 6 + 1:
            # Need to assign a day to the festival here
            # since the angam did not touch kaala on either day
            # BUT ONLY IF YESTERDAY WASN'T ALREADY ASSIGNED,
            # THIS BEING PURVAVIDDHA
            # Perhaps just need better checking of
            # conditions instead of this fix
            if festival_name in self.panchaanga.fest_days:
              if self.panchaanga.fest_days[festival_name].count(d - 1) == 0:
                self.add_festival(festival_name, d, debug_festivals)
            else:
              self.add_festival(festival_name, d, debug_festivals)

  def assign_vishesha_saptami(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # SPECIAL SAPTAMIs
      if self.panchaanga.weekday[d] == 0 and (self.panchaanga.tithi_sunrise[d] % 15) == 7:
        festival_name = 'bhAnusaptamI'
        if self.panchaanga.tithi_sunrise[d] == 7:
          festival_name = 'vijayA' + '~' + festival_name
        if self.panchaanga.nakshatram_sunrise[d] == 27:
          # Even more auspicious!
          festival_name += '★'
        self.add_festival(festival_name, d, debug_festivals)

      if NakshatraDivision(self.panchaanga.jd_sunrise[d], ayanamsha_id=self.panchaanga.ayanamsha_id).get_anga(
          zodiac.NAKSHATRA_PADA) == 49 and \
          self.panchaanga.tithi_sunrise[d] == 7:
        self.add_festival('bhadrA~saptamI', d, debug_festivals)

      if self.panchaanga.solar_month_end_time[d] is not None:
        # we have a Sankranti!
        if self.panchaanga.tithi_sunrise[d] == 7:
          self.add_festival('mahAjayA~saptamI', d, debug_festivals)

  def assign_ekadashi_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # checking @ 6am local - can we do any better?
      local_time = tz(self.panchaanga.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
      # compute offset from UTC in hours
      tz_off = (datetime.utcoffset(local_time).days * 86400 +
                datetime.utcoffset(local_time).seconds) / 3600.0

      # EKADASHI Vratam
      # One of two consecutive tithis must appear @ sunrise!

      if (self.panchaanga.tithi_sunrise[d] % 15) == 10 or (self.panchaanga.tithi_sunrise[d] % 15) == 11:
        yati_ekadashi_fday = smaarta_ekadashi_fday = vaishnava_ekadashi_fday = None
        ekadashi_tithi_days = [x % 15 for x in self.panchaanga.tithi_sunrise[d:d + 3]]
        if self.panchaanga.tithi_sunrise[d] > 15:
          ekadashi_paksha = 'krishna'
        else:
          ekadashi_paksha = 'shukla'
        if ekadashi_tithi_days in [[11, 11, 12], [10, 12, 12]]:
          smaarta_ekadashi_fday = d + 1
          tithi_arunodayam = NakshatraDivision(
            self.panchaanga.jd_sunrise[d + 1] - (1 / 15.0) * (self.panchaanga.jd_sunrise[d + 1] - self.panchaanga.jd_sunrise[d]),
            ayanamsha_id=self.panchaanga.ayanamsha_id).get_tithi()
          if tithi_arunodayam % 15 == 10:
            vaishnava_ekadashi_fday = d + 2
          else:
            vaishnava_ekadashi_fday = d + 1
        elif ekadashi_tithi_days in [[10, 12, 13], [11, 12, 13], [11, 12, 12], [11, 12, 14]]:
          smaarta_ekadashi_fday = d
          tithi_arunodayam = NakshatraDivision(
            self.panchaanga.jd_sunrise[d] - (1 / 15.0) * (self.panchaanga.jd_sunrise[d] - self.panchaanga.jd_sunrise[d - 1]),
            ayanamsha_id=self.panchaanga.ayanamsha_id).get_tithi()
          if tithi_arunodayam % 15 == 11 and ekadashi_tithi_days in [[11, 12, 13], [11, 12, 14]]:
            vaishnava_ekadashi_fday = d
          else:
            vaishnava_ekadashi_fday = d + 1
        elif ekadashi_tithi_days in [[10, 11, 13], [11, 11, 13]]:
          smaarta_ekadashi_fday = d
          vaishnava_ekadashi_fday = d + 1
          yati_ekadashi_fday = d + 1
        else:
          pass
          # These combinations are taken care of, either in the past or future.
          # if ekadashi_tithi_days == [10, 11, 12]:
          #     logging.debug('Not assigning. Maybe tomorrow?')
          # else:
          #     logging.debug(('!!', d, ekadashi_tithi_days))

        if yati_ekadashi_fday == smaarta_ekadashi_fday == vaishnava_ekadashi_fday is None:
          # Must have already assigned
          pass
        elif yati_ekadashi_fday is None:
          if smaarta_ekadashi_fday == vaishnava_ekadashi_fday:
            # It's sarva ekadashi
            self.add_festival(
              'sarva-' + names.get_ekadashi_name(ekadashi_paksha, self.panchaanga.lunar_month[d]),
              smaarta_ekadashi_fday, debug_festivals)
            if ekadashi_paksha == 'shukla':
              if self.panchaanga.solar_month[d] == 9:
                self.add_festival('sarva-vaikuNTha-EkAdazI', smaarta_ekadashi_fday, debug_festivals)
          else:
            self.add_festival(
              'smArta-' + names.get_ekadashi_name(ekadashi_paksha, self.panchaanga.lunar_month[d]),
              smaarta_ekadashi_fday, debug_festivals)
            self.add_festival(
              'vaiSNava-' + names.get_ekadashi_name(ekadashi_paksha, self.panchaanga.lunar_month[d]),
              vaishnava_ekadashi_fday, debug_festivals)
            if ekadashi_paksha == 'shukla':
              if self.panchaanga.solar_month[d] == 9:
                self.add_festival('smArta-vaikuNTha-EkAdazI', smaarta_ekadashi_fday, debug_festivals)
                self.add_festival('vaiSNava-vaikuNTha-EkAdazI', vaishnava_ekadashi_fday,
                                  debug_festivals)
        else:
          self.add_festival('smArta-' + names.get_ekadashi_name(ekadashi_paksha,
                                                                self.panchaanga.lunar_month[d]) + ' (gRhastha)',
                            smaarta_ekadashi_fday, debug_festivals)
          self.add_festival('smArta-' + names.get_ekadashi_name(ekadashi_paksha, self.panchaanga.lunar_month[
            d]) + ' (sannyastha)', yati_ekadashi_fday, debug_festivals)
          self.add_festival(
            'vaiSNava-' + names.get_ekadashi_name(ekadashi_paksha, self.panchaanga.lunar_month[d]),
            vaishnava_ekadashi_fday, debug_festivals)
          if self.panchaanga.solar_month[d] == 9:
            if ekadashi_paksha == 'shukla':
              self.add_festival('smArta-vaikuNTha-EkAdazI (gRhastha)', smaarta_ekadashi_fday,
                                debug_festivals)
              self.add_festival('smArta-vaikuNTha-EkAdazI (sannyastha)', yati_ekadashi_fday,
                                debug_festivals)
              self.add_festival('vaiSNava-vaikuNTha-EkAdazI', vaishnava_ekadashi_fday, debug_festivals)

        if yati_ekadashi_fday == smaarta_ekadashi_fday == vaishnava_ekadashi_fday is None:
          # Must have already assigned
          pass
        else:
          if self.panchaanga.solar_month[d] == 8 and ekadashi_paksha == 'shukla':
            # self.add_festival('guruvAyupura-EkAdazI', smaarta_ekadashi_fday, debug_festivals)
            self.add_festival('guruvAyupura-EkAdazI', vaishnava_ekadashi_fday, debug_festivals)
            self.add_festival('kaizika-EkAdazI', vaishnava_ekadashi_fday, debug_festivals)

          # Harivasara Computation
          if ekadashi_paksha == 'shukla':

            harivasara_end = brentq(
              lambda x: NakshatraDivision(x, ayanamsha_id=self.panchaanga.ayanamsha_id).get_anga_float(
                zodiac.TITHI_PADA, -45, False),
              self.panchaanga.jd_sunrise[smaarta_ekadashi_fday] - 2,
              self.panchaanga.jd_sunrise[smaarta_ekadashi_fday] + 2)
          else:
            harivasara_end = brentq(
              lambda x: NakshatraDivision(x, ayanamsha_id=self.panchaanga.ayanamsha_id).get_anga_float(
                anga_type=zodiac.TITHI_PADA, offset_angas=-105, debug=False),
              self.panchaanga.jd_sunrise[smaarta_ekadashi_fday] - 2,
              self.panchaanga.jd_sunrise[smaarta_ekadashi_fday] + 2)
          [_y, _m, _d, _t] = temporal.jd_to_utc_gregorian(harivasara_end + (tz_off / 24.0))
          hariv_end_time = Hour(temporal.jd_to_utc_gregorian(harivasara_end + (tz_off / 24.0))[3]).toString(
            format=self.panchaanga.fmt)
          fday_hv = temporal.utc_gregorian_to_jd(_y, _m, _d, 0) - self.panchaanga.jd_start_utc + 1
          self.panchaanga.festivals[int(fday_hv)].append(
            'harivAsaraH\\textsf{%s}{\\RIGHTarrow}\\textsf{%s}' % ('', hariv_end_time))

  def assign_mahadwadashi(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)
      # 8 MAHA DWADASHIS
      if (self.panchaanga.tithi_sunrise[d] % 15) == 11 and (self.panchaanga.tithi_sunrise[d + 1] % 15) == 11:
        self.add_festival('unmIlanI~mahAdvAdazI', d + 1, debug_festivals)

      if (self.panchaanga.tithi_sunrise[d] % 15) == 12 and (self.panchaanga.tithi_sunrise[d + 1] % 15) == 12:
        self.add_festival('vyaJjulI~mahAdvAdazI', d, debug_festivals)

      if (self.panchaanga.tithi_sunrise[d] % 15) == 11 and (self.panchaanga.tithi_sunrise[d + 1] % 15) == 13:
        self.add_festival('trisparzA~mahAdvAdazI', d, debug_festivals)

      if (self.panchaanga.tithi_sunrise[d] % 15) == 0 and (self.panchaanga.tithi_sunrise[d + 1] % 15) == 0:
        # Might miss out on those parva days right after Dec 31!
        if (d - 3) > 0:
          self.add_festival('pakSavardhinI~mahAdvAdazI', d - 3, debug_festivals)

      if self.panchaanga.nakshatram_sunrise[d] == 4 and (self.panchaanga.tithi_sunrise[d] % 15) == 12:
        self.add_festival('pApanAzinI~mahAdvAdazI', d, debug_festivals)

      if self.panchaanga.nakshatram_sunrise[d] == 7 and (self.panchaanga.tithi_sunrise[d] % 15) == 12:
        self.add_festival('jayantI~mahAdvAdazI', d, debug_festivals)

      if self.panchaanga.nakshatram_sunrise[d] == 8 and (self.panchaanga.tithi_sunrise[d] % 15) == 12:
        self.add_festival('jayA~mahAdvAdazI', d, debug_festivals)

      if self.panchaanga.nakshatram_sunrise[d] == 8 and (self.panchaanga.tithi_sunrise[d] % 15) == 12 and self.panchaanga.lunar_month[d] == 12:
        # Better checking needed (for other than sunrise).
        # Last occurred on 27-02-1961 - pushya nakshatra and phalguna krishna dvadashi (or shukla!?)
        self.add_festival('gOvinda~mahAdvAdazI', d, debug_festivals)

      if (self.panchaanga.tithi_sunrise[d] % 15) == 12:
        if self.panchaanga.nakshatram_sunrise[d] in [21, 22, 23]:
          # We have a dwadashi near shravana, check for Shravana sparsha
          for td in self.panchaanga.tithi_data[d:d + 2]:
            (t12, t12_end) = td[0]
            if t12_end is None:
              continue
            if (t12 % 15) == 11:
              if NakshatraDivision(t12_end, ayanamsha_id=self.panchaanga.ayanamsha_id).get_anga(
                  zodiac.NAKSHATRAM) == 22:
                if (self.panchaanga.tithi_sunrise[d] % 15) == 12 and (self.panchaanga.tithi_sunrise[d + 1] % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d, debug_festivals)
                elif (self.panchaanga.tithi_sunrise[d] % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d, debug_festivals)
                elif (self.panchaanga.tithi_sunrise[d + 1] % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d + 1, debug_festivals)
            if (t12 % 15) == 12:
              if NakshatraDivision(t12_end, ayanamsha_id=self.panchaanga.ayanamsha_id).get_anga(
                  zodiac.NAKSHATRAM) == 22:
                if (self.panchaanga.tithi_sunrise[d] % 15) == 12 and (self.panchaanga.tithi_sunrise[d + 1] % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d, debug_festivals)
                elif (self.panchaanga.tithi_sunrise[d] % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d, debug_festivals)
                elif (self.panchaanga.tithi_sunrise[d + 1] % 15) == 12:
                  self.add_festival('vijayA/zravaNa-mahAdvAdazI', d + 1, debug_festivals)

      if self.panchaanga.nakshatram_sunrise[d] == 22 and (self.panchaanga.tithi_sunrise[d] % 15) == 12:
        self.add_festival('vijayA/zravaNa-mahAdvAdazI', d, debug_festivals)

  def assign_pradosha_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)
      # compute offset from UTC in hours
      # PRADOSHA Vratam
      pref = ''
      if self.panchaanga.tithi_sunrise[d] in (12, 13, 27, 28):
        tithi_sunset = NakshatraDivision(self.panchaanga.jd_sunset[d], ayanamsha_id=self.panchaanga.ayanamsha_id).get_tithi() % 15
        tithi_sunset_tmrw = NakshatraDivision(self.panchaanga.jd_sunset[d + 1],
                                              ayanamsha_id=self.panchaanga.ayanamsha_id).get_tithi() % 15
        if tithi_sunset <= 13 and tithi_sunset_tmrw != 13:
          fday = d
        elif tithi_sunset_tmrw == 13:
          fday = d + 1
        if self.panchaanga.weekday[fday] == 1:
          pref = 'sOma-'
        elif self.panchaanga.weekday[fday] == 6:
          pref = 'zani-'
        self.add_festival(pref + 'pradOSa-vratam', fday, debug_festivals)

  def assign_amavasya_yoga(self, debug_festivals=False):
    if 'amAvAsyA' not in self.panchaanga.fest_days:
      logging.error('Must compute amAvAsyA before coming here!')
    else:
      ama_days = self.panchaanga.fest_days['amAvAsyA']
      for d in ama_days:
        # Get Name
        if self.panchaanga.lunar_month[d] == 6:
          pref = '(%s) mahAlaya ' % (
            names.get_chandra_masa(self.panchaanga.lunar_month[d], names.NAMES, 'hk', visarga=False))
        elif self.panchaanga.solar_month[d] == 4:
          pref = '%s (kaTaka) ' % (
            names.get_chandra_masa(self.panchaanga.lunar_month[d], names.NAMES, 'hk', visarga=False))
        elif self.panchaanga.solar_month[d] == 10:
          pref = 'mauni (%s/makara) ' % (
            names.get_chandra_masa(self.panchaanga.lunar_month[d], names.NAMES, 'hk', visarga=False))
        else:
          pref = names.get_chandra_masa(self.panchaanga.lunar_month[d], names.NAMES, 'hk',
                                        visarga=False) + '-'

        ama_nakshatram_today = self.panchaanga.get_angas_for_interval_boundaries(d, lambda x: NakshatraDivision(x,
                                                                                                                ayanamsha_id=self.panchaanga.ayanamsha_id).get_nakshatra(),
                                                          'aparaahna')[:2]
        suff = ''
        # Assign
        if 23 in ama_nakshatram_today and self.panchaanga.lunar_month[d] == 10:
          suff = ' (alabhyam–zraviSThA)'
        elif 24 in ama_nakshatram_today and self.panchaanga.lunar_month[d] == 10:
          suff = ' (alabhyam–zatabhiSak)'
        elif ama_nakshatram_today[0] in [15, 16, 17, 6, 7, 8, 23, 24, 25]:
          suff = ' (alabhyam–%s)' % names.NAMES['NAKSHATRAM_NAMES']['hk'][ama_nakshatram_today[0]]
        elif ama_nakshatram_today[1] in [15, 16, 17, 6, 7, 8, 23, 24, 25]:
          suff = ' (alabhyam–%s)' % names.NAMES['NAKSHATRAM_NAMES']['hk'][ama_nakshatram_today[1]]
        if self.panchaanga.weekday[d] in [1, 2, 4]:
          if suff == '':
            suff = ' (alabhyam–puSkalA)'
          else:
            suff = suff.replace(')', ', puSkalA)')
        self.add_festival(pref + 'amAvAsyA' + suff, d, debug_festivals)
    if 'amAvAsyA' in self.panchaanga.fest_days:
      del self.panchaanga.fest_days['amAvAsyA']

    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)

      # SOMAMAVASYA
      if self.panchaanga.tithi_sunrise[d] == 30 and self.panchaanga.weekday[d] == 1:
        self.add_festival('sOmavatI amAvAsyA', d, debug_festivals)

      # AMA-VYATIPATA YOGAH
      # श्रवणाश्विधनिष्ठार्द्रानागदैवतमापतेत् ।
      # रविवारयुतामायां व्यतीपातः स उच्यते ॥
      # व्यतीपाताख्ययोगोऽयं शतार्कग्रहसन्निभः ॥
      # “In Mahabharata, if on a Sunday, Amavasya and one of the stars –
      # Sravanam, Asvini, Avittam, Tiruvadirai or Ayilyam, occurs, then it is called ‘Vyatipatam’.
      # This Vyatipata yoga is equal to a hundred Surya grahanas in merit.”
      tithi_sunset = NakshatraDivision(self.panchaanga.jd_sunset[d], ayanamsha_id=self.panchaanga.ayanamsha_id).get_anga(
        zodiac.TITHI)
      if self.panchaanga.weekday[d] == 0 and (self.panchaanga.tithi_sunrise[d] == 30 or tithi_sunset == 30):
        # AMAVASYA on a Sunday
        if (self.panchaanga.nakshatram_sunrise[d] in [1, 6, 9, 22, 23] and self.panchaanga.tithi_sunrise[d] == 30) or \
            (tithi_sunset == 30 and NakshatraDivision(self.panchaanga.jd_sunset[d],
                                                      ayanamsha_id=self.panchaanga.ayanamsha_id).get_anga(
              zodiac.NAKSHATRAM) in [
               1, 6, 9, 22, 23]):
          festival_name = 'vyatIpAta-yOgaH (alabhyam)'
          self.add_festival(festival_name, d, debug_festivals)
          logging.debug('* %d-%02d-%02d> %s!' % (y, m, dt, festival_name))

  def assign_chandra_darshanam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)
      # Chandra Darshanam
      if self.panchaanga.tithi_sunrise[d] == 1 or self.panchaanga.tithi_sunrise[d] == 2:
        tithi_sunset = NakshatraDivision(self.panchaanga.jd_sunset[d], ayanamsha_id=self.panchaanga.ayanamsha_id).get_tithi()
        tithi_sunset_tmrw = NakshatraDivision(self.panchaanga.jd_sunset[d + 1], ayanamsha_id=self.panchaanga.ayanamsha_id).get_tithi()
        # if tithi_sunset <= 2 and tithi_sunset_tmrw != 2:
        if tithi_sunset <= 2:
          if tithi_sunset == 1:
            self.panchaanga.festivals[d + 1].append('candra-darzanam')
          else:
            self.panchaanga.festivals[d].append('candra-darzanam')
        elif tithi_sunset_tmrw == 2:
          self.panchaanga.festivals[d + 1].append('candra-darzanam')

  def assign_vishesha_trayodashi(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.panchaanga.jd_start_utc + d - 1)
      # VARUNI TRAYODASHI
      if self.panchaanga.lunar_month[d] == 12 and self.panchaanga.tithi_sunrise[d] == 28:
        if NakshatraDivision(self.panchaanga.jd_sunrise[d], ayanamsha_id=self.panchaanga.ayanamsha_id).get_anga(
            zodiac.NAKSHATRAM) == 24:
          vtr_name = 'vAruNI~trayOdazI'
          if self.panchaanga.weekday[d] == 6:
            vtr_name = 'mahA' + vtr_name
            if NakshatraDivision(self.panchaanga.jd_sunrise[d], ayanamsha_id=self.panchaanga.ayanamsha_id).get_anga(
                zodiac.YOGA) == 23:
              vtr_name = 'mahA' + vtr_name
          self.add_festival(vtr_name, d, debug_festivals)