"""Дополнить _mob.csv маршрутов мобами, которых бот видел в прогоне, но не узнал.
python -X utf8 bot_mobfix.py <лог игры> [--write]
Источник строк: _mob.csv из JMC БОТ АЙЛИНА\\areas, JMC БОТ ИНКА\\areas, Bot_Inka\\...\\Bot_ZayNew\\areas* (не эксплор_, не городские стражи).
Строка комнаты сверяется без хвоста аффектов (« ...слеп», « ...огненный щит»). Без --write только показывает."""
import os, sys, re, glob, shutil, time, collections
R = r"C:\Users\User\Desktop\Клод мад"
AREAS = os.path.join(R, "JMC БОТ АЙЛИНА", "areas")
SRC = [AREAS, os.path.join(R, "JMC БОТ ИНКА", "areas")] + glob.glob(os.path.join(R, "Bot_Inka", "Bot_Inka", "Bot_ZayNew", "areas*"))
BAD = re.compile(r"Городской страж|Начальник (городской )?стражи|присматривает за порядком в городе|следит за порядком в городе")


def norm(s):
    return re.sub(r"\s+\.\.\..*$", "", s.strip().strip('"')).strip()


db = {}
for d in SRC:
    for f in glob.glob(os.path.join(d, "*_mob.csv")):
        if os.path.basename(f).startswith("эксплор_"): continue
        for l in open(f, encoding="cp1251", errors="replace").read().splitlines()[1:]:
            p = l.split('";"')
            if len(p) > 2 and norm(p[1]) and not BAD.search(l) and not norm(p[1]).startswith("[Зона"):
                db.setdefault(norm(p[1]), l)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import route_check as rc
G, NAMES, ZONES = rc.graph()
PEACE = re.compile(r"Бармен|Мудрый целитель|Мастер чайных церемоний|Продавец|Продавщица|Кладовщик|Нищий|Стражник|стражник|Охранник|охранник|Учитель|учитель")
log = open(sys.argv[1], encoding="cp1251", errors="replace").read().splitlines()
zone = None; inroom = False; seen = collections.defaultdict(set); cur = None
for l in log:
    t = l[9:] if re.match(r"\d\d:\d\d:\d\d ", l) else l
    m = re.search(r"## BOT_START zone=(\S+)", t)
    if m: zone = m.group(1); continue
    if "## ZONE_END" in t or "## BOT_STOP" in t: zone = None; continue
    if not zone: continue
    ms = re.search(r"## STEP \d+ vn=(\d+) cmd=.*\{([^{}]+)\}\s*$", t)
    if ms:
        d = rc.DIRW.get(ms.group(2).strip().lower()); cur = G.get(ms.group(1), {}).get(d) if d else ms.group(1); continue
    if t.startswith("[ Exits:"): inroom = not (cur and str(ZONES.get(cur, "")).startswith("Город")); continue
    if re.search(r"\d+H \d+M \d+V", t) or t.startswith("##") or t.startswith(">>"): inroom = False; continue
    if inroom and t.strip() and not t.startswith("   ") and not PEACE.search(t): seen[zone].add(norm(t))

ONLY = set(a[7:] for a in sys.argv if a.startswith("--zone="))
for z, lines in seen.items():
    if ONLY and z not in ONLY: continue
    f = os.path.join(AREAS, z + "_mob.csv")
    if not os.path.exists(f): continue
    have = set(norm(l.split('";"')[1]) for l in open(f, encoding="cp1251", errors="replace").read().splitlines()[1:] if '";"' in l)
    add = [db[s] for s in sorted(lines) if s in db and s not in have]
    if not add: continue
    print("=== %s: +%d" % (z, len(add)))
    for a in add: print("   ", a.split('";"')[0].strip('"'), "|", a.split('";"')[1][:60])
    if "--write" in sys.argv:
        shutil.copy(f, f + ".bak_" + time.strftime("%Y%m%d_%H%M"))
        txt = open(f, encoding="cp1251", errors="replace").read().rstrip("\r\n")
        nl = "\r\n" if "\r\n" in txt else "\n"
        open(f, "w", encoding="cp1251", errors="replace").write(txt + nl + nl.join(add) + nl)


