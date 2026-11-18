"""Выполнить внутриигровой `путь <куда>` в JMC и записать пройденный путь (по строкам «Вы направились на …») + vnum конца.

  python -X utf8 tools/walk_capture.py "путь банк" [секунд_ожидания=25]
Печатает: ходы списком и сжатым спидволком, vnum конца (через ClaudeLog.note VN=...). Использовать только в городах (по слову пользователя).
"""
import os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\claude_game.log"
cmd = sys.argv[1]
wait = float(sys.argv[2]) if len(sys.argv) > 2 else 25
D = {"север": "n", "юг": "s", "восток": "e", "запад": "w", "вверх": "u", "вниз": "d"}
start = os.path.getsize(LOG)
subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "jmc.py"), "type", cmd, "--force"], check=True, capture_output=True)
t0 = time.time(); last = 0
while time.time() - t0 < wait:
    time.sleep(1.5)
    txt = open(LOG, "rb").read()[start:].decode("cp1251", "replace")
    if "Вы достигли пункта назначения" in txt or "не удалось" in txt.lower():
        break
subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "jmc.py"), "type", "#scr ClaudeLog.note('VN=' + $MsdpRoomVnum)", "--force"], check=True, capture_output=True)
time.sleep(1.5)
txt = open(LOG, "rb").read()[start:].decode("cp1251", "replace")
ms = re.findall(r"Вы направились на (север|юг|восток|запад|вверх|вниз)", txt)
vn = re.findall(r"## VN=(\d+)", txt)
s = "".join(D[m] for m in ms)
comp = re.sub(r"(.)\1+", lambda m: str(len(m.group(0))) + m.group(1), s)
print("ходов:", len(ms), "|", comp, "| vnum конца:", vn[-1] if vn else "?", "| достигли:", "Вы достигли пункта назначения" in txt)
print(" ".join(ms))
