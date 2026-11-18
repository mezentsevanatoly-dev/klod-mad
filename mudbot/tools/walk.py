"""Общая ходьба по картам эксплора: путь одной строкой; если очередь сбросило (бой, автомол) — дослать от текущей клетки.
from walk import walk; walk(<клетка>) -> True/False"""
import os, sys, time
os.environ.setdefault("JMC_TARGET", r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jmc, speedwalk
from where import where


def walk(target, tries=10, G=None):
    G = G or speedwalk.graph()[0]
    for attempt in range(tries):
        cur = where()[0]
        if cur == target:
            return True
        p = speedwalk.path(cur, target, G)
        if p is None:
            print("нет пути из", cur, "в", target)
            return False
        if attempt:
            time.sleep(3)                       # дать закончиться бою / молитве
        jmc.type_line(";".join(p), force=True)
        time.sleep(max(2.5, len(p) * 0.15))
    return where()[0] == target
