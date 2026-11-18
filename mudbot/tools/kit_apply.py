"""Разложить выбранные комплекты по отделам КСК: python -X utf8 tools/kit_apply.py <план.json> [--dry]
Для каждой вещи комплекта N: если она не в :следакN — забрать (`кз :отдел слова`) и сдать (`кс :следакN слова`) по одной; рынок (биржа)
не трогаем. Лишнее из :следак1/2/3 (не из планов) уходит в :общий. Стоим в комнате склада. Журнал: tools/kit_apply.log.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = dict(os.environ, MUD_VIA="bot")
STOP = {"из", "с", "в", "на", "и", "для", "от", "под", "над", "по"}
LOG = open(os.path.join(ROOT, "tools", "kit_apply.log"), "a", encoding="utf-8")


def say(s):
    LOG.write(s + "\n")
    LOG.flush()
    print(s, flush=True)


def cmd(c):
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(ROOT, "tools", "cmd.py"), c], env=ENV, cwd=ROOT, capture_output=True,
                       encoding="utf-8", errors="replace", timeout=120)
    return r.stdout


def kw(name):
    words = [w for w in re.sub(r"[*,\[\]#\d]", " ", name).split() if w.lower() not in STOP]
    return ".".join(w[:5] for w in words)


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_collect as K  # noqa: E402


def take(dept, word):
    """Забрать с повтором: бывает, что игра на первую команду ничего не отвечает."""
    for _ in range(3):
        out = cmd(f"кз :{dept} {word}|2")             # |2: ждать 2 с тишины, игра отвечает с задержкой
        if re.search(r"Вы (?:взяли|забрали|получили)|забрал", out) or "нет '" in out or "нет доступа" in out:
            return out
    return out


def listing(dept):
    out = K.cmd_pages(f"ксклад :{dept}")
    items = []
    for l in out.splitlines():
        m = re.match(r"^ (.+?)(?: \[(\d+)\])?\s*$", l)
        if m and not l.startswith((" Всего", ">>>")) and "хранятся" not in l and "Вых:" not in l and "[cur]" not in l \
                and not m.group(1).startswith("Ничего"):
            items += [m.group(1).strip()] * int(m.group(2) or 1)
    return items


def kw_index(items, name):
    """Номер совпадения для `кз :отдел N<слова>`: среди вещей отдела с теми же словами берём позицию нужной (звёзды в названии различаются)."""
    parts = kw(name).split(".")
    def match(it):
        words = [w.lower() for w in re.sub(r"[*,\[\]#\d]", " ", it).split()]
        return all(any(w.startswith(p.lower()) for w in words) for p in parts)
    hits = [it for it in items if match(it)]
    return (hits.index(name) + 1) if name in hits else 1


def main():
    plan = json.load(open(sys.argv[1], encoding="utf-8"))
    dry = "--dry" in sys.argv
    want = {}
    for sid, ch in plan.items():
        for slot, picks in ch.items():
            for p in picks:
                if p["src"].startswith("КСК"):
                    want.setdefault(sid, []).append(p)
    for sid in ("3", "2", "1"):
        target = f"следак{sid}"
        have = listing(target)
        say(f"== {target}: сейчас {len(have)} предметов")
        for p in want.get(sid, []):
            dept = p["src"].split(":", 1)[1].lower()
            if p["name"] in have:                                   # такая вещь уже лежит в целевом отделе (в т.ч. другой экземпляр)
                have.remove(p["name"])
                say(f"  уже там: {p['name']}")
                continue
            say(f"  {p['name']}: :{dept} -> :{target}")
            if dry:
                continue
            idx = kw_index(listing(dept), p["name"])
            word = (str(idx) if idx > 1 else "") + kw(p["name"])
            out = take(dept, word)
            if not re.search(r"Вы (?:взяли|забрали|получили)|забрал", out):
                say("    не забралось: " + " | ".join(l for l in out.splitlines() if l.strip())[:200])
                continue
            out2 = cmd(f"кс :{target} {kw(p['name'])}|2")
            say("    сдано: " + " | ".join(l for l in out2.splitlines() if l.strip() and "[cur]" not in l)[:140])
    # лишнее из следак1 -> общий
    norm = lambda s: re.sub(r"[\s*]+$", "", s.replace("*", "")).strip()
    keep = {norm(p["name"]) for sid in want for p in want[sid]} | {"палица битв", "легкая палица битв"}
    for sid in ("1", "2", "3"):
        for name in listing(f"следак{sid}"):
            if norm(name) not in keep:
                dst = "колбы" if name.startswith(("настойка", "эликсир", "свиток", "колба")) else "общий"     # расходники храним на :Колбы
                say(f"лишнее :следак{sid}: {name} -> :{dst}")
                if not dry:
                    cmd(f"кз :следак{sid} {kw(name)}")
                    cmd(f"кс :{dst} {kw(name)}")


if __name__ == "__main__":
    main()
