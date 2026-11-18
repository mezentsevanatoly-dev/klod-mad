"""Партия эксплора: по очереди explore_zone.py для каждой пары (клетка перехода, направление).
Останавливается, если зона закончилась не ГОТОВО. Лог: mudbot\\data\\explore_batch.log"""
import os, sys, subprocess, time
T = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(os.path.dirname(T), "data", "explore_batch.log")
batch = [a.split(":") for a in sys.argv[1:]]          # "94099:восток" ...


def wait_idle():
    """Если в JMC ещё идёт эксплор (последняя строка EXPLORE не ГОТОВО/СТОП) — ждать до 15 мин."""
    import re
    L = os.path.join(os.path.dirname(os.path.dirname(T)), "JMC БОТ АЙЛИНА", "claude_game.log")
    for _ in range(180):
        ex = [l for l in open(L, encoding="cp1251", errors="replace") if "EXPLORE" in l]
        if not ex or re.search(r"EXPLORE (ГОТОВО|СТОП|НЕТ ПОЛЁТА|не запущен)", ex[-1]):
            return
        time.sleep(5)


wait_idle()
with open(LOG, "a", encoding="utf-8") as lg:
    for frm, d in batch:
        lg.write("\n=== %s %s %s\n" % (time.strftime("%H:%M:%S"), frm, d)); lg.flush()
        r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(T, "explore_zone.py"), frm, d],
                           capture_output=True, text=True, encoding="utf-8")
        lg.write(r.stdout + r.stderr); lg.flush()
        print(frm, d, "->", (r.stdout.strip().splitlines() or [r.stderr.strip()])[-1])
        if "ГОТОВО" not in r.stdout:
            print("СТОП партии на", frm, d); break
subprocess.run([sys.executable, "-X", "utf8", os.path.join(T, "zones_summary.py")], capture_output=True)
