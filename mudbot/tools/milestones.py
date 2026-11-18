"""Вехи по уровням (из логов пользователя): что надо сделать, дойдя до уровня N.

python tools/milestones.py            -> узнать уровень (`сч`) и вывести несделанное для всех уровней <= текущего
python tools/milestones.py --level N  -> то же, без запроса к игре
python tools/milestones.py --done 8:кск   -> отметить веху сделанной (ключ = «уровень:метка»)
Состояние: data/milestones_done.json. inc_run.py вызывает проверку в конце этапа, cron-проверка читает вывод.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "..", "data", "milestones_done.json")

# уровень -> [(метка, что сделать)]
MILESTONES = {
    1: [("старт", "КСК =варвар =1 (следак1), режимы, Колбы, палицы заточены (7-8 ч)")],
    4: [("гильдия4", "Гильдия Варваров 100169: куп 1, изуч 1 (атака второй рукой), уч атак 10, уч дуби 20, трен ловк")],
    8: [("кск8", "КСК/биржа: шлем с рогами*, пластинч.-кож. доспех*, морской плащ, пояс из чёрного меха*, сапоги кожи тролля, поножи чешуйч.*, браслет фокусника, кольцо из тумана; склизкий браслет до 8 лвл"),
        ("гильдия8", "уч дуби 20, уч атак 20 (цены растут, делить пул вручную)")],
    12: [("кск12", "КСК/биржа: золотая фибула, камзол из стальных полос*, тонкий серый плащ*, гномьи перчатки*, наручи из тёмного металла***"),
         ("доп_атака", "Гильдия: купить доп.атаку (по логу «доп_атака»)")],
    15: [("кск15", "КСК/биржа; Военная гильдия: трен ловк, уч дуби")],
    18: [("кск18", "КСК/биржа")],
    20: [("кск20", "КСК/биржа"), ("ярость", "Эрдер: купить ярость (гильдия варваров Эрдера)"),
         ("оружие20", "СМЕНА ОРУЖИЯ: рукопашный бой на боевых перчатках — тяжёлая боевая перчатка на правую и на левую (КСК :Барб3/:Селлин), заточить в Эрдере, особ леву ловк, палицы битв сдать в :Следак1; выучить рукопашный бой (уч рукопаш)")],
    23: [("кск23", "КСК/биржа")],
    25: [("кск25", "КСК/биржа")],
    28: [("кск28", "КСК/биржа")],
}


def load():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return {}


def level_now():
    env = dict(os.environ, MUD_VIA="bot")
    out = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "cmd.py"), "сч|2"], capture_output=True, text=True,
                         encoding="utf-8", env=env).stdout
    m = re.search(r"Варвар (\d+) уровня", out)
    return int(m.group(1)) if m else None


def pending(level):
    done = load()
    return [(lv, key, text) for lv in sorted(MILESTONES) if lv <= level for key, text in MILESTONES[lv] if f"{lv}:{key}" not in done]


def main():
    argv = sys.argv[1:]
    if "--done" in argv:
        k = argv[argv.index("--done") + 1]
        d = load()
        d[k] = True
        json.dump(d, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("отмечено:", k)
        return
    lv = int(argv[argv.index("--level") + 1]) if "--level" in argv else level_now()
    if lv is None:
        print("уровень не определён")
        return
    todo = pending(lv)
    print(f"УРОВЕНЬ {lv}: несделанных вех {len(todo)}")
    for l, key, text in todo:
        print(f"  [{l}:{key}] {text}")


if __name__ == "__main__":
    main()

