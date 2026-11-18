"""Старт сессии по Маду (запускается хуком SessionStart): собирает ВСЮ память в один файл и печатает обязательные правила.

  data/МАД_ВСЯ_ПАМЯТЬ.md = MEMORY.md + ВСЕ файлы памяти целиком + user_teachings.md (каждый раз заново, всегда актуален)
Печать в stdout попадает в контекст новой сессии.
"""
import glob
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEM = os.path.expanduser(r"~\.claude\projects\C--Users-User-Desktop---------\memory")
TEACH = os.path.join(os.path.dirname(HERE), "_архив_мад", "skills", "mud", "reference", "user_teachings.md")
OUT = os.path.join(HERE, "data", "МАД_ВСЯ_ПАМЯТЬ.md")

RULES = """\
=== МАД: ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА (пользователь Эсхирд; нарушал их многократно, потратил недельный лимит и 1,5 часа на одно и то же) ===
1. СНАЧАЛА ЧИТАТЬ, ПОТОМ ДЕЙСТВОВАТЬ: прочитай ПОЛНОСТЬЮ файл {out} (Read кусками offset/limit до самого конца), и только потом отвечай.
2. НЕ ЗНАЕШЬ — СПРОСИ ОДНИМ КОРОТКИМ ВОПРОСОМ. Не гадай, не «чини симптомы» новыми скриптами. Перед вопросом: grep по data/user_phrases.md (все реплики пользователя дословно).
3. НИЧЕГО НЕ ЗАПУСКАТЬ В ИГРЕ (скрипты, обходы, replay, walk), пока пользователь не сказал что именно. Он дважды подряд отклонил мои запуски: после отказа — только по прямому слову.
4. У пользователя есть ЛОГИ его прохождений (Клод мад\\JMC\\*) — это источник истины. Повторять ЕГО команды с чистого начала сегмента, в той же стартовой позиции. Не строить свои обходы/графы/сверки. Двери и лут делают триггеры бота (mudbot/triggers.txt), их команды из лога не дублировать.
5. Статус квестов — команда `зада` в зоне. Квестовых NPC не бить до сдачи; NPC-спутника (отшельник) не уводить из его территории; при перезаходе группа распадается.
6. `путь` — один раз и только в городах; из зон выходить пешком (не реколлом); спидволки писать ТУДА И ОБРАТНО; карты — Mapper (mapper_rooms) + rooms из MSDP.
7. Логин и пароль вводит ТОЛЬКО пользователь (бот запускать во вкладке Terminal «bot»: python -X utf8 run_school.py). Никогда не читать и не повторять пароли.
8. Не убивать все python-процессы: стопать только свои PID.
9. Токены: короткие ответы, минимум вызовов, без пересказа очевидного и без «умных» проверок, которых не просили.
10. Каждое замечание пользователя — сразу в память (feedback_*.md) и в user_phrases; он не должен повторять одно и то же.
Веб-интерфейс: python -X utf8 webui/server.py → http://127.0.0.1:8765. База: data/game.db. Все реплики: data/user_phrases.md.
=== конец правил ===
"""


def main():
    try:                                                          # заодно обновить архив всех реплик пользователя из сохранённых сессий
        import contextlib
        import io
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import save_user_phrases
        with contextlib.redirect_stdout(io.StringIO()):
            save_user_phrases.main()
    except Exception:
        pass
    parts = []
    files = [os.path.join(MEM, "MEMORY.md")] + sorted(f for f in glob.glob(os.path.join(MEM, "*.md")) if os.path.basename(f) != "MEMORY.md")
    for f in files:
        try:
            parts.append(f"\n\n########## {os.path.basename(f)} ##########\n" + open(f, encoding="utf-8-sig").read())
        except OSError:
            pass
    if os.path.exists(TEACH):
        parts.append("\n\n########## user_teachings.md (выжимка учений пользователя) ##########\n" + open(TEACH, encoding="utf-8-sig").read())
    text = f"# ВСЯ ПАМЯТЬ ПО МАДУ (собрано {time.strftime('%d.%m.%Y %H:%M')}; файлов памяти: {len(files)})\n" + "".join(parts)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(text)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(RULES.format(out=OUT))
    print(f"Файл собран: {OUT} ({len(text) // 1024} КБ, {len(files)} файлов памяти). Читай целиком.")


if __name__ == "__main__":
    main()
