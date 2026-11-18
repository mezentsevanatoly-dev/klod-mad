"""Саммари по опыту за последний проход зоны в JMC-логе (Тадия\\claude_game.log) и запись убийств в data/game.db (mob_kills).

  python -X utf8 tools/zone_exp.py            -> последний BOT_START ... конец (ZONE_END/BOT_STOP или конец лога); печать + запись в БД + data/zone_exp/<зона>_<время>.md
  python -X utf8 tools/zone_exp.py --no-db    -> только печать
  python -X utf8 tools/zone_exp.py --from "14:22"  -> с метки времени (HH:MM) вместо последнего BOT_START
Убийство = строка «<Имя> мертв(а). R.I.P.», опыт = ближайшая за ней «Вы получили N единиц опыта» (в пределах 6 строк).
Уровень игрока: по «Вы <раса> <имя>, <класс> N уровня.» (сч) и «Вы поднялись на уровень!» (+1).
"""
import collections, os, re, sqlite3, sys, time

LOG = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\claude_game.log"
DB = r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db"
OUT = r"C:\Users\User\Desktop\Клод мад\mudbot\data\zone_exp"
args = sys.argv[1:]
no_db = "--no-db" in args
frm = args[args.index("--from") + 1] if "--from" in args else None

L = open(LOG, "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
TS = re.compile(r"^(\d\d:\d\d:\d\d) (.*)$")
start = None
for i, l in enumerate(L):
    m = TS.match(l)
    if not m:
        continue
    if frm:
        if m.group(1) >= frm + ":00" and start is None:
            start = i
    elif "## BOT_START" in l:
        start = i
if start is None:
    sys.exit("нет BOT_START в логе")
seg = L[start:]
zone = "зона"
for l in list(reversed(L[max(0, start - 400):start + 1])) + seg:
    z = re.search(r"## BOT_START zone=(\S+)", l)
    if z:
        zone = z.group(1)
        break
end = len(seg)
for i, l in enumerate(seg):
    if "## ZONE_END" in l or "## LEVEL_REACHED" in l:
        end = i + 1
        break
seg = seg[:end]

level = None
for l in L[max(0, start - 3000):start]:
    m = re.search(r"^\d\d:\d\d:\d\d Вы .+, .+ (\d+) уровня\.", l)
    if m:
        level = int(m.group(1))
kills = []        # (время, имя, опыт, уровень_игрока)
for i, l in enumerate(seg):
    m = TS.match(l)
    if not m:
        continue
    t, body = m.groups()
    mm = re.match(r"^Вы .+, .+ (\d+) уровня\.", body)
    if mm:
        level = int(mm.group(1))
    if body.startswith("Вы поднялись на уровень"):
        level = (level or 0) + 1
    k = re.match(r"^(.+?) мертв[аоы]?\. R\.I\.P\.", body)
    if k:
        exp = None
        for j in range(i + 1, min(i + 7, len(seg))):
            e = re.match(r"^\d\d:\d\d:\d\d Вы получили (\d+) (?:единиц[ауы]?|ед\.?) опыта", seg[j])
            if e:
                exp = int(e.group(1)); break
        kills.append((t, k.group(1), exp, level))

by = collections.OrderedDict()
for t, name, exp, lv in kills:
    by.setdefault(name, []).append((exp, lv))
tot = sum(e for _, _, e, _ in kills if e)
ZN = {"аллея": "Аллея", "парк": "Парк", "школа": "Мад школа", "канал": "Канализация"}.get(zone, zone)
_c = sqlite3.connect(DB)
def card(name):
    r = _c.execute("select level, prof from mob_cards where name=? order by (zone=?) desc limit 1", (name, ZN)).fetchone()
    return r if r else ("?", "?")
lines = ["# Опыт за проход зоны «%s» (%s .. %s)" % (zone, seg[0][:8], seg[-1][:8]), "",
         "убийств: %d, опыта: %d, уровень игрока: %s" % (len(kills), tot, kills[0][3] if kills else level), "",
         "| моб | ур. моба | профа | убито | опыт за моба (мин-макс) | всего |", "|---|---|---|---|---|---|"]
for name, v in sorted(by.items(), key=lambda kv: -sum(e or 0 for e, _ in kv[1])):
    es = [e for e, _ in v if e is not None]
    lv, pf = card(name)
    lines.append("| %s | %s | %s | %d | %s | %d |" % (name, lv, pf, len(v), ("%d-%d" % (min(es), max(es))) if es else "?", sum(es)))
text = "\n".join(lines)
print(text)
os.makedirs(OUT, exist_ok=True)
fn = os.path.join(OUT, "%s_%s.md" % (zone, time.strftime("%d%m_%H%M")))
open(fn, "w", encoding="utf-8").write(text + "\n")
print("\nсохранено:", fn)

if not no_db and kills:
    c = sqlite3.connect(DB)
    c.execute("create table if not exists mob_kills (ts TEXT, zone TEXT, name TEXT, mob_level TEXT, my_level INTEGER, exp INTEGER, secs REAL)")
    zname = ZN
    day = time.strftime("%d.%m")
    n = 0
    for t, name, exp, lv in kills:
        ts = "%s %s" % (day, t)
        if c.execute("select 1 from mob_kills where ts=? and name=?", (ts, name)).fetchone():
            continue
        r = c.execute("select level from mob_cards where name=? order by (zone=?) desc limit 1", (name, zname)).fetchone()
        c.execute("insert into mob_kills(ts,zone,name,mob_level,my_level,exp,secs) values (?,?,?,?,?,?,NULL)", (ts, zname, name, r[0] if r else None, lv, exp))
        n += 1
    c.commit()
    print("в mob_kills добавлено строк:", n)
