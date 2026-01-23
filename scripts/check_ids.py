import re, pathlib
p=pathlib.Path('.')
py_files=list(p.rglob('*.py'))
ids_decl=set()
ids_used=set()
pattern_decl=re.compile(r"id\s*=\s*['\"]([A-Za-z0-9_\-]+)['\"]")
pattern_input=re.compile(r"Input\(\s*['\"]([A-Za-z0-9_\-]+)['\"]")
pattern_output=re.compile(r"Output\(\s*['\"]([A-Za-z0-9_\-]+)['\"]")
for f in py_files:
    txt=f.read_text(encoding='utf-8')
    for m in pattern_decl.finditer(txt):
        ids_decl.add(m.group(1))
    for m in pattern_input.finditer(txt):
        ids_used.add(m.group(1))
    for m in pattern_output.finditer(txt):
        ids_used.add(m.group(1))

missing = sorted([i for i in ids_used if i not in ids_decl])
print('Declared IDs (count):', len(ids_decl))
print('Used IDs (count):', len(ids_used))
print('\nMissing IDs referenced in callbacks (used but not declared):')
for m in missing:
    print('-', m)
