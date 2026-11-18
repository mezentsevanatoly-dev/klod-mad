"""Все реплики пользователя дословно из сессий Claude Code (jsonl) -> таблица user_phrases в data/game.db и data/user_phrases.md.
  python tools/save_user_phrases.py            все сессии проекта
Берутся только сообщения пользователя (не результаты инструментов, не системные вставки).
"""
import glob
import json
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(HERE, "data", "game.db")
OUT = os.path.join(HERE, "data", "user_phrases.md")
PROJ = os.path.expanduser(r"~\.claude\projects")
SRCS = [os.path.join(PROJ, d) for d in os.listdir(PROJ) if d.startswith("C--Users-User-Desktop")]      # все проекты на рабочем столе
SKIP = re.compile(r"^\s*(<system-reminder|<task-notification|<command-|\[SYSTEM|This session is being continued|Caveat:)", re.I)


def texts(msg):
    c = msg.get("content")
    if isinstance(c, str):
        yield c
    elif isinstance(c, list):
        for p in c:
            if isinstance(p, dict) and p.get("type") == "text":
                yield p.get("text", "")


def main():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS user_phrases (session TEXT, ts TEXT, text TEXT, PRIMARY KEY (session, ts, text))")
    n = 0
    lines = ["# Реплики пользователя (дословно, из всех сессий)\n"]
    for f in sorted([p for s in SRCS for p in glob.glob(os.path.join(s, "*.jsonl"))], key=os.path.getmtime):
        sid = os.path.basename(f)[:8]
        lines.append(f"\n## сессия {sid}\n")
        for raw in open(f, encoding="utf-8", errors="replace"):
            try:
                d = json.loads(raw)
            except Exception:
                continue
            if d.get("type") != "user" or d.get("isSidechain"):
                continue
            for t in texts(d.get("message", {})):
                t = t.strip()
                if not t or SKIP.match(t) or "tool_use_id" in t[:40]:
                    continue
                ts = d.get("timestamp", "")
                c.execute("INSERT OR IGNORE INTO user_phrases VALUES (?,?,?)", (sid, ts, t))
                lines.append(f"- [{ts[:16]}] {t}\n")
                n += 1
    c.commit()
    open(OUT, "w", encoding="utf-8").write("".join(lines))
    print("реплик:", n, "->", OUT)


if __name__ == "__main__":
    main()
