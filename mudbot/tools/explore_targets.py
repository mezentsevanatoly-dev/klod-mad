"""Эксплор зон из списка (прокачка инкарнаций 1–30) + дороги между ними. Сам выбирает ближайшую по карте.
Отчёт по каждой зоне -> ЗОНЫ\\ОТЧЁТ_ЭКСПЛОРА.md. Стоп: DANGER в логе, смерть, мало хп.
Нет дороги по картам -> переезд через Аватару в следующий город из CITIES (из Геоланта).
python -X utf8 tools/explore_targets.py [минут=180]"""
import os, sys, subprocess, time, glob, re
T = os.path.dirname(os.path.abspath(__file__))
K = os.path.dirname(os.path.dirname(T))
sys.path.insert(0, T)
os.environ.setdefault("JMC_TARGET", os.path.join(K, "JMC БОТ АЙЛИНА"))
import jmc, speedwalk
from where import where
from walk import walk

TARGETS = ["Мад-школа", "Парк", "Канализация", "Аллея", "Болото", "Окрестные поля", "Заливные луга",
           "Деревня рыбаков", "Лагерь кочевников", "Храм пламенного меча", "Тоннель бесов", "Темный лес",
           "Далекая крепость", "Военный гарнизон", "Деревня варваров", "Южный лес", "Город Эрдер",
           "Восточная окраина Эрдера", "Во тьме", "Логовище Орды", "Хутор Аргниста", "Порт Элендора",
           "Город Элендор", "Больница", "Катакомбы Геоланта", "Селение человекоящеров", "Змеиное гнездо", "Яр",
           "Лагерь археологов", "Город Гален", "Город Стэдвик", "Каньон поющей воды", "Паучьи пещеры", "Кладбище",
           "Поляна в густом лесу", "Магический лес", "Холм фаэри", "Эльфийская застава", "Город Артуанель",
           "Дремучий лес", "Затерянный остров", "Поселок хоббитов", "Западные равнины", "Лагерь полуорков",
           "Кладбище полуорков", "Морское побережье", "Крепость Тима", "Старая библиотека", "Развалины Элендора",
           "Башня магов", "Притон", "Парк аттракционов", "Здание стражи Элендора", "Окружная дорога"]
SKIP = {"Тюрьма Геоланта", "Лаборатория Фелонада", "Зоопарк", "Город Шиар"}
CITIES = ["элендор", "фелонад", "эрдер", "гален", "артуанель", "стэдвик"]
REPORT = os.path.join(K, "ЗОНЫ", "ОТЧЁТ_ЭКСПЛОРА.md")
LOG = os.path.join(K, "JMC БОТ АЙЛИНА", "claude_game.log")
SKIPF = os.path.join(K, "mudbot", "data", "explore_skip.txt")


def ok_zone(z):
    z2 = z.replace('"', "'")
    if z in SKIP:
        return False
    return z in TARGETS or z2 in TARGETS or re.search(r"(?i)^дорог|^тракт|^южная дорога|^северная", z)


def explored():
    return {os.path.basename(os.path.dirname(f)) for f in glob.glob(os.path.join(K, "ЗОНЫ", "*", "клетки.csv"))}


def candidates():
    done = explored()
    skip = set(open(SKIPF, encoding="utf-8").read().split()) if os.path.exists(SKIPF) else set()
    out = []
    for f in glob.glob(os.path.join(K, "ЗОНЫ", "*", "переходы.csv")):
        for l in open(f, encoding="cp1251").read().splitlines()[1:]:
            p = l.split(";")
            if len(p) < 4 or p[3].replace('"', "'") in done or (p[0] + ":" + p[1]) in skip or not ok_zone(p[3]):
                continue
            out.append((p[0], p[1], p[3]))
    return out


def report(line):
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def danger_since(pos):
    with open(LOG, "rb") as f:
        f.seek(pos)
        t = f.read().decode("cp1251", "replace")
    m = re.search(r"## DANGER ([^\n]+)|Вы мертвы\. R\.I\.P", t)
    return m.group(0) if m else None


def run_zone(args):
    pos = os.path.getsize(LOG)
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(T, "explore_zone.py")] + args,
                       capture_output=True, text=True, encoding="utf-8")
    return r.stdout, danger_since(pos)


def summary(zone):
    d = os.path.join(K, "ЗОНЫ", zone.replace('"', "'"))
    f = os.path.join(d, "клетки.csv")
    if not os.path.exists(f):
        return "нет файла"
    R = [l.split(";") for l in open(f, encoding="cp1251").read().splitlines()[1:]]
    closed = sum(1 for r in R if len(r) > 3 and r[3] and "другая зона" not in r[3])
    tr = len(open(os.path.join(d, "переходы.csv"), encoding="cp1251").read().splitlines()) - 1
    mf = os.path.join(K, "JMC БОТ АЙЛИНА", "areas", "эксплор_" + zone.replace('"', "'").replace(" ", "_") + "_mob.csv")
    mobs = len(open(mf, encoding="cp1251", errors="replace").read().splitlines()) - 1 if os.path.exists(mf) else 0
    return "клеток %d, мобов %d, переходов %d, клеток с закрытыми выходами %d" % (len(R), mobs, tr, closed)


def travel(city):
    """Из Геоланта через Аватару в город."""
    if not walk("115144"):
        return False
    for c, w in (("войти портал", 3), ("куп 1", 6), ("путь " + city, 30), ("войти портал", 4)):
        jmc.type_line(c, force=True); time.sleep(w)
    return True


minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 180
t0 = time.time()
report("\n## %s — запуск explore_targets" % time.strftime("%d.%m %H:%M"))
cities = list(CITIES)
while time.time() - t0 < minutes * 60:
    best = None
    G, _ = speedwalk.graph()
    cur, _, area = where()
    if cur not in G and area and ok_zone(area) and area.replace('"', "'") not in explored():
        out, dng = run_zone(["here"])
        zone = area
    else:
        best = None
        for frm, d, zone in candidates():
            p = speedwalk.path(cur, frm, G)
            if p is not None and (best is None or len(p) < best[0]):
                best = (len(p), frm, d, zone)
        if not best:
            if not cities:
                report("- нечего больше проходить по картам, города для переезда кончились"); break
            city = cities.pop(0)
            report("- нет дороги по картам — еду через Аватару в %s" % city)
            if not walk("115092") or not travel(city):
                report("  не доехала"); continue
            out, dng = run_zone(["here"])
            zone = where()[2]
        else:
            _, frm, d, zone = best
            out, dng = run_zone([frm, d])
    last = (out.strip().splitlines() or ["?"])[-1]
    ok = "ГОТОВО" in out
    report("- %s **%s** — %s; %s%s" % (time.strftime("%H:%M"), zone, "готово" if ok else "НЕ ДО КОНЦА: " + last[-80:],
                                       summary(zone), "; ОПАСНОСТЬ: " + dng if dng else ""))
    if not ok and best:
        open(SKIPF, "a", encoding="utf-8").write(best[1] + ":" + best[2] + "\n")
    if dng:
        report("  СТОП партии: " + dng); break
subprocess.run([sys.executable, "-X", "utf8", os.path.join(T, "zones_summary.py")], capture_output=True)
report("## конец %s" % time.strftime("%H:%M"))
