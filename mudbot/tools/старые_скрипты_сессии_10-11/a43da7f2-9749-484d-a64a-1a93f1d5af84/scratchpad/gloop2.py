import re, time, subprocess, os, sys
LOG = r"C:\Users\User\Desktop\Тадия\claude_game.log"
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
pos = max(0, os.path.getsize(LOG) - 2500); fails = 0; t0 = time.time()
J = ["python", "-X", "utf8", r"C:\Users\User\Desktop\Клод мад\mudbot\tools\jmc.py", "do", "--force"]
buf = ""
while time.time() - t0 < 270:
    time.sleep(2)
    sz = os.path.getsize(LOG)
    if sz <= pos: continue
    with open(LOG, "rb") as f:
        f.seek(pos); chunk = f.read().decode("cp1251", "replace"); pos = sz
    buf += chunk
    if ("ZONE_END zone=" + sys.argv[1]) in buf: print("ZONE_END гоблины"); break
    m = re.search(r"## BOT_STOP step=(\d+)/(\d+)", buf)
    if m:
        ctx = buf[max(0, m.start() - 300): m.start()]
        if "Вы не можете идти" in ctx or "Хмм" in buf[m.start():]:
            step = int(m.group(1)) - 1
            print("сбой хода на шаге", step); r = subprocess.run(["python", "-X", "utf8", S + r"\gdrop.py", str(step), sys.argv[1]], capture_output=True, text=True); print(r.stdout.strip()[:200])
            buf = ""; pos = os.path.getsize(LOG); fails += 1
            if fails > 12: break
        else:
            print("стоп не по ходу:", ctx[-200:]); break
print("итого сбоев", fails)
