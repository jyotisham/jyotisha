"""Shared helper for description text that lives as a Python str.format()-style template in a
TOML rule's `[description] en = "..."` field (a "sAmAnya" rule), rather than as Python
string-building code.

This is the preferred pattern going forward for any family of dynamically-generated festival
descriptions: Python computes the substitution values (positions, dates, motion etc.), but the
actual wording lives in TOML and can be edited without touching code. mAudhya/bAlya/vArdhakya
descriptions (see EclipticFestivalAssigner.add_maudhya_events/add_baalya_vardhakya_events) are
the first family built this way; eclipse_description.py, graha_yuddha_description.py,
ekadashi_description.py, adhyayana_description.py etc. may be migrated to it over time, one
family at a time.
"""


def render_template(rule, **fields):
  """
  :param rule: a HinduCalendarEvent (or None, in which case '' is returned)
  :param fields: values to substitute into the template's {placeholders}

  Deliberately reads `rule.description['en']` directly rather than going through
  `rule.get_description_dict()`/`summary.get_description_str_with_shlokas()`: those
  unconditionally run backtick-quoted spans through transliteration to ISO as soon as the rule
  is fetched (`summary.get_english_description`) -- which would corrupt a template's own
  `` `{placeholder}` `` markup (transliterating the literal text "{placeholder}", before any
  value has been substituted in). Instead, substitution happens first here on the raw template,
  and backtick-transliteration of the *substituted* text is left to the same downstream pass
  that already handles it for FestivalInstance.description text in general
  (`festival._get_description_dict` -> `summary.transliterate_backticked_terms`), exactly as
  eclipse_description.py/graha_yuddha_description.py's own hand-built text already relies on.
  """
  if rule is None or rule.description is None or 'en' not in rule.description:
    return ''
  template = rule.description['en'].strip()
  if not template:
    return ''
  return template.format(**fields)
