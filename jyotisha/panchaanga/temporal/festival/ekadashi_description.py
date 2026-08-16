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


def _assemble(blurb, detailed, shlokas='', references='', url=''):
  return {
    'blurb': blurb,
    'detailed': detailed,
    'image': '',
    'references': references,
    'url': url,
    'shlokas': shlokas,
  }


def describe_ekadashi(ekad_base, paksha, month_sa, legend='', general_note='', shlokas='', references='', url=''):
  """
  :param ekad_base: e.g. 'AmalakI-EkAdazI' (names.get_ekaadashii_name's return value)
  :param paksha: 'shukla' or 'krishna'
  :param month_sa: the lunar month name (raw HK-Dravidian roman, no visarga), e.g. 'phAlguna' --
    transliterated to the actual output script only at render time, same as any other
    backtick-quoted term
  :param legend: any genuine unique story/detail for this ekad_base, or '' -- joined onto the
    opening sentence (same paragraph), matching how the original per-name TOML files authored
    the legend directly after the name-identifying sentence
  :param general_note: the shared shloka+merit boilerplate text, or '' -- its own paragraph(s),
    separated from the opening (+ legend) by a blank line, matching the original TOML's
    paragraph break between the name-identifying sentence and the "fruits of fasting" text
  :param shlokas: the shloka block to show -- the ekad_base's own (if it has unique verses
    beyond the shared ones) or else the shared EkAdazI-sAmAnya-niyamAH block
  :param references: the applicable rule's own references (its own legend rule's, if the
    ekad_base still has one, else the shared boilerplate's), or ''
  :param url: ditto, the "edit this file" URL of whichever rule the above came from
  """
  opening = "The %s-paksha Ekadashi of `%s` month is known as `%s`." % (PAKSHA_EN[paksha], month_sa, ekad_base)
  # No get_timing_summary()-equivalent exists for these (they were never scheduled off a
  # populated [timing] block to begin with -- Python computes their schedule directly), so
  # there's nothing informative to put in blurb; leave it empty rather than repeat the name
  # that's already in the festival's own title/heading.
  blurb = ''

  first_para = "%s %s" % (opening, legend) if legend else opening
  parts = [first_para]
  if general_note:
    parts.append(general_note)
  detailed = '\n\n'.join(parts)

  return _assemble(blurb, detailed, shlokas=shlokas, references=references, url=url)
