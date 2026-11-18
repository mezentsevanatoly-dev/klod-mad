"""Прогнать бота по списку зон (маршруты JMC БОТ АЙЛИНА\\areas): bot_batch.py зона1 зона2 ...
Старт зоны: клетка, из которой шаги до первого #if с номером приводят в этот номер (кандидаты: склады/ренты городов).
Доводит (walk), запускает bot_run.py, итог — в mudbot\\data\\bot_batch.log и на экран. Стоп партии: смерть / не дошла."""
import os, sys, re, subprocess, time
os.environ.setdefault("JMC_TARGET", r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА")
T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, T)
from walk import walk
from where import where
import route_check as rc
AREAS = r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА\areas"
LOG = os.path.join(os.path.dirname(T), "data", "bot_batch.log")
STARTS = ["100076", "115092", "100001", "100071", "115144"]   # склад Элендора, склад Геоланта, рента Элендора, холл, портал Геоланта
G, names, zones = rc.graph()


def start_of(zone):
    pre = []
    for l in open(os.path.join(AREAS, zone + ".botp"), encoding="cp1251", errors="replace").read().splitlines():
        m = rc.VN.search(l)
        if m: target = m.group(1); break
        w = l.strip().lower()
        if w in rc.DIRW: pre.append(rc.DIRW[w])
    else:
        return None
    if not pre: return target
    for s in STARTS + list(G):
        cur = s
        for d in pre:
            cur = G.get(cur, {}).get(d)
            if not cur: break
        if cur == target: return s
    return None


with open(LOG, "a", encoding="utf-8") as lg:
    for z in sys.argv[1:]:
        st = start_of(z)
        head = "=== %s %s старт %s (%s)" % (time.strftime("%H:%M:%S"), z, st, names.get(st, "?"))
        print(head, flush=True); lg.write(head + "\n"); lg.flush()
        if st and not walk(st):
            subprocess.run([sys.executable, "-X", "utf8", os.path.join(T, "go_any.py"), st], capture_output=True, text=True, encoding="utf-8", cwd=T)
        if not st or where()[0] != st:
            msg = "не дошла до старта %s, стою %s" % (st, where()); print(msg, flush=True); lg.write(msg + "\n"); break
        r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(T, "bot_run.py"), z, "25"], capture_output=True, text=True, encoding="utf-8", cwd=T)
        print(r.stdout.strip(), flush=True); lg.write(r.stdout + r.stderr); lg.flush()
        if "Вы мертвы" in r.stdout: print("СТОП: смерть"); break
print("партия закончена", where())

