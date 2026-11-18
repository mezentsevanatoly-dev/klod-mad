"""Потратить запас особенностей (звёзды) на АС у вещей комплектов :следак1/2/3: взять -> `особенность <вещь> ас` пока получается -> сдать обратно.
python -X utf8 tools/kit_stars.py [--dry]     (список берётся из ksk_items: dept Следак*, stars>0; перед запуском kit_collect.py)
1-е улучшение стоит 1 звезду, 2-е той же характеристики 2, 3-е 3: на ***  это +АС дважды.
"""
import os
import re
import sqlite3
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_collect as K  # noqa: E402
LOG = open(os.path.join(ROOT, "tools", "kit_stars.log"), "a", encoding="utf-8")


def say(s):
    LOG.write(s + "\n")
    LOG.flush()
    print(s, flush=True)


def main():
    dry = "--dry" in sys.argv
    db = sqlite3.connect(K.DB)
    rows = db.execute("select dept,name,cnt,stars,ac from ksk_items where dept like 'Следак%' and stars>0 order by dept,name").fetchall()
    for dept, name, cnt, stars, ac in rows:
        word = K.keyword(name)
        for i in range(max(cnt, 1)):
            say(f"{dept}: {name} (звёзд {stars}, АС {ac})")
            if dry:
                continue
            out = K.cmd(f"кз :{dept.lower()} {word}|2")
            if "забрали" not in out:
                say("   не забралось: " + " | ".join(l for l in out.splitlines() if l.strip())[:140])
                continue
            done = 0
            for _ in range(4):
                out = K.cmd(f"особенность {word} ас|2")
                if "Вы добавили" in out:
                    done += 1
                    say("   " + [l for l in out.splitlines() if "Вы добавили" in l][0][:110])
                else:
                    say("   стоп: " + " | ".join(l for l in out.splitlines() if l.strip() and "[cur]" not in l)[:140])
                    break
            out = K.cmd(f"кс :{dept.lower()} {word}|2")
            say("   сдано: " + ("да" if "сдали" in out else "НЕТ: " + out[-120:]))


if __name__ == "__main__":
    main()
