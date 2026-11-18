"""Отдых до полного хп и энергии: отдых, ждать ($MsdpHealth/$MsdpHealthMax, $MsdpMovement/$MsdpMovementMax), максимум 10 мин, вст."""
import os, sys, time
os.environ.setdefault("JMC_TARGET", r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jmc


def stat():
    s = jmc.log_size()
    jmc.type_line("#scr ClaudeLog.note('HP $MsdpHealth|$MsdpHealthMax|$MsdpMovement|$MsdpMovementMax')", force=True)
    time.sleep(1)
    for l in jmc.read_log(s):
        if "## HP " in l:
            try:
                return [int(x) for x in l.split("## HP ")[1].strip().split("|")]
            except ValueError:
                pass
    return [0, 1, 0, 1]


def full(st):
    return st[0] >= st[1] and st[2] >= st[3]


st = stat()
print("хп %d/%d, энергия %d/%d" % tuple(st))
if not full(st):
    jmc.type_line("отдых", force=True)
    t0 = time.time()
    while time.time() - t0 < 600:
        time.sleep(15)
        st = stat()
        if full(st):
            break
    jmc.type_line("вст", force=True)
print("стало: хп %d/%d, энергия %d/%d" % tuple(stat()))
