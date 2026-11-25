#!/usr/bin/env python3
"""Build the Smriti Kaustubha review page for one month.

    python3 build_page.py items.json "Jyeṣṭha" "117–137" decisions-jyestha out.html

items.json: a list of items, one per adyatithi entry (see example_items.json):
  doc         db document id: letters, digits and '-' only, unique (e.g. "j-nirjala-EkAdazI")
  key         "sh:<id>"
  id, file    adyatithi entry id and its path relative to the adyatithi root
  existing    the entry's current shlokas (shown collapsed; "" if none)
  after       shlokas to append ("" for a reference-only item)
  ref         reference to add, e.g. "Smriti Kaustubham p.119" ("" for none)
  refkey      "references_primary" or "references_secondary"
  replace_ref optional: an existing Smriti Kaustubham reference that `ref` replaces
  note        one or two sentences for the reviewer (overlaps, [?] readings, timing disagreements)

Publish out.html as an Artifact with capabilities {"db": {}}. Decisions are saved to the
db collection named on the command line, one document per item `doc`: {key, status, after, ref}.
"""
import json, sys
items, month, pages, collection, out = sys.argv[1:6]
here = __file__.rsplit('/', 1)[0]
t = open(here + '/template.html').read()
data = json.dumps({'refs': [], 'shlokas': json.load(open(items))}, ensure_ascii=False).replace('<', '\\u003c')
for k, v in (('__MONTH__', month), ('__PAGES__', pages), ('__COLLECTION__', collection), ('__DATA__', data)):
    t = t.replace(k, v)
open(out, 'w').write(t)
print('wrote', out)
