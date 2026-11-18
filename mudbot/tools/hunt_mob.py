"""Охота на ходячего моба: обход заданного маршрута, после КАЖДОГО шага смотрит текст комнаты;
при имени моба в строках комнаты останавливается и бьёт (убить <слово>), ждёт конца боя.
Запуск: python -X utf8 tools/hunt_mob.py <регэксп_имени> <слово_для_убить> "<шаги через пробел>" [кругов]"""
import os, sys, re, time
os.environ.setdefault("JMC_TARGET", r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА")
sys.path.insert(0, os.path.dirname(__file__))
import jmc, step_vn

pat = re.compile(sys.argv[1], re.I)
kw = sys.argv[2]
steps = sys.argv[3].split()
laps = int(sys.argv[4]) if len(sys.argv) > 4 else 3
edit = jmc.find_input(jmc.find_window())


def send(cmd, wait=1.0, quiet=1.2, maxwait=25):
    start = jmc.log_size()
    jmc.type_line(cmd, True, edit)
    time.sleep(wait)
    t0 = time.time(); last = jmc.log_size(); lc = time.time()
    while time.time() - t0 < maxwait:
        time.sleep(0.4)
        sz = jmc.log_size()
        if sz != last:
            last = sz; lc = time.time()
        lines = [re.sub(r"^\d\d:\d\d:\d\d ", "", l) for l in jmc.read_log(start)]
        fight = any(re.match(r"^\d+H .*\[Айлина:", l) for l in lines[-3:])
        if time.time() - lc >= quiet and not fight:
            break
    return [re.sub(r"^\d\d:\d\d:\d\d ", "", l) for l in jmc.read_log(start) if l.strip()]


step_vn.close_errors()
for lap in range(laps):
    for s in steps:
        out = send(s)
        txt = "\n".join(out)
        print(f"{lap}:{s}", "|", " ".join(l for l in out if pat.search(l))[:80], flush=True)
        if "мертв" in txt and pat.search(txt):
            print("УБИТ:", [l for l in out if "получили" in l or "Вы взяли" in l]); sys.exit(0)
        if pat.search(txt):
            for _ in range(6):
                o2 = send(f"убить {kw}", wait=1.0, quiet=2.0, maxwait=40)
                t2 = "\n".join(o2)
                print("  бой:", [l for l in o2 if "мертв" in l or "получили" in l or "Вы взяли" in l], flush=True)
                if "мертв" in t2:
                    sys.exit(0)
print("не нашла")
