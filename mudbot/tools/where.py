"""Где стоит персонаж в JMC: номер клетки, название, зона (из MSDP). python -X utf8 tools/where.py"""
import os, sys, time
os.environ.setdefault("JMC_TARGET", r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jmc


def where():
    s = jmc.log_size()
    jmc.type_line("#scr ClaudeLog.note('WHERE $MsdpRoomVnum|$MsdpRoomName|$MsdpRoomArea')", force=True)
    time.sleep(1)
    for l in jmc.read_log(s):
        if "## WHERE " in l:
            return l.split("## WHERE ")[1].strip().split("|", 2)
    return None, None, None


if __name__ == "__main__":
    print(where())
