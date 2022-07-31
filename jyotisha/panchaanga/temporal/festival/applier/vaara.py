import sys

from jyotisha.panchaanga.temporal import zodiac
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.festival import FestivalInstance
from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision, AngaType
import logging
from sanskrit_data.schema import common


class VaraFestivalAssigner(FestivalAssigner):
  def assign_all(self):
    self.assign_bhriguvara_subrahmanya_vratam()
    self.assign_masa_vara_yoga_kRttikaa()
    self.assign_masa_vara_yoga_fests_tn()
    self.assign_nakshatra_vara_yoga_vratam()
    self.assign_ayushman_bava_saumya_yoga()
    self.assign_tithi_vara_yoga_mangala_angaaraka()
    self.assign_tithi_vara_yoga_kRSNAGgAraka()
    self.assign_tithi_vara_yoga_budhaaShTamii()


  def assign_bhriguvara_subrahmanya_vratam(self):
    festival_name = 'bhRguvAra-subrahmaNya-vratam'
    if festival_name not in self.rules_collection.name_to_rule:
      return 
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      # BHRGUVARA SUBRAHMANYA VRATAM
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 7 and self.daily_panchaangas[d].date.get_weekday() == 5:
        if festival_name not in self.panchaanga.festival_id_to_days:
          # only the first bhRguvAra of tulA mAsa is considered (skAnda purANam)
          # https://youtu.be/rgXwyo0L3i8?t=222
          self.panchaanga.add_festival(fest_id=festival_name, date=self.daily_panchaangas[d].date)

  def assign_masa_vara_yoga_kRttikaa(self):
    festival_name = 'kRttikA~sOmavAsaraH'
    if festival_name not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):

      # KRTTIKA SOMAVASARA
      if self.daily_panchaangas[d].lunar_month_sunrise.index == 8 and self.daily_panchaangas[d].date.get_weekday() == 1:
        self.panchaanga.add_festival(fest_id='kRttikA~sOmavAsaraH', date=self.daily_panchaangas[d].date)

  def assign_masa_vara_yoga_fests_tn(self):
    festival_name = 'AvaNi~JAyir2r2ukkizhamai'
    if festival_name not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      # SOLAR MONTH-WEEKDAY FESTIVALS
      for (mwd_fest_m, mwd_fest_wd, mwd_fest_name) in ((5, 0, 'AvaNi~JAyir2r2ukkizhamai'),
                                                       (6, 6, 'puraTTAci~can2ikkizhamai'),
                                                       (8, 0, 'kArttigai~JAyir2r2ukkizhamai'),
                                                       (4, 5, 'ADi~veLLikkizhamai'),
                                                       (10, 5, 'tai~veLLikkizhamai'),
                                                       (11, 2, 'mAci~cevvAy')):
        if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == mwd_fest_m and self.daily_panchaangas[d].date.get_weekday() == mwd_fest_wd:
          self.panchaanga.add_festival(fest_id=mwd_fest_name, date=self.daily_panchaangas[d].date)

  def assign_tithi_vara_yoga_mangala_angaaraka(self):
    if 'aGgAraka-caturthI' not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      # MANGALA-CHATURTHI
      tithi_sunset = self.daily_panchaangas[d].sunrise_day_angas.get_anga_at_jd(jd=self.daily_panchaangas[d].jd_sunset, anga_type=AngaType.TITHI) % 15
      if self.daily_panchaangas[d].date.get_weekday() == 2 and (self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise.index % 15 == 4 or tithi_sunset == 4):
        festival_name = 'aGgAraka-caturthI'
        if self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise.index == 4 or tithi_sunset == 4:
          festival_name = 'sukhA' + '~' + festival_name
        self.panchaanga.add_festival(fest_id=festival_name, date=self.daily_panchaangas[d].date)

  def assign_tithi_vara_yoga_kRSNAGgAraka(self):
    if 'kRSNAGgAraka-caturdazI-puNyakAlaH_or_yamatarpaNam' not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      # KRISHNA ANGARAKA CHATURDASHI
      if self.daily_panchaangas[d].date.get_weekday() == 2 and self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise.index == 29:
        # Double-check rule. When should the vyApti be?
        self.panchaanga.add_festival(fest_id='kRSNAGgAraka-caturdazI-puNyakAlaH or yamatarpaNam', date=self.daily_panchaangas[d].date)
        if self.daily_panchaangas[d].lunar_month_sunrise.index == 1:
          self.panchaanga.add_festival(fest_id='pizAcamOcanam', date=self.daily_panchaangas[d].date)

  def assign_tithi_vara_yoga_budhaaShTamii(self):
    if 'budhASTamI' not in self.rules_collection.name_to_rule:
      return 
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      # BUDHASHTAMI
      if self.daily_panchaangas[d].date.get_weekday() == 3 and self.daily_panchaangas[d].sunrise_day_angas.tithi_at_sunrise.index == 8:
        if self.daily_panchaangas[d].lunar_month_sunrise.index == 10:
          # Pausha Shukla Ashtami + Budha vasara
          self.panchaanga.add_festival(fest_id='mahAbhadrA~budhASTamI', date=self.daily_panchaangas[d].date)
        elif self.daily_panchaangas[d].lunar_month_sunrise.index in [1, 5, 6, 7, 8]:
          # सायाह्नकाले चैत्रमासे श्रावणादिमासचतुष्टये कृष्णपक्षे च न ग्राह्या ॥
          pass
        else:
          self.panchaanga.add_festival(fest_id='budhASTamI', date=self.daily_panchaangas[d].date)


  def assign_nakshatra_vara_yoga_vratam(self):
    if 'Adityahasta-yOgaH' not in self.rules_collection.name_to_rule:
      return 
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      # NAKSHATRA-WEEKDAY FESTIVALS
      for (nwd_fest_n, nwd_fest_wd, nwd_fest_name) in ((13, 0, 'Adityahasta-yOgaH'),
                                                       (8, 0, 'ravipuSyayOga-yOgaH'),
                                                       (22, 1, 'sOmazrAvaNI-yOgaH'),
                                                       (5, 1, 'sOmamRgazIrSa-yOgaH'),
                                                       (1, 2, 'bhaumAzvinI-yOgaH'),
                                                       # (6, 2, 'bhaumArdrA-yOgaH'), removed because no pramANam
                                                       (17, 3, 'budhAnurAdhA-yOgaH'),
                                                       (8, 4, 'gurupuSya-yOgaH'),
                                                       (27, 5, 'bhRgurEvatI-yOgaH'),
                                                       (4, 6, 'zanirOhiNI-yOgaH'),
                                                       ):
        n_prev = ((nwd_fest_n - 2) % 27) + 1
        if (self.daily_panchaangas[d].sunrise_day_angas.nakshatra_at_sunrise.index == nwd_fest_n or self.daily_panchaangas[d].sunrise_day_angas.nakshatra_at_sunrise.index == n_prev) and self.daily_panchaangas[
          d].date.get_weekday() == nwd_fest_wd:
          # Is it necessarily only at sunrise?
          d0_angas = self.daily_panchaangas[d].day_length_based_periods.dinamaana.get_boundary_angas(anga_type=AngaType.NAKSHATRA, ayanaamsha_id=self.ayanaamsha_id)

          # if any(x == nwd_fest_n for x in [self.daily_panchaangas[d].sunrise_day_angas.nakshatra_at_sunrise.index, d0_angas.start.index, d0_angas.end.index]):
          #   self.panchaanga.add_festival(fest_id=nwd_fest_name, date=self.daily_panchaangas[d].date)

          nakshatram_praatah = self.daily_panchaangas[d].sunrise_day_angas.nakshatra_at_sunrise.index
          nakshatram_saayam = NakshatraDivision(jd=self.daily_panchaangas[d].jd_sunset, ayanaamsha_id=self.panchaanga.computation_system.ayanaamsha_id).get_anga(anga_type=AngaType.NAKSHATRA).index

          if nakshatram_praatah == nakshatram_saayam == n_prev:
            continue

          if nwd_fest_n == nakshatram_praatah == nakshatram_saayam:
            self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=nwd_fest_name), date=self.daily_panchaangas[d].date)
          else:
            (nakshatra_ID, nakshatra_end_jd) = (self.daily_panchaangas[d].sunrise_day_angas.nakshatras_with_ends[0].anga.index,
                                                self.daily_panchaangas[d].sunrise_day_angas.nakshatras_with_ends[0].jd_end)

            if nwd_fest_n == nakshatram_praatah:
              # assert nwd_fest_n == nakshatra_ID
              self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=nwd_fest_name, interval=Interval(jd_start=None, jd_end=nakshatra_end_jd)), date=self.daily_panchaangas[d].date)
            elif nwd_fest_n == nakshatram_saayam:
              # assert n_prev == nakshatra_ID
              self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=nwd_fest_name, interval=Interval(jd_start=nakshatra_end_jd, jd_end=None)), date=self.daily_panchaangas[d].date)
            else:
              logging.error('Should never be here!')



  def assign_ayushman_bava_saumya_yoga(self):
    if 'AyuSmad-bava-saumya-saMyOgaH' not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      # AYUSHMAN BAVA SAUMYA
      if self.daily_panchaangas[d].date.get_weekday() == 3 and NakshatraDivision(self.daily_panchaangas[d].jd_sunrise, ayanaamsha_id=self.ayanaamsha_id).get_anga(
          zodiac.AngaType.YOGA).index == 3:
        if NakshatraDivision(self.daily_panchaangas[d].jd_sunrise, ayanaamsha_id=self.ayanaamsha_id).get_anga(
            zodiac.AngaType.KARANA).index in list(range(2, 52, 7)):
          self.panchaanga.add_festival(fest_id='AyuSmad-bava-saumya-saMyOgaH', date=self.daily_panchaangas[d].date)
      if self.daily_panchaangas[d].date.get_weekday() == 3 and NakshatraDivision(self.daily_panchaangas[d].jd_sunset, ayanaamsha_id=self.ayanaamsha_id).get_anga(
          zodiac.AngaType.YOGA).index == 3:
        if NakshatraDivision(self.daily_panchaangas[d].jd_sunset, ayanaamsha_id=self.ayanaamsha_id).get_anga(
            zodiac.AngaType.KARANA).index in list(range(2, 52, 7)):
          self.panchaanga.add_festival(fest_id='AyuSmad-bava-saumya-saMyOgaH', date=self.daily_panchaangas[d].date)


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
