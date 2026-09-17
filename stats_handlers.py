"""
Фрагменты вызовов статистики и отчётов для ДЗ по логированию.

В учебном боте (модуль 5): команда /stats → DatabaseLogger.get_stats().
В new_assist_bot: команда /report → Excel из логов (+ get_stats в скрипте экспорта).
"""

from __future__ import annotations

# --- /stats (паттерн из telegram-бота урока) ---

STATS_COMMAND_EXAMPLE = '''
async def stats_command(self, update, context):
    """Обработчик команды /stats — метрики из DatabaseLogger."""
    log_stats = self.logger.get_stats()
    stats_message = f"""
СТАТИСТИКА:

Логи:
  • Всего запросов: {log_stats['total_requests']}
  • Из кеша: {log_stats['cached_requests']}
  • Уникальных пользователей: {log_stats['unique_users']}
  • Среднее время ответа: {log_stats['avg_response_time_ms']:.0f} мс
"""
    await update.message.reply_text(stats_message.strip())
'''

# --- /report (паттерн из new_assist_bot/bot/handlers.py) ---

REPORT_COMMAND_EXAMPLE = '''
async def handle_report(update, context):
    """Админ: Excel из логов → письмо / файл (см. scripts/export_logs_email.py)."""
    # внутри job():
    #   db = DatabaseLogger(path)
    #   stats = db.get_stats()
    #   path = db.export_to_xlsx(...)  # или export_to_csv
    await update.message.reply_text("Собираю отчёт из логов…")
'''


def format_stats_text(log_stats: dict) -> str:
    """Готовый текст метрик — удобно вызвать из /stats или консоли."""
    avg = log_stats.get("avg_response_time_ms") or 0
    return (
        "СТАТИСТИКА ЛОГОВ:\n"
        f"  • Всего запросов: {log_stats.get('total_requests', 0)}\n"
        f"  • Из кеша: {log_stats.get('cached_requests', 0)}\n"
        f"  • Уникальных пользователей: {log_stats.get('unique_users', 0)}\n"
        f"  • По источникам: {log_stats.get('by_source', {})}\n"
        f"  • Среднее время ответа: {avg:.0f} мс"
    )


if __name__ == "__main__":
    from pathlib import Path

    from db_logger import DatabaseLogger

    sample_db = Path(__file__).parent / "samples" / "interactions_redacted.db"
    if not sample_db.exists():
        print("Нет samples/interactions_redacted.db — сначала запустите scripts/make_sample_logs.py")
    else:
        db = DatabaseLogger(str(sample_db))
        print(format_stats_text(db.get_stats()))
