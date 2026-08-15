"""Dynamic description generation for anadhyAya ("no Vedic study") festivals.

Of the ~76 anadhyAya TOML files, ~63 cluster into 6 groups that share
byte-identical (or near-identical, differing only in one label word)
[description] text -- the file count is driven by scheduling variety
(which manvantara/yuga/veda/tithi triggers the day), not by any real
difference in what to say about the day itself. The remaining ~13 are
genuine one-offs (a specific rule with its own unique circumstance, e.g.
`adhika-trayOdazI` or `dvAdazI-yOgaH`) and are left as ordinary TOML-backed
FestivalInstances, untouched by this module.

Unlike Pushkara/Ekadashi, anadhyAya instances are not built by a dedicated
Python method with full context -- they come out of the generic
RuleLookupAssigner/apply_month_anga_events machinery shared by ~50 other
festival families (see rule_repo_based/__init__.py), which must not be
taught per-family fest_id branching. So AdhyayanaFestivalInstance is
attached via a post-hoc "upgrade pass" (TithiFestivalAssigner
.upgrade_anadhyayana_festival_instances, run last in
Panchaanga.update_festival_details) that reclassifies already-built
instances by inspecting their *retained* [timing] rule (anchor_festival_id
or anga_number -- only [description]/[shlokas]/[references_primary] were
stripped from the TOML, not [timing]), rather than by fest_id pattern
matching at construction time.
"""
CLUSTER_BOILERPLATE_IDS = {
  'ayana_vishu': 'anadhyAyaH-ayana-viSu-sAmAnya-niyamAH',
  'nitya_tithi': 'anadhyAyaH-nitya-tithi-sAmAnya-niyamAH',
  'utsarga': 'anadhyAyaH-utsarga-sAmAnya-niyamAH',
  'aSTakA': 'anadhyAyaH-aSTakA-sAmAnya-niyamAH',
  'shakradhvaja': 'anadhyAyaH-zakradhvaja-sAmAnya-niyamAH',
  'caturmasya_prathama': 'anadhyAyaH-cAturmAsya-prathamA-sAmAnya-niyamAH',
  'caturmasya_dvitiya': 'anadhyAyaH-cAturmAsya-dvitIyA-sAmAnya-niyamAH',
  'caturmasya_tritiya': 'anadhyAyaH-cAturmAsya-tRtIyA-sAmAnya-niyamAH',
}

# anga_number (tithi) -> the nitya-anadhyayana label named in the shared boilerplate.
NITYA_TITHI_LABELS = {
  1: 'prathamA', 16: 'prathamA',
  8: 'aSTamI', 23: 'aSTamI',
  14: 'caturdazI', 29: 'caturdazI',
  15: 'pUrNimA',
  30: 'amAvAsyA',
}


def _assemble(blurb, detailed, shlokas=''):
  return {
    'blurb': blurb,
    'detailed': detailed,
    'image': '',
    'references': '',
    'url': '',
    'shlokas': shlokas,
  }


def describe_labeled(label, general_note, shlokas=''):
  """For clusters whose shared note is prefixed by a per-instance label
  (ayana_vishu: 'manvAdi'/'yugAdi'/'uttarAyaNa'/...; nitya_tithi: 'prathamA'/'aSTamI'/...).
  """
  opening = "Anadhyayana on account of `%s`." % label
  detailed = "%s %s" % (opening, general_note) if general_note else opening
  return _assemble(blurb="%s " % label, detailed=detailed, shlokas=shlokas)


def describe_boilerplate(general_note, shlokas=''):
  """For clusters with no per-instance label -- the shared note is the whole description
  (utsarga, aSTakA, shakradhvaja, the 3 cAturmAsya sub-clusters)."""
  return _assemble(blurb='anadhyAyaH ', detailed=general_note, shlokas=shlokas)


def classify(rule):
  """
  :param rule: a HinduCalendarEvent whose id contains 'anadhyAyaH'
  :return: (cluster_key, label) if `rule` belongs to one of the 6 collapsible clusters
    (label is the substituted word for 'ayana_vishu'/'nitya_tithi', else None), or
    (None, None) if it's a one-off that should keep going through ordinary TOML lookup.
  """
  timing = rule.timing
  if timing is None:
    return None, None

  anchor = timing.anchor_festival_id
  if anchor is not None:
    if anchor.startswith('manvAdiH'):
      return 'ayana_vishu', 'manvAdi'
    if anchor.endswith('yugAdiH'):
      return 'ayana_vishu', 'yugAdi'
    if anchor == 'dakSiNAyana-puNyakAlaH':
      return 'ayana_vishu', 'dakSiNAyana'
    if anchor == 'uttarAyaNa-puNyakAlaH':
      return 'ayana_vishu', 'uttarAyaNa'
    if anchor == 'viSu-puNyakAlaH':
      return 'ayana_vishu', 'viSu'
    if anchor == 'cAturmAsyavrata-samApanam':
      return 'ayana_vishu', 'viSNu-prabOdhOtsava'
    if anchor == 'zAkavrata-ArambhaH':
      return 'ayana_vishu', 'viSNuzayanOtsava'
    if anchor in ('taittirIya-utsargaH_paurNamAsyAm', 'RgvEda-upAkarma', 'sAmavEda-upAkarma', 'yajurvEda-upAkarma'):
      return 'utsarga', None
    if anchor.endswith('aSTakA-zrAddham'):
      return 'aSTakA', None
    if anchor in ('zakradhvajapAtaH', 'zakradhvajotthApanam'):
      return 'shakradhvaja', None
    if anchor.startswith('cAturmAsya-dvitIyA'):
      offset = None if timing.offset is None else int(timing.offset)
      if offset == -1:
        return 'caturmasya_prathama', None
      if offset == 0:
        return 'caturmasya_dvitiya', None
      if offset == 1:
        return 'caturmasya_tritiya', None
    return None, None

  if timing.anga_type == 'tithi' and timing.anga_number is not None:
    label = NITYA_TITHI_LABELS.get(int(timing.anga_number))
    if label is not None:
      return 'nitya_tithi', label

  return None, None
