"""Хук: сессия узнаёт, что файл, которым она пользовалась, изменили (другая сессия, JMC, пользователь).

Подключён в Клод мад\\.claude\\settings.json:
  PreToolUse  (PowerShell|Bash)  -> pre   : перед командой запомнить чужие изменения (чтобы не спутать со своими)
  PostToolUse (все инструменты)  -> post  : Read/Edit/Write — файл в «использованных»; Edit/Write — запись в журнал;
                                             после PowerShell/Bash свои изменения не считаются чужими; выдать уведомление
  UserPromptSubmit               -> check : выдать уведомление
Данные: mudbot\\data\\session_files\\<сессия>.json (файл -> время изменения), changes.jsonl (кто что менял).
Правило: ПРАВИЛА\\СЕССИИ.md"""
import json, os, sys, time

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "session_files")
CHANGES = os.path.join(DATA, "changes.jsonl")
SKIP_EXT = (".log", ".lock", ".tmp", ".pyc")
SKIP_PARTS = ("\\logs\\", "\\claude\\", "\\.claude\\", "\\session_files\\", "\\__pycache__\\")
READ_TOOLS = ("Read",)
WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
SHELL_TOOLS = ("PowerShell", "Bash")


def norm(p):
    return os.path.normcase(os.path.abspath(p))


def skip(p):
    low = p.lower()
    return low.endswith(SKIP_EXT) or any(s in low for s in SKIP_PARTS)


def mtime(p):
    try:
        return os.path.getmtime(p)
    except OSError:
        return None


def load(sid):
    try:
        with open(os.path.join(DATA, sid + ".json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"files": {}, "pending": []}


def save(sid, st):
    os.makedirs(DATA, exist_ok=True)
    tmp = os.path.join(DATA, sid + ".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False)
    os.replace(tmp, os.path.join(DATA, sid + ".json"))


def who_changed(path, since, sid):
    """Сессии (не эта), которые меняли файл после since — по журналу Edit/Write."""
    out = []
    try:
        with open(CHANGES, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("file") == path and (r.get("m") or 0) > since and r.get("session") != sid:
                    out.append(r.get("session", "?")[:8])
    except OSError:
        pass
    return sorted(set(out))


def collect(sid, st):
    """Найти использованные файлы, изменённые не этой сессией; обновить их время."""
    found = []
    for path, old in list(st["files"].items()):
        now = mtime(path)
        if now is None:
            if old is not None:
                found.append((path, "удалён", []))
                st["files"][path] = None
            continue
        if old is None or now > old + 0.5:
            found.append((path, time.strftime("%d.%m %H:%M:%S", time.localtime(now)), who_changed(path, old or 0, sid)))
            st["files"][path] = now
    return found


def message(items):
    lines = ["ФАЙЛЫ, КОТОРЫМИ ЭТА СЕССИЯ ПОЛЬЗОВАЛАСЬ, ИЗМЕНЕНЫ СНАРУЖИ (другая сессия, JMC или пользователь). Перечитай их перед работой с ними:"]
    for path, when, who in items:
        src = ("сессия " + ", ".join(who)) if who else "не через Edit/Write другой сессии (JMC, скрипт или пользователь)"
        lines.append("- %s — %s; %s" % (path, when, src))
    return "\n".join(lines)


def emit(event, items):
    if not items:
        return
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": message(items)}}, ensure_ascii=False))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    try:
        inp = json.loads(sys.stdin.read() or "{}")
    except Exception:
        inp = {}
    sid = inp.get("session_id") or "unknown"
    st = load(sid)
    st.setdefault("files", {}); st.setdefault("pending", [])
    tool = inp.get("tool_name", "")
    ti = inp.get("tool_input") or {}

    if mode == "pre":                                   # перед командой оболочки: чужое — в отложенные
        st["pending"] += collect(sid, st)
        save(sid, st)
        return

    if mode == "post":
        if tool in SHELL_TOOLS:                         # свои изменения командой — не чужие
            for path in st["files"]:
                st["files"][path] = mtime(path)
        p = ti.get("file_path") or ti.get("notebook_path")
        if p and (tool in READ_TOOLS or tool in WRITE_TOOLS):
            path = norm(p)
            if not skip(path):
                st["files"][path] = mtime(path)
                if tool in WRITE_TOOLS:
                    os.makedirs(DATA, exist_ok=True)
                    with open(CHANGES, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"t": time.time(), "m": st["files"][path], "session": sid, "file": path}, ensure_ascii=False) + "\n")

    items = st["pending"] + collect(sid, st)
    st["pending"] = []
    save(sid, st)
    emit("PostToolUse" if mode == "post" else "UserPromptSubmit", items)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass                                            # хук не должен мешать работе
