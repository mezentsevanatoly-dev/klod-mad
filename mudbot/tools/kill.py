"""Убить моба и дождаться конца боя: python -X utf8 tools/kill.py <слово> [мин_хп_%=40]
Бой виден по промпту с [имя:состояние]. Хп ниже порога -> убежать. Печатает итог."""
import os, sys, time, re
os.environ.setdefault("JMC_TARGET", r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jmc
word = sys.argv[1]
minpct = int(sys.argv[2]) if len(sys.argv) > 2 else 40
s = jmc.log_size()
jmc.type_line("убить " + word, force=True)
t0, calm, maxhp = time.time(), 0, 1709
dead, fled = [], False
while time.time() - t0 < 180:
    time.sleep(1)
    L = [re.sub(r"^\d\d:\d\d:\d\d ", "", l) for l in jmc.read_log(s)]
    s = jmc.log_size()
    for l in L:
        if "мертв" in l and "R.I.P" in l:
            dead.append(l.strip())
        m = re.search(r"(-?\d+)H \d+M", l)
        if m:
            hp = int(m.group(1))
            fight = bool(re.search(r"\[[^\]]+:[^\]]+\]", l))
            calm = 0 if fight else calm + 1
            if fight and hp * 100 < minpct * maxhp and not fled:
                jmc.type_line("убежать", force=True); fled = True
                print("хп", hp, "— убегаю")
    if calm >= 2 and time.time() - t0 > 4:
        break
print("убиты:", dead)
print("убежала" if fled else "бой окончен")
