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


def _assemble(blurb, detailed, shlokas='', references='', url=''):
  return {
    'blurb': blurb,
    'detailed': detailed,
    'image': '',
    'references': references,
    'url': url,
    'shlokas': shlokas,
  }


def describe_pushkara(role, stage, rashi_sa, river_sa, general_note='', shlokas='', references='', url=''):
  """
  :param role: ROLE_ADYA (pushkaram beginning as Guru enters the rashi) or ROLE_ANTYA
    (pushkaram ending as Guru is about to leave the rashi)
  :param stage: STAGE_ARAMBHAH (start of this 12-day window) or STAGE_SAMAPANAM (end of it)
  :param rashi_sa: the rashi name (raw HK-Dravidian roman, matching how backtick-quoted terms
    are authored in TOML `en` descriptions -- transliterated to the actual output script only
    at render time, same as any other backtick term) associated with this role (the *incoming*
    rashi for Adya, the *outgoing* one for antya)
  :param river_sa: the river name (raw HK-Dravidian roman, same convention) for that rashi
  """
  if role == ROLE_ADYA:
    stage_note = "begins" if stage == STAGE_ARAMBHAH else "ends its first 12 days"
    closing = "Following Guru's transition into `%s`, `puSkararAja` takes up residence in the `%s` river." % (rashi_sa, river_sa)
  else:
    stage_note = "begins its closing 12 days" if stage == STAGE_ARAMBHAH else "ends"
    closing = "As Guru is about to leave `%s`, `puSkararAja`'s residence in the `%s` river draws to a close." % (rashi_sa, river_sa)

  blurb = "puSkara %s (%s), `%s`. " % (role, stage, river_sa)
  # Matches the original TOML's own paragraph break between the boilerplate residency note and
  # the river-specific closing sentence (a literal single newline in the source `en` string).
  detailed = "%s\n%s" % (general_note, closing) if general_note else closing
  return _assemble(blurb, detailed, shlokas=shlokas, references=references, url=url)
