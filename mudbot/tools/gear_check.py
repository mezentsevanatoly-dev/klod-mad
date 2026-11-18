"""Проверка снаряжения на новом уровне: оценка Дк надетых вещей против биржи и кланового склада.

python tools/gear_check.py   -> по каждому слоту лучшие лоты биржи и вещи кск с оценкой выше нашей (=я !оценка+1)
Ничего не покупает и не берёт: решение за пользователем. Итог пишется в data/gear_<уровень>.txt.
"""
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from explore_msdp import ROOT, Explorer  # noqa: E402

SLOTS = {"приколото к груди": "допслот", "надето на шее": "шея", "надето на теле": "тело", "наброшено на плечи": "плечи",
         "надето на талии": "талия", "надето на кисти рук": "кисти", "надето на руки": "руки", "надето на ноги": "ноги",
         "используется как обувь": "обувь", "запястье": "запястье", "палец": "палец", "надето на голову": "голова",
         "используется как щит": "щит"}
MORE = "<Enter> - показать следующую страницу"


def paged(ex, cmd, wait=2.0):
    """Ответ команды со всеми страницами (листаем Enter)."""
    out = ex.answer(cmd, wait)
    for _ in range(30):
        if not any(MORE in l for l in out[-3:]):
            break
        out = [l for l in out if MORE not in l] + ex.answer("", wait)
    return [l for l in out if MORE not in l]


def rating(ex, word):
    lines = ex.answer("осмотреть " + word, 1.5)
    for i, l in enumerate(lines):
        if l.startswith("Оценка:") and i:
            r = dict(zip(lines[i - 1].split(), [x.strip() for x in l[7:].split(",")]))
            return int(r.get("Дк", 0))
    return 0


def main():
    ex = Explorer()
    worn = []
    for l in ex.answer("экипировка", 1.5):
        m = re.match(r"^ <(.+?)>\s+(.+?)\s*(?:[#*]|\[)", l)
        if m:
            slot = next((v for k, v in SLOTS.items() if k in m.group(1)), None)
            if slot:
                worn.append((slot, m.group(2).strip()))
    lvl = next((m.group(1) for l in ex.answer("счет", 1.5) if (m := re.search(r"(\d+) уровня", l))), "?")
    report = [f"Проверка снаряжения, уровень {lvl}, {time.strftime('%Y-%m-%d %H:%M')}"]
    best = {}
    for slot, name in worn:
        r = rating(ex, ".".join(name.split()[:2]))
        report.append(f"{slot:9} {name}: Дк {r}")
        best[slot] = min(best.get(slot, 999), r)          # на парных слотах сравниваем с худшей вещью
    for slot, r in best.items():
        for where, cmd in (("биржа", f"биржа предложения одежда *{slot} =я !{r + 1}"),
                           ("кск", f"клан склад одежда *{slot} =я !{r + 1}")):
            out = paged(ex, cmd)
            if where == "биржа":
                lots = [l for l in out if re.match(r"^\s*\d+\.", l)]
            else:                               # кск: « имя» между «хранятся:» и «Всего N предметов»
                lots = [l for l in out if l.startswith(" ") and not l.startswith("<<")]
            report.append(f"-- {slot} (у меня {r}) {where}: {len(lots)}")
            report += ["   " + l.strip() for l in lots[:15]]
    path = os.path.join(ROOT, "data", f"gear_{lvl}.txt")
    open(path, "w", encoding="utf-8").write("\n".join(report) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    main()
