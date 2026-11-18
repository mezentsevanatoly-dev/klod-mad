"""База умений и заклинаний по профессиям: data/skills.json.

1) из data/help/<профессия>.txt берём списки «Умения:» и «Заклинания:»;
2) по каждому читаем справку (?заклинание_X / ?умение_X), сохраняем в data/help/;
3) из таблицы «Профессии, у которых есть ... Необходимый уровень» берём уровень для каждой профессии.
python tools/build_skills.py [заклинания|умения|разбор]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
from dump_help import OUT, fetch  # noqa: E402
from explore_zone import FileClient  # noqa: E402

CLASSES = {"воин": "Воин", "варвар": "Варвар", "следопыт": "Следопыт", "вор": "Вор", "паладин": "Паладин",
           "дк": "Рыцарь смерти", "маг": "Маг", "друид": "Друид", "лекарь": "Лекарь", "некромант": "Некромант"}


def class_lists():
    skills, spells = {}, {}
    for f, cname in CLASSES.items():
        txt = open(os.path.join(OUT, f + ".txt"), encoding="utf-8").read().splitlines()
        sec = None
        for l in txt:
            s = l.strip()
            if s.startswith("Оружейные умения"):
                sec = None
            elif s.startswith("Умения:"):
                sec = "skill"
            elif s.startswith("Заклинания:"):
                sec = "spell"
            elif s.startswith("Смотрите также"):
                sec = None
            elif sec and s:
                m = re.match(r"^(.+?)\s{2,}(\d+)%(?:\s+(\S+))?", s)
                if m:
                    d = skills if sec == "skill" else spells
                    d.setdefault(m.group(1), {})[cname] = {"spec": int(m.group(2))}
                    if sec == "spell" and m.group(3):
                        d[m.group(1)]["_sphere"] = m.group(3)
    return skills, spells


def topic(kind, name):
    return ("заклинание_" if kind == "spell" else "умение_") + name.lower().replace(" ", "_")


def fn(t):
    return os.path.join(OUT, re.sub(r"[^\w]+", "_", t) + ".txt")


def fetch_all(kind):
    skills, spells = class_lists()
    names = spells if kind == "spell" else skills
    c = FileClient()
    for n in names:
        t = topic(kind, n)
        if os.path.exists(fn(t)) and os.path.getsize(fn(t)) > 200:
            continue
        txt = fetch(c, t)
        if "СПРАВКА_НЕ_НАЙДЕНА" in txt:          # у некоторых умений тема без префикса
            txt = fetch(c, n.lower().replace(" ", "_"))
        open(fn(t), "w", encoding="utf-8").write(txt)
        print(t, len(txt.splitlines()), flush=True)


def parse_levels(txt):
    """{профессия: уровень} из таблицы «Пpофессии, у котоpых есть»."""
    res, on = {}, False
    for l in txt.splitlines():
        if "Необходимый уровень" in l:
            on = True
            continue
        if on:
            m = re.match(r"^\s{2}(\S.*?)\s{2,}(\d+)%\s+(\d+)", l)
            if m:
                res[m.group(1).strip()] = int(m.group(3))
            elif l.startswith("Смотрите"):
                break
    return res


def build():
    skills, spells = class_lists()
    db = {"skills": {}, "spells": {}}
    for kind, names, key in (("skill", skills, "skills"), ("spell", spells, "spells")):
        for n, classes in names.items():
            path = fn(topic(kind, n))
            txt = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            levels = parse_levels(txt)
            m = re.search(r"Описание\s*:\s*(.+)", txt)
            db[key][n] = {"classes": {c: {**v, "level": levels.get(c)} for c, v in classes.items() if not c.startswith("_")},
                          "sphere": classes.get("_sphere", ""),
                          "about": m.group(1).strip() if m else (txt.splitlines()[2].strip() if len(txt.splitlines()) > 2 else "")}
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    json.dump(db, open(os.path.join(ROOT, "data", "skills.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    no_lvl = [n for k in db for n, v in db[k].items() if any(c["level"] is None for c in v["classes"].values())]
    print(f"умений {len(db['skills'])}, заклинаний {len(db['spells'])}, без уровня: {len(no_lvl)} {no_lvl[:15]}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "разбор"
    if mode == "заклинания":
        fetch_all("spell")
    elif mode == "умения":
        fetch_all("skill")
    else:
        build()
