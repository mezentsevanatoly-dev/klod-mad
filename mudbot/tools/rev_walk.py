# -*- coding: utf-8 -*-
"""Вернуть Айлину назад по уже пройденным шагам маршрута зоны: python tools/rev_walk.py <зона> <N шагов пройдено>.
Идёт в обратном порядке по ходам из первых N строк .botp. Первый обратный ход может упереться в стену (последний шаг не успел) - это нормально."""
import os, re, sys, time, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
zone, N = sys.argv[1], int(sys.argv[2])
jaba = os.path.join(BASE, "JMC БОТ АЙЛИНА")
env = dict(os.environ, JMC_TARGET=jaba); log = os.path.join(jaba, "claude_game.log")
opp = {"север": "юг", "юг": "север", "запад": "восток", "восток": "запад", "вверх": "вниз", "вниз": "вверх"}
L = open(os.path.join(jaba, "areas", zone + ".botp"), "rb").read().decode("cp1251").splitlines()[:N]
moves = []
for s in L:
    s = s.strip()
    m = re.search(r"\{(север|юг|запад|восток|вверх|вниз)\}\s*$", s)
    if m:
        moves.append(m.group(1))
    elif s in opp:
        moves.append(s)
rev = [opp[d] for d in reversed(moves)]
print("ходов назад:", len(rev), flush=True)
for i, d in enumerate(rev):
    pos = os.path.getsize(log)
    subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "jmc.py"), "do", "--force", d, "0.9"], env=env, capture_output=True)
    new = open(log, "rb").read()[pos:].decode("cp1251", "replace")
    if "слишком устали" in new:
        time.sleep(4)
    if re.search(r"Вы не можете идти", new) and i > 2:
        print("ПРЕРВАНО на", i + 1, d); sys.exit(2)
print("готово")
