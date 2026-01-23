import re, pathlib
p=pathlib.Path('.')
py_files=[f for f in p.rglob('*.py') if 'venv' not in str(f).split('\\') and 'Lib\\site-packages' not in str(f)]
pattern_decl=re.compile(r"id\s*=\s*['\"]([A-Za-z0-9_\-]+)['\"]")
pattern_input=re.compile(r"Input\(\s*['\"]([A-Za-z0-9_\-]+)['\"]")
pattern_output=re.compile(r"Output\(\s*['\"]([A-Za-z0-9_\-]+)['\"]")
ids_decl=set(); decl_locations={}
ids_used=set(); used_locations={}
for f in py_files:
    txt=f.read_text(encoding='utf-8')
    for m in pattern_decl.finditer(txt):
        ids_decl.add(m.group(1))
        decl_locations.setdefault(m.group(1), []).append((str(f), txt[:m.start()].count('\n')+1))
    for m in pattern_input.finditer(txt):
        ids_used.add(m.group(1))
        used_locations.setdefault(m.group(1), []).append((str(f), txt[:m.start()].count('\n')+1))
    for m in pattern_output.finditer(txt):
        ids_used.add(m.group(1))
        used_locations.setdefault(m.group(1), []).append((str(f), txt[:m.start()].count('\n')+1))

missing = sorted([i for i in ids_used if i not in ids_decl])
print('Missing IDs referenced in callbacks (used but not declared):')
for m in missing:
    print('\n- ', m)
    for loc in used_locations.get(m, []):
        print('   used at', loc[0], 'line', loc[1])

print('\nAlso: IDs declared but not used (sample 20):')
unused=sorted([i for i in ids_decl if i not in ids_used])
for i in unused[:20]:
    print('-', i)
