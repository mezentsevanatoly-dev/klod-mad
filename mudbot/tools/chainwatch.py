"""Сторож цепочки зон JMC-бота: чинит остановки BOT_STOP по ходу (потерянный шаг плоского маршрута) и снимает ложные ПнП-паузы.
  python -X utf8 tools/chainwatch.py            (работает до Ctrl+C / файла tools/chainwatch.stop)
Логика BOT_STOP step=N/M после «Вы не можете идти»:
  1) ищем среди последних STEP пару подряд с одинаковым vn и ходом -> потерян шаг k -> перезапуск с k;
  2) иначе удаляем сбойную команду (шаг N-1) из .botp ЗОНЫ, если она плоская (без #if) и перезапуск с N-1.
Ничего не делает при остановке по другой причине (смерть, ручной стоп) - только пишет в chainwatch.log."""
import os, re, subprocess, sys, time

LOG = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\claude_game.log"
AREAS = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\areas"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "chainwatch.log")
STOPF = os.path.join(HERE, "chainwatch.stop")
J = [sys.executable, "-X", "utf8", os.path.join(HERE, "jmc.py"), "do", "--force"]

def note(s):
    with open(OUT, "a", encoding="utf-8") as f: f.write(time.strftime("%H:%M:%S ") + s + "\n")

def jm(x):
    subprocess.run(J + [x], stdout=subprocess.DEVNULL); time.sleep(2)

def resume(zone, step):
    for x in ["#scr botCore.enableBot=false", "#scr botCore.loadZone('%s')" % zone, "#scr seekstep=%d" % step,
              "#scr botCore.BotInZone=true", "#scr botCore.enableBot=true", "look краткий"]:
        jm(x)

def zone_by_total(total, hint):
    cand = []
    for fn in os.listdir(AREAS):
        if fn.endswith(".botp"):
            try:
                n = len([x for x in open(os.path.join(AREAS, fn), "rb").read().decode("cp1251").split("\r\n") if x != ""])
            except Exception: continue
            if n == total: cand.append(fn[:-5])
    if hint in cand or len(cand) != 1: return hint if hint in cand else (cand[0] if len(cand) == 1 else None)
    return cand[0]

pos = os.path.getsize(LOG); buf = ""; zone = None; steps = []   # (idx, vn, cmd)
_tail = open(LOG, "rb").read()[-400000:].decode("cp1251", "replace")
_m = re.findall(r"## BOT_START zone=(\S+)", _tail)
if _m: zone = _m[-1]
lastact = time.time(); fixes = 0; tries = {}
note("старт сторожа")
while not os.path.exists(STOPF):
    time.sleep(2)
    sz = os.path.getsize(LOG)
    if sz <= pos: continue
    with open(LOG, "rb") as f:
        f.seek(pos); chunk = f.read().decode("cp1251", "replace"); pos = sz
    buf += chunk
    for m in re.finditer(r"## BOT_START zone=(\S+)", chunk): zone = m.group(1); steps = []
    for m in re.finditer(r"## STEP (\d+) vn=(\S*) cmd=(.*)", chunk): steps.append((int(m.group(1)), m.group(2), m.group(3).strip()))
    steps = steps[-40:]
    m = None
    for m in re.finditer(r"## BOT_STOP step=(\d+)/(\d+)", chunk): pass
    if m and zone and "Вы не можете идти" in buf[-1500:]:
        n = int(m.group(1)); buf = ""
        zone = zone_by_total(int(m.group(2)), zone) or zone
        k = None
        for a, b in zip(steps[:-1], steps[1:]):
            if a[1] == b[1] and a[2] in ("север", "юг", "восток", "запад", "вверх", "вниз") and a[0] >= n - 8: k = a[0]; break
        if k is not None:
            tries[(zone, k)] = tries.get((zone, k), 0) + 1
            if tries[(zone, k)] > 2:
                note("зона %s: шаг %d падает снова - нужен человек" % (zone, k))
            else:
                note("зона %s: потерян шаг %d (vn повторился) -> перезапуск с %d" % (zone, k, k)); resume(zone, k); fixes += 1
        else:
            note("зона %s: сбой хода на шаге %d, нужен человек (файл не трогаю)" % (zone, n - 1))
    elif m:
        note("BOT_STOP не по ходу (зона %s, шаг %s)" % (zone, m.group(1))); buf = ""
    buf = buf[-3000:]
note("сторож остановлен")
