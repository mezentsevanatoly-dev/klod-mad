# -*- coding: utf-8 -*-
"""Разведка города (Огис 1-2 ярус): обход ВСЕХ клеток по графу game.db, в каждой клетке `смотреть N.` для каждой строки-моба -> карточка
(имя, уровень, профессия, навыки). Смотрит карточки и бьёт (правила пользователя 12.11): моб до +3 лвл от слабейшего в группе; один моб в клетке - бить даже кастера; несколько - кастеры первыми; смерть - стоп и запись. Результат: data/recon/огис_город/{мобы.json,мобы.md,маршрут.botp}.
Запуск (жаба Айлины, бот выключен, персонаж стоит в стартовой комнате):  JMC_TARGET=... python tools/explore_city.py <старт_vnum> [префикс_vnum=180]
Ничего не отправляет кроме ходов и `смотреть`."""
import os, re, sys, json, time, sqlite3, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import inc_supervisor as S

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "recon", "огис_город"); os.makedirs(OUT, exist_ok=True)
START = sys.argv[1] if len(sys.argv) > 1 else "180154"
PFX = sys.argv[2] if len(sys.argv) > 2 else "180"
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
OPP = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}
c = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
G = {}; NAME = {}
for v, n, e in c.execute("select vnum,name,exits from rooms where vnum like ?", (PFX + "%",)):
    G[str(v)] = {d: str(t) for d, t in json.loads(e or "{}").items() if str(t).startswith(PFX)}; NAME[str(v)] = n

CARD = re.compile(r"^(.+?) \[уровень (\d+)\], (.+)$")


def cmd_out(cmd, wait=1.6):
    pos = S.log_size(); S.jmc(cmd); time.sleep(wait)
    _, ls = S.lines_from(pos)
    return [re.sub(r"^\d\d:\d\d:\d\d ", "", x).rstrip() for x in ls]


def room_mobs(ls):
    """Строки после [ Exits ... ] до приглашения: кандидаты в мобы/предметы."""
    out = []; on = False; name = None
    for i, t in enumerate(ls):
        if re.match(r"^\[ Exits:", t): on = True; continue
        if on:
            if re.search(r"Вых:", t) or not t.strip(): break
            if t.startswith("[Зона") or "Кимпи" in t or t.startswith("Труп") or "Айлина" in t: continue
            out.append(t.strip())
    for t in ls:                                   # название комнаты: первая непустая строка после «>> см»
        if t.strip() and not t.startswith(">>") and not re.search(r"Вых:", t): name = t.strip(); break
    return name, out


cards = {}                                          # имя карточки -> данные
rooms = {}                                          # vnum -> [{line, card}]
visited = set(); route = []


def look_here(vn):
    ls = cmd_out("см", 1.6)
    name, lines = room_mobs(ls)
    recs = []
    for k, line in enumerate(lines):
        got = None
        for n in (k + 2, k + 1, k + 3):             # нумерация зависит от группы/порядка: пробуем соседние номера
            o = cmd_out("см %d." % n, 1.3)
            for j, t in enumerate(o):
                m = CARD.match(t.strip())
                if m:
                    prof = m.group(3).split(",")[0].strip()
                    sk = ""
                    for t2 in o[j + 1:j + 4]:
                        if t2.startswith("Навыки:"): sk = t2[7:].strip()
                    got = {"name": m.group(1), "level": int(m.group(2)), "prof": prof, "skills": sk}
                    break
            if got: break
        recs.append({"line": line, "card": got})
        if got: cards[got["name"]] = got
    rooms[vn] = {"room": name, "mobs": recs}
    if not fight_room(vn, recs):
        raise SystemExit("смерть - стоп")
    print(vn, name, "|", "; ".join((r["card"]["name"] + " " + str(r["card"]["level"])) if r["card"] else "?" for r in recs), flush=True)


MY_LEVEL = int(os.environ.get("EXPLORE_LEVEL", "21"))          # слабейший в группе (Кимпи 21)
MAX_MOB = MY_LEVEL + 3
CASTERS = ("Маг", "Волшебник", "Колдун", "Некромант", "Жрец", "Лекарь", "Целитель", "Друид", "Шаман", "Ведьма", "Заклинатель", "Чернокнижник", "Колдунья", "Баньши", "Лич", "Монах")
SPELLS = re.compile(r"огненн|ледян|стрела|проклят|придержать|слабост|шар|молни|оцепен|слепот|яд|вампир|удар молнии|ритуал", re.I)
DEATH = re.compile(r"Вы (умерли|мертвы|погибли|убиты)|вас убил|Вы очнулись|Вы воскресли")
LOG = os.path.join(OUT, "происшествия.md")


def note(text):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("- [%s] %s\n" % (time.strftime("%H:%M:%S"), text))
    print("ЗАПИСЬ:", text, flush=True)


def is_caster(card):
    return card["prof"].strip() in CASTERS or bool(SPELLS.search(card["skills"] or ""))


def fight_room(vn, recs):
    alive = [r for r in recs if r["card"]]
    if not alive: return True
    one = len(recs) == 1
    todo = [r for r in alive if r["card"]["level"] <= MAX_MOB]
    for r in recs:
        if r["card"] and r["card"]["level"] > MAX_MOB:
            note("%s %s: %s ур.%d (%s) - выше +3 от %d, не бью" % (vn, NAME.get(vn, ""), r["card"]["name"], r["card"]["level"], r["card"]["prof"], MY_LEVEL))
    todo.sort(key=lambda r: (0 if is_caster(r["card"]) else 1, r["card"]["level"]))
    for r in todo:
        cd = r["card"]
        if not one and False: pass
        o = cmd_out("уби " + cd["name"].replace(" ", "."), 3.0)
        t0 = time.time(); txt = "\n".join(o)
        while time.time() - t0 < 40 and "R.I.P" not in txt and not DEATH.search(txt):
            pos = S.log_size(); time.sleep(2.5); _, ls = S.lines_from(pos); txt += "\n" + "\n".join(ls)
            if re.search(r"Вы не можете.*(мирн|напасть)|не стоит нападать|под защитой", txt): break
        if DEATH.search(txt):
            note("СМЕРТЬ в %s (%s) от/при %s ур.%d (%s, навыки: %s). Дальше: ждать возврата экипа на склад (разведку остановил)." % (vn, NAME.get(vn, ""), cd["name"], cd["level"], cd["prof"], cd["skills"]))
            return False
        if "R.I.P" in txt:
            note("%s %s: убит %s ур.%d (%s)%s" % (vn, NAME.get(vn, ""), cd["name"], cd["level"], cd["prof"], " (одиночный кастер)" if one and is_caster(cd) else ""))
        else:
            note("%s %s: %s ур.%d - не убит за 40 с (мирный/недоступен?)" % (vn, NAME.get(vn, ""), cd["name"], cd["level"]))
    return True


def move(d, to):
    route.append((to, RU[d]))
    o = cmd_out(RU[d], 1.4)
    return o


def dfs(v):
    visited.add(v)
    look_here(v)
    for d in ["N", "E", "S", "W", "U", "D"]:
        t = G.get(v, {}).get(d)
        if t and t not in visited and OPP[d] in G.get(t, {}):
            cur = (cmd_out(RU[d], 1.4))
            route.append((v, RU[d]))
            dfs(t)
            cmd_out(RU[OPP[d]], 1.4)
            route.append((t, RU[OPP[d]]))


if __name__ == "__main__":
    S.say("РАЗВЕДКА ГОРОДА: старт", START, "клеток в графе", len(G))
    dfs(START)
    json.dump({"rooms": rooms, "cards": cards, "route": route}, open(os.path.join(OUT, "мобы.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "мобы.md"), "w", encoding="utf-8") as f:
        f.write("# Разведка города (только карточки, без боя)\n\n")
        for n, cd in sorted(cards.items(), key=lambda x: -x[1]["level"]):
            f.write("- %s | ур.%d | %s | %s\n" % (n, cd["level"], cd["prof"], cd["skills"]))
    S.say("РАЗВЕДКА ГОРОДА: готово; комнат", len(rooms), "карточек", len(cards), "->", OUT)
