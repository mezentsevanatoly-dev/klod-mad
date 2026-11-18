"""Эксплор зоны Айлиной (обход в глубину с записью клеток, мобов, карточек, опыта).
Запуск (из mudbot): python -X utf8 tools/explore.py <папка_результата> [--stop-on отшельник,...]
Стартовая клетка = текущая. Результат: data/recon/<папка>/explore.jsonl (одна строка на клетку) и explore.log.
Перед шагом смотрит названия соседних клеток через 'огл' и НЕ заходит в ДТ-имена (BAD_NAMES).
Моба: карточки 'см N.', убийство по первому слову имени из карточки; остановка, если имя в STOP_NAMES или HP < 50%."""
import os, sys, re, json, time
os.environ.setdefault("JMC_TARGET", r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА")
sys.path.insert(0, os.path.dirname(__file__))
import jmc
import step_vn

BAD_NAMES = ["Обрыв", "Сорвавшись", "пропаст", "бездн"]
STOP_NAMES = ["отшельник"]
DIRS = {"N": ("с", "S"), "S": ("ю", "N"), "E": ("в", "W"), "W": ("з", "E"), "U": ("вверх", "D"), "D": ("вниз", "U")}
LABEL = {"севере": "N", "юге": "S", "востоке": "E", "западе": "W"}

zone = sys.argv[1]
extra_stop = []
if "--stop-on" in sys.argv:
    extra_stop = sys.argv[sys.argv.index("--stop-on") + 1].split(",")
STOP = [s.lower() for s in STOP_NAMES + extra_stop]
SKIP_DIRS = sys.argv[sys.argv.index("--skip-dirs") + 1].split(",") if "--skip-dirs" in sys.argv else []
SKIP_AT = sys.argv[sys.argv.index("--skip-at") + 1].split(",") if "--skip-at" in sys.argv else []   # формат vnum:направление, напр. 159013:U
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "recon", zone)
os.makedirs(OUT, exist_ok=True)
JL = open(os.path.join(OUT, "explore.jsonl"), "a", encoding="utf-8")
LOG = open(os.path.join(OUT, "explore.log"), "a", encoding="utf-8")
DJ = open(os.path.join(OUT, "doors.jsonl"), "a", encoding="utf-8")   # двери/замки: клетка, направление, название, итог
EDIT = jmc.find_input(jmc.find_window())
ANSI = re.compile(r"^\d\d:\d\d:\d\d ")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n"); LOG.flush()


def send(cmd, wait=1.2, quiet=1.5, maxwait=25):
    """Отправить команду и дождаться тишины в логе без боя. Возврат: строки ответа."""
    start = jmc.log_size()
    jmc.type_line(cmd, True, EDIT)
    time.sleep(wait)
    t0 = time.time(); last = jmc.log_size(); lastchg = time.time()
    while time.time() - t0 < maxwait:
        time.sleep(0.5)
        sz = jmc.log_size()
        if sz != last:
            last = sz; lastchg = time.time()
        lines = [ANSI.sub("", l) for l in jmc.read_log(start)]
        in_fight = bool(lines) and any(re.match(r"^\d+H .*\[Айлина:", l) for l in lines[-3:])
        if time.time() - lastchg >= quiet and not in_fight:
            break
    return [ANSI.sub("", l) for l in jmc.read_log(start) if l.strip()]


def vnum():
    start = jmc.log_size()
    jmc.type_line("#scr ClaudeLog.note($MsdpRoomVnum)", True, EDIT)
    time.sleep(0.8)
    for l in reversed(jmc.read_log(start)):
        m = re.search(r"## (\d+)\s*$", l)
        if m:
            return int(m.group(1))
    return None


def hp():
    start = jmc.log_size()
    time.sleep(0.2)
    lines = send("", wait=0.5, quiet=0.6, maxwait=3) if False else []
    return None


def count_mobs(mob_lines):
    """Сколько мобов в строках комнаты: строка с хвостом [N] = N мобов, иначе 1."""
    n = 0
    for s in mob_lines:
        m = re.search(r"\[(\d+)\]\s*$", s)
        n += int(m.group(1)) if m else 1
    return n


def parse_room(lines):
    name = None; exits = ""; mobs = []
    for i, l in enumerate(lines):
        if l.startswith("[ Exits:"):
            exits = l
            j = i + 1
            while j < len(lines) and not re.match(r"^\d+H ", lines[j]) and not lines[j].startswith("[Зона") and "Вы " not in lines[j][:4]:
                mobs.append(lines[j]); j += 1
            if i >= 1:
                pass
            break
    # название = последняя непустая строка без отступа перед описанием
    for l in lines:
        if l and not l.startswith(" ") and not l.startswith(">>") and not re.match(r"^\d+H ", l) and not l.startswith("[") and not l.startswith("##"):
            name = l; break
    ex = re.findall(r"\[ Exits: (.*?) \]", exits)
    ex = ex[0].split() if ex else []
    return name, [e.strip("()") for e in ex], mobs


def look_names():
    lines = send("огл", wait=0.8, quiet=0.8, maxwait=6)
    res = {}
    for l in lines:
        m = re.match(r"^\s*(На (\w+)|Вверху|Внизу|Наверху|Сверху|Снизу):\s*(.*)$", l)
        if not m:
            continue
        if m.group(2) in LABEL:
            res[LABEL[m.group(2)]] = m.group(3).strip()
        elif m.group(1) in ("Вверху", "Наверху", "Сверху"):
            res["U"] = m.group(3).strip()
        elif m.group(1) in ("Внизу", "Снизу"):
            res["D"] = m.group(3).strip()
    return res


def cards(limit=1):
    """Карточки мобов. limit = число строк-кандидатов в комнате (мобы идут первыми: 2., 3., ...).
    Остановка на первом ответе без '[уровень' (дальше пошли бы МОИ вещи: 'Предмет ...', 'Айлина использует')."""
    cs = []
    for n in range(2, 4 + max(limit, 1)):       # вошёл я: я = 1., первый моб = 2.; вошедшие позже идут с 1. и сдвигают меня (см 1. только при нехватке)
        lines = send(f"см {n}.", wait=0.5, quiet=0.7, maxwait=5)
        txt = "\n".join(lines)
        if "Вы не видите" in txt:
            break
        if "минотавр" in txt:
            continue                              # это я (моя карточка тоже содержит 'использует:'), дальше смотрим
        if "Предмет '" in txt:
            break                                 # дальше пошли мои вещи (верхняя = медаль): мобы кончились
        if len(cs) >= limit and limit > 0 and False:
            break
        m = re.search(r"^(.+?) \[уровень (\d+)\], (.+)$", txt, re.M)
        if m:
            h = re.search(r"Хиты: (\d+)/", txt); sk = re.search(r"Навыки:\s*(.*)", txt)
            cs.append({"n": n, "имя": m.group(1), "лвл": int(m.group(2)), "проф": m.group(3), "хп": int(h.group(1)) if h else None,
                       "навыки": sk.group(1).strip() if sk else ""})
        else:
            break
    if len(cs) < limit:                         # мобов меньше, чем строк в комнате: вошедший позже моб стал 1. -> см 1.
        lines = send("см 1.", wait=0.5, quiet=0.7, maxwait=5)
        txt = "\n".join(lines)
        m = re.search(r"^(.+?) \[уровень (\d+)\], (.+)$", txt, re.M)
        if m and "минотавр" not in txt:
            h = re.search(r"Хиты: (\d+)/", txt); sk = re.search(r"Навыки:\s*(.*)", txt)
            cs.append({"n": 1, "имя": m.group(1), "лвл": int(m.group(2)), "проф": m.group(3), "хп": int(h.group(1)) if h else None,
                       "навыки": sk.group(1).strip() if sk else ""})
    return cs


def kill_all(cs, rec):
    for c in cs:
        low = c["имя"].lower()
        if any(s in low for s in STOP):
            say("СТОП: моб из списка стоп:", c["имя"]); return "stop"
    tries = 0
    while tries < 14:
        rl = send("см", wait=0.5, quiet=0.8, maxwait=6)          # смотрим комнату, а не см N. (иначе покажет мои вещи)
        _n, _e, mobs2 = parse_room(rl)
        mobs2 = [m for m in mobs2 if not re.search(r"(лежит|лежат|валяется|валяются) (здесь|тут)", m)]
        if not mobs2:
            return "ok"
        cs2 = cards(count_mobs(mobs2))
        if not cs2:
            return "ok"
        HOLD = ("Маг", "Некромант", "Друид", "Рыцарь смерти")
        def prio(x):                      # холдер по ПРОФЕССИИ первым, потом Лекарь/Паладин, остальные
            p = x["проф"].strip()
            return 0 if p in HOLD else (1 if p in ("Лекарь", "Паладин") else 2)
        c = min(cs2, key=prio)
        if any(s in c["имя"].lower() for s in STOP):
            say("СТОП: моб из списка стоп:", c["имя"]); return "stop"
        kw = re.split(r"[\s\-]", c["имя"])[0].lower()
        if c["имя"].split()[-1].lower() not in kw:
            kw = c["имя"].split()[-1].lower()
        lines = send(f"убить {kw}", wait=1.0, quiet=2.0, maxwait=40)
        txt = "\n".join(lines)
        exp = re.findall(r"Вы получили (\d+) (?:единиц|единицы|единица) опыта", txt)
        rec["убито"].append({"имя": c["имя"], "лвл": c["лвл"], "проф": c["проф"], "хп": c["хп"], "навыки": c["навыки"],
                              "kw": kw, "опыт": [int(x) for x in exp], "первый": "ударил вас" in txt or "попытал" in txt})
        low = txt.lower()
        if "вы слишком" in low:
            say("устала, пью восстановление"); send("осуш восст", quiet=1)
        tries += 1
    return "ok"


def ensure_weapon():
    """Проверка оружия: нет '<в обеих руках>' -> взя все, пауза (болит рука), од все; не вышло -> False."""
    for attempt in range(3):
        lines = send("экип", wait=0.5, quiet=0.8, maxwait=5)
        if any("в обеих руках" in l or "правой руке" in l for l in lines):
            return True
        say("  ОРУЖИЯ НЕТ в руках, поднимаю")
        send("взя все", wait=0.5, quiet=0.8, maxwait=5)
        time.sleep(7)
        send("од все", wait=0.5, quiet=0.8, maxwait=5)
    return False


def hp_ok():
    lines = send("", wait=0.4, quiet=0.8, maxwait=3)
    for l in reversed(lines):
        m = re.match(r"^(\d+)H ", l)
        if m:
            return int(m.group(1)) >= 850
    return True


visited = set(); stack = []
START = None
KNOWN = {}
_jp = os.path.join(OUT, "explore.jsonl")
if os.path.exists(_jp):
    for _l in open(_jp, encoding="utf-8"):
        try:
            _r = json.loads(_l)
            _m = [s for s in _r.get("строки", []) if not re.search(r"(лежит|лежат|валяется|валяются) (здесь|тут)", s)]
            if not _r.get("стоп") and not (_m and len(_r.get("убито", [])) < count_mobs(_m)):   # комнаты с неубитыми мобами не «известные»
                KNOWN[_r["vnum"]] = _r
        except Exception:
            pass


def explore(prev_dir_back=None, depth=0):
    vn = vnum()
    if vn in visited:
        return "seen"
    visited.add(vn)
    if vn in KNOWN:                      # клетка уже снята: берём из файла, мобов не трогаем
        rec = KNOWN[vn]; name = rec["имя"]; exits = rec["выходы"]; names = rec.get("соседи", {})
        say(f"[{vn}] {name} (известна)")
        return walk_exits(vn, exits, names, prev_dir_back, depth)
    lines = send("см", wait=0.5, quiet=0.8, maxwait=6)
    name, exits, mobs = parse_room(lines)
    raw = next((re.findall(r"\[ Exits: (.*?) \]", l)[0] for l in lines if "[ Exits:" in l), "")
    rec = {"vnum": vn, "имя": name, "выходы": exits, "выходы_сырые": raw, "строки": mobs, "убито": [], "карточки": []}
    mobs = [m for m in mobs if not re.search(r"(лежит|лежат|валяется|валяются) (здесь|тут)", m)]
    if mobs:
        cs = cards(count_mobs(mobs))
        rec["карточки"] = cs
        if cs:
            r = kill_all(cs, rec)
            if r == "stop":
                rec["стоп"] = True
                JL.write(json.dumps(rec, ensure_ascii=False) + "\n"); JL.flush()
                return "stop"
    if (mobs or rec["убито"]) and not ensure_weapon():
        say("ОРУЖИЯ НЕТ: остановка (топор на складе: путь склад, забрать топор)")
        JL.write(json.dumps(rec, ensure_ascii=False) + "\n"); JL.flush(); return "hp"
    if not hp_ok():
        say("HP ниже 850: остановка"); JL.write(json.dumps(rec, ensure_ascii=False) + "\n"); JL.flush(); return "hp"
    names = look_names() if exits else {}
    rec["соседи"] = names
    JL.write(json.dumps(rec, ensure_ascii=False) + "\n"); JL.flush()
    say(f"[{vn}] {name} {exits} мобов:{len(mobs)} убито:{len(rec['убито'])}")
    return walk_exits(vn, exits, names, prev_dir_back, depth)


def walk_exits(vn, exits, names, prev_dir_back, depth):
    for e in exits:
        if e not in DIRS or e in SKIP_DIRS or f"{vn}:{e}" in SKIP_AT:
            continue
        nb = names.get(e, "")
        if any(b.lower() in nb.lower() for b in BAD_NAMES):
            say(f"  пропуск {e}: {nb} (ДТ)")
            continue
        cmd, back = DIRS[e]
        if e == prev_dir_back:
            continue
        before = vn
        out = send(cmd, wait=0.8, quiet=1.2, maxwait=30)
        nv = vnum()
        if nv == before:                 # закрыто/заперто: отпереть и открыть по названию из сообщения игры
            txt = "\n".join(out)
            m = re.search(r"сначала открыть ([^.\n]+)\.", txt)
            door = {"vnum": before, "направление": e, "сообщение": txt[:200]}
            if m:
                door["дверь"] = m.group(1)
                # справка ДВЕРИ: открыть <дверь> [направление]; при одноимённых дверях направление обязательно
                k = m.group(1).split()[0][:4]         # 'гудящую плиту' -> 'гуд'
                send(f"отпер {k} {cmd}", wait=0.5, quiet=0.8, maxwait=6)
                send(f"откр {k} {cmd}", wait=0.5, quiet=0.8, maxwait=6)
                out = send(cmd, wait=0.8, quiet=1.2, maxwait=30)
                nv = vnum()
                if nv == before:
                    say(f"  {e}: заперто ({m.group(1)}), нет ключа")
                    door["итог"] = "заперто, нужен ключ"
                else:
                    door["итог"] = "открыто и пройдено"
            else:
                door["итог"] = "не прошёл, причина не 'открыть'"
            DJ.write(json.dumps(door, ensure_ascii=False) + "\n"); DJ.flush()
            if nv == before:
                say(f"  не прошёл {e}")
                continue
        if nv == before or nv is None:
            say(f"  не прошёл {e}")
            continue
        if START is not None and nv // 1000 != START // 1000:
            say(f"  {e}: выход из зоны ({nv}), возвращаюсь")
            send(DIRS[back][0], wait=0.8, quiet=1.0)
            continue
        if nv in visited:
            send(DIRS[back][0], wait=0.8, quiet=1.0)
            continue
        r = explore(back, depth + 1)
        if r in ("stop", "hp"):
            return r
        # назад
        send(DIRS[back][0], wait=0.8, quiet=1.2, maxwait=30)
    return "ok"


if __name__ == "__main__":
    step_vn.close_errors()
    START = vnum()
    say("=== старт эксплора", zone, START, time.strftime("%H:%M:%S"))
    r = explore()
    say("=== конец:", r, "клеток:", len(visited))
