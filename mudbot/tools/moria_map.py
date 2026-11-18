"""Разметка шагов маршрута Мории (рр5_Мория.botp): индекс:vnum (T — триггер-строка)."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import botp_walk as b  # noqa: E402

s = b.load_steps(r"C:\Users\User\Desktop\мад\БОТ ЧВЫРЛА\areas\рр5_Мория.botp")


def rng(a, z):
    print(f"{a}-{z}:", " ".join(f"{i}:{x[1][-5:] if x[0] == 'step' else 'T'}" for i, x in enumerate(s) if a <= i < z))


for a, z in [(371, 404), (520, 562), (586, 600), (644, 652), (688, 696), (736, 748), (760, 790)]:
    rng(a, z)
