# -*- coding: utf-8 -*-
"""Бот группы через клиент МАД ГРАФИКА: Айлина (лидер, окно 8765) ведёт, Кимпи (8766) следует и бьёт.

python -X utf8 bot.py зона1 [зона2 ...] [--loop] [--goal=30] [--cd=30]
Маршрут: JMC БОТ АЙЛИНА\\areas\\<зона>.botp (шаг привязан к клетке MSDP), мобы: <зона>_mob.csv (бьём только их, по имени).
Словари мирных/обходимых/первых — из BotCore.js. Бегство при хп делает игра (реж трус 30), бот не останавливается.
Лог: МАД БОТ\\бот.log; убийства — в РЕПОПЫ.csv (для таймеров репопа).
Стоп: файл МАД БОТ\\бот.стоп (создать — бот остановится после шага).
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

БЕЗ_КОЛБ = "--с-колбами" not in sys.argv     # тестовая копия: на локальном стенде колб нет, докупка и питьё выключены
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AREAS = os.path.join(ROOT, "JMC БОТ АЙЛИНА", "areas")
BOTCORE = os.path.join(ROOT, "JMC БОТ АЙЛИНА", "scripts", "BotCore.js")
LOG = os.path.join(HERE, "бот.log")
STOPF = os.path.join(HERE, "бот.стоп")
REPOP = os.path.join(ROOT, "РЕПОПЫ.csv")
def find_port(name, default):
    """Окно клиента с этим профилем (порты 8765..8774) — как в play.py."""
    for p in range(8765, 8775):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{p}/api/info", timeout=0.5) as r:
                if (json.loads(r.read().decode("utf-8")).get("name") or "").lower() == name.lower():
                    return p
        except Exception:
            continue
    return default


A, K = find_port("Айлина", 8765), find_port("Кимпи", 8766)   # Айлина, Кимпи
NAMES = {A: "Айлина", K: "Кимпи"}
DIRS = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}


def say(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")


def http(port, path, data=None):
    url = f"http://127.0.0.1:{port}{path}"
    req = urllib.request.Request(url, data=data.encode("utf-8") if data is not None else None,
                                 method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=10) as r:
        b = r.read().decode("utf-8")
    return json.loads(b) if b[:1] in "{[" else b


def st(port):
    return http(port, "/api/state")


def send(port, *cmds):
    http(port, "/send", "\n".join(cmds))


def log_from(port, n):
    d = http(port, f"/log?from={n}")
    return d["lines"], d["next"]


def norm(s):
    s = re.sub(r"\s*\(x\d+\)|\s*\[\d+\]|\s*\(невидим[а-я]*\)", "", s or "")
    s = re.sub(r"\s+\.\.\..*$", "", s)
    return s.strip().rstrip(".").lower().replace("ё", "е")


# ---------- словари из BotCore.js ----------
def botcore_dicts():
    t = open(BOTCORE, encoding="cp1251", errors="replace").read()

    def rx(name):
        m = re.search(r"var %s = /(.*?)/(i?);" % name, t)
        return re.compile(m.group(1), re.I if m and m.group(2) else 0) if m else None

    def obj(name):
        m = re.search(r"var %s = \{(.*?)\};" % name, t)
        return set(re.findall(r'"([^"]+)"\s*:', m.group(1))) if m else set()
    return rx("PEACE_MOBS"), rx("AVOID_MOBS"), obj("HOLDERS") | obj("FIRST_MOBS")


PEACE, AVOID, FIRST = botcore_dicts()


# ---------- маршрут и мобы ----------
def load_zone(z):
    steps = []
    for ln in open(os.path.join(AREAS, z + ".botp"), encoding="cp1251", errors="replace").read().splitlines():
        ln = ln.strip()
        if not ln:
            continue
        m = re.search(r"\$MsdpRoomVnum == (\d+)\}\s*\{(.*)\}\s*$", ln)
        if m:
            steps.append((m.group(1), m.group(2).strip()))
        elif ln.startswith(".пауза"):
            steps.append((None, ln))
        elif ln.startswith(".триг"):
            steps.append((None, ln))
        else:
            steps.append((None, ln))
    mobs = []
    p = os.path.join(AREAS, z + "_mob.csv")
    if os.path.exists(p):
        for ln in open(p, encoding="cp1251", errors="replace").read().splitlines()[1:]:
            c = [x.strip('"') for x in ln.split(";")]
            if len(c) > 1 and c[0]:
                mobs.append({"name": c[0], "line": norm(c[1]), "assist": (c[10] if len(c) > 10 else "") == "true"})
    return steps, mobs


# приоритеты и «вместе не бить» по зонам (слова пользователя)
ZONE_RULES = {
    # 16.11: «в гномах приоритет маг, знахарь. если маг и знахарь в одной клетке, то лучше подождать, пока они разойдутся
    #         или идти дальше, а потом вернуться. лидеров бить, дозорных тоже. всех»
    "гномы_цели": {"first": ["Маг", "Знахарь"], "not_together": [("Маг", "Знахарь")]},
    # 16.11: «Минотавр-патрульный- их 2 группы по 3шт. остальных минотавров бить не надо.»
    # 15.11: «первый ярус … только группу на вторых воротах через уб гном» — стражей вторых ворот нет в csv, а они вступаются
    # 16.11: «тоже убивать, говорил же. всех, кроме группы летописца, правителя, сеятеля чумы»
    "огис_цели": {"all": True, "first": ["Грустный голубоглазый гном"],
                  "extra": [("Страж вторых ворот", "Страж вторых ворот внимательно разглядывает прохожих.")],
                  "extra_rx": [r"^страж (вторых|третьих|четвертых) ворот"],
                  # 15.11: «5й ярус всех. кроме группы летописца, на этаже дворца- всех, кроме группы правителя» —
                  # 16.11 бот убил летописца, старого рыцаря и стражей пятых ворот (моё правило «стражи всех ворот»): клетку с ними не трогать
                  "expect": {"Страж ущелья": 4},       # группа стражей у ворот ущелья (180011)
                  "avoid_rx": [r"летописец|старый рыцарь|страж пятых ворот|правитель города|хранитель покоя|дворцовый страж"]},
    "гео_цели": {"skip": ["Пьяный минотавр", "Седой минотавр"], "expect": {"Минотавр-патрульный": 6, "Охранник банка": 2}},
}
RULES = {}
BAD = set()        # строки, на которые «Кого вы хотите ударить?» — не бить снова


class Target(str):
    """Имя моба (строка) + номер в клетке (.num) — бить «уби N.»: имя в csv бывает чужого клана."""
    def __new__(cls, name, num, line="", known=True):
        o = str.__new__(cls, name)
        o.num, o.line, o.known = num, line, known
        return o


PEACEFUL = {}      # строка моба -> True (мирный) / False — по карточке «Особенности: [Мирный]»
NAMES_JSON = os.path.join(HERE, "имена_мобов.json")
try:
    NAMEMAP = json.load(open(NAMES_JSON, encoding="utf-8-sig"))    # строка в комнате -> имя из карточки
except Exception:
    NAMEMAP = {}
CARD_RX = re.compile(r"([А-ЯЁ][^\[>]{1,60}?) \[уровень (\d+)\], (\S+)")


def look_card(cmd):
    n0 = log_from(A, 0)[1]
    send(A, cmd)
    time.sleep(1.0)
    text = "\n".join(log_from(A, n0)[0])
    m = CARD_RX.search(text)
    return (m.group(1).strip() if m else None), "[Мирный]" in text, "Вы не видите" in text


def resolve(t):
    """Имя моба по карточке (16.11): «см СЛОВО» по словам строки; везде «Вы не видите» — «см N.» по нумерации.
    Строку и имя из карточки запомнить; дальше «убить» по имени."""
    key = norm(t.line)
    if key in NAMEMAP:
        return NAMEMAP[key]
    name, peace = None, False
    words = [w.lower() for w in re.findall(r"[А-Яа-яЁё\-]{3,}", re.sub(r"\.\.\..*$", "", t.line))][:6]
    for w in words:
        name, peace, miss = look_card(f"смотреть {w}")
        if name:
            break
    if not name and t.num:
        name, peace, _ = look_card(f"смотреть {t.num}.")
    if name:
        NAMEMAP[key] = name
        PEACEFUL[key] = peace
        json.dump(NAMEMAP, open(NAMES_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        say(f"  карточка: «{t.line[:45]}» = {name}" + (" [Мирный]" if peace else ""))
    return name


def peaceful(t):
    """Мирный? Для мобов не из списка зоны — один раз «смотреть N.» и «Особенности: … [Мирный]» (16.11: мирных не бить)."""
    key = norm(t.line)
    if key in PEACEFUL:
        return PEACEFUL[key]
    n0 = log_from(A, 0)[1]
    send(A, f"смотреть {t.num}.")
    time.sleep(1.2)
    text = "\n".join(log_from(A, n0)[0])
    PEACEFUL[key] = "[Мирный]" in text
    if PEACEFUL[key]:
        say(f"  {t} — [Мирный], не бью")
    return PEACEFUL[key]


def targets(room_mobs, mobs):
    """Строки мобов в комнате -> имена для убить (только из csv, не мирные). None — клетку сейчас не трогать."""
    out = []
    num = 1                                               # номер существа в клетке: с 2 (1 — ты сам), предметы не считаются
    for line, _c in room_mobs:
        nl = norm(line)
        if line.startswith("[") or re.search(r"(лежит|лежат|валяется) (здесь|тут)|^труп |^останки ", nl):
            continue                                      # «[Зона, на север: …]», предмет, труп — не существа (16.11 «уби 4.» мимо)
        num += 1
        if nl in BAD:
            continue                                      # «Кого вы хотите ударить?» — это не существо (предмет)
        core = re.sub(r"\s*\(.*?\)|\s*\.\.\..*$", "", line).strip()
        is_player = bool(re.search(r"\s[А-ЯЁ][а-яё]+(,| (стоит|сидит|летает|отдыхает|спит|лежит|сражается)\b)", core)) and "здесь" in core
        if AVOID and AVOID.search(line):
            return None                                   # в клетке обходимый (Сеятель чумы и т.п.) — не бить никого
        if any(re.search(rx, nl) for rx in RULES.get("avoid_rx", [])):
            return None                                   # запретная группа зоны в клетке — никого не бить
        if any(re.search(rx, nl) for rx in RULES.get("extra_rx", [])) or (RULES.get("all") and not is_player):
            if PEACEFUL.get(nl) or (PEACE and PEACE.search(line)):
                continue                                  # мирный: по карточке или по словарю мирных BotCore
            out.append(Target(re.match(r"\S+(\s\S+){0,2}", line).group(0), num, line, known=False))
            continue
        for m in mobs:
            if m["line"] and (nl == m["line"] or nl.startswith(m["line"]) or m["line"].startswith(nl)):
                if (PEACE and PEACE.search(m["name"])) or m["name"] in RULES.get("skip", []):
                    break
                out.append(Target(m["name"], num, line))
                break
    for a, b in RULES.get("not_together", []):
        if any(n.startswith(a) for n in out) and any(n.startswith(b) for n in out):
            return "later"
    first = RULES.get("first", [])
    out.sort(key=lambda n: (0 if n in FIRST else 1, next((k for k, p in enumerate(first) if n.startswith(p)), 99)))
    return out


# ---------- бой ----------
BR = re.compile(r"\[([^\]:]+):([^\]]+)\]")


def fight_info(port):
    """Скобки из последней строки состояния: [я] [моб] или [я] [кого бьют] [моб]. [] — не в бою."""
    try:
        d = http(port, "/log?from=%d" % max(0, log_from(port, 0)[1] - 12))
    except Exception:
        return []
    cand = d["lines"] + [re.sub(r"\x1b\[[0-9;]*m", "", d.get("partial", ""))]
    for l in reversed(cand):
        if PROMPT_RX.match(l):
            head = l.split("Вых:")[0]
            return [(a.strip(), b.strip()) for a, b in BR.findall(head)]
    return []


def in_fight(port):
    return bool(fight_info(port))


RESCUE = {"last": 0}


def guard_kimpi():
    """Авторескью: моб бьёт Кимпи -> Айлина «спасти кимпи» (нет умения/не в бою — «помочь кимпи»)."""
    f = fight_info(K)
    if not f:
        return
    tank_is_kimpi = len(f) == 2 or (len(f) >= 3 and f[1][0].lower().startswith("кимпи"))
    if not tank_is_kimpi or time.time() - RESCUE["last"] < 2.6:
        return
    RESCUE["last"] = time.time()
    say(f"  моб ({f[-1][0]}) бьёт Кимпи — спасаю")
    send(A, "спасти кимпи")
    if not in_fight(A):
        time.sleep(0.8)
        if not in_fight(A):
            send(A, "помочь кимпи")


def wait_fight_end(timeout=120):
    t0, calm = time.time(), 0
    while time.time() - t0 < timeout:
        guard_kimpi()
        if in_fight(A) or in_fight(K):
            calm = 0
        else:
            calm += 1
            if calm >= 3:
                return True
        time.sleep(0.5)
    return False


def kill_word(name):
    return name.lower().replace(" ", ".")


PROMPT_RX = re.compile(r"^\d+H \d+M \d+V \S+ \d+C ")
LAST_MOVE = {"n": None}


def room_from_arrival():
    """Мобы клетки из вывода последнего шага (после «[ Exits: … ]» до строки состояния); None — нет данных."""
    n = LAST_MOVE.get("n")
    LAST_MOVE["n"] = None
    if n is None:
        return None
    lines, _ = log_from(A, n)
    ex = max((k for k, l in enumerate(lines) if l.strip().startswith("[ Exits:")), default=None)
    if ex is None:
        return None
    mobs = []
    for l in lines[ex + 1:]:
        if PROMPT_RX.match(l):
            return {"mobs": mobs}
        if l.strip():
            mobs.append([l.strip(), ""])
    return None


def fresh_room(timeout=4):
    """`смотреть` и разбор вывода: строки после «[ Exits: … ]» до строки состояния — существа и предметы."""
    n0 = log_from(A, 0)[1]
    send(A, "смотреть")
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(0.3)
        lines, _ = log_from(A, n0)
        d = http(A, f"/log?from={n0}")
        allp = lines + [re.sub(r"\x1b\[[0-9;]*m", "", d.get("partial", ""))]
        ex = next((k for k, l in enumerate(allp) if l.strip().startswith("[ Exits:")), None)
        if ex is None:
            continue
        mobs = []
        for l in allp[ex + 1:]:
            if PROMPT_RX.match(l):
                return {"mobs": mobs}
            if l.strip():
                mobs.append([l.strip(), ""])
    return {"mobs": []}


def repop_note(what, vnum, event):
    new = not os.path.exists(REPOP)
    with open(REPOP, "a", encoding="utf-8") as f:
        if new:
            f.write("дата;время;что;где;событие;минут_с_убийства;заметка\n")
        f.write(f"{time.strftime('%d.%m.%Y')};{time.strftime('%H:%M:%S')};{what};{vnum};{event};;бот\n")


def clear_room(mobs, vnum, stats):
    """Бить целей в клетке, пока есть: после боя `смотреть`, остался кто-то из целей — бить, из клетки не уходить
    (16.11: «3й не умер — бот пишет см, видит, что стражник не убит и не уходит из клетки, пока не убил»)."""
    first = True
    for p in (A, K):                                        # защита клиента от зацикливания могла выключить триггеры
        try:
            http(p, "/api/triggers?on=1")
        except Exception:
            pass
    for _ in range(25):
        if cur(K) != cur(A) or in_fight(K):        # 16.11: «айлина без кимпи мобов не била, а ждала ее»
            ensure_group()
        r = room_from_arrival() if first else None   # при входе комната уже показана — без лишнего «смотреть»
        first = False
        if r is None:
            r = fresh_room()
        t = targets(r.get("mobs") or [], mobs)
        if t is None:
            say(f"  {vnum}: обходимый моб в клетке — не бью")
            return
        if t == "later":
            say(f"  {vnum}: маг и знахарь вместе — вернусь потом")
            stats.setdefault("later", []).append(vnum)
            return
        if not t:
            return
        live = []
        for x in t:                                          # имя по карточке (и мирный ли) — до удара
            cn = resolve(x)
            if cn and PEACEFUL.get(norm(x.line)):
                continue
            if cn:
                live.append((x, cn))
        if not live:
            for x in t:
                BAD.add(norm(x.line))
            return
        name, cname = live[0]
        n0 = log_from(A, 0)[1]
        say(f"  {vnum}: бью {cname}" + (f" (ещё {len(live) - 1})" if len(live) > 1 else ""))
        send(A, "уби " + cname.lower().replace(" ", "."))   # по имени из карточки, не по номеру
        time.sleep(0.6)
        send(K, "помочь Айлина")
        wait_fight_end()
        lines, _ = log_from(A, n0)
        exp = sum(int(x) for x in re.findall(r"Вы получили (\d+) единиц опыта", "\n".join(lines)))
        dead = any(re.search(r"(мертв|мертва|мертво)[,.]", l) for l in lines)
        if any(l.startswith("Вы мертвы") for l in lines):          # «Моб мертв. R.I.P.» — это моб
            say("СМЕРТЬ Айлины — собираю на складе")
            time.sleep(5)
            regroup()
        if dead or exp:
            stats["kills"] += 1
            stats["exp"] += exp
            stats.setdefault("killed", []).append(cname)
            repop_note(cname, vnum, "убил")
        else:
            say(f"  {vnum}: {cname} — не убила, смотрю ещё раз")
            stats.setdefault("missed", []).append(f"{cname} ({vnum})")
            if any("Кого вы хотите ударить" in l or "Ударить себя" in l for l in lines):
                NAMEMAP.pop(norm(name.line), None)          # имя не подошло — в следующий раз смотреть карточку заново
                if stats.setdefault("badtry", {}).setdefault(norm(name.line), 0) >= 1:
                    BAD.add(norm(name.line))
                stats["badtry"][norm(name.line)] += 1
            time.sleep(1)


# ---------- ходьба ----------
def cur(port):
    return (st(port).get("cur") or {}).get("vnum")


def stand_up():
    for p in (A, K):
        send(p, "вст")
    time.sleep(0.6)


def feed():
    """Голод/жажда (видно в выводе) -> осуш насыщ."""
    if БЕЗ_КОЛБ:
        return
    for p in (A, K):
        try:
            tail = "\n".join(log_from(p, max(0, log_from(p, 0)[1] - 60))[0])
        except Exception:
            continue
        if re.search(r"Вы (хотите есть|хотите пить|проголодались|чувствуете жажду)", tail):
            send(p, "осуш насыщ")
            time.sleep(1)


# колбы: (как в инвентаре, ключ для «кз :колбы», сколько держать) — по +колб2/+колб1 профилей (16.11: «настойки забирай, которые кончаются»)
KOLBY = [("настойк\\S* насыщения", "насыщ", 1), ("настойк\\S* восстановления", "восс", 2), ("эликсир\\S* летучей мыши", "мыши", 2),
         ("охранн\\S* свит", "охр", 2), ("(колб|эликсир)\\S* прозрения", "прозр", 2), ("свит\\S* панацеи", "панац", 2),
         ("свит\\S* заклинателя камней", "камн", 1), ("микстур\\S* освобождения", "м.осво", 3)]


def inv_counts(p):
    n0 = log_from(p, 0)[1]
    send(p, "инв")
    time.sleep(1.2)
    text = log_from(p, n0)[0]
    out = {}
    for rx, key, _need in KOLBY:
        c = 0
        for l in text:
            if re.search(rx, l, re.I):
                m = re.search(r"\[(\d+)\]", l)
                c += int(m.group(1)) if m else 1
        out[key] = c
    return out


def restock():
    """Каких колб меньше нормы — на склад (путь склад) и забрать из :колбы."""
    if БЕЗ_КОЛБ:
        return
    need = {}
    for p in (A, K):
        have = inv_counts(p)
        miss = [(key, n - have.get(key, 0)) for _rx, key, n in KOLBY if have.get(key, 0) < n]
        if miss:
            need[p] = miss
    if not need:
        return
    say("КОЛБЫ: не хватает — " + "; ".join(f"{NAMES[p]}: " + ", ".join(f"{k}×{n}" for k, n in m) for p, m in need.items()))
    stand_up()
    send(A, "путь склад")                                   # ближайший склад города, где стоим (Кимпи следует)
    last, still, t0 = None, 0, time.time()
    while time.time() - t0 < 120 and still < 5:              # дошла — клетка не меняется 5 с
        time.sleep(1)
        c = cur(A)
        still = still + 1 if c == last else 0
        last = c
    ensure_group()
    for p, miss in need.items():
        for key, n in miss:
            for _ in range(n):
                send(p, f"кз :колбы {key}")
                time.sleep(0.4)
    time.sleep(1.5)
    feed()


def walk_to(vnum, limit=200):
    stand_up()
    for _ in range(3):
        c = cur(A)
        if c == vnum:
            return True
        p = http(A, f"/api/path?a={c}&b={vnum}")
        if not p.get("words"):
            say(f"нет пути {c} -> {vnum}")
            return False
        for k, w in enumerate(p["words"][:limit]):
            send(A, w)
            time.sleep(0.35)
            if k % 5 == 4:                                 # дальняя дорога: каждые 5 шагов ждать Кимпи
                t1 = time.time()
                while cur(K) != cur(A) and time.time() - t1 < 12:
                    time.sleep(0.5)
        time.sleep(2)
    return cur(A) == vnum


ARR = {"n": 0}
# 16.11: «они не только ходят. там множество вариантов. от появился до прикатился» — ловим откуда пришёл, а не глагол
# только строка-событие целиком: «Маг западного клана пришел с запада.», «Мышь прилетела сверху.», «Призрак появился.»
# (не описание комнаты: «…А с севера и запада раздаются…» — 16.11 бот крутил «смотреть» по кругу)
ARR_RX = re.compile(r"^[А-ЯЁA-Z][^.!?]{2,70}\s(?:(?:с|со)\s(?:запада|востока|севера|юга)|сверху|снизу)\.$"
                    r"|^[А-ЯЁA-Z][^.!?]{2,70}\s(?:появил|возник|материализовал)\S*(?:\s[^.!?]{0,30})?\.$")


def arrivals():
    """Кто-то пришёл в клетку с момента прошлой проверки (16.11: «Маг западного клана пришел с запада» — нет реакции)."""
    lines, n = log_from(A, ARR["n"])
    ARR["n"] = n
    return [l for l in lines if ARR_RX.search(l) and not re.match(r"^(Кимпи|Вы)\s", l)]


def step_move(cmd, want_from):
    c0 = cur(A)
    n0 = log_from(A, 0)[1]
    ARR["n"] = n0                                           # пришедшие до шага уже обработаны
    send(A, cmd)
    t0 = time.time()
    while time.time() - t0 < 6:
        time.sleep(0.2)
        c = cur(A)
        if c != c0:
            LAST_MOVE["n"] = n0
            time.sleep(0.25)                                  # дождаться вывода комнаты до строки состояния
            return True
        lines, _ = log_from(A, n0)
        if any(l.startswith("Вы слишком устали") for l in lines):     # энергия: осуш восст и повтор шага
            send(A, "осуш восст")
            time.sleep(1.2)
            send(A, cmd)
            n0 = log_from(A, 0)[1]
            continue
        if any("Вам лучше встать на ноги" in l or "Вы сидите" in l or "Вы отдыхаете" in l for l in lines):
            stand_up()
            send(A, cmd)
            n0 = log_from(A, 0)[1]
            continue
        if any(re.search(r"Вы не можете идти|Не получится! Вы сражаетесь|заперт|Попробуйте сначала открыть", l) for l in lines):
            return False
    return cur(A) != c0


class Regrouped(Exception):
    pass


def check_menu():
    """После смерти — меню аккаунта «Ваш выбор:» -> 1 (войти в игру)."""
    for p in (A, K):
        try:
            d = http(p, "/log?from=999999")
            if re.sub(r"\x1b\[[0-9;]*m", "", d.get("partial", "")).rstrip().endswith("Ваш выбор:"):
                say(f"{NAMES[p]}: меню входа (смерть/обрыв) — вхожу")
                send(p, "1")
                time.sleep(3)
        except Exception:
            pass


def path_len(a, b):
    try:
        p = http(A, f"/api/path?a={a}&b={b}")
        return len(p.get("path") or []) if p.get("path") is not None else 999
    except Exception:
        return 999


def regroup():
    """Рекол/смерть (слова пользователя 16.11): «путь склад», собрать обеих там, группа, дальше по кругу."""
    say("СБОР: рекол/смерть — оба на склад")
    check_menu()
    stand_up()
    send(K, "путь склад")
    last, still = None, 0
    t0 = time.time()
    while time.time() - t0 < 180 and still < 6:          # Кимпи дошла: клетка не меняется 6 с
        time.sleep(1)
        c = cur(K)
        still = still + 1 if c == last else 0
        last = c
    target = cur(K)
    if not walk_to(target):
        stand_up()
        send(A, "путь склад")
        time.sleep(40)
    if cur(A) != cur(K):                                  # всё ещё врозь — Кимпи к Айлине по карте
        p = http(K, f"/api/path?a={cur(K)}&b={cur(A)}")
        for w in (p.get("words") or [])[:80]:
            send(K, w)
            time.sleep(0.4)
    send(K, "следовать Айлина")
    time.sleep(1)
    n0 = log_from(A, 0)[1]
    send(A, "гр")
    time.sleep(1.5)
    gl = log_from(A, n0)[0]
    if not any(re.match(r"^\s*\*?\s*Кимпи\s", l) for l in gl):   # «группа Кимпи» — переключатель: только если её нет
        send(A, "группа Кимпи")
    say(f"СБОР: вместе в {cur(A)} / {cur(K)}")
    raise Regrouped()


def group_status():
    """`гр` у Айлины -> {имя: (позиция, рядом)} (слова пользователя 16.11: статус в гр — сражается, стоит, сидит…)."""
    # пгр со столбцом холда: «Стоит» в холде — двигаться не может (16.11). Таблицу читаем прямо из вывода (быстро).
    # строка пгр: «  Кимпи           Стоит       Д     Н» — читаем по словам (строки «гр» с #### сюда не подходят)
    row = re.compile(r"^\s*\*?\s*([А-ЯЁ][а-яё]+)\s+(Стоит|Сидит|Отдыхает|Спит|Лежит|Сражается|Оглушен\S*|Без\s+сознания|Умирает)\s+([ДН])\s+([ДН])\s*$")
    n0 = log_from(A, 0)[1]
    send(A, "пгр позиц ряд холд")
    t0, out = time.time(), {}
    while time.time() - t0 < 2.5:
        time.sleep(0.15)
        for l in log_from(A, n0)[0]:
            m = row.match(l)
            if m:
                out[m.group(1)] = (m.group(2), m.group(3), m.group(4))
        if "Айлина" in out and "Кимпи" in out:
            return out
    return out


def ensure_group(limit=90):
    """Шаг дальше только когда Кимпи «Стоит» и «Рядом Д»."""
    t0 = time.time()
    last_invite = 0.0                       # «группа Кимпи» — переключатель: не чаще раза в 12 с (стенд, 18.11)
    while time.time() - t0 < limit:
        if os.path.exists(STOPF):
            return False
        g = group_status()
        poz, near, khold = g.get("Кимпи", ("", "", "Н"))
        apoz, _an, ahold = g.get("Айлина", ("", "", "Н"))
        if "Д" in (khold, ahold):
            say(f"  холд ({'Кимпи' if khold == 'Д' else 'Айлина'}) — стоим, ждём, пока пройдёт")
            time.sleep(2.5)
            continue
        if apoz in ("Сидит", "Отдыхает", "Спит", "Лежит"):
            send(A, "вст")
        elif apoz.startswith("Сраж"):
            wait_fight_end()
            continue
        # 16.11: «если в группе любой персонаж не стоит, мы никуда не идем. если кто-то не рядом — ждем статуса стоит»
        if poz == "Стоит" and near == "Д" and apoz == "Стоит" and cur(K) == cur(A):
            return True
        if poz in ("Сидит", "Отдыхает", "Спит", "Лежит"):
            say(f"  Кимпи {poz.lower()} — встаю")
            send(K, "вст")
        elif poz.startswith("Сраж"):
            if near != "Д":
                p = http(A, f"/api/path?a={cur(A)}&b={cur(K)}")
                if p.get("words") and len(p["words"]) <= 8:
                    say(f"  Кимпи сражается в {cur(K)} — Айлина к ней")
                    for w in p["words"]:
                        send(A, w)
                        time.sleep(0.4)
            send(A, "спасти кимпи")
            time.sleep(0.8)
            if not in_fight(A):
                send(A, "помочь кимпи")
            wait_fight_end()
            send(K, "следовать Айлина")
        elif not poz:
            # «группа Кимпи» — переключатель (исключает, если она в группе): только если гр точно без неё
            n0 = log_from(A, 0)[1]
            send(A, "гр")
            time.sleep(1.2)
            gl = log_from(A, n0)[0]
            if any(re.search(r"Имя\s+H", l) for l in gl) and not any(re.match(r"^\s*\*?\s*Кимпи\s", l) for l in gl):
                if time.time() - last_invite < 12:
                    time.sleep(1)
                    continue
                say("  Кимпи нет в группе — принимаю")
                send(K, "следовать Айлина")
                time.sleep(1)
                send(A, "группа Кимпи")
                last_invite = time.time()
                time.sleep(2.5)                      # дать группе собраться, не переключать обратно
        elif near != "Д" or cur(K) != cur(A):
            k, a = cur(K), cur(A)
            if path_len(k, a) > 15:
                return wait_kimpi()
            p = http(K, f"/api/path?a={k}&b={a}")
            for w in (p.get("words") or [])[:15]:
                send(K, w)
                time.sleep(0.4)
            send(K, "следовать Айлина")
        time.sleep(1)
    say("  группа не собралась за 90 с — дальше ждёт wait_kimpi")
    return wait_kimpi()


def wait_kimpi(t=8):
    """Кимпи не терять: ждать в той же клетке; не догнала — довести к Айлине по карте и снова «следовать»."""
    t0 = time.time()
    while time.time() - t0 < t:
        guard_kimpi()
        if cur(K) == cur(A):
            return True
        if in_fight(K) and not in_fight(A):                 # Кимпи дерётся в другой клетке — вернуться к ней
            p = http(A, f"/api/path?a={cur(A)}&b={cur(K)}")
            if p.get("words") and len(p["words"]) <= 6:
                say(f"  Кимпи в бою в {cur(K)} — Айлина идёт к ней")
                for w in p["words"]:
                    send(A, w)
                    time.sleep(0.4)
                time.sleep(1)
                send(A, "спасти кимпи")
                time.sleep(0.8)
                if not in_fight(A):
                    send(A, "помочь кимпи")
                wait_fight_end()
                send(K, "следовать Айлина")
        time.sleep(0.4)
    check_menu()
    for _ in range(3):
        a, k = cur(A), cur(K)
        if a == k:
            return True
        if path_len(k, a) > 15:                            # далеко: идёт следом — ждать; стоит — рекол/смерть, собрать
            moving = False
            for _ in range(15):
                time.sleep(4)
                k2 = cur(K)
                if k2 == cur(A):
                    return True
                if k2 != k:
                    moving, k = True, k2
                elif moving:
                    moving = False
                else:
                    break
            if cur(K) != cur(A) and path_len(cur(K), cur(A)) > 15:
                regroup()
        say(f"  Кимпи отстала ({k}, Айлина {a}) — веду к ней")
        if in_fight(K):
            wait_fight_end()
        p = http(K, f"/api/path?a={k}&b={a}")
        for w in (p.get("words") or [])[:40]:
            send(K, w)
            time.sleep(0.4)
        send(K, "следовать Айлина")
        t0 = time.time()
        while time.time() - t0 < 6:
            if cur(K) == cur(A):
                return True
            time.sleep(0.4)
    say("  Кимпи не догнала — жду её на месте")
    while cur(K) != cur(A):
        if os.path.exists(STOPF):
            return False
        time.sleep(2)
    return True


def run_zone(z, stats):
    steps, mobs = load_zone(z)
    ARR["n"] = log_from(A, 0)[1]                             # старые строки лога — не «пришедшие»
    RULES.clear()
    RULES.update(ZONE_RULES.get(z, {}))
    for name, line in RULES.get("extra", []):
        mobs.append({"name": name, "line": norm(line), "assist": True})
    say(f"=== ЗОНА {z}: шагов {len(steps)}, мобов в csv {len(mobs)}")
    start = next((v for v, _ in steps if v), None)
    if in_fight(A) or in_fight(K):                          # запуск посреди драки — сначала довести бой
        guard_kimpi()
        wait_fight_end()
        ensure_group()
    if start and cur(A) != start and steps and any(v == cur(A) for v, _ in steps):
        say(f"стою на маршруте ({cur(A)}) — продолжаю отсюда")
        start = None
    if start and cur(A) != start:
        say(f"иду на старт {start}")
        if not walk_to(start):
            say("СТОП: не дошла до старта")
            return False
    i, stuck = 0, 0
    if start is None and steps:                              # продолжаем с текущей клетки маршрута
        i = next((k for k, (v, _) in enumerate(steps) if v == cur(A)), 0)
    while i < len(steps):
        if os.path.exists(STOPF):
            say("СТОП по файлу бот.стоп")
            return False
        v, cmd = steps[i]
        if cmd.startswith(".пауза"):
            time.sleep(int(re.sub(r"\D", "", cmd) or 10) / 10)
            i += 1
            continue
        if cmd.startswith(".триг"):
            c = cmd[5:].strip()
            if not c.startswith("#"):
                send(A, c)
            time.sleep(0.5)
            i += 1
            continue
        here = cur(A)
        if v and here != v:                                   # не та клетка: найти шаг из текущей рядом (RESYNC)
            best = next((k for d in range(1, 25) for k in (i + d, i - d)
                         if 0 <= k < len(steps) and steps[k][0] == here), None)
            if best is not None:
                say(f"  RESYNC шаг {i} -> {best} (клетка {here})")
                i = best
                continue
            stuck += 1
            if stuck > 3:
                say(f"не на маршруте (клетка {here}, ждала {v}) — рекол? собираю")
                regroup()
            time.sleep(2)
            continue
        stuck = 0
        if i % 10 == 0:                                        # раз в 10 шагов — полный пгр (холд/сидит без отставания)
            ensure_group()
        a = (st(A).get("cur") or {}).get("area")
        if a and a not in stats.setdefault("areas", []):
            stats["areas"].append(a)
        guard_kimpi()
        if in_fight(A) or in_fight(K):
            wait_fight_end()
        if cur(K) != cur(A):
            wait_kimpi()
        clear_room(mobs, here, stats)
        came, rounds = arrivals(), 0
        while came and cur(A) == here and rounds < 3:       # пока чистили/ждали — кто-то пришёл: осмотреть и бить
            rounds += 1
            say(f"  {here}: пришли — {'; '.join(c.strip()[:50] for c in came[:3])}")
            clear_room(mobs, here, stats)
            came = arrivals()
        if not step_move(cmd, here):
            say(f"  шаг {i} '{cmd}' не прошёл из {here}, повтор")
            time.sleep(1.5)
            if not step_move(cmd, here):
                i += 1                                          # пропустить (дверь/закрыто), дальше RESYNC
                continue
        i += 1
        t1 = time.time()                                       # Кимпи следует сама — обычно догоняет за доли секунды
        while cur(K) != cur(A) and time.time() - t1 < 2:
            time.sleep(0.2)
        if cur(K) != cur(A) or in_fight(A) or in_fight(K):    # пгр — только если что-то не так
            ensure_group()
    for v in list(dict.fromkeys(stats.get("later", []))):          # вернуться в отложенные клетки
        say(f"  возвращаюсь в {v}")
        if walk_to(v):
            stats["later"] = []
            clear_room(mobs, v, stats)
    say(f"=== ЗОНА {z} пройдена: убито {stats['kills']}, опыт Айлины +{stats['exp']}")
    report(z, mobs, stats)
    return True


def report(z, mobs, stats):
    """Отчёт по зоне для проверки: кого убил, кого не добил, кого из csv не встретил."""
    from collections import Counter
    k = Counter(stats.get("killed", []))
    exp_names = Counter(m["name"] for m in mobs)
    say(f"ОТЧЁТ {z}: убиты — " + (", ".join(f"{n} ×{c}" for n, c in k.items()) or "никто"))
    if stats.get("missed"):
        say("ОТЧЁТ: видела, но не убила — " + ", ".join(stats["missed"]))
    for n, want in RULES.get("expect", {}).items():
        if k.get(n, 0) < want:
            say(f"ОТЧЁТ: {n} — убито {k.get(n, 0)} из {want}")
    absent = [n for n in exp_names if n not in k and n not in RULES.get("skip", [])]
    if absent:
        say("ОТЧЁТ: из списка зоны не встретила — " + ", ".join(absent))
    if stats.get("later"):
        say("ОТЧЁТ: отложены клетки — " + ", ".join(stats["later"]))


# ---------- таймеры областей (слова пользователя 16.11: «повтор идет по таймеру из области») ----------
AREAS_JSON = os.path.join(HERE, "области.json")
GROUP_CD = 25 * 60       # зоны без области (города): пробный репоп групп 25 мин (ПРАВИЛА\РЕПОП.md)


def areas_load():
    try:
        return json.load(open(AREAS_JSON, encoding="utf-8-sig"))
    except Exception:
        return {"ready": {}, "zone_areas": {}, "last_run": {}}


def areas_save(d):
    json.dump(d, open(AREAS_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def read_obl(d):
    """`обл` -> когда можно создать новый экземпляр каждой области."""
    n0 = log_from(A, 0)[1]
    send(A, "обл")
    time.sleep(2)
    for l in log_from(A, n0)[0]:
        # «активен  129   Подземелье гномов    -          35   14 минут 3 секунды» (статус номер название лидер репоп таймер)
        t = re.search(r"^\s*\S+\s+\d+\s+(.+?)\s{2,}\S+\s+(\d+)\s+(?:(\d+)\s+минут\S*)?\s*(?:(\d+)\s+секунд\S*)?\s*$", l.split(">")[-1])
        if t and (t.group(3) or t.group(4)):
            secs = int(t.group(3) or 0) * 60 + int(t.group(4) or 0)
            d["ready"][t.group(1).strip()] = time.time() + secs + 60
            repop_note("область " + t.group(1).strip(), "", f"репоп {t.group(2)} мин, до репопа {secs // 60} мин {secs % 60} с")
            continue
        m = re.search(r"'([^']+)'.*?через\s+(?:(\d+)\s+минут\S*)?\s*(?:(\d+)\s+секунд\S*)?", l)
        if m and (m.group(2) or m.group(3)):
            secs = int(m.group(2) or 0) * 60 + int(m.group(3) or 0)
            d["ready"][m.group(1)] = time.time() + secs + 60
            repop_note("область " + m.group(1), "", f"таймер {secs // 60} мин {secs % 60} с")
        elif m:
            d["ready"].setdefault(m.group(1), 0)
    for l in log_from(A, n0)[0]:
        if l.strip():
            say("  обл: " + l.strip()[:110])


def zone_ready(z, d):
    now = time.time()
    areas = d["zone_areas"].get(z, [])
    inst = [a for a in areas if a in d["ready"]]
    if inst:
        return all(d["ready"][a] <= now for a in inst)
    return now - d["last_run"].get(z, 0) >= GROUP_CD


def kimpi_level():
    n0 = log_from(K, 0)[1]
    send(K, "сч")
    time.sleep(2)
    t = "\n".join(log_from(K, n0)[0])
    lv = re.search(r"(\d+) уровня\.", t)
    need = re.search(r"надо набрать (\d+) опыта", t)
    return (int(lv.group(1)) if lv else None), (int(need.group(1)) if need else None)


SKLAD = "115092"          # склад Геоланта
UNDRESS = {               # -сет в профилях через #scr (клиент не умеет) — команды из Айлина.md и СКРИПТЫ\Проверка.md
    A: ["сдай", "сня все", "кс :барб3 все16"],
    K: ["сдай", "сня все", "кс :следак4 перчатка.правую", "кс :следак4 перчатка.левую", "кс :следак3 все15"],
}


def undress():
    say("РАЗДЕТЬСЯ: веду на склад Геоланта")
    if not walk_to(SKLAD):
        say("не дошла до склада — раздеваю где стою не буду")
        return
    time.sleep(2)
    for p in (A, K):
        for c in UNDRESS[p]:
            send(p, c)
            time.sleep(0.8)
    time.sleep(3)
    for p in (A, K):
        n0 = log_from(p, 0)[1]
        send(p, "экип")
        time.sleep(1.5)
        left = [l for l in log_from(p, n0)[0] if l.strip().startswith("<")]
        say(f"{NAMES[p]}: на себе осталось {len(left)} вещей")


def main():
    if "--раздеться" in sys.argv:
        undress()
        return
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    goal = int(next((a[7:] for a in sys.argv if a.startswith("--goal=")), "30"))
    cd = 60 * float(next((a[5:] for a in sys.argv if a.startswith("--cd=")), "30"))
    loop = "--loop" in sys.argv
    if os.path.exists(STOPF):
        os.remove(STOPF)
    for p in (A, K):                                         # 16.11: «реж кратк да 1 раз напиши и все»
        send(p, "реж кратк да")
    D = areas_load()
    lv, need = kimpi_level()
    say(f"СТАРТ: Кимпи {lv} ур., до следующего {need}; цель {goal}; зоны {args}; круг={loop}")
    while True:
        did = False
        for z in args:
            if lv and lv >= goal:
                say(f"ЦЕЛЬ: Кимпи {lv} уровня")
                return
            if not zone_ready(z, D):
                continue
            stats = {"kills": 0, "exp": 0}
            check_menu()
            for p in (A, K):                                  # триггеры (встать, усталость, монеты…) — включены всегда
                try:
                    http(p, "/api/triggers?on=1")
                except Exception:
                    pass
            stand_up()
            try:
                restock()
                feed()
            except Regrouped:                                # сбор во время пополнения — ничего, дальше зона
                pass
            if cur(A) != cur(K):
                try:
                    regroup()
                except Regrouped:
                    pass
            ok = False
            for attempt in range(3):                       # после сбора — зона заново
                try:
                    ok = run_zone(z, stats)
                    break
                except Regrouped:
                    say(f"после сбора — зона {z} заново")
                    if os.path.exists(STOPF):
                        return
            if ok:
                D["last_run"][z] = time.time()             # неудачный проход — не считать (зона не пройдена)
            D["zone_areas"][z] = sorted(set(D["zone_areas"].get(z, [])) | set(stats.get("areas", [])))
            read_obl(D)
            areas_save(D)
            did = True
            lv2, need2 = kimpi_level()
            gain = (need - need2) if (need and need2 and lv2 == lv) else (f"новый уровень {lv2}!" if lv2 and lv and lv2 > lv else "?")
            say(f"ИТОГ {z}: Кимпи {lv2} ур., до след. {need2}, получила {gain}")
            lv, need = lv2 or lv, need2 or need
            if not ok:
                say(f"зона {z} не пройдена — дальше по кругу")     # не останавливаться (слова пользователя)
                if not walk_to(SKLAD):
                    send(A, "путь склад")
                    send(K, "путь склад")
                    time.sleep(30)
        if not loop:
            return
        if not did:
            time.sleep(60)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        say("СТОП:", e)
    except Exception as e:
        say("ОШИБКА:", repr(e))
        raise
