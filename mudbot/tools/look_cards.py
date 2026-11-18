"""Посмотреть мобов в текущей клетке и дописать карточки в mob.csv зоны.
python -X utf8 tools/look_cards.py <файл_mob.csv> "<слово>|<строка в комнате>" ..."""
import os, sys, time, re
os.environ.setdefault("JMC_TARGET", r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jmc


def card(word):
    s = jmc.log_size()
    jmc.type_line("look " + word, force=True)
    time.sleep(2)
    c = {}
    for l in [re.sub(r"^\d\d:\d\d:\d\d ", "", x) for x in jmc.read_log(s)]:
        m = re.match(r"^(.+?) \[уровень (\d+)\], (.+)$", l)
        if m: c.update(name=m.group(1), level=m.group(2), prof=m.group(3).strip())
        m = re.match(r"^Особенности: (.*)$", l)
        if m: c["flags"] = m.group(1).strip()
        m = re.match(r"^Хиты: (\d+)/(\d+), мана: (\d+)/(\d+)", l)
        if m: c.update(hp=m.group(1), maxhp=m.group(2), mp=m.group(3), maxmp=m.group(4))
        m = re.match(r"^Навыки:\s*(.*)$", l)
        if m: c["skills"] = m.group(1).strip()
        m = re.match(r"^Вы видите перед собой (.+)\.$", l)
        if m: c["race"] = m.group(1)
    return c


if __name__ == "__main__":
    path = sys.argv[1]
    rows = open(path, encoding="cp1251", errors="replace").read().splitlines()
    for arg in sys.argv[2:]:
        word, desc = arg.split("|", 1)
        c = card(word)
        print(word, "->", c)
        if "name" not in c:
            continue
        f = [c["name"], desc + " ", c.get("hp", ""), c.get("mp", ""), c.get("maxhp", ""), c.get("maxmp", ""), "", "",
             c["level"], "false", "false", c.get("skills", ""), c["prof"], c.get("race", ""), c.get("flags", "")]
        rows = [r for r in rows if desc not in r]
        rows.append(";".join('"%s"' % x for x in f))
    open(path, "w", encoding="cp1251", newline="\r\n").write("\n".join(rows) + "\n")
