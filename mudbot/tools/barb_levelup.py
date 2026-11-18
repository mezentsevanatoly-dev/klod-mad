"""Готовый скрипт прокачки орка-варвара 1 -> 21 лвл (Сфера Миров, бот mudbot).

python tools/barb_levelup.py status            состояние персонажа (лвл, ДСУ, HP, монеты, пул тренировки)
python tools/barb_levelup.py plan              показать план этапов и что ещё не пройдено
python tools/barb_levelup.py run [--to 21] [--dry] [--from <этап>]   пройти план (продолжает с текущего уровня)
python tools/barb_levelup.py gear <1|8|12|16|18|20>   переодеться в набор лвл (сдаёт старое в клан по отделам)
python tools/barb_levelup.py train             потратить пул тренировки поровну (по +1% по кругу)
python tools/barb_levelup.py sharpen           проверить заточку, при необходимости съездить в Эрдер
python tools/barb_levelup.py supplies          расходники: взять с :Колбы, докупить, лут сдать

Правила (из логов пользователя и сессии 03.11, см. skills/mud/reference/lessons_2026-11-03.md):
  * опыт = потолок МОЕГО лвл при лвле моба >= мой-2; мобов выше себя не бьём (mapfight --extra 0), осмотр `см` перед боем;
  * вид, давший < 40% потолка, больше не бьём; «потолочных» M >= мой-1 оставляем до повышения (hunt_luga.capped);
  * в школе на 4 лвл бить, пока ДСУ > 60; зоны: один заход, респаун не ждём; спидволки (tools/trip.py в:<место|номер комнаты>);
  * тихий лог игры > STALL_SEC = обрыв связи: скрипт останавливает охотника и пишет levelup.alarm (реконнект делает человек).
Состояние: data/barb_state.json (выполненные вехи), журнал: tools/levelup.log.
"""
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PY = sys.executable
ENV = dict(os.environ, MUD_VIA="bot")
OUT = os.path.join(ROOT, "out.log")
STATE = os.path.join(ROOT, "data", "barb_state.json")
JOURNAL = os.path.join(HERE, "levelup.log")
ALARM = os.path.join(ROOT, "levelup.alarm")
STALL_SEC = 150
DRY = False


# ------------------------------------------------------------------ служебное
def say(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    try:
        open(JOURNAL, "a", encoding="utf-8").write(s + "\n")
    except Exception:
        pass


def run(args, timeout=900):
    if DRY:
        say("[dry]", " ".join(args))
        return ""
    r = subprocess.run([PY, "-X", "utf8"] + args, cwd=ROOT, env=ENV, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    return (r.stdout or "") + (r.stderr or "")


def cmd(*cmds, wait=2):
    """Команды в игру через tools/cmd.py, вернуть текст ответа."""
    return run([os.path.join("tools", "cmd.py")] + [f"{c}|{wait}" for c in cmds], timeout=300)


def state():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return {}


def mark(key):
    s = state()
    s[key] = time.strftime("%d.%m %H:%M")
    json.dump(s, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def done(key):
    return key in state()


def log_age():
    try:
        return time.time() - os.path.getmtime(OUT)
    except OSError:
        return 1e9


class Stall(Exception):
    pass


# ------------------------------------------------------------------ состояние персонажа
def status():
    t = cmd("сч", wait=3)
    d = {}
    m = re.search(r"Варвар (\d+) уровня", t)
    d["lvl"] = int(m.group(1)) if m else None
    m = re.search(r"Вам надо набрать (\d+) опыта", t)
    d["dsu"] = int(m.group(1)) if m else None
    m = re.search(r"Вы имеете (\d+)\((\d+)\) здоровья", t)
    d["hp"], d["maxhp"] = (int(m.group(1)), int(m.group(2))) if m else (None, None)
    m = re.search(r"имеете (\d+)\(", t)
    d["coins"] = int(m.group(1)) if m else None
    m = re.search(r"можете использовать (\d+) опыта", t)
    d["pool"] = int(m.group(1)) if m else 0
    m = re.search(r"У вас есть (\d+) тренировк", t)
    d["trains"] = int(m.group(1)) if m else 0
    d["vamp"] = "вампиризм" in t
    return d


def where():
    t = cmd("где", wait=2)
    m = re.search(r"\[cur\] \{'vnum': '(\d+)', 'area': '([^']*)'", t)
    return (m.group(1), m.group(2)) if m else (None, None)


def level():
    return status().get("lvl") or 1


# ------------------------------------------------------------------ перемещения
STABLE = {"Город Элендор": "100147", "Город Геолант": "115061", "Город Огис": "180154", "Город Стэдвик": "12172"}
RIDE = {"Город Элендор": "элен", "Город Геолант": "гео", "Город Огис": "огис", "Город Стэдвик": "стэдвик"}


def travel(dest):
    """Спидволк до комнаты (место из trip.PLACES или номер vnum)."""
    if dest == "эл_склад" and not DRY:                      # в другом городе склад свой: команда «путь склад», пешком через зоны не ходить
        vnum, area = where()
        if area and area.startswith("Город ") and "Элендор" not in area:
            cmd("путь склад", wait=8)
            say("travel склад (путь склад) в", area)
            return True
    out = run([os.path.join("tools", "trip.py"), "в:" + str(dest)], timeout=300)
    ok = "ok за" in out
    say("travel", dest, "ok" if ok else "ОШИБКА")
    if not ok and not DRY and where()[1] and where()[1].startswith("Город Элендор"):     # goto только внутри Элендора (через зоны не ходить)
        out = run([os.path.join("tools", "goto.py"), str(dest)], timeout=600)      # запасной вариант: пошаговый goto
        ok = "пришли" in out
    return ok


def ride(city_area):
    """Повозкой в город (из любого города; сначала на повозки текущего)."""
    vnum, area = where()
    if DRY:
        say("[dry] ride ->", city_area)
        return True
    if area == city_area:
        return True
    if area not in STABLE:                                       # мы в зоне (например Катакомбы): выходим пешком к конюшне ближайшего города
        say("ride: не в городе с повозками:", area, "- иду к конюшне Геоланта/Элендора пешком")
        travel(STABLE["Город Элендор"] if area in ("Болото", "Парк", "Аллея", "Канализация", "Заливные луга") else STABLE["Город Геолант"])
        vnum, area = where()
        if area not in STABLE:
            return False
    travel(STABLE[area])
    cmd("ехать " + RIDE[city_area], wait=3)
    t0 = time.time()
    while time.time() - t0 < 360:
        time.sleep(5)
        if log_age() > STALL_SEC:
            raise Stall()
        v, a = where()
        if a == city_area:
            say("ride ok:", city_area)
            return True
    return False


def city_hub(city_area):
    ride(city_area)


# ------------------------------------------------------------------ снаряжение
# слот -> (отдел КСК, ключевое слово для кз/кс)
GEAR = {
    1: {"рюкзак": (":следак1", "рюкзак"), "голова": (":следак1", "шлем.из.толст"), "тело": (":следак1", "доспех.из.толст"),
        "руки": (":следак1", "наручи.из.толст"), "кисти": (":следак1", "перчатки.из.грубой"), "ноги": (":следак1", "поножи.из.толст"),
        "обувь": (":следак1", "сапоги.из.толст"), "плащ": (":следак1", "плотный"), "шея1": (":следак1", "шарфик"),
        "шея2": (":следак1", "шарфик"), "пояс": (":следак1", "змеиный"), "запя": (":следак1", "склизкий"),
        "правая": (":следак1", "палица.битв"), "левая": (":следак1", "легкая.палица")},
    8: {"рюкзак": None, "голова": (":следак1", "шлем.с.рогами"), "тело": (":следак1", "пластинчато"),
        "руки": (":следак1", "наручи.из.кожи"), "кисти": (":следак1", "перчатки.из.грубой.кожи"), "ноги": (":следак1", "чешуйчатые"),
        "обувь": (":следак1", "сапоги.из.кожи"), "плащ": (":следак1", "морской"), "пояс": (":следак1", "пояс.из.черного"),
        "запя2": (":следак1", "браслет.фокус"), "кольцо": (":следак1", "кольцо.сотканное")},
    12: {"доп": (":барб2", "фибула"), "голова": (":следак1", "шлем.с.рогами"), "шея1": (":барб2", "ожерелье"), "шея2": (":барб2", "ожерелье"),
         "тело": (":барб3", "камзол"), "плащ": (":барб3", "тонкий"), "кисти": (":барб2", "гномьи"),
         "руки": (":барб2", "наручи.из.темного"), "ноги": (":барб3", "чешуйчатые"), "запя2": (":барб2", "стальной")},
    16: {"голова": (":барб3", "череп"), "руки": (":общий", "наручи.лорда"), "ноги": (":общий", "поножи.из.паутины")},
    18: {"плащ": (":общий", "плащ.хамелеона"), "ноги": (":общий", "отполированные"), "кисти": (":селлин", "голубые")},
    20: {"тело": (":общий", "доспех.из.большого"), "голова": (":селлин", "голова"), "плащ": (":селлин", "шкура"),
         "кольцо": (":селлин", "кольцо.драконьей"), "правая": (":барб3", "перчатка.правую"), "левая": (":барб3", "перчатка.левую")},
}
# кому какой набор: накапливается (каждый следующий набор переопределяет слоты предыдущих)
SET_ORDER = [1, 8, 12, 16, 18, 20]


def gear_slots(upto):
    cur = {}
    for k in SET_ORDER:
        if k > upto:
            break
        for slot, v in GEAR[k].items():
            if v is None:
                cur.pop(slot, None)
            else:
                cur[slot] = v
    # склизкий браслет (запя) остаётся с лвл 1 и носится на одном запястье; стальной на другом
    return cur


ALL_ITEMS = [v for k in SET_ORDER for v in GEAR[k].values() if v]


def dept_for(worn_name):
    """Отдел клана для названия надетой вещи (по ключевым словам известных вещей), иначе None -> личный склад."""
    low = worn_name.lower()
    for dept, kw in ALL_ITEMS:
        words = [w for w in kw.split(".") if w]
        if all(w in low for w in words[:2] if len(w) > 3) and words and words[0] in low:
            return dept, kw
    return None


def strip_all(back=None):
    """Снять всё и сдать по отделам (оружие первым: у вещей со статами выпадает оружие, триггер бота может одеть обратно)."""
    for _ in range(3):
        t = cmd("э", wait=3)
        worn = re.findall(r"<[^>]+>\s+(.+?)\s+\[", t)
        if not worn:
            return
        worn.sort(key=lambda n: 0 if "перчатка" in n or "палица" in n else 1)
        for n in worn:
            word = [w for w in re.split(r"\s+", n.replace("*", "").strip()) if len(w) > 2]
            key = ".".join(word[:2]) if len(word) >= 2 else word[0]
            cmd("сня " + key, wait=1)
            hit = dept_for(n)
            if hit:
                cmd(f"ксдать {hit[0]} {hit[1]}", wait=1)
            elif back:
                cmd(f"ксдать {back} {key}", wait=1)
            else:
                cmd("сдать " + word[-1], wait=1)


# комплекты пользователя: каждый лежит целиком в своём отделе КСК (пришёл на 1 — взял всё из следак1 и надел,
# пришёл на 8 — снял всё, сдал в следак1, взял всё из барб1)
SET_DEPT = {1: ":следак1", 2: ":следак2", 3: ":следак3"}     # комплект 1 (1-8 лвл), 2 (8-15), 3 (15-20)
SET_OF = {1: 1, 8: 2, 15: 3, 16: 3}                           # веха -> номер комплекта
PALITS = ("палица.битв", "легк.палиц")                         # одна пара на лвл 1-19 (заточка на 1 лвле); на 20 боевые перчатки


def swap_gear(upto):
    """Алиасы пользователя: -сетN = «сня все; кс :следакN все 17», +сетM = «кз :следакM все 17; од все». Палицы общие: после сдачи
    комплекта забираем их из того же отдела и берём в руки (иначе они остались бы лежать в отделе прежнего комплекта)."""
    n = SET_OF.get(upto)
    if not n:
        say("для вехи", upto, "новый комплект не нужен")
        mark(f"gear{upto}")
        return
    travel("эл_склад")
    cur = max([k for k in (1, 2, 3) if done(f"set{k}")] or [0])
    if cur and cur != n:
        cmd("взять все рюкзак", wait=2)                        # содержимое рюкзака (вещи на вырост, расходники) не сдаём с комплектом
        cmd("кс :колбы все.настойка", "кс :колбы все.эликсир", "кс :колбы все.свиток", wait=2)     # `все 17` сдаёт ВСЁ из инвентаря: расходники отдельно
        cmd("сня все", f"кс {SET_DEPT[cur]} все 17", wait=3)
        src = SET_DEPT[cur]
    else:
        src = SET_DEPT[n]
    for w in PALITS:                                           # палицы лежат в отделе прежнего комплекта: берём и надеваем первыми
        cmd(f"кз {src} {w}", wait=2)                            # (лимит предметов на низком лвл: 20 с учётом надетого)
    cmd("од все", wait=2)
    cmd(f"кз {SET_DEPT[n]} все 17", "од все", wait=4)
    mark(f"set{n}")
    tidy(n)                                                      # не надеваемое сейчас (мин. лвл выше) возвращаем в отдел комплекта, с собой не носим
    unstash_consumables()                                        # расходники нужны в инвентаре: `осушить`/`зачитать` не берут из рюкзака
    mark(f"set{n}")
    supplies()
    mark(f"gear{upto}")


def unstash_consumables():
    cmd("взять все.настойка рюкзак", "взять все.эликсир рюкзак", "взять все.свиток рюкзак", wait=1)


CONS_WORDS = ("настойка", "эликсир", "свиток", "колба")
PLAN_JSON = os.path.join(ROOT, "data", "kit_plan_ksk.json")
STOPW = {"из", "с", "в", "на", "и", "для", "от", "под", "над", "по"}


def kwords(name):
    return ".".join(w[:5] for w in re.sub(r"[*,\[\]#\d]", " ", name).split() if w.lower() not in STOPW)


def norm_name(s):
    return re.sub(r"\s+", " ", s.replace("*", "")).strip().lower()


def tidy(cur=None):
    """С собой только надетое и расходники (правило пользователя 07.11: «зачем носишь одежду на 12 лвл»). Всё остальное — из инвентаря и рюкзака
    обратно в отдел КСК своего комплекта (по плану data/kit_plan_ksk.json; одинаковые вещи — в отдел текущего комплекта)."""
    cur = cur or max([k for k in (1, 2, 3) if done(f"set{k}")] or [1])
    try:
        plan = json.load(open(PLAN_JSON, encoding="utf-8"))
    except Exception:
        plan = {}
    owner = {}
    for sid, ch in plan.items():
        for picks in ch.values():
            for p in picks:
                owner.setdefault(norm_name(p["name"]), set()).add(int(sid))
    owner[norm_name("склизкий браслет")] = {1, 2}                        # на КСК два склизких: один в сет 1, второй в сет 2
    cmd("взять все рюкзак", wait=1)
    inv = cmd("инв", wait=2)
    for l in inv.splitlines():
        if not l.startswith(" ") or l.startswith((" Вы ", " Ничего")) or "Вых:" in l or "[cur]" in l:
            continue
        name = re.sub(r"\s*\[\d+\]\s*$", "", l.strip())
        if not name or name.startswith(CONS_WORDS) or "палица" in name:
            continue
        sets = owner.get(norm_name(name), {cur})
        n = cur if cur in sets else min(sets)
        cmd(f"кс {SET_DEPT[n]} {kwords(name)}", wait=1)


def reequip():
    """Перед этапом: на новом лвл надеть то, что стало доступно (вещи комплекта лежат в рюкзаке), остальное обратно; расходники в инвентарь;
    вампиризм (эликсир летучей мыши), если не горит."""
    cur = max([k for k in (1, 2, 3) if done(f"set{k}")] or [1])
    cmd("взять все рюкзак", f"кз {SET_DEPT[cur]} все 17", "од все", wait=3)         # ближайшее по лвл из своего комплекта
    tidy(cur)                                                                         # не надетое (мин. лвл выше) возвращаем в отдел
    unstash_consumables()
    aff = cmd("аф", wait=2)
    if "вампиризм" not in aff:
        cmd("осуш мыш", wait=2)
    if "инфразрение" not in aff:
        cmd("осуш инфраз", wait=2)


def gloves20():
    """20 лвл: рукопашный бой на тяжёлых боевых перчатках (КСК :барб3), палицы сдаём в отдел текущего комплекта."""
    travel("эл_склад")
    cur = max([k for k in (1, 2, 3) if done(f"set{k}")] or [1])
    cmd("сня палица", "сня легкая", wait=2)
    for w in PALITS:
        cmd(f"кс {SET_DEPT[cur]} {w}", wait=2)
    cmd("кз :барб3 перчатка.правую", "кз :барб3 перчатка.левую", "воор перчатка.правую", "держ перчатка.левую", "од все", wait=2)
    mark("gear20")


# ------------------------------------------------------------------ тренировки, покупки, заточка
SKILLS = {"рукопашный": "рукопашный", "доп": "дополнительная атака", "атак": "атака второй рукой", "ярость": "ярость сражения",
          "дуби": "дубины и палицы"}


def train(skills, reserve=0.0, max_rounds=80):
    """Потратить пул поровну: по +1% по кругу, пока хватает (в Гильдии Варваров 100169)."""
    travel("эл_гильдия")
    for r in range(max_rounds):
        spent = False
        for s in skills:
            o = cmd(f"уч {s} 1", wait=2)
            if "потренировали умение" in o:
                spent = True
        if not spent:
            break
    say("тренировка закончена; пул:", status().get("pool"))


def chars(n_trains):
    t = status()
    if t.get("trains", 0) >= 3:
        cmd("трен сила", "трен тело", "трен сила", wait=1)


def guild4():
    travel("эл_гильдия")
    cmd("куп 1", "изуч 1", "уч атак 10", "уч дуби 20", "трен ловк", "трен ловк", "трен ловк", wait=2)
    mark("guild4")


def guild12_dop():
    """Доп. атака: Стэдвик, быстрая дощечка 20 000."""
    if (status().get("coins") or 0) < 25000:                    # быстрая дощечка 20 000: деньги из казны клана
        ride("Город Элендор")
        travel("эл_банк")
        cmd("клан снять 30000", wait=3)
    ride("Город Стэдвик")
    travel("стэд_гильдия")
    cmd("куп 1", "изуч дощ", "уч доп 30", wait=3)
    ride("Город Элендор")
    mark("dop12")


def sharpen_left():
    t = cmd("осм палица", "осм перчатка.правую", wait=2)
    m = re.search(r"Заточка \((?:(\d+) час[а-я]* )?(?:(\d+) минут[а-я]*)?\)", t)
    if not m:
        return 0
    return int(m.group(1) or 0) * 60 + int(m.group(2) or 0)


def sharpen(force=False):
    left = sharpen_left()
    say("заточка осталось минут:", left)
    if left >= 40 and not force:
        return
    st = status()
    travel("эл_банк")
    if (st.get("coins") or 0) < 340000:
        cmd("клан снять 340000", wait=3)
    travel("эл_склад")
    out = run([os.path.join("tools", "trip.py"), "эрдер_точильщик"], timeout=900)
    say(out.strip().splitlines()[-1] if out.strip() else "эрдер?")
    if level() >= 20:
        cmd("заточить маст перчатка.правую", "заточить маст перчатка.левую", wait=4)
    else:
        cmd("заточить маст палица", "заточить маст легкая", wait=4)
    out = run([os.path.join("tools", "trip.py"), "точильщик_склад"], timeout=900)
    mark("sharpen")


def erder_rage():
    """Дощечка ярости 40 000 в Эрдере (можно с 19 лвл)."""
    if done("rage"):
        return
    travel("эл_банк")
    cmd("клан снять 100000", wait=3)
    travel("эл_склад")
    run([os.path.join("tools", "trip.py"), "эрдер_точильщик", "в:эрдер_гильдия"], timeout=900)
    cmd("куп 2", "изуч дощ", wait=3)
    run([os.path.join("tools", "trip.py"), "в:эрдер_портал"], timeout=300)
    mark("rage")


def supply_need(lvl):
    """Расходники из :Колбы так, как берёт пользователь в своих логах (start2: насыщение ×2, восстановление ×3, вампиризм,
    левитация = полёт, внимательность, прозрение). Не придумывать свои нормы; другие уровни — смотреть логи этапа."""
    # обязательный набор пользователя (07.11): охранный свиток, панацея, восстановление, насыщение, прозрение, мыши
    return {"охранный": 1, "панацеи": 1, "восстановления": 3, "насыщения": 2, "прозрения": 1, "летучей": 1, "инфразрения": 1}   # + темнота


def count_item(inv, word):
    n = 0
    for l in inv.splitlines():
        if word in l and ">>>" not in l:
            m = re.search(r"\[(\d+)\]\s*$", l)
            n += int(m.group(1)) if m else 1
    return n


def supplies():
    """Расходники по уровню: недостающее взять с :Колбы, лишнее (в т. ч. из рюкзака) вернуть туда, лут сдать."""
    travel("эл_склад")
    need = supply_need(level())
    unstash_consumables()
    inv = cmd("инв", wait=2)                                    # считаем только то, что в инвентаре, рюкзак для расходников не используем
    for word, n in need.items():
        have = count_item(inv, word)
        for _ in range(max(0, n - have)):
            cmd(f"кз :колбы {word}", wait=1)
        if have > n:
            cmd(f"взять все.{word} рюк", wait=1)
            for _ in range(have - n):
                cmd(f"ксдать :колбы {word}", wait=1)
    for word in ("настойка", "эликсир", "свиток"):   # виды, которых по уровню не нужно вовсе
        for l in inv.splitlines():
            if l.startswith(" ") and word in l and not any(w in l for w in need):
                w = l.strip().split(" [")[0]
                cmd(f"взять все.{w.split()[-1]} рюк", f"ксдать :колбы {w.split()[-1]}", wait=1)
    mark("supplies")


# ------------------------------------------------------------------ запуск охоты
LAST_HUNT = None


def hunt(name, args, dsu_stop=None, stop_lvl=None, timeout_min=60):
    """Запустить tools/*.py в фоне, следить за логом игры, питанием и вампиризмом. Вернуть причину завершения."""
    if DRY:
        say("[dry] hunt", name, args)
        return "dry"
    logf = os.path.join(HERE, f"run_{name}.log")
    errf = os.path.join(HERE, f"run_{name}.err")
    p = subprocess.Popen([PY, "-X", "utf8"] + args, cwd=ROOT, env=ENV, stdout=open(logf, "w", encoding="utf-8"),
                         stderr=open(errf, "w", encoding="utf-8"))
    open(os.path.join(HERE, "run_lvl.pid"), "w").write(str(p.pid))
    say("охота", name, "pid", p.pid, " ".join(args[1:]))
    t0, last_upkeep, last_aff = time.time(), 0, 0
    reason = "timeout"
    while time.time() - t0 < timeout_min * 60:
        time.sleep(3)
        if p.poll() is not None:
            tail = open(logf, encoding="utf-8", errors="replace").read()[-600:]
            reason = "level" if "ДОСТИГНУТ" in tail else "cleared" if "зона пройдена" in tail else "dead" if "ПОГИБ" in tail else "exit"
            break
        if log_age() > STALL_SEC:
            p.kill()
            open(ALARM, "w").write(time.strftime("%H:%M:%S обрыв связи, лог игры стоит\n"))
            say("ТИХИЙ ЛОГ: обрыв связи, охота остановлена; нужен реконнект (/кон) и вход человека")
            raise Stall()
        if dsu_stop is not None and os.path.exists(OUT):
            tail = open(OUT, encoding="utf-8", errors="replace").read()[-3000:]
            ms = re.findall(r"X(\d+)X", tail)
            if ms and int(ms[-1]) <= dsu_stop:
                p.kill()
                reason = "dsu"
                break
        if time.time() - last_upkeep > 50:                   # питание, энергия, вампиризм
            last_upkeep = time.time()
            tail = open(OUT, encoding="utf-8", errors="replace").read()[-2500:]
            if "Вы хотите есть" in tail or "Вы хотите пить" in tail:
                cmd("осуш насы", wait=1)
            if re.search(r"V([0-9]|1[0-4])V/", tail):
                cmd("осуш восст", wait=1)
            if "Здесь темно" in tail[-900:]:                      # зоны темны, мобы видны как «Кто-то»: нужен инфразрение (польз. 07.11)
                cmd("осуш инфраз", wait=1)
            if time.time() - last_aff > 240:                       # раз в 4 мин: аффекты (инфразрение ~15 мин, вампиризм ~25)
                last_aff = time.time()
                aff = cmd("аф", wait=2)
                if "инфразрение" not in aff:
                    cmd("осуш инфраз", wait=1)
                if "вампиризм" not in aff:
                    cmd("осуш мыш", wait=1)
    else:
        p.kill()
    say("охота", name, "->", reason)
    global LAST_HUNT
    LAST_HUNT = reason
    return reason


def mapfight(name, routes, zone, stop, avoid=(), strict=False, extra=0, below=3, dsu_stop=None, timeout_min=45):
    zarg = f'"{zone}"' if " " in zone else zone
    # пользователь 07.11: бить ВСЕХ мобов из списка именно этого захода (имена из логов routes), ничего из списка не пропускать по уровню,
    # но и никого вне списка: «бить всех на 3 лвл выше» опасно (повариха на складе). Списки по заходам: склад1/склад2, привы1/привы2.
    a = [os.path.join("tools", "mapfight.py"), str(stop), "--route"] + list(routes) + ["--zone", zone, "--extra", "5",
                                                                                         "--below", "99", "--skip", "0", "--strict"]
    if avoid:
        a += ["--avoid"] + [str(x) for x in avoid]
    return hunt(name, a, dsu_stop=dsu_stop, timeout_min=timeout_min)


def inc_run(name, route, stop, extra_args=(), timeout_min=40):
    return hunt(name, [os.path.join("tools", "inc_run.py"), route, str(stop)] + list(extra_args), timeout_min=timeout_min)


def replay(route, a, b):
    return run([os.path.join("tools", "replay.py"), route, "--here", "--from", str(a), "--to", str(b)], timeout=300)


AREA_TIMERS = os.path.join(ROOT, "data", "area_timers.json")


def timers_load():
    try:
        return json.load(open(AREA_TIMERS, encoding="utf-8"))
    except Exception:
        return {}


def timers_save(d):
    json.dump(d, open(AREA_TIMERS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def area_rows():
    """Таблица `область`: [(статус, номер, зона, репоп_мин, осталось_сек|None, текст_таймера)]."""
    rows = []
    for l in cmd("область", wait=2).splitlines():
        m = re.match(r"^\s*(\S+)\s+(\d+)\s+(.+?)\s{2,}(\S+)\s+(\d+)\s+(.+?)\s*$", l)
        if not m or m.group(1) in ("Статус",):
            continue
        t = m.group(6)
        sec = None
        if re.search(r"\d", t):
            sec = sum(int(n) * k for n, k in (re.findall(r"(\d+)\s*час", t) and [(re.findall(r"(\d+)\s*час", t)[0], 3600)] or []) +
                      (re.findall(r"(\d+)\s*минут", t) and [(re.findall(r"(\d+)\s*минут", t)[0], 60)] or []) +
                      (re.findall(r"(\d+)\s*секунд", t) and [(re.findall(r"(\d+)\s*секунд", t)[0], 1)] or []))
        rows.append((m.group(1), int(m.group(2)), m.group(3).strip(), int(m.group(5)), sec, t))
    return rows


def create(direction, zone=None):
    """Область для зоны: срок = таймер из таблицы + 1 мин (правило пользователя 07.11). Перед созданием: если прошлая область этой зоны
    отработала (в таблице «удалите вручную» или срок вышел) — `обл удал <направление>`; если ещё идёт — ждём до срока+1 мин (не больше 3 мин),
    иначе идём в уже существующую область (она нужна для лёгких мобов)."""
    tm = timers_load()
    row = next((r for r in area_rows() if zone and r[2] == zone), None)
    if row:
        status, num, z, repop, sec, ttxt = row
        expired = sec is None or sec <= 0 or "удал" in ttxt
        due = tm.get(z, {}).get("ready_at", 0)
        if not expired and time.time() < due and (due - time.time()) <= 180:
            say(f"область «{z}» ещё {int(due - time.time())} с до срока+1 мин: жду")
            time.sleep(due - time.time() + 2)
            expired = True
        if expired or time.time() >= due and due:
            say(f"область «{z}» отработала ({ttxt}): обл удал {direction}")
            cmd(f"обл удал {direction}", wait=3)
    t = cmd(f"обл соз {direction}", wait=3)
    ok = "Создан" in t or "уже создан" in t
    if not ok and "сможете создать новый экземпляр" in t:       # та же фраза и при уже активной области: смотрим таблицу `область`
        ok = "активен" in cmd("область", wait=2)
    if ok and zone:
        r = next((r for r in area_rows() if r[2] == zone), None)
        if r and "Создан" in t:
            tm[zone] = {"created": time.time(), "ready_at": time.time() + (r[4] or r[3] * 60) + 60}   # таймер + 1 мин
            timers_save(tm)
    say("область", direction, "создана" if ok else "НЕ создана: " + re.sub(r"\s+", " ", t)[:120])
    cmd(direction, wait=3)
    return ok


def hatch():
    cmd("отпер люк", "откр люк", wait=1)


# ------------------------------------------------------------------ этапы
def st_school():
    travel("эл_склад")
    inc_run("school", "start2", 4, ["--all"])
    if level() == 4:
        inc_run("school2", "start2", 5, ["--here", "--noentry", "--all"], timeout_min=15)       # добор до ДСУ <= 60 делает наблюдатель в hunt


def st_school_dsu():
    # охота на 4 лвл пока ДСУ > 60 (правило пользователя): запустить второй проход школы со стопом по ДСУ
    a = [os.path.join("tools", "inc_run.py"), "start2", "5", "--here", "--noentry", "--all"]
    hunt("school_dsu", a, dsu_stop=60, timeout_min=20)


def st_park():
    travel("парк_вход")
    if create("з", "Парк"):
        mapfight("park", ["парк"], "Парк", 5)


def st_alleya():
    travel("аллея_вход")
    if create("с", "Аллея"):
        mapfight("alleya", ["аллея"], "Аллея", 8)


def st_kanal():
    travel("канал_вход")
    if create("вни", "Канализация"):
        mapfight("kanal", ["канал"], "Канализация", 10)


def st_bolot():
    inc_run("bolot", "болото_часть", 11)


def st_pritn():
    travel("притон_вход")
    if create("с", "Притон"):
        mapfight("pritn", ["притон"], "Притон", 12)


def st_sklad1():
    ride("Город Геолант")
    travel("гео_перед_складом")
    if create("в", "Склад в Геоланте"):
        mapfight("sklad1", ["склад1"], "Склад в Геоланте", 12)           # 1-й заход (10-11 лвл): только животные из лога склад1


def st_privy1():
    ride("Город Геолант")
    travel("огис_дорога")
    if create("в", "Дом с привидениями"):
        mapfight("privy1", ["привы1"], "Дом с привидениями", 13)


def st_lecheb():
    ride("Город Огис")                                      # повозкой в Огис, вход в лечебницу — «Зеленая улица» 180048, область на север
    travel("180048")
    if create("с", "Лечебница для животных"):
        mapfight("lecheb", ["огис_лечеб"], "Лечебница для животных", 14)


def st_kat_top():
    ride("Город Геолант")
    travel("гео_тупик")
    if create("вни", "Катакомбы Геоланта"):
        hatch()
        mapfight("katak_top", ["каналгео1"], "Катакомбы Геоланта", 15)


def st_luga():
    ride("Город Элендор")
    travel("140003")
    mapfight("luga", ["луга", "луга2"], "Заливные луга", 20)


def st_sklad2():
    ride("Город Геолант")
    travel("гео_перед_складом")
    if create("в", "Склад в Геоланте"):
        mapfight("sklad2", ["склад2"], "Склад в Геоланте", 17)            # 2-й заход (15-16 лвл): все остальные из лога склад2


def st_privy2():
    ride("Город Геолант")
    travel("огис_дорога")
    if create("в", "Дом с привидениями"):
        mapfight("privy2", ["привы2"], "Дом с привидениями", 17)         # 2-й заход (15-16 лвл): привидения и дом из лога привы2


def st_tea():
    ride("Город Геолант")
    travel("гео_конюшня")
    inc_run("tea", "чайный_домик", 18, ["--here", "--seq", "--from", "15"])


def st_gobl():
    ride("Город Геолант")
    travel("гео_склад")
    replay("гоблины", 0, 31)
    mapfight("gobl", ["гоблины"], "Лагерь гоблинов", 19)


def st_port():
    ride("Город Элендор")
    travel("эл_конюшня")
    replay("порт", 1, 19)
    mapfight("port", ["порт"], "Порт Элендора", 17)


def st_kat_low():
    ride("Город Геолант")
    travel("гео_тупик")
    if create("вни", "Катакомбы Геоланта"):
        hatch()
        travel("226124")
        mapfight("katak_low", ["геокаты2", "каналгео1"], "Катакомбы Геоланта", 21, avoid=[226125])


def st_arh():
    ride("Город Геолант")
    travel("гео_конюшня")
    replay("арх", 0, 12)
    cmd("ю", wait=3)
    mapfight("arh", ["арх"], "Лагерь археологов", 21)


def st_luga21():
    ride("Город Элендор")
    travel("140003")
    mapfight("luga21", ["луга2", "луга"], "Заливные луга", 22, below=2)


# (имя, от лвл, до лвл, функция, веха ПОСЛЕ этапа)
PLAN = [
    ("школа", 1, 4, st_school, None),
    ("школа_дсу", 4, 5, st_school_dsu, "guild4"),
    ("парк", 4, 5, st_park, None),
    ("аллея", 5, 8, st_alleya, "gear8"),
    ("канал", 8, 10, st_kanal, None),
    ("болото", 9, 11, st_bolot, None),
    ("притон", 11, 12, st_pritn, None),
    ("склад1", 10, 12, st_sklad1, "dop12"),          # 1-й заход: животные, 10-11 лвл
    ("привы1", 12, 13, st_privy1, None),
    ("лечебница", 13, 14, st_lecheb, None),
    # катакомбы_верх убран 07.11: 1-й этаж (каналгео1) мобы 5-14 лвл, но охота уходила на нижние этажи к кобольдам (23+) и умирала; 2-й этаж (геокаты2) только 18-19 лвл
    ("привы2", 15, 17, st_privy2, None),             # 15-16 лвл: вторые заходы (склад2, привы2) и порт — по словам пользователя 07.11
    ("склад2", 15, 17, st_sklad2, "gear16"),
    ("порт", 15, 17, st_port, None),
    ("чайный", 17, 18, st_tea, None),
    ("гоблины", 18, 19, st_gobl, "gear18"),
    ("луга", 18, 20, st_luga, "rage"),               # 18-19 лвл: бьём всех мобов 15-22
    ("катакомбы_низ", 18, 20, st_kat_low, "weapon20"),     # геокаты2 = 2-й этаж, 18-19 лвл; 3-й этаж (геоканал3, кобольды) только 23+
    ("археологи", 20, 21, st_arh, None),
    ("луга_животные", 21, 22, st_luga21, None),
]


def milestone(key, lvl):
    """Действия между этапами. Вызывается после этапа с ключом, если уровень уже достигнут."""
    if key == "guild4" and lvl >= 4 and not done("guild4"):
        guild4()
    elif key == "gear8" and lvl >= 8 and not done("gear8"):
        swap_gear(8)
    elif key == "dop12" and lvl >= 12 and not done("dop12"):
        guild12_dop()                                   # комплект 2 остаётся до 15 лвл
    elif key == "gear16" and lvl >= 15 and not done("gear16"):
        swap_gear(16)
    elif key == "gear18" and lvl >= 18 and not done("gear18"):
        mark("gear18")
    elif key == "rage" and lvl >= 19 and not done("rage"):
        erder_rage()
    elif key == "weapon20" and lvl >= 20 and not done("gear20"):
        gloves20()
        train(["рукопашный", "доп", "ярость", "атак"])
        sharpen(force=True)
    elif key == "train":
        train(["доп", "атак", "ярость"])


def start_setup():
    if done("start"):
        return
    say("старт: режимы, снаряжение 1 лвл, расходники, заточка")
    cmd("реж трус 40", "реж форс да", "реж удары да", "реж повр да", "реж возврат да", "реж опыт кратк", "реж время да",
        "реж карта сверху", wait=1)
    if not done("gear1"):
        swap_gear(1)
    if not done("supplies"):
        supplies()
    sharpen()  # заточка уже может держаться (осталось >= 40 мин) — в Эрдер не ездить
    mark("start")


def plan_text(lvl):
    for n, a, b, f, ms in PLAN:
        mark_ = "  <- сейчас" if a <= lvl < b else ""
        say(f"{n:16} {a:>2}->{b:<2}  веха после: {ms or '-'}{mark_}")


def main():
    global DRY
    argv = sys.argv[1:]
    DRY = "--dry" in argv
    cmdname = argv[0] if argv else "plan"
    if cmdname == "status":
        print(json.dumps(status(), ensure_ascii=False))
    elif cmdname == "plan":
        plan_text(level())
        print("вехи выполнены:", sorted(state()))
    elif cmdname == "gear":
        swap_gear(int(argv[1]))
    elif cmdname == "train":
        train(["рукопашный", "доп", "ярость", "атак"])
    elif cmdname == "sharpen":
        sharpen(force="--force" in argv)
    elif cmdname == "supplies":
        supplies()
    elif cmdname == "run":
        to = int(argv[argv.index("--to") + 1]) if "--to" in argv else 21
        try:
            start_setup()
            tol, repeats = 0, 0                                             # допуск по лвл: сначала точные окна, потом -1, -2 (не больше!)
            HARD = {"склад2", "привы2", "порт", "чайный", "гоблины", "луга", "катакомбы_низ", "археологи", "луга_животные"}   # без допуска: опасные/сильные
            while tol <= 2:
                ran = False
                for n, a, b, f, ms in PLAN:
                    lvl = level()
                    if lvl >= to:
                        say("цель достигнута: лвл", lvl)
                        return
                    if "--from" in argv and not ran and n != argv[argv.index("--from") + 1] and not done("_from"):
                        continue
                    mark("_from")
                    if done(f"stage_{n}") or not (a - (0 if n in HARD else tol) <= lvl < b):      # зона уже пройдена (в области нет репопа)
                        continue
                    say(f"=== этап {n}: лвл {lvl}, цель {b} (допуск {tol}) ===")
                    reequip()
                    global LAST_HUNT
                    LAST_HUNT = None
                    f()
                    if LAST_HUNT in ("cleared", "level", "dsu", "timeout") or n.startswith("школа"):
                        mark(f"stage_{n}")                                    # этап пройден
                    else:                                                      # охота не состоялась / вылетела: не больше 2 попыток, потом пропуск
                        fails = int(state().get(f"fail_{n}", "0") or 0) + 1
                        mark(f"fail_{n}") if False else None
                        s = state(); s[f"fail_{n}"] = str(fails); json.dump(s, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                        say(f"этап {n} не состоялся (охота: {LAST_HUNT}), попытка {fails}")
                        if fails >= 2:
                            mark(f"stage_{n}")
                    lvl = level()
                    if ms:
                        milestone(ms, lvl)
                    supplies() if lvl in (8, 12, 16) else None
                    sharpen()
                    ran, tol = True, 0
                    for key in ("guild4", "gear8", "dop12", "gear16", "gear18", "rage", "weapon20"):      # догнать вехи, чей этап прошёл раньше уровня
                        milestone(key, level())
                if not ran:
                    tol += 1
                    if tol > 2 and repeats < 60:                              # нет подходящих этапов: повторный заход в лёгкую зону (область пересоздаётся после срока+1 мин)
                        lvl = level()
                        EASY = ("лечебница", "привы1", "притон", "канал", "болото", "аллея")        # лёгкие зоны для повторов (катакомбы не повторять)
                        cand = [(a, n) for n, a, b, f, ms in PLAN if n in EASY and a <= lvl + 1 and done(f"stage_{n}")]
                        if cand:
                            nm = max(cand)[1]
                            repeats += 1
                            s = state()
                            for k in (f"stage_{nm}", f"fail_{nm}"):
                                s.pop(k, None)
                            json.dump(s, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                            say(f"нет подходящих этапов на {lvl} лвл: повторный заход «{nm}» (#{repeats})")
                            tol = 0
            say("план пройден или нет подходящих этапов; лвл", level())
        except Stall:
            say("ОСТАНОВКА: обрыв связи. Реконнект: /кон в консоли бота, вход человека, затем `run` продолжит с этапа по уровню.")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
