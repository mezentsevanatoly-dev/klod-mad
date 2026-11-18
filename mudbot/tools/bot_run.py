"""Прогнать бота по зоне и отчитаться: bot_run.py <зона> [минут=20]
Шлёт `.бот старт <зона>`, ждёт ZONE_END / BOT_STOP / смерть; печатает: время, шаги, бои (убил кого), повторы шага,
застревания (клетка не меняется > 60 с), DANGER. В конце — где стоит."""
import os, sys, time, re, collections
os.environ.setdefault("JMC_TARGET", r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jmc
from where import where
zone = sys.argv[1]
lim = float(sys.argv[2]) * 60 if len(sys.argv) > 2 else 1200
print("старт:", where(), flush=True)
s = jmc.log_size()
jmc.type_line(".бот старт " + zone, force=True)
t0 = last_move = time.time(); end = None
kills = collections.Counter(); blocked = 0; waits = 0; said = 0
while time.time() - t0 < lim:
    time.sleep(1)
    for l in jmc.read_log(s):
        if "[ Exits:" in l: last_move = time.time()
        m = re.search(r"\d\d:\d\d:\d\d (.+?) мертв[аоы]?\. R\.I\.P", l)
        if m: kills[m.group(1)] += 1
        if "MOVE_BLOCKED" in l: blocked += 1
        if re.search(r"BOT_START|ZONE_END|BOT_STOP|DANGER|## UD |Вы мертвы|не можете идти|У вас нет нужного ключа|ЗАПЕРТО", l):
            print(l.strip(), flush=True)
        if "ZONE_END" in l or "BOT_STOP" in l or re.search(r"^\S+\s+Вы мертвы", l): end = l
    s = jmc.log_size()
    if end: break
    if time.time() - last_move > 60 and time.time() - said > 60:
        print("стоит > 60 с:", where(), flush=True); said = time.time()
print("ИТОГ:", (end or "лимит времени").strip(), "|", round((time.time() - t0) / 60, 1), "мин | повторов шага (бой):", blocked, flush=True)
print("убила:", dict(kills), flush=True)
print("сейчас:", where(), flush=True)
