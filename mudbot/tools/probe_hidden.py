"""Поиск скрытых проходов: для каждой пары клетка:направление — дойти, шагнуть, посмотреть, сменилась ли клетка, вернуться.
python -X utf8 tools/probe_hidden.py 154014:восток 154015:запад ..."""
import os, sys, time
os.environ.setdefault("JMC_TARGET", r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jmc, speedwalk
from where import where
from walk import walk
OPP = {"север": "юг", "юг": "север", "запад": "восток", "восток": "запад", "вверх": "вниз", "вниз": "вверх"}
G, names = speedwalk.graph()
for arg in sys.argv[1:]:
    cell, d = arg.split(":")
    if not walk(cell, G=G):
        print(arg, "не дошла"); continue
    jmc.type_line(d, force=True); time.sleep(2)
    nv, nn, na = where()
    if nv != cell:
        print("СКРЫТЫЙ ПРОХОД:", cell, d, "->", nv, nn, na)
        jmc.type_line(OPP[d], force=True); time.sleep(2)
        print("  назад:", where()[0])
    else:
        print(arg, "— нет")
