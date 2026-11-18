p = r"C:\Users\User\Desktop\Клод мад\mudbot\tools\mk_zone_geo.py"
s = open(p, encoding="utf-8").read()
s = s.replace('import collections, json, os, sqlite3, sys, shutil', 'import collections, json, os, re, sqlite3, sys, shutil')
s = s.replace('''for l in log[i0 + 1:]:
    s = SH.get(l.strip(), l.strip())
    if s in INV:''', '''for l in log[i0 + 1:]:
    s = SH.get(l.strip(), l.strip())
    if re.match(r"^(отпер|откр) \\S+( \\S+)?$", s):
        path.append((cur, "." + s))              # команда двери в текущей клетке
        continue
    if s in INV:''')
s = s.replace('ends = [i for i, (v, m) in enumerate(path) if i > 0 and str(R[v][INV[m]]) == end]', 'ends = [i for i, (v, m) in enumerate(path) if i > 0 and not m.startswith(".") and str(R[v][INV[m]]) == end]')
s = s.replace('first = str(R[cut[0][0]][INV[cut[0][1]]])', 'first = next(str(R[v][INV[m]]) for v, m in cut if not m.startswith("."))')
s = s.replace('vl = lambda p: [V.format(v=v, c=m) for v, m in p]', 'vl = lambda p: [(".триг " + V.format(v=v, c=m[1:])) if m.startswith(".") else V.format(v=v, c=m) for v, m in p]')
open(p, "w", encoding="utf-8").write(s)
print("ok")
