"""Прохождение зоны руками -> .botp с vnum. Комнаты берём из out.log (MSDP — это правда о том, где мы были), команды — из sent.log.

python tools/walk_to_botp.py <метка_создания_в_out.log> <метка_в_sent.log> <выход.botp> [метка_конца_в_sent.log]
  пример: python tools/walk_to_botp.py "создал экземпляр зоны 'Башня магов'" "гг !обл с з +2" areas/routes/БМ_руками.botp

Алгоритм: последние строки «[msdp] комната …» после строки создания — реальная цепочка комнат; клетка до неё — клетка создания (outer).
Команды sent.log после метки идут по порядку: движение считается удавшимся, если направление ведёт из текущей комнаты в следующую
реальную (по exits из MSDP) — иначе шаг не вышел (дверь, страж) и пропускается; прочие значимые команды привязываются к текущей
комнате. Отбрасываются: боевые хоткеи (гг !фраг, гг !пом, пом, к землетряс), автооткрывание дверей триггерами (отпереть X; открыть X;
открыть X <напр.>), «смотреть», «оч», «пгр …», взять все (его добавит сам бот после боя), и строки с цифрами numpad
(комментарии, набранные в консоль) — они печатаются отдельно, их стоит прочитать.
Карта разведки не нужна: работает и для неразведанных зон. Запись — cp1251, как у Чвырлы.
"""
import ast
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from explore_msdp import CMD  # noqa: E402

RU = {v: k for k, v in CMD.items()}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MSDP = re.compile(r"^\[msdp\] комната (\d+) \| (.*?) \| (.*?) \| (\{.*\})\s*$")
DOOR_SPAM = re.compile(r"^(отпереть|открыть) \S+( (север|юг|восток|запад|вверх|вниз))?$")
NOISE = re.compile(r"^(гг !(фраг|пом)|пом|к землетряс|смотреть|оч|пгр .*|гр|кто|аф|инв|взять все|взя все|взя все все\.труп|задания.*|зада|"
                   r"тр|мс|мв|очистить|вст|огл|гг !очистить|гг !вст|гг !од все|од все|гг !.*)$")
KEEP = re.compile(r"^(отпер|откр|взя все \S|дать|г |говорить|уби|установ|положить|вставить|сказ|пнуть|нажать|повернуть|толкнуть|потянуть|"
                  r"войти|плыть|нырнуть|залезть|слезть|осмотреть|ос )")


def tail_lines(path, mb=40):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        f.seek(max(0, size - mb * 1024 * 1024))
        return f.read().decode("utf-8", errors="replace").splitlines()


def main():
    cre_mark, sent_mark, out = sys.argv[1:4]
    end_mark = sys.argv[4] if len(sys.argv) > 4 else None
    log = tail_lines(os.path.join(ROOT, "out.log"))
    ci = max((i for i, l in enumerate(log) if cre_mark in l), default=None)
    if ci is None:
        raise SystemExit("метка создания не найдена в out.log (последние 40 МБ)")
    rooms = []                                         # [(vnum, name, exits)]
    for l in log[ci + 1:]:
        m = MSDP.match(l)
        if m and (not rooms or rooms[-1][0] != m.group(1)):
            try:
                ex = {k: str(v) for k, v in ast.literal_eval(m.group(4)).items()}
            except Exception:
                ex = {}
            rooms.append((m.group(1), m.group(3), ex))
    before = next((MSDP.match(l) for l in reversed(log[:ci]) if MSDP.match(l)), None)
    if not before:
        raise SystemExit("не нашла клетку создания (MSDP до строки создания)")
    outer = (before.group(1), before.group(3), ast.literal_eval(before.group(4)))
    outer = (outer[0], outer[1], {k: str(v) for k, v in outer[2].items()})
    chain = [outer] + rooms
    sent = open(os.path.join(ROOT, "sent.log"), encoding="utf-8", errors="replace").read().splitlines()
    a = max((i for i, l in enumerate(sent) if sent_mark in l), default=None)
    if a is None:
        raise SystemExit("метка не найдена в sent.log")
    sent = sent[a + 1:]
    if end_mark:
        b = next((i for i, l in enumerate(sent) if end_mark in l), None)
        sent = sent[:b] if b is not None else sent
    k = 0                                              # индекс текущей комнаты в chain
    res = ["#if {$MsdpRoomVnum ==%s} {#var SumReset 0}" % chain[0][0]]
    comments, skipped = [], 0
    for l in sent:
        m = re.match(r"(\d\d:\d\d:\d\d) (.*)", l)
        if not m:
            continue
        t, c = m.group(1), m.group(2).strip()
        if not c or DOOR_SPAM.match(c):
            continue
        d = RU.get(c.replace("подкр ", ""))
        cur = chain[k]
        if d:
            if k + 1 < len(chain) and cur[2].get(d) == chain[k + 1][0]:
                res.append("#if {$MsdpRoomVnum ==%s} {%s}" % (cur[0], c))
                k += 1
            else:
                skipped += 1                           # шаг не вышел (дверь, страж, бой) — пользователь повторял
            continue
        if NOISE.match(c):
            continue
        if re.search(r"\d{3,}|[+/]\d", c):
            comments.append(f"{t} [комната {cur[0]} {cur[1]}] {c}")
            continue
        if KEEP.match(c):
            res.append("#if {$MsdpRoomVnum ==%s} {%s}" % (cur[0], c))
        else:
            comments.append(f"{t} (не распознано) {c}")
    open(out, "w", encoding="cp1251", newline="\r\n", errors="replace").write("\n".join(res) + "\n")
    print(f"клетка создания {outer[0]} {outer[1]}; реальных комнат после создания {len(rooms)}; принято движений {k}, "
          f"не вышедших шагов {skipped}; строк маршрута {len(res)} -> {out}")
    print("конечная комната:", chain[k][0], chain[k][1], "| реальная последняя:", chain[-1][0], chain[-1][1])
    if k + 1 < len(chain):
        print(f"ВНИМАНИЕ: {len(chain) - 1 - k} реальных переходов не нашли команды (перемещали чем-то другим: портал, телепорт, призыв)")
    if comments:
        print("комментарии/нераспознанное:", *comments, sep="\n  ")


if __name__ == "__main__":
    main()
