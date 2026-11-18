"""Довести персонажа в JMC до клетки по картам эксплора: python -X utf8 tools/go.py <куда_vnum>
Путь одной строкой; если очередь сбросило (бой, автомол) — досылает от текущей клетки (walk.py)."""
import os, sys
os.environ.setdefault("JMC_TARGET", r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import speedwalk
from where import where
from walk import walk

target = sys.argv[1]
G, names = speedwalk.graph()
cur = where()[0]
print("из", cur, names.get(cur), "в", target, names.get(target))
ok = walk(target, G=G)
now = where()[0]
print("теперь:", now, names.get(now), "OK" if ok else "НЕ ДОШЛА")
