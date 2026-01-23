import re, pathlib
p=pathlib.Path('.')
files=[f for f in p.rglob('*.py') if 'venv' not in str(f).split('\\') and 'Lib\\site-packages' not in str(f)]
callback_pattern=re.compile(r"@app\.callback\((.*?)\)\s*\ndef\s+([A-Za-z0-9_]+)\s*\(", re.S)
output_pattern=re.compile(r"Output\(\s*['\"]([A-Za-z0-9_\-]+)['\"]\s*,\s*['\"]([A-Za-z0-9_\-]+)['\"]\s*\)")
outputs_map = {}
for f in files:
    txt=f.read_text(encoding='utf-8')
    for m in callback_pattern.finditer(txt):
        args = m.group(1)
        func = m.group(2)
        outs = output_pattern.findall(args)
        # Also handle list of Outputs e.g. [Output(...), Output(...)]
        if not outs:
            # try to find Outputs within following lines up to def
            pass
        for out in outs:
            key = (out[0], out[1])
            outputs_map.setdefault(key, []).append((str(f), func))

# Report duplicates
duplicates = {k:v for k,v in outputs_map.items() if len(v) > 1}
if not duplicates:
    print('No duplicate Outputs found in decorators (literal outputs).')
else:
    print('Duplicate Outputs found:')
    for k, v in duplicates.items():
        print(f'Output target: {k}')
        for loc in v:
            print(' -', loc[0], 'function', loc[1])

# Also do a looser check: find any Output('id','prop') strings across files and group
all_outputs = []
for f in files:
    txt=f.read_text(encoding='utf-8')
    for m in re.finditer(r"Output\(\s*['\"]([A-Za-z0-9_\-]+)['\"]\s*,\s*['\"]([A-Za-z0-9_\-]+)['\"]", txt):
        all_outputs.append(((m.group(1), m.group(2)), str(f)))
from collections import defaultdict
by_target=defaultdict(list)
for t, f in all_outputs:
    by_target[t].append(f)
mult = {k:v for k,v in by_target.items() if len(v) > 1}
if mult:
    print('\nLooser duplicates (same Output used across decorators, may be legitimate if combined):')
    for k,v in mult.items():
        print(k, len(v))
        for f in v:
            print(' -', f)
else:
    print('\nNo looser duplicates found.')
