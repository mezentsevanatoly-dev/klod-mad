"""Очередь непрочитанных справок: все темы из «Смотрите также» в data/help/*.txt минус уже сохранённые.

python tools/help_todo.py   -> data/help_todo.txt (тема и откуда на неё ссылаются)
"""
import collections
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
HELP = os.path.join(ROOT, "data", "help")
# справки, прочитанные вручную в игре (вне data/help)
READ_MANUALLY = {
    "СПРАВКА", "ПИЩА_И_ВОДА", "КЛАДОВЩИК", "ПЕРЕДВИЖЕНИЕ", "СЧЕТ", "ОПЫТ", "ГИЛЬДИЯ", "ПОВРЕЖДЕНИЯ", "РАУНД",
    "ОЧИСТИТЬ", "ЭКИПИРОВКА", "ПЕРСОНАЛЬНЫЕ_КВЕСТЫ", "КВЕСТЫ", "РЕЖИМЫ", "БАНК", "БИРЖА", "ФИЛЬТР_ПРЕДМЕТОВ",
    "ВАРВАР", "РАСЫ", "ОРК", "БЕРСЕРК", "УЧИТЬ", "ТРЕНИРОВАТЬ", "ЭНЕРГИЯ", "ОТДЫХАТЬ", "ВЕС", "ИНВЕНТАРЬ", "ВЗЯТЬ",
    "БРОСИТЬ", "ДАТЬ", "ПОЛОЖИТЬ", "КОНТЕЙНЕРЫ", "НАПОЛНИТЬ", "ПУТЬ", "ОБЛАСТЬ", "КЛАНСКЛАД", "ИДЕНТИФИКАЦИЯ",
    "ПРЕДМЕТЫ", "БОТИНГ", "ПРОВЕРКА_ПРИСУТСТВИЯ", "ПЕРСОНАЛЬНЫЙ_РЕЖИМ_!БОТ", "НАПИТОК_МОГУЩЕСТВА", "ОЗАРЕНИЯ",
    "ПЕРЕЛИТЬ_ПЕРСОНАЖА", "КОМАНДЫ", "СОКРАЩЕНИЯ", "ДК", "ВАМПИРИЗМ", "НАСЫЩЕНИЕ", "ОКОСТЕНЕНИЕ", "УСКОРЕНИЕ",
    "ИНФРАЗРЕНИЕ", "ЗАЩИТА", "СИЛА", "ВОССТАНОВЛЕНИЕ", "АТАКА_ВТОРОЙ_РУКОЙ", "БОЙ", "СПЕЦИАЛИЗАЦИЯ",
}


def main():
    have = set(READ_MANUALLY)
    refs = collections.defaultdict(set)
    for f in os.listdir(HELP):
        txt = open(os.path.join(HELP, f), encoding="utf-8").read()
        first = txt.strip().splitlines()[0] if txt.strip() else ""
        have.update(w for w in first.split() if w.isupper())          # ключевые слова темы
        have.add(os.path.splitext(f)[0].upper())
        for m in re.finditer(r"Смотрите (?:также|так же):\s*(.+?)(?:\n\S|\Z)", txt, re.S):
            for t in re.split(r"[,\s]+", m.group(1).replace("\n", " ")):
                t = t.strip(".").upper()
                if t and t.replace("_", "").isalpha():
                    refs[t].add(os.path.splitext(f)[0])
    todo = sorted((t for t in refs if t not in have), key=lambda t: -len(refs[t]))
    with open(os.path.join(ROOT, "data", "help_todo.txt"), "w", encoding="utf-8") as out:
        for t in todo:
            out.write(f"{t}\t{', '.join(sorted(refs[t]))[:120]}\n")
    print(f"непрочитано тем: {len(todo)}")
    for t in todo[:40]:
        print(f"  {t}  ({len(refs[t])} ссылок)")


if __name__ == "__main__":
    main()
