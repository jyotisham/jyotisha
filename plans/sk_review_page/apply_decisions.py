#!/usr/bin/env python3
"""Apply approved review decisions to adyatithi TOML files.

    python3 apply_decisions.py items.json decisions_dir /path/to/adyatithi

decisions_dir: the folder written by ArtifactData action "list" with out_dir
(one <doc>.json per decision). Only status "approved" is applied; the reviewer's edited
`after` / `ref` win over the drafted ones. Prints what the reviewer changed.
"""
import json, re, sys, glob, os, difflib, tomllib
items_f, dec_dir, root = sys.argv[1:4]
items = {i['doc']: i for i in json.load(open(items_f))}
for f in sorted(glob.glob(os.path.join(dec_dir, '**', '*.json'), recursive=True)):
    d = json.load(open(f)); it = items.get(os.path.basename(f)[:-5])
    if not it: continue
    print(it['id'], d.get('status'))
    if d.get('status') != 'approved': continue
    sh = (d['after'] if d.get('after') is not None else it['after']).strip('\n')
    ref = d['ref'] if d.get('ref') is not None else it['ref']
    if sh != it['after'].strip('\n'):
        print('\n'.join('   ' + l for l in difflib.unified_diff(it['after'].split('\n'), sh.split('\n'), lineterm='', n=0)))
    p = os.path.join(root, it['file']); s = open(p).read(); ins = ''
    if sh:
        if re.search(r'^shlokas = """', s, re.M):
            s = re.sub(r'(^shlokas = """\n.*?)(\n?""")', lambda m: m.group(1).rstrip('\n') + '\n\n' + sh + '\n"""', s, count=1, flags=re.M | re.S)
        else:
            ins += 'shlokas = """\n' + sh + '\n"""\n'
    if ref:
        k = it['refkey']
        if it.get('replace_ref') and '"' + it['replace_ref'] + '"' in s:
            s = s.replace('"' + it['replace_ref'] + '"', '"' + ref + '"')
        else:
            m = re.search(r'^' + k + r' = \[(.*)\]$', s, re.M)
            if m:
                inner = m.group(1).strip().rstrip(',').strip()
                s = s[:m.start()] + k + ' = [ ' + inner + ', "' + ref + '",]' + s[m.end():]
            else:
                ins += k + ' = [ "' + ref + '",]\n'
    if ins:
        s = s.replace('jsonClass = "HinduCalendarEvent"\n', ins + 'jsonClass = "HinduCalendarEvent"\n', 1)
    open(p, 'w').write(s)
    tomllib.loads(s)  # fails loudly if the edit broke the TOML
