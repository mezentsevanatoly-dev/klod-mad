"""Осмотр всех мобов в комнате по номерам (`см 1.`, `см 2.` …) и запись карточек в data/game.db (таблица mob_cards).

  python tools/survey_here.py "<зона>" [макс_номер]

Карточка моба в игре:
  Мотылек [уровень 1], Воин
  Хиты: 6/6, мана: 10/10
  Навыки: -
  <описание> ... Вы видите перед собой насекомое.
Нумерация: сначала мобы комнаты, потом игроки (в т.ч. я сама), потом предметы. Останавливаемся на первой карточке не-моба
(«Вы видите перед собой орка» с именем персонажа, «Предмет '…'», «Вы не видите»).
"""
import os
import re
import sqlite3
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(HERE, "data", "game.db")
CARD = re.compile(r"^(.+?) \[уровень (\d+)\](?:, (.+))?$")


def send(cmds):
    env = dict(os.environ, MUD_VIA="bot", PYTHONUTF8="1")
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "tools", "cmd.py")] + [f"{c}|1.3" for c in cmds],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=HERE, env=env)
    return r.stdout


def parse(out):
    """-> список блоков по командам `см N.`"""
    blocks, cur = {}, None
    for l in out.split("\n"):
        m = re.match(r"^>>> см (\d+)\.", l)
        if m:
            cur = int(m.group(1))
            blocks[cur] = []
        elif cur is not None:
            blocks[cur].append(l.rstrip())
    return blocks


def main(zone, n=8):
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS mob_cards (zone TEXT, name TEXT, level INTEGER, prof TEXT, hp TEXT, mana TEXT, skills TEXT,
                 kind TEXT, desc TEXT, room TEXT, PRIMARY KEY (zone, name))""")
    out = send([f"см {i}." for i in range(1, n + 1)])
    blocks = parse(out)
    got = []
    for i in range(1, n + 1):
        b = blocks.get(i, [])
        head = next((x for x in b if CARD.match(x.strip())), None)
        if not head:
            if any(x.startswith("Вы не видите") for x in b):
                break                                        # номеров больше нет
            continue                                         # я сама или предмет: 1. — ты, 2. — первый моб, вошедший моб становится 1.
        m = CARD.match(head.strip())
        hp = mana = skills = kind = ""
        desc = []
        for x in b:
            s = x.strip()
            mm = re.match(r"^Хиты: (\S+), мана: (\S+)", s)
            if mm:
                hp, mana = mm.group(1).rstrip(","), mm.group(2)
            elif s.startswith("Навыки:"):
                skills = s.split(":", 1)[1].strip()
            elif s.startswith("Вы видите перед собой"):
                kind = s.replace("Вы видите перед собой", "").strip(" .")
            elif s and not s.startswith(("[cur]",)) and not re.match(r"^\d+H ", s) and s != head.strip() and not s.startswith(("Хиты", "Навыки")):
                desc.append(s)
        c.execute("INSERT OR REPLACE INTO mob_cards VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (zone, m.group(1), int(m.group(2)), m.group(3) or "", hp, mana, skills, kind, " ".join(desc)[:300], ""))
        got.append((i, m.group(1), m.group(2), m.group(3) or "", hp, skills))
    c.commit()
    c.close()
    for g in got:
        print("  ".join(str(x) for x in g))
    print(f"осмотрено мобов: {len(got)}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 8)
