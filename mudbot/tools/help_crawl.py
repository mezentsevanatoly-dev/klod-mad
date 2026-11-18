"""Вся справка игры: оглавление перебором префиксов, затем каждая статья в data/help/.

?<префикс> выдаёт первую подходящую статью и либо список «Также найдены следующие разделы…»,
либо «Количество других найденных разделов…: N» (слишком много — уточняем префикс ещё одной буквой).
python tools/help_crawl.py index   -> data/help_index.json (все ключевые слова)
python tools/help_crawl.py fetch   -> статьи, которых ещё нет в data/help/
Прогресс сохраняется, можно прерывать и запускать снова.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from dump_help import OUT, fetch  # noqa: E402
from explore_zone import FileClient  # noqa: E402

INDEX = os.path.join(OUT, "..", "help_index.json")
ABC = "абвгдежзийклмнопрстуфхцчшщъыьэюя"
TOPIC_RE = re.compile(r"^ ([A-ZА-ЯЁ0-9_!'\-]+)\s*$")


def fname(topic):
    return os.path.join(OUT, re.sub(r"[^\w!]+", "_", topic) + ".txt")


def save_article(txt):
    """Статья из ответа (без хвоста со списком найденных); имя файла — первое ключевое слово."""
    body = re.split(r"\n\s*\n(?:Также найдены|Количество других)", txt)[0].strip()
    lines = body.splitlines()
    if not lines or "СПРАВКА_НЕ_НАЙДЕНА" in lines[0]:
        return set()
    keys = header_keys(body)
    if keys:
        path = fname(lines[0].split()[0])
        if os.path.exists(path) and header_keys(open(path, encoding="utf-8").read()) != keys:
            path = path[:-4] + "_2.txt"           # другая статья с тем же первым словом
        if not os.path.exists(path):
            open(path, "w", encoding="utf-8").write(body)
    return keys


def header_keys(txt):
    """Ключевые слова статьи: заглавные слова строк до первой пустой."""
    keys = set()
    for l in txt.strip().splitlines():
        if not l.strip():
            break
        keys |= {w for w in l.split() if w.isupper()}
    return keys


def bigrams():
    """Пары букв, которые бывают в словах справки: «афб» не проверяем."""
    bg = set()
    for f in os.listdir(OUT):
        for w in re.findall(r"[а-яё_]+", open(os.path.join(OUT, f), encoding="utf-8").read().lower()):
            bg.update(w[i:i + 2] for i in range(len(w) - 1))
    return bg


MAX_DEPTH = 4          # глубже префиксы растут комбинаторно; остальное добираем по «Смотрите также»


def children(p, bg):
    if len(p) >= MAX_DEPTH or "_" in p:
        return []
    return [p + ch for ch in ABC if (p[-1] + ch) in bg]


def load():
    if os.path.exists(INDEX):
        return json.load(open(INDEX, encoding="utf-8"))
    return {"done": [], "todo": list(ABC), "topics": []}


def index():
    st = load()
    c = FileClient()
    topics, done = set(st["topics"]), set(st["done"])
    bg = bigrams()
    st["todo"] = [p for p in st["todo"] if len(p) == 1 or (p[-2:] in bg and len(p) <= MAX_DEPTH and "_" not in p)]
    while st["todo"]:
        p = st["todo"].pop(0)
        if p in done:
            continue
        txt = fetch(c, p)
        topics |= save_article(txt)
        found = [m.group(1) for l in txt.splitlines() if (m := TOPIC_RE.match(l))]
        topics |= set(found)
        if re.search(r"Количество других найденных разделов", txt):
            st["todo"] = children(p, bg) + st["todo"]       # слишком много: глубже
        done.add(p)
        st["done"], st["topics"] = sorted(done), sorted(topics)
        json.dump(st, open(INDEX, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"{p}: +{len(found)}, всего тем {len(topics)}, в очереди {len(st['todo'])}", flush=True)


def known_and_refs():
    """Ключевые слова скачанных статей и все темы из их «Смотрите также»."""
    have, refs = set(), set()
    for f in os.listdir(OUT):
        txt = open(os.path.join(OUT, f), encoding="utf-8").read()
        have |= header_keys(txt)
        for m in re.finditer(r"Смотрите (?:также|так же):\s*(.+?)(?:\n\S|\Z)", txt, re.S):
            refs |= {t.strip(".").upper() for t in re.split(r"[,\s]+", m.group(1)) if t.strip(".")}
    return have, {r for r in refs if r.replace("_", "").isalpha()}


def fetch_all():
    st = load()
    c = FileClient()
    tried = set()
    while True:                                   # по оглавлению и ссылкам, пока появляются новые темы
        have, refs = known_and_refs()
        todo = sorted((set(st["topics"]) | refs) - have - tried)
        if not todo:
            break
        print(f"статей скачать: {len(todo)}", flush=True)
        for t in todo:
            if t in have:
                continue
            tried.add(t)
            have |= save_article(fetch(c, t))
            print(t, flush=True)
    print(f"готово: статей {len(os.listdir(OUT))}, ключевых слов {len(have)}", flush=True)


if __name__ == "__main__":
    {"index": index, "fetch": fetch_all}[sys.argv[1] if len(sys.argv) > 1 else "index"]()
