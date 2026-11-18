"""Маршрут зоны из СЫРОГО лога пользователя (JMC\\<лог>) + граф комнат game.db (без log_prep, который теряет ходы).

  python -X utf8 tools/raw_route.py <лог> <старт_vnum> [--create "область создать вн"]
Берёт ходы (север/юг/…/вверх/вниз и сокращения) после строки создания области; ход, которого нет на графе, пропускается
(в логе он не удался). Печатает: число ходов, клетки, конец, клетки зоны (по vnum-диапазону входа), которых путь не касается.
Результат: data/recon/<лог>/raw_path.json = [[vnum, ход], ...] для сборки V.
"""
import json, os, re, sqlite3, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JMC = os.path.join(os.path.dirname(ROOT), "JMC")
name, start = sys.argv[1], sys.argv[2]
create = "область создать"
if "--create" in sys.argv:
    create = sys.argv[sys.argv.index("--create") + 1]
SH = {"с": "север", "ю": "юг", "в": "восток", "з": "запад", "вв": "вверх", "вн": "вниз"}
D = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
log = open(os.path.join(JMC, name), "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
i0 = next(i for i, l in enumerate(log) if l.strip().startswith(create))
c = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
N = {str(v): n for v, n in c.execute("select vnum,name from rooms")}
cur, path, bad = start, [], []
for l in log[i0 + 1:]:
    s = SH.get(l.strip(), l.strip())
    if s in D:
        nxt = R.get(cur, {}).get(D[s])
        if nxt is None:
            bad.append((len(path), cur, s)); continue
        path.append((cur, s)); cur = str(nxt)
    if re.match(r"^(Вы вышли из зоны|Вы покинули зону)", l):
        break
seen = {p[0] for p in path} | {cur}
print("ходов:", len(path), "конец:", cur, N.get(cur), "| невозможных ходов:", len(bad), bad[:6])
lo = min(int(v) for v in seen if v != start) // 100 * 100
zone = {v for v in R if int(v) // 100 == lo // 100 or (int(v) >= lo and int(v) < lo + 100)}
miss = sorted(zone - seen, key=int)
print("клеток этого блока vnum:", len(zone), "не тронуто:", [(v, N.get(v)) for v in miss][:20])
out = os.path.join(ROOT, "data", "recon", name)
os.makedirs(out, exist_ok=True)
json.dump(path, open(os.path.join(out, "raw_path.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("сохранено:", os.path.join(out, "raw_path.json"))
