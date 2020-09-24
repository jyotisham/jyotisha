from jyotisha.panchaanga.temporal import time
from jyotisha.panchaanga import temporal
from jyotisha.panchaanga.temporal import zodiac
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision


class VaraFestivalAssigner(FestivalAssigner):
  def assign_all(self, debug=False):
    self.assign_bhriguvara_subrahmanya_vratam(debug_festivals=debug)
    self.assign_masa_vara_yoga_vratam(debug_festivals=debug)
    self.assign_nakshatra_vara_yoga_vratam(debug_festivals=debug)
    self.assign_ayushman_bava_saumya_yoga(debug_festivals=debug)
    self.assign_tithi_vara_yoga(debug_festivals=debug)


  def assign_bhriguvara_subrahmanya_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

      # BHRGUVARA SUBRAHMANYA VRATAM
      if self.panchaanga.solar_month[d] == 7 and self.panchaanga.daily_panchaangas[d].date.get_weekday() == 5:
        festival_name = 'bhRguvAra-subrahmaNya-vratam'
        if festival_name not in self.panchaanga.fest_days:
          # only the first bhRguvAra of tulA mAsa is considered (skAnda purANam)
          # https://youtu.be/rgXwyo0L3i8?t=222
          self.add_festival(festival_name, d, debug_festivals)

  def assign_masa_vara_yoga_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):

      # KRTTIKA SOMAVASARA
      if self.panchaanga.lunar_month[d] == 8 and self.panchaanga.daily_panchaangas[d].date.get_weekday() == 1:
        self.add_festival('kRttikA~sOmavAsaraH', d, debug_festivals)

      # SOLAR MONTH-WEEKDAY FESTIVALS
      for (mwd_fest_m, mwd_fest_wd, mwd_fest_name) in ((5, 0, 'ta:AvaNi~JAyir2r2ukkizhamai'),
                                                       (6, 6, 'ta:puraTTAci~can2ikkizhamai'),
                                                       (8, 0, 'ta:kArttigai~JAyir2r2ukkizhamai'),
                                                       (4, 5, 'ta:ADi~veLLikkizhamai'),
                                                       (10, 5, 'ta:tai~veLLikkizhamai'),
                                                       (11, 2, 'ta:mAci~cevvAy')):
        if self.panchaanga.solar_month[d] == mwd_fest_m and self.panchaanga.daily_panchaangas[d].date.get_weekday() == mwd_fest_wd:
          self.add_festival(mwd_fest_name, d, debug_festivals)

  def assign_tithi_vara_yoga(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

      # MANGALA-CHATURTHI
      if self.panchaanga.daily_panchaangas[d].date.get_weekday() == 2 and (self.panchaanga.daily_panchaangas[d].tithi_at_sunrise % 15) == 4:
        festival_name = 'aGgAraka-caturthI'
        if self.panchaanga.daily_panchaangas[d].tithi_at_sunrise == 4:
          festival_name = 'sukhA' + '~' + festival_name
        self.add_festival(festival_name, d, debug_festivals)

      # KRISHNA ANGARAKA CHATURDASHI
      if self.panchaanga.daily_panchaangas[d].date.get_weekday() == 2 and self.panchaanga.daily_panchaangas[d].tithi_at_sunrise == 29:
        # Double-check rule. When should the vyApti be?
        self.add_festival('kRSNAGgAraka-caturdazI-puNyakAlaH/yamatarpaNam', d, debug_festivals)

      # BUDHASHTAMI
      if self.panchaanga.daily_panchaangas[d].date.get_weekday() == 3 and (self.panchaanga.daily_panchaangas[d].tithi_at_sunrise % 15) == 8:
        self.add_festival('budhASTamI', d, debug_festivals)


  def assign_nakshatra_vara_yoga_vratam(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

      # NAKSHATRA-WEEKDAY FESTIVALS
      for (nwd_fest_n, nwd_fest_wd, nwd_fest_name) in ((13, 0, 'Adityahasta-puNyakAlaH'),
                                                       (8, 0, 'ravipuSyayOga-puNyakAlaH'),
                                                       (22, 1, 'sOmazrAvaNI-puNyakAlaH'),
                                                       (5, 1, 'sOmamRgazIrSa-puNyakAlaH'),
                                                       (1, 2, 'bhaumAzvinI-puNyakAlaH'),
                                                       (6, 2, 'bhaumArdrA-puNyakAlaH'),
                                                       (17, 3, 'budhAnurAdhA-puNyakAlaH'),
                                                       (8, 4, 'gurupuSya-puNyakAlaH'),
                                                       (27, 5, 'bhRgurEvatI-puNyakAlaH'),
                                                       (4, 6, 'zanirOhiNI-puNyakAlaH'),
                                                       ):
        n_prev = ((nwd_fest_n - 2) % 27) + 1
        if (self.panchaanga.daily_panchaangas[d].nakshatra_at_sunrise == nwd_fest_n or self.panchaanga.daily_panchaangas[d].nakshatra_at_sunrise == n_prev) and self.panchaanga.daily_panchaangas[
          d].date.get_weekday() == nwd_fest_wd:
          # Is it necessarily only at sunrise?
          angams = self.panchaanga.get_angas_for_interval_boundaries(d, lambda x: NakshatraDivision(x,
                                                                                                    ayanamsha_id=self.panchaanga.ayanamsha_id).get_nakshatra(),
                                              'dinamaana')
          if any(x == nwd_fest_n for x in [self.panchaanga.daily_panchaangas[d].nakshatra_at_sunrise, angams[0], angams[1]]):
            self.add_festival(nwd_fest_name, d, debug_festivals)


  def assign_ayushman_bava_saumya_yoga(self, debug_festivals=False):
    for d in range(1, self.panchaanga.duration + 1):
      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

      # AYUSHMAN BHAVA SAUMYA
      if self.panchaanga.daily_panchaangas[d].date.get_weekday() == 3 and NakshatraDivision(self.panchaanga.daily_panchaangas[d].jd_sunrise, ayanamsha_id=self.panchaanga.ayanamsha_id).get_anga(
          zodiac.AngaType.NAKSHATRA) == 3:
        if NakshatraDivision(self.panchaanga.daily_panchaangas[d].jd_sunrise, ayanamsha_id=self.panchaanga.ayanamsha_id).get_anga(
            zodiac.AngaType.KARANA) in list(range(2, 52, 7)):
          self.add_festival('AyuSmad-bava-saumya-saMyogaH', d, debug_festivals)
      if self.panchaanga.daily_panchaangas[d].date.get_weekday() == 3 and NakshatraDivision(self.panchaanga.daily_panchaangas[d].jd_sunset, ayanamsha_id=self.panchaanga.ayanamsha_id).get_anga(
          zodiac.AngaType.NAKSHATRA) == 3:
        if NakshatraDivision(self.panchaanga.daily_panchaangas[d].jd_sunset, ayanamsha_id=self.panchaanga.ayanamsha_id).get_anga(
            zodiac.AngaType.KARANA) in list(range(2, 52, 7)):
          self.add_festival('AyuSmad-bava-saumya-saMyogaH', d, debug_festivals)