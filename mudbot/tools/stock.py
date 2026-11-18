"""Проверка расходников и полёта перед выходом из ренты (через JMC): python tools/stock.py
Читает data/stock.tsv (что носить и сколько держать в КСК :Колбы), смотрит `аффекты`, `инвентарь`, `ксклад :колбы`
и печатает нехватку: что взять из :Колбы (команда кзабрать готова) и что докупить.
ПОЛЁТ: из ренты без аффекта «плавная левитация» (= полёт) не выходить.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jmc  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_items(lines):
    """«настойка насыщения [2]» -> [(название, число)]; строки вида ' название' или '[Колбы]:  название'."""
    res = []
    for l in lines:
        m = re.match(r"^\s*(?:\[[^\]]*\]:\s+)?(\S.*?)(?:\s+\[(\d+)\])?\s*$", l)
        if not m or l.startswith(("<", "Вы ", "Всего", "В отделе", "На складе", "Аффекты")):
            continue
        res.append((m.group(1), int(m.group(2) or 1)))
    return res


def main():
    out = dict(jmc.do_many(["аффекты", "инвентарь", "ксклад :колбы"], 1.5))
    aff = "\n".join(out["аффекты"])
    print("полёт (плавная левитация):", "ЕСТЬ" if "плавная левитация" in aff else "НЕТ — из ренты не выходить!")
    inv, kolby = parse_items(out["инвентарь"]), parse_items(out["ксклад :колбы"])
    print(f"{'расходник':34}{'при себе':>9}{'норма':>7}{'в Колбах':>10}{'запас':>7}")
    take, buy = [], []
    for line in open(os.path.join(ROOT, "data", "stock.tsv"), encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        name, key, carry, reserve, words = line.rstrip("\n").split("\t")
        carry, reserve = int(carry), int(reserve)
        have = sum(n for t, n in inv if re.search(key, t))
        kol = sum(n for t, n in kolby if re.search(key, t))
        print(f"{name:34}{have:>9}{carry:>7}{kol:>10}{reserve:>7}")
        need = max(0, carry - have)
        if need:
            t = min(need, kol)
            if t:
                take.append(f"{words} " * t)
            if need > t:
                buy.append(f"{name}: не хватает {need - t} при себе")
        if kol < reserve:
            buy.append(f"{name}: в :Колбы {kol} из {reserve}")
    if take:
        print("\nвзять из :Колбы:  кзабрать :колбы " + " ".join(take).strip())
    if buy:
        print("\nдокупить/пополнить:\n  " + "\n  ".join(buy))


if __name__ == "__main__":
    main()
