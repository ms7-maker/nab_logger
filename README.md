# Логирование взаимодействий (ДЗ)

Private-репозиторий для сдачи ДЗ по уроку логирования.

Содержит:
- `db_logger.py` — `DatabaseLogger` (SQLite, `get_stats()`, `export_to_csv`)
- `stats_handlers.py` — примеры вызовов `/stats` и `/report`
- `samples/logs_redacted.csv` — обезличенные записи логов
- `samples/interactions_redacted.db` — та же выборка в SQLite

Telegram `user_id` / username в samples заменены на демо-значения.

## Быстрая проверка метрик

```powershell
cd nab_logger
python scripts/make_sample_logs.py   # если нужно пересобрать samples
python stats_handlers.py
```

## Связь с проектом

Логгер используется в боте `new_assist_bot` (запись диалогов + `/report`).  
Сайт портфолио / бот на VPS: IP:порт или домен указываются отдельно при сдаче ДЗ.
