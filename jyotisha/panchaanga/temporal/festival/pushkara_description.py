"""Dynamic description generation for Pushkara (river-residency) festivals.

Pushkara festival ids are combinatorial (12 rivers x Adya/antya x
ArambhaH/samApanam), and `EclipticFestivalAssigner.set_jupiter_transits`
already has full context (both rashis, both river names, via
`names.NAMES['PUSHKARA_NAMES']`) to build both the fest_id and description
in Python -- no per-river TOML file is needed, mirroring the eclipse
migration. The old per-file text was itself buggy in places (the `antya`
files' closing sentence was a copy-paste of the `Adya` one, describing
Guru's arrival into the *new* rashi instead of its imminent departure from
the *old* one); this module fixes that by deriving the sentence from
`role` instead of hand-authoring text per file.
"""
ROLE_ADYA = 'Adya'
ROLE_ANTYA = 'antya'
STAGE_ARAMBHAH = 'ArambhaH'
STAGE_SAMAPANAM = 'samApanam'


def _assemble(blurb, detailed, shlokas=''):
  return {
    'blurb': blurb,
    'detailed': detailed,
    'image': '',
    'references': '- References\n  - Pushkara rashi/river pairing and the 12-day residency rule follow this pancAnga\'s puSkara-sAmAnya-niyamAH entry.\n',
    'url': '',
    'shlokas': shlokas,
  }


def describe_pushkara(role, stage, rashi_sa, river_sa, general_note='', shlokas=''):
  """
  :param role: ROLE_ADYA (pushkaram beginning as Guru enters the rashi) or ROLE_ANTYA
    (pushkaram ending as Guru is about to leave the rashi)
  :param stage: STAGE_ARAMBHAH (start of this 12-day window) or STAGE_SAMAPANAM (end of it)
  :param rashi_sa: the rashi name (ISO-transliterated, for embedding in English text) associated
    with this role (the *incoming* rashi for Adya, the *outgoing* one for antya)
  :param river_sa: the river name (ISO-transliterated) for that rashi
  """
  if role == ROLE_ADYA:
    stage_note = "begins" if stage == STAGE_ARAMBHAH else "ends its first 12 days"
    closing = "Following Guru's transition into `%s`, `puSkararAja` takes up residence in the `%s` river." % (rashi_sa, river_sa)
  else:
    stage_note = "begins its closing 12 days" if stage == STAGE_ARAMBHAH else "ends"
    closing = "As Guru is about to leave `%s`, `puSkararAja`'s residence in the `%s` river draws to a close." % (rashi_sa, river_sa)

  blurb = "puSkara %s (%s), %s. " % (role, stage, river_sa)
  detailed = "%s %s" % (general_note, closing) if general_note else closing
  return _assemble(blurb, detailed, shlokas=shlokas)
