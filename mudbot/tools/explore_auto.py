"""Автоэксплор: ближайшая по карте непройденная зона (по переходам из ЗОНЫ\\*\\переходы.csv), уровень зоны <= MAXLVL.
python -X utf8 tools/explore_auto.py [минут=60]
Неудачные переходы — в mudbot\\data\\explore_skip.txt (больше не пробует). Лог: mudbot\\data\\explore_batch.log"""
import os, sys, subprocess, time, glob, re, collections
T = os.path.dirname(os.path.abspath(__file__))
K = os.path.dirname(os.path.dirname(T))
sys.path.insert(0, T)
os.environ.setdefault("JMC_TARGET", os.path.join(K, "JMC БОТ АЙЛИНА"))
import jmc, speedwalk
MAXLVL = 26                               # нижняя граница зоны: на 2 ниже уровня Айлины (28); 15.11 Лаборатория Фелонада 30-33 чуть не убила
SKIPF = os.path.join(K, "mudbot", "data", "explore_skip.txt")
LOG = os.path.join(K, "mudbot", "data", "explore_batch.log")
SKIP_ZONES = {"Тюрьма Геоланта", "Лаборатория Фелонада"}          # заперто, нужен ключ (см. ЗОНЫ\Тюрьма Геоланта\заметки.md)

levels = {}
for l in open(os.path.join(K, "mudbot", "data", "zones_game.txt"), encoding="utf-8", errors="replace"):
    m = re.match(r"\s*\d+\s+(.+?)\s{2,}(\d+)-\s*(\d+)\s", l)
    if m:
        levels[m.group(1).strip().lower()] = int(m.group(2))


def lvl(zone):
    z = zone.lower().replace('"', "")
    for k, v in levels.items():
        if k.replace('"', "") == z:
            return v
    return None                            # неизвестно — пробуем


def where():
    s = jmc.log_size()
    jmc.type_line('#scr ClaudeLog.note("WHERE $MsdpRoomVnum")', force=True)
    time.sleep(1)
    for l in jmc.read_log(s):
        if "## WHERE " in l:
            return l.split("## WHERE ")[1].strip()


def explored():
    return {os.path.basename(os.path.dirname(f)) for f in glob.glob(os.path.join(K, "ЗОНЫ", "*", "клетки.csv"))}


def candidates():
    done, skip = explored(), set()
    if os.path.exists(SKIPF):
        skip = set(open(SKIPF, encoding="utf-8").read().split())
    out = []
    for f in glob.glob(os.path.join(K, "ЗОНЫ", "*", "переходы.csv")):
        for l in open(f, encoding="cp1251").read().splitlines()[1:]:
            p = l.split(";")
            if len(p) < 4 or p[3].replace('"', "'") in done or p[3] in SKIP_ZONES or (p[0] + ":" + p[1]) in skip:
                continue
            lv = lvl(p[3])
            if lv is not None and lv > MAXLVL:
                continue
            out.append((p[0], p[1], p[3], lv))
    return out


minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 60
t0 = time.time()
with open(LOG, "a", encoding="utf-8") as lg:
    while time.time() - t0 < minutes * 60:
        C = candidates()
        if not C:
            print("непройденных зон в досягаемости нет"); break
        G, _ = speedwalk.graph()
        cur = where()
        if cur not in G:                       # стоим в непройденной зоне — пройти её отсюда
            lg.write("\n=== %s AUTO здесь (%s)\n" % (time.strftime("%H:%M:%S"), cur)); lg.flush()
            r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(T, "explore_zone.py"), "here"],
                               capture_output=True, text=True, encoding="utf-8")
            lg.write(r.stdout + r.stderr); lg.flush()
            print("здесь ->", (r.stdout.strip().splitlines() or [r.stderr.strip()])[-1])
            if "ГОТОВО" not in r.stdout:
                print("не смогла пройти зону, где стою — стоп"); break
            continue
        best = None
        for frm, d, zone, lv in C:
            p = speedwalk.path(cur, frm, G)
            if p is not None and (best is None or len(p) < best[0]):
                best = (len(p), frm, d, zone, lv)
        if not best:
            print("до оставшихся зон нет пути:", sorted({c[2] for c in C})); break
        _, frm, d, zone, lv = best
        lg.write("\n=== %s AUTO %s (ур %s) из %s %s\n" % (time.strftime("%H:%M:%S"), zone, lv, frm, d)); lg.flush()
        r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(T, "explore_zone.py"), frm, d],
                           capture_output=True, text=True, encoding="utf-8")
        lg.write(r.stdout + r.stderr); lg.flush()
        last = (r.stdout.strip().splitlines() or [r.stderr.strip()])[-1]
        print(zone, "->", last)
        if "ГОТОВО" not in r.stdout:
            open(SKIPF, "a", encoding="utf-8").write(frm + ":" + d + "\n")
            if "СТОП" in r.stdout and "хп" in r.stdout:
                print("СТОП: мало хп — прекращаю"); break
subprocess.run([sys.executable, "-X", "utf8", os.path.join(T, "zones_summary.py")], capture_output=True)
