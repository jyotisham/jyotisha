"""Dynamic description generation for the regular monthly Ekadashi festivals.

Most of the ~28 per-name Ekadashi TOML files shared byte-identical shloka and
"fruits of fasting" boilerplate, differing only in one opening sentence
("The Shukla-paksha Ekadashi of `X` month is known as `Y`"), which is fully
derivable from (paksha, month) -- so it doesn't need to be authored per file
at all. A handful of names carry a genuine unique legend/detail beyond that
opening sentence (e.g. Ajaikadashi's Harishchandra story); those are kept as
small per-name TOML entries and appended here when present, via `legend`.

Named ekadashis added as bonus festivals alongside the regular one (vaikuNTha,
guruvAyupura, kaizika, raMgabharI, ASADhI-vArI) are unaffected by this module
-- they're constructed directly by their own exact fest_id, not through
(paksha, month) derivation, so they keep going through the ordinary TOML
lookup unchanged.
"""
PAKSHA_EN = {'shukla': 'Shukla', 'krishna': 'Krishna'}


def _assemble(blurb, detailed, shlokas=''):
  return {
    'blurb': blurb,
    'detailed': detailed,
    'image': '',
    'references': '- References\n  - Shared Ekadashi shloka and merit paragraph follow EkAdazI-sAmAnya-niyamAH.\n',
    'url': '',
    'shlokas': shlokas,
  }


def describe_ekadashi(ekad_base, paksha, month_sa, legend='', general_note='', shlokas=''):
  """
  :param ekad_base: e.g. 'AmalakI-EkAdazI' (names.get_ekaadashii_name's return value)
  :param paksha: 'shukla' or 'krishna'
  :param month_sa: the lunar month name (raw HK-Dravidian roman, no visarga), e.g. 'phAlguna' --
    transliterated to the actual output script only at render time, same as any other
    backtick-quoted term
  :param legend: any genuine unique story/detail for this ekad_base, or ''
  :param general_note: the shared shloka+merit boilerplate text, or ''
  :param shlokas: the shloka block to show -- the ekad_base's own (if it has unique verses
    beyond the shared ones) or else the shared EkAdazI-sAmAnya-niyamAH block
  """
  opening = "The %s-paksha Ekadashi of `%s` month is known as `%s`." % (PAKSHA_EN[paksha], month_sa, ekad_base)
  blurb = "`%s` " % ekad_base

  parts = [opening]
  if legend:
    parts.append(legend)
  if general_note:
    parts.append(general_note)
  detailed = ' '.join(parts)

  return _assemble(blurb, detailed, shlokas=shlokas)
