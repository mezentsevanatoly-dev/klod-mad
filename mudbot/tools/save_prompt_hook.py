"""Хук UserPromptSubmit: каждое сообщение пользователя дословно -> data/user_phrases_live.md и таблица user_phrases (session 'live').
Ничего не печатает и никогда не падает (код выхода 0), чтобы не мешать работе.
"""
import json
import os
import sqlite3
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", "replace")
        d = json.loads(raw)
        t = (d.get("prompt") or d.get("user_prompt") or "").strip()
        if not t or t.startswith("<") or t.startswith("[SYSTEM"):
            return
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        with open(os.path.join(HERE, "data", "user_phrases_live.md"), "a", encoding="utf-8") as f:
            f.write(f"- [{ts}] {t}\n")
        c = sqlite3.connect(os.path.join(HERE, "data", "game.db"), timeout=10)
        c.execute("CREATE TABLE IF NOT EXISTS user_phrases (session TEXT, ts TEXT, text TEXT, PRIMARY KEY (session, ts, text))")
        c.execute("INSERT OR IGNORE INTO user_phrases VALUES ('live', ?, ?)", (ts, t))
        c.commit()
        c.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()
    sys.exit(0)
